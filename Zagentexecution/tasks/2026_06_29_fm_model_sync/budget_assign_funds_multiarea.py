"""Load fund-level ENTR/B1 disponible for 6 specific funds into D01 for FY2026 (latest-year P01 amount)."""
import sys, datetime
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
from pyrfc import ABAPApplicationError
MODE=sys.argv[1] if len(sys.argv)>1 else 'dry'
YEAR='2026'
AREAS=['IBE','ICBA','ICTP','IIEP','MGIE','UBO','UIL','UIS','UNES']
FUNDS=['196EAR4042','650RER0008','538GLO5000','301EGY4072','469GLO2000','465BRZ0002']
TVAL=[f'TVAL{i:02d}' for i in range(1,17)]
def num(s):
    s=(s or '').strip(); return (-float(s[:-1]) if s.endswith('-') else float(s)) if s else 0.0
def read(c,tab,fl,where):
    try:
        res=c.call('RFC_READ_TABLE',QUERY_TABLE=tab,FIELDS=[{'FIELDNAME':x} for x in fl],OPTIONS=[{'TEXT':where}],ROWCOUNT=0)
    except ABAPApplicationError as e: return []
    m=res['FIELDS']; return [{x['FIELDNAME']:r['WA'][int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m} for r in res['DATA']]
def fikrs_of(c,f):
    for a in AREAS:
        if read(c,'FMFINCODE',['TYPE'],f"FIKRS = '{a}' AND FINCODE = '{f}'"): return a
    return None
def main():
    p=get_connection('P01'); d=get_connection('D01'); today=datetime.date.today().strftime('%Y%m%d')
    for F in FUNDS:
        fk=fikrs_of(p,F)
        lines=[r for r in read(p,'FMBL',['FISCYEAR','FUNDSCTR','CMMTITEM','FUNCAREA','BUDCAT','TCURR']+TVAL,f"FUND = '{F}' AND PROCESS = 'ENTR'")
               if r.get('BUDCAT') is not None]
        b1=[r for r in read(p,'FMBL',['FISCYEAR','FUNDSCTR','CMMTITEM','FUNCAREA','BUDCAT','VALTYPE','BUDTYPE','TCURR']+TVAL,f"FUND = '{F}' AND PROCESS = 'ENTR'")
            if r.get('VALTYPE')=='B1' and r.get('BUDTYPE')=='3000']
        if not b1: print(f"{F} [{fk}]: no ENTR/B1 in P01 -> skip"); continue
        latest=max(r['FISCYEAR'] for r in b1)
        use=[r for r in b1 if r['FISCYEAR']==latest]
        # already has FY2026 ENTR?
        have=read(d,'FMBL',['DOCNR'],f"FUND = '{F}' AND PROCESS = 'ENTR' AND FISCYEAR = '{YEAR}'")
        items=[]; n=0
        for r in use:
            amt=sum(num(r[t]) for t in TVAL)
            if abs(amt)<0.01: continue
            n+=1
            items.append({'ITEM_NUM':f'{n:03d}','FISC_YEAR':YEAR,'BUDCAT':r['BUDCAT'] or '9F','BUDTYPE':'3000',
                'FUND':F,'FUNDS_CTR':r['FUNDSCTR'],'CMMT_ITEM':r['CMMTITEM'],'FUNC_AREA':r['FUNCAREA'],
                'VALTYPE':'B1','TRANS_CURR':r['TCURR'] or 'USD','TOTAL_AMOUNT':abs(amt),'DISTKEY':'1'})
        tot=sum(i['TOTAL_AMOUNT'] for i in items)
        tag='SKIP(has FY26)' if have else ('WOULD post' if MODE!='run' else 'POSTING')
        print(f"{F} [{fk}] latest={latest} -> {tag}: {tot:,.2f} ({len(items)} lines: {[(i['FUNDS_CTR'],i['CMMT_ITEM']) for i in items]})")
        if have or MODE!='run' or not items: continue
        hdr={'FM_AREA':fk,'VERSION':'000','DOCDATE':today,'DOCTYPE':'2000','PROCESS':'ENTR','DOCSTATE':'1'}
        r=d.call('BAPI_0050_CREATE',HEADER_DATA=hdr,ITEM_DATA=items,TESTRUN=' ')
        errs=[m for m in r.get('RETURN',[]) if m.get('TYPE') in 'EAX']
        if errs: d.call('BAPI_TRANSACTION_ROLLBACK'); print(f"    ERR {[m['MESSAGE'][:60] for m in errs]}")
        else:
            d.call('BAPI_TRANSACTION_COMMIT',WAIT='X')
            av=read(d,'FMAVCT',['RFUND'],f"RFUND = '{F}'")
            print(f"    POSTED doc={r.get('DOCUMENTNUMBER')}/{r.get('DOCUMENTYEAR')} | FMAVCT rows={len(av)}")
    p.close(); d.close()
if __name__=="__main__": main()

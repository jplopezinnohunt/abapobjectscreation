"""
Create the cost-recovery DISPONIBLE assignment (ENTR budget entry) in <TARGET> for the CR test funds,
replicating P01's ENTR / VALTYPE=B1 / BUDTYPE=3000 lines via BAPI_0050_CREATE (FMBB budget doc).
Usage: python budget_assign_entr.py <TARGET> <test|commit> [FUND]

Reads each fund's ENTR lines from P01 FMBL (exact FUNDSCTR + CMMTITEM + FISCYEAR + amount), then posts
one budget entry document per fund in the target. ASSIGNMENT only (process ENTR) — recovery (COSD/CORV)
is a separate process, not posted here.
Header params verified from P01 doc 2000032048: DOCTYPE=2000, PROCESS=ENTR, VERSION=000, BUDCAT=9F.
"""
import sys, datetime
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
MODE   = sys.argv[2] if len(sys.argv) > 2 else "test"
ONLY   = sys.argv[3] if len(sys.argv) > 3 else None
FUNDS  = [ONLY] if ONLY else ['567KEN2000','537RAF4006','218MAR2000','263KEN5000','235MAG5003']
TVAL=[f'TVAL{i:02d}' for i in range(1,17)]
def num(s):
    s=(s or '').strip(); return (-float(s[:-1]) if s.endswith('-') else float(s)) if s else 0.0

def p01_entr(p, fund):
    fl=['FISCYEAR','FUNDSCTR','CMMTITEM','FUNCAREA','BUDCAT','VALTYPE','BUDTYPE','TCURR']+TVAL
    res=p.call('RFC_READ_TABLE',QUERY_TABLE='FMBL',FIELDS=[{'FIELDNAME':x} for x in fl],
               OPTIONS=[{'TEXT':f"FUND = '{fund}' AND PROCESS = 'ENTR'"}],ROWCOUNT=0)
    m=res['FIELDS']; out=[]
    for r in res['DATA']:
        wa=r['WA']; rec={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        rec['_AMT']=round(sum(num(rec[t]) for t in TVAL),2)
        if rec['VALTYPE']=='B1' and rec['BUDTYPE']=='3000' and abs(rec['_AMT'])>0.001:
            out.append(rec)
    return out

def post(t, fund, lines, testrun, today):
    items=[]; n=0
    for r in lines:
        n+=1
        items.append({'ITEM_NUM':f'{n:03d}','FISC_YEAR':r['FISCYEAR'],'BUDCAT':r['BUDCAT'] or '9F','BUDTYPE':'3000',
                      'FUND':fund,'FUNDS_CTR':r['FUNDSCTR'],'CMMT_ITEM':r['CMMTITEM'],
                      'FUNC_AREA':r['FUNCAREA'],'VALTYPE':'B1','TRANS_CURR':r['TCURR'] or 'USD',
                      'TOTAL_AMOUNT':abs(r['_AMT']),'DISTKEY':'1'})
    hdr={'FM_AREA':'UNES','VERSION':'000','DOCDATE':today,'DOCTYPE':'2000','PROCESS':'ENTR','DOCSTATE':'1'}
    kw=dict(HEADER_DATA=hdr,ITEM_DATA=items)
    kw['TESTRUN']='X' if testrun else ' '
    r=t.call('BAPI_0050_CREATE',**kw)
    return r

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    today=datetime.date.today().strftime('%Y%m%d')
    for fund in FUNDS:
        # idempotency: skip if target already has ENTR/B1/3000 for this fund
        chk=t.call('RFC_READ_TABLE',QUERY_TABLE='FMBL',FIELDS=[{'FIELDNAME':'DOCNR'}],
                   OPTIONS=[{'TEXT':f"FUND = '{fund}' AND PROCESS = 'ENTR'"}],ROWCOUNT=1)
        if chk['DATA'] and MODE=='commit':
            print(f"\n=== {fund}: already has ENTR in {TARGET} -> SKIP ==="); continue
        lines=p01_entr(p,fund)
        tot=sum(abs(r['_AMT']) for r in lines)
        print(f"\n=== {fund}  ENTR lines={len(lines)}  total={tot:,.2f} ({MODE}) ===")
        for r in lines: print(f"   yr{r['FISCYEAR']} FC={r['FUNDSCTR']} CI={r['CMMTITEM']} {r['TCURR']} {abs(r['_AMT']):,.2f}")
        res=post(t,fund,lines,MODE!='commit',today)
        ret=res.get('RETURN',[])
        errs=[m for m in ret if m.get('TYPE') in ('E','A','X')]
        if errs:
            for m in errs[:5]: print(f"   [{m['TYPE']}] {m.get('ID')}{m.get('NUMBER')}: {m.get('MESSAGE')}")
            if MODE=='commit': t.call('BAPI_TRANSACTION_ROLLBACK')
        elif MODE=='commit':
            cc=t.call('BAPI_TRANSACTION_COMMIT',WAIT='X')
            print(f"   POSTED  doc={res.get('DOCUMENTNUMBER')}/{res.get('DOCUMENTYEAR')}  commit={cc.get('RETURN',{}).get('TYPE') or 'OK'}")
        else:
            print(f"   TEST OK  msgs={[m.get('MESSAGE','')[:50] for m in ret][:2]}")
    p.close(); t.close()

if __name__=="__main__": main()

"""
Sync a FUND FAMILY by FINCODE prefix  P01 -> <TARGET>  (create missing + reconcile drift to P01).
Usage: python fund_family_sync.py <TARGET> <PREFIX>   e.g.  D01 633CRP9   (the Cost-Recovery credit funds)

Built s093 to fix the CRP credit funds (633CRP9*) whose validity was expired in D01 (e.g. 9000/9003
expired 2017/2018 vs P01 2027) — these are the cover/credit funds for the cost-recovery AVC mechanism.
Same engine as fund_sync/fund_reconcile: raw-table source, date-sanitize, FM_FUND_CREATE/CHANGE_RFC,
TESTRUN=' ' + COMMIT='X', verify by re-read. Some CHANGEs are refused by SAP if D01 budget exists and
the change would shorten validity (benign — leaves D01 longer than P01).
"""
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "633CRP9"
FIKRS  = sys.argv[3] if len(sys.argv) > 3 else "UNES"
DATA=['SPONSOR','FINUSE','PROFIL','KZBST','AUGRP','DATAB','DATBIS','PERIV','TYPE','DATE_EXP','DATE_CAN',
      'LOGSYSTEM','DECKUNG','ZZIBF','ZZOUTPUT','STR_ID','FDSUB1','FDSUB2']

def raw(c, where, flds):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINCODE',FIELDS=[{'FIELDNAME':x} for x in ['FINCODE']+flds],
               OPTIONS=[{'TEXT':where}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; dd={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[dd['FINCODE']]=dd
    return out

def txt(c, where):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINT',FIELDS=[{'FIELDNAME':'FINCODE'},{'FIELDNAME':'BEZEICH'},{'FIELDNAME':'BESCHR'}],
               OPTIONS=[{'TEXT':where}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; dd={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[dd['FINCODE']]=dd
    return out

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    W=f"FIKRS = '{FIKRS}' AND FINCODE LIKE '{PREFIX}%'"
    pr=raw(p,W,DATA); pt=txt(p,W+" AND SPRAS = 'E'"); dr=raw(t,W,['DATBIS'])
    print(f"P01 {PREFIX}* funds = {len(pr)}  | {TARGET} has = {len(dr)}")
    created=changed=fail=0; fails=[]
    for f,row in sorted(pr.items()):
        isd={k:row.get(k,'') for k in DATA}
        for dk in ('DATAB','DATBIS','DATE_EXP','DATE_CAN'):
            if isd.get(dk)=='00000000': isd[dk]=''
        tt=pt.get(f,{}); ist={'SPRAS':'E','BEZEICH':tt.get('BEZEICH',''),'BESCHR':tt.get('BESCHR','')}
        exists=f in dr; fn='FM_FUND_CHANGE_RFC' if exists else 'FM_FUND_CREATE_RFC'
        try:
            r=t.call(fn,I_FM_AREA=FIKRS,I_FUND=f,IS_FUND_DATA=isd,IS_FUND_TEXT=ist,I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
            errs=[m['MESSAGE'] for m in r.get('ET_MESSAGES',[]) if m['TYPE'] in 'EAX']
            if errs: fail+=1; fails.append((f,errs[0]))
            elif exists: changed+=1
            else: created+=1
        except Exception as e: fail+=1; fails.append((f,str(e)[:50]))
    print(f"created={created} changed={changed} failed={fail}")
    for f,e in fails: print(f"  {f}: {e}")
    dv=raw(t,W,['DATBIS'])
    bad=[(f,pr[f]['DATBIS'],dv.get(f,{}).get('DATBIS','MISS')) for f in pr if dv.get(f,{}).get('DATBIS')!=pr[f]['DATBIS']]
    print("DATBIS still != P01:", bad or "NONE - all match P01")
    p.close(); t.close()

if __name__=="__main__": main()

"""
Reconcile FUND field drift  P01 -> <TARGET>  for the CURRENT BIENNIUM (C5/43).
Makes funds that exist in BOTH but differ identical to P01 (field-level), via FM_FUND_CHANGE_RFC.
Usage: python fund_reconcile.py D01   (or V01)

Scope = funds in YTFM_FUND_C5 C5_ID='43' present in both systems.
Channel = FM_FUND_CHANGE_RFC (I_FLG_TESTRUN=' ' + I_FLG_COMMIT='X' — same TESTRUN-default gotcha).
NOTE: BLANK_BPD is in FMFINCODE but NOT in FMFUND_DATA -> cannot be set via this FM (reported, not fixed).
"""
import sys, sqlite3, time
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
AREAS=['IBE','ICBA','ICTP','IIEP','MGIE','UBO','UIL','UIS','UNES']
DATA_FLDS=['SPONSOR','FINUSE','PROFIL','KZBST','AUGRP','DATAB','DATBIS','PERIV','TYPE',
           'DATE_EXP','DATE_CAN','LOGSYSTEM','DECKUNG','ZZIBF','ZZOUTPUT','STR_ID','FDSUB1','FDSUB2']
CMP=[f for f in DATA_FLDS if f!='LOGSYSTEM']  # functional fields the FM can set

def rows(c,a,flds=CMP):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINCODE',FIELDS=[{'FIELDNAME':x} for x in ['FINCODE']+flds],
               OPTIONS=[{'TEXT':f"FIKRS = '{a}'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[d['FINCODE']]=d
    return out

def fund_text(c,a):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINT',FIELDS=[{'FIELDNAME':'FINCODE'},{'FIELDNAME':'BEZEICH'},{'FIELDNAME':'BESCHR'}],
               OPTIONS=[{'TEXT':f"FIKRS = '{a}' AND SPRAS = 'E'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[d['FINCODE']]=d
    return out

def main():
    g=sqlite3.connect(GOLD); p=get_connection('P01'); t=get_connection(TARGET)
    active={}
    for a,f in g.execute("SELECT FIKRS,FINCODE FROM ytfm_fund_c5 WHERE C5_ID='43'"):
        active.setdefault(a.strip(),set()).add(f.strip())
    total_fixed=0; total_drift=0; fail=0
    for a in AREAS:
        if a not in active: continue
        pr=rows(p,a); dr=rows(t,a)
        both=active[a] & set(pr) & set(dr)
        drift=[f for f in both if any(pr[f][k]!=dr[f][k] for k in CMP)]
        total_drift+=len(drift)
        if not drift: continue
        # source full data + text from RAW P01 tables (no I_DATE validity dependency)
        praw=rows(p,a,DATA_FLDS); ptxt=fund_text(p,a)
        print(f"[{a}] drift funds = {len(drift)}")
        for f in drift:
            isd={k:praw[f].get(k,'') for k in DATA_FLDS}
            for dk in ('DATAB','DATBIS','DATE_EXP','DATE_CAN'):   # pyrfc rejects '00000000' for DATS
                if isd.get(dk)=='00000000': isd[dk]=''
            tt=ptxt.get(f,{})
            ist={'SPRAS':'E','BEZEICH':tt.get('BEZEICH',''),'BESCHR':tt.get('BESCHR','')}
            try:
                r=t.call("FM_FUND_CHANGE_RFC",I_FM_AREA=a,I_FUND=f,IS_FUND_DATA=isd,IS_FUND_TEXT=ist,
                       I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
                errs=[m['MESSAGE'] for m in r.get('ET_MESSAGES',[]) if m['TYPE'] in 'EAX']
                if errs: fail+=1; print(f"   ERR {f}: {errs[:1]}")
            except Exception as e:
                fail+=1; print(f"   FAIL {f}: {str(e)[:60]}"); continue
        # verify this area
        dr2=rows(t,a)
        still=[f for f in drift if any(pr[f][k]!=dr2[f][k] for k in CMP)]
        total_fixed += len(drift)-len(still)
        print(f"   fixed={len(drift)-len(still)}  still-drift={len(still)} {still[:5]}")
        time.sleep(0.3)
    print(f"\nRECONCILE C5/43: drift found={total_drift}  fixed={total_fixed}  failed={fail}")
    g.close(); p.close(); t.close()

if __name__=="__main__": main()

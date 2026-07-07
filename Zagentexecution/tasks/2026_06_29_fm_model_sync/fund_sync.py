"""
FM FUND master sync  P01 -> <TARGET>  (TARGET = D01 default, or V01)  scope = biennium C5/43.
Reusable: `python fund_sync.py D01`  or  `python fund_sync.py V01`.

Method (verified s093 2026-06-29):
  source P01 read  : FM_FUND_GET_DETAIL_RFC  (full master, gold cache is key-only -> not a write source)
  target write     : FM_FUND_CREATE_RFC  with I_FLG_TESTRUN=' ' AND I_FLG_COMMIT='X'
  CRITICAL gotcha  : I_FLG_TESTRUN defaults to 'X' -> omit it = silent no-op (ET_MESSAGES empty).
                     ET_MESSAGES is empty even on a real create -> raw read-back verify is MANDATORY.
  scope            : funds in YTFM_FUND_C5 where C5_ID='43' (2026-2027), missing in target.
"""
import sys, sqlite3, time
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
AREAS = ['IBE','ICBA','ICTP','IIEP','MGIE','UBO','UIL','UIS','UNES']
DATA_FLDS = ['SPONSOR','FINUSE','PROFIL','KZBST','AUGRP','DATAB','DATBIS','PERIV','TYPE',
             'DATE_EXP','DATE_CAN','LOGSYSTEM','DECKUNG','ZZIBF','ZZOUTPUT','STR_ID','FDSUB1','FDSUB2']
TEXT_FLDS = ['SPRAS','BEZEICH','BESCHR']

def target_funds(t, area):
    res = t.call("RFC_READ_TABLE", QUERY_TABLE="FMFINCODE", FIELDS=[{'FIELDNAME':'FINCODE'}],
                 OPTIONS=[{'TEXT':f"FIKRS = '{area}'"}], ROWCOUNT=0)
    m=res['FIELDS'][0]; o=int(m['OFFSET']); l=int(m['LENGTH'])
    return set(row['WA'][o:o+l].strip() for row in res['DATA'])

def raw_rows(c, area, flds):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINCODE',FIELDS=[{'FIELDNAME':x} for x in ['FINCODE']+flds],
               OPTIONS=[{'TEXT':f"FIKRS = '{area}'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[d['FINCODE']]=d
    return out

def fund_text(c, area):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINT',FIELDS=[{'FIELDNAME':'FINCODE'},{'FIELDNAME':'BEZEICH'},{'FIELDNAME':'BESCHR'}],
               OPTIONS=[{'TEXT':f"FIKRS = '{area}' AND SPRAS = 'E'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[d['FINCODE']]=d
    return out

def main():
    g=sqlite3.connect(GOLD); p=get_connection('P01'); t=get_connection(TARGET)
    print(f"=== FUND SYNC P01 -> {TARGET} (scope C5/43) ===")
    active={}  # area -> set(fincode) in biennium 43
    for a,f in g.execute("SELECT FIKRS,FINCODE FROM ytfm_fund_c5 WHERE C5_ID='43'"):
        active.setdefault(a.strip(),set()).add(f.strip())
    total_created=total_fail=total_skip=0
    for area in AREAS:
        act=active.get(area,set())
        if not act: continue
        have=target_funds(t, area)
        todo=sorted(act-have)
        print(f"\n[{area}] active C5/43={len(act)}  {TARGET} has={len(act & have)}  to create={len(todo)}")
        if not todo: continue
        praw=raw_rows(p, area, DATA_FLDS); ptxt=fund_text(p, area)   # RAW source (no I_DATE validity dependency)
        for i,f in enumerate(todo,1):
            try:
                if f not in praw: total_fail+=1; print(f"   FAIL {f}: not in P01 FMFINCODE"); continue
                isd={k:praw[f].get(k,'') for k in DATA_FLDS}
                for dk in ('DATAB','DATBIS','DATE_EXP','DATE_CAN'):   # pyrfc rejects '00000000' for DATS
                    if isd.get(dk)=='00000000': isd[dk]=''
                tt=ptxt.get(f,{})
                ist={'SPRAS':'E','BEZEICH':tt.get('BEZEICH',''),'BESCHR':tt.get('BESCHR','')}
                r=t.call("FM_FUND_CREATE_RFC",I_FM_AREA=area,I_FUND=f,IS_FUND_DATA=isd,IS_FUND_TEXT=ist,
                       I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
                errs=[m['MESSAGE'] for m in r.get('ET_MESSAGES',[]) if m['TYPE'] in 'EAX']
                if errs: total_fail+=1; print(f"   ERR {f}: {errs[:1]}")
                else: total_created+=1
            except Exception as e:
                total_fail+=1; print(f"   FAIL {f}: {str(e)[:70]}")
            if i % 200 == 0:
                print(f"   {area}: {i}/{len(todo)} processed..."); time.sleep(0.2)
    # verify
    print("\n=== VERIFY gap C5/43 ===")
    rem=0
    for area in AREAS:
        act=active.get(area,set())
        if not act: continue
        have=target_funds(t, area)
        miss=len(act-have); rem+=miss
        if miss: print(f"  [{area}] still missing={miss}")
    print(f"\nDONE -> created={total_created} failed={total_fail}  | remaining C5/43 gap={rem}")
    g.close(); p.close(); t.close()

if __name__=="__main__": main()

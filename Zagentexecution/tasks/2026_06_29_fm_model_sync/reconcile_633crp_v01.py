"""Reconcile FUND validity/fields  P01 -> V01  for 633CRP* ONLY (existing funds; NO create).
Same method as the D01 sync: FM_FUND_CHANGE_RFC (I_FLG_TESTRUN=' ' + I_FLG_COMMIT='X').
Scope = funds FINCODE LIKE '633CRP%' present in BOTH P01 and V01 that differ. Missing funds are
NOT created (user directive). Read-back verify per area.
Usage: python reconcile_633crp_v01.py [--dry]   (target fixed = V01)
"""
import sys, time
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = "V01"
DRY = "--dry" in sys.argv
PREFIX = "633CRP"
DATA_FLDS=['SPONSOR','FINUSE','PROFIL','KZBST','AUGRP','DATAB','DATBIS','PERIV','TYPE',
           'DATE_EXP','DATE_CAN','LOGSYSTEM','DECKUNG','ZZIBF','ZZOUTPUT','STR_ID','FDSUB1','FDSUB2']
CMP=[f for f in DATA_FLDS if f!='LOGSYSTEM']   # functional fields the FM can set

def rows(c, flds=CMP):
    """All 633CRP* rows across every FM area (FINCODE LIKE), keyed (FIKRS,FINCODE)."""
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINCODE',
               FIELDS=[{'FIELDNAME':x} for x in ['FIKRS','FINCODE']+flds],
               OPTIONS=[{'TEXT':f"FINCODE LIKE '{PREFIX}%'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[(d['FIKRS'],d['FINCODE'])]=d
    return out

def fund_text(c):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFINT',
               FIELDS=[{'FIELDNAME':x} for x in ['FIKRS','FINCODE','BEZEICH','BESCHR']],
               OPTIONS=[{'TEXT':f"FINCODE LIKE '{PREFIX}%' AND SPRAS = 'E'"}],ROWCOUNT=0)
    m=res['FIELDS']; out={}
    for r in res['DATA']:
        wa=r['WA']; d={x['FIELDNAME']:wa[int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m}
        out[(d['FIKRS'],d['FINCODE'])]=d
    return out

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    print(f"=== RECONCILE 633CRP* validity  P01 -> {TARGET}  {'(DRY-RUN)' if DRY else '(LIVE WRITE)'} ===")
    pr=rows(p); dr=rows(t)
    both=sorted(set(pr) & set(dr))
    # VALIDITY-ONLY scope: only DATAB/DATBIS. Everything else (ZZOUTPUT, ZZIBF, ...) is left
    # untouched at V01's current value (preserve V01 test-data, CP-001/CP-002).
    VALID=['DATAB','DATBIS']
    drift=[k for k in both if any(pr[k][f]!=dr[k][f] for f in VALID)]
    print(f"P01 633CRP*={len(pr)}  {TARGET} 633CRP*={len(dr)}  in-both={len(both)}  differ-on-validity={len(drift)}")
    print("(surgical: only DATAB/DATBIS pushed; all other fields kept at V01 value)")
    if not drift:
        print("Nothing to reconcile."); p.close(); t.close(); return
    for k in drift:
        diffs=[f"{f}(P01={pr[k][f]!r} {TARGET}={dr[k][f]!r})" for f in VALID if pr[k][f]!=dr[k][f]]
        print(f"  {k[0]:6} {k[1]:12} -> {', '.join(diffs)}")
    if DRY:
        print(f"\nDRY-RUN: would FM_FUND_CHANGE_RFC (validity-only) on {len(drift)} funds. No writes."); p.close(); t.close(); return

    ttxt=fund_text(t); fixed=fail=0     # keep V01's OWN text (do not overwrite descriptions)
    print(f"\n--- writing {len(drift)} FM_FUND_CHANGE_RFC (validity-only) to {TARGET} ---")
    for i,k in enumerate(drift,1):
        fik,fin=k
        # BASE = V01 current data; override ONLY DATAB/DATBIS with P01. Everything else stays V01.
        isd={f:dr[k].get(f,'') for f in DATA_FLDS}
        isd['DATAB']=pr[k]['DATAB']; isd['DATBIS']=pr[k]['DATBIS']
        for dk in ('DATAB','DATBIS','DATE_EXP','DATE_CAN'):     # pyrfc rejects '00000000' for DATS
            if isd.get(dk)=='00000000': isd[dk]=''
        tt=ttxt.get(k,{})
        ist={'SPRAS':'E','BEZEICH':tt.get('BEZEICH',''),'BESCHR':tt.get('BESCHR','')}
        try:
            r=t.call("FM_FUND_CHANGE_RFC",I_FM_AREA=fik,I_FUND=fin,IS_FUND_DATA=isd,IS_FUND_TEXT=ist,
                     I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
            errs=[m['MESSAGE'] for m in r.get('ET_MESSAGES',[]) if m['TYPE'] in 'EAX']
            if errs: fail+=1; print(f"   ERR {fik}/{fin}: {errs[:1]}")
        except Exception as e:
            fail+=1; print(f"   FAIL {fik}/{fin}: {str(e)[:70]}")
        if i%50==0: print(f"   {i}/{len(drift)} processed..."); time.sleep(0.2)

    # read-back verify (ET_MESSAGES is empty even on success -> raw re-read is mandatory)
    dr2=rows(t)
    VALID=['DATAB','DATBIS']
    still=[k for k in drift if any(pr[k][f]!=dr2[k][f] for f in VALID)]
    fixed=len(drift)-len(still)
    print(f"\nDONE -> validity fixed={fixed}  still-drift={len(still)}  fm-errors={fail}")
    # confirm we did NOT disturb the preserved fields
    KEEP=[f for f in CMP if f not in VALID]
    disturbed=[k for k in drift if any(dr[k][f]!=dr2[k][f] for f in KEEP)]
    print(f"preserved-field check: {len(disturbed)} funds had a non-validity field change (expected 0)")
    for k in disturbed[:10]:
        ch=[f"{f}({dr[k][f]!r}->{dr2[k][f]!r})" for f in KEEP if dr[k][f]!=dr2[k][f]]
        print(f"   DISTURBED {k[0]}/{k[1]}: {', '.join(ch)}")
    if still:
        for k in still[:20]:
            diffs=[f"{f}(P01={pr[k][f]!r} {TARGET}={dr2[k][f]!r})" for f in VALID if pr[k][f]!=dr2[k][f]]
            print(f"   STILL {k[0]}/{k[1]}: {', '.join(diffs)}")
    p.close(); t.close()

if __name__=="__main__": main()

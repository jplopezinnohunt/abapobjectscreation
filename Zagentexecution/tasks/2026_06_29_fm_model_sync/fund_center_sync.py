"""
FM FUND CENTER master sync  P01 -> <TARGET>  (D01 default, or V01).
Reusable: `python fund_center_sync.py D01`  or  `python fund_center_sync.py V01`.

Method (verified s093 2026-06-29 — 135/135 to D01, gap=0):
  source P01 read : FM_FUNDS_CTR_GET_DETAILS_RFC (I_FLG_HIER=X, I_FLG_TEXT=X, I_LANGUAGE=E)
  target write    : FM_FUNDS_CTR_CREATE_RFC  with I_FLG_TESTRUN=' ' AND I_FLG_COMMIT='X'
  hierarchy       : IS_FUNDS_CTR_HIVARNT = {HIVARNT (from HISV, '0000'), PARENT_ST}
                    -> TOPOLOGICAL waves: a node is creatable only once its PARENT_ST exists in target.
  gotcha TESTRUN  : default 'X' -> must pass ' ' or it silently no-ops (ET_MESSAGES empty).
  gotcha BOSS     : strip BOSS_CODE/BOSSID/BOSSNAME/BOSSOT — responsible-person user may not exist in
                    target -> FM errors 'User name X does not exist'. Cosmetic for dev/validation.
  verify          : raw FMFCTR read-back per node (ET_MESSAGES empty even on real create).
"""
import sys, time
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
SKIP={'MANDT','FIKRS','FICTR','CTR_OBJNR','AENDAT','AENNAME','ERFDAT','ERFNAME',
      'BOSS_CODE','BOSSID','BOSSNAME','BOSSOT'}

def live_fc(c):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE='FMFCTR',FIELDS=[{'FIELDNAME':'FIKRS'},{'FIELDNAME':'FICTR'}],OPTIONS=[],ROWCOUNT=0)
    m=res['FIELDS']; s=set()
    for row in res['DATA']:
        wa=row['WA']; s.add(tuple(wa[int(f['OFFSET']):int(f['OFFSET'])+int(f['LENGTH'])].strip() for f in m))
    return s

def detail(p, fk, fc):
    r=p.call('FM_FUNDS_CTR_GET_DETAILS_RFC',I_FM_AREA=fk,I_FUNDS_CTR=fc,
             I_FLG_HIER='X',I_FLG_TEXT='X',I_LANGUAGE='E',I_DATE='20260601')
    return r.get('ES_FUNDS_CTR_DATA',{}), r.get('ES_FUNDS_CTR_TEXT',{}), r.get('ES_FUNDS_CTR_HISV',{})

def create(t, fk, fc, dat, txt, his):
    row={k:v for k,v in dat.items() if k not in SKIP and v!=''}
    row.setdefault('DATAB','19000101'); row.setdefault('DATBIS','99991231')
    trow={'DATAB':row['DATAB'],'DATBIS':row['DATBIS'],'SPRAS':'E',
          'BEZEICH':txt.get('BEZEICH',''),'BESCHR':txt.get('BESCHR','')}
    hiv={'HIVARNT':his.get('HIVARNT','0000') or '0000','PARENT_ST':his.get('PARENT_ST','').strip()}
    r=t.call('FM_FUNDS_CTR_CREATE_RFC',I_FM_AREA=fk,I_FUNDS_CTR=fc,
             IT_FUNDS_CTR_DATA=[row],IT_FUNDS_CTR_TEXT=[trow],IS_FUNDS_CTR_HIVARNT=hiv,
             I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
    return [m['MESSAGE'] for m in r.get('ET_MESSAGES',[]) if m['TYPE'] in 'EAX']

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    print(f"=== FUND CENTER SYNC P01 -> {TARGET} ===")
    have=live_fc(t); missing=sorted(live_fc(p)-have)
    print(f"Missing to create: {len(missing)}")
    info={(fk,fc):detail(p,fk,fc) for fk,fc in missing}
    parent={k:info[k][2].get('PARENT_ST','').strip() for k in missing}
    todo=set(missing); created=[]; failed=[]; wave=0
    while todo:
        wave+=1
        ready=[(fk,fc) for (fk,fc) in todo if not parent[(fk,fc)] or (fk,parent[(fk,fc)]) in have]
        if not ready:
            failed+=[(fk,fc,'parent unresolved') for fk,fc in todo]
            print(f"  wave {wave}: {len(todo)} STUCK (parent unresolved)"); break
        for fk,fc in ready:
            dat,txt,his=info[(fk,fc)]
            errs=create(t,fk,fc,dat,txt,his)
            chk=t.call('RFC_READ_TABLE',QUERY_TABLE='FMFCTR',FIELDS=[{'FIELDNAME':'FICTR'}],
                       OPTIONS=[{'TEXT':f"FIKRS = '{fk}' AND FICTR = '{fc}'"}],ROWCOUNT=0)
            if chk['DATA']: created.append((fk,fc)); have.add((fk,fc))
            else: failed.append((fk,fc,errs[:1]))
            todo.discard((fk,fc))
        print(f"  wave {wave}: +{len(ready)} -> created={len(created)} remaining={len(todo)}")
        time.sleep(0.3)
    print(f"\nDONE -> created={len(created)} failed={len(failed)}")
    if failed: print("  FAILED:", failed[:20])
    p.close(); t.close()

if __name__=="__main__": main()

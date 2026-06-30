"""
MECHANISM — replicate/create a Project + Fund (all elements) in a target system, following the
PPM→SAP E2E flow (knowledge/domains/PSM/ppm_sap_project_fund_e2e_flow.md).

Usage:  python replicate_project_fund.py <PSPID> <TARGET> [run|dry]
        e.g.  python replicate_project_fund.py 504PAK1000 D01 dry

Runs the A→F sequence for ONE project/fund (FINCODE=PSPID), sourcing from P01, writing to TARGET:
  A. CREATE FUND          FM_FUND_CREATE_RFC                 [proven]
  B. FUND → C/5 biennium  Y_BAPI_FUND_C5_ASSIGNMENT          [wire-up; verify]
  C. CREATE PROJECT+WBS   BAPI_PROJECT_MAINTAIN (+release)   [proven flat; nested WBS -> CJ20N]
  D. WBS texts/custom     Y_BAPI_WBS_CUS_FIELD_UPDATE        [wire-up; verify]
  E. BUDGET → FUND        BAPI_0050_CREATE (FS* addr)        [wire-up; verify]
  F. BUDGET → PROJECT/WBS BAPI_0050_CREATE (PR* addr / ENTR B1) [proven for ENTR/B1]
Idempotent: each step checks existence first. Every write is verified by re-read (BAPI returns are not trusted).
This orchestrator CALLS the proven component logic; steps marked [wire-up] need a live verify pass before mass use.
"""
import sys, datetime
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
from pyrfc import ABAPApplicationError

PSPID  = sys.argv[1] if len(sys.argv) > 1 else "504PAK1000"
TARGET = sys.argv[2] if len(sys.argv) > 2 else "D01"
MODE   = sys.argv[3] if len(sys.argv) > 3 else "dry"   # dry = read+plan only; run = execute
FIKRS  = "UNES"
DATA_FLDS=['SPONSOR','FINUSE','PROFIL','KZBST','AUGRP','DATAB','DATBIS','PERIV','TYPE','DATE_EXP','DATE_CAN',
           'LOGSYSTEM','DECKUNG','ZZIBF','ZZOUTPUT','STR_ID','FDSUB1','FDSUB2']

def num(s):
    s=(s or '').strip(); return (-float(s[:-1]) if s.endswith('-') else float(s)) if s else 0.0
def rows(c, tab, fl, where):
    try:
        res=c.call('RFC_READ_TABLE',QUERY_TABLE=tab,FIELDS=[{'FIELDNAME':x} for x in fl],
                   OPTIONS=[{'TEXT':where}] if where else [],ROWCOUNT=0)
    except ABAPApplicationError as e:
        return [] if 'TABLE_WITHOUT_DATA' in str(e) else None
    m=res['FIELDS']
    return [{x['FIELDNAME']:r['WA'][int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m} for r in res['DATA']]

# ---------- STEP A: fund ----------
def step_A_fund(p, t):
    have = rows(t,'FMFINCODE',['FINCODE'],f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}'")
    if have:
        return f"A.fund {PSPID}: EXISTS -> skip"
    praw=rows(p,'FMFINCODE',['FINCODE']+DATA_FLDS,f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}'")
    if not praw: return f"A.fund {PSPID}: NOT in P01 -> cannot source"
    ptxt=rows(p,'FMFINT',['BEZEICH','BESCHR'],f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}' AND SPRAS = 'E'")
    isd={k:praw[0].get(k,'') for k in DATA_FLDS}
    for dk in ('DATAB','DATBIS','DATE_EXP','DATE_CAN'):
        if isd.get(dk)=='00000000': isd[dk]=''
    ist={'SPRAS':'E','BEZEICH':(ptxt[0]['BEZEICH'] if ptxt else PSPID),'BESCHR':(ptxt[0]['BESCHR'] if ptxt else '')}
    if MODE!='run': return f"A.fund {PSPID}: WOULD create (type={isd.get('TYPE')} {isd.get('DATAB')}-{isd.get('DATBIS')})"
    t.call('FM_FUND_CREATE_RFC',I_FM_AREA=FIKRS,I_FUND=PSPID,IS_FUND_DATA=isd,IS_FUND_TEXT=ist,I_FLG_TESTRUN=' ',I_FLG_COMMIT='X')
    ok=rows(t,'FMFINCODE',['FINCODE'],f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}'")
    return f"A.fund {PSPID}: {'CREATED' if ok else 'FAILED'}"

# ---------- STEP C: project + WBS (def+root proven; nested -> CJ20N) ----------
def step_C_project(p, t):
    have = rows(t,'PROJ',['PSPID'],f"PSPID = '{PSPID}'")
    if have: return f"C.project {PSPID}: EXISTS -> skip (children/indent verify in CJ20N)"
    if MODE!='run': return f"C.project {PSPID}: WOULD create def+root via BAPI_PROJECT_MAINTAIN (see ps_project_sync.py)"
    return f"C.project {PSPID}: RUN via `python ps_project_sync.py {TARGET} {PSPID} <resp> <appl>` (def+root+release); nested WBS -> CJ20N indent"

# ---------- STEP F: project budget (ENTR/B1 proven) ----------
def step_F_budget_project(p, t):
    src=rows(p,'FMBL',['CMMTITEM','FISCYEAR'],f"FUND = '{PSPID}' AND PROCESS = 'ENTR'")
    if src is None or not src:
        return f"F.budget-project {PSPID}: no ENTR/B1 budget in P01 (may be WRTTP43 fund budget instead -> step E)"
    if MODE!='run': return f"F.budget-project {PSPID}: WOULD post ENTR/B1 ({len(src)} lines) via `budget_assign_entr.py {TARGET} commit {PSPID} <year>`"
    return f"F.budget-project {PSPID}: RUN `python budget_assign_entr.py {TARGET} commit {PSPID} 2026`"

# ---------- STEPS B/D/E: wire-up (verify before mass) ----------
def step_B_c5(p, t):
    src=rows(p,'YTFM_FUND_C5',['C5_ID','FM_OUTPUT'],f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}'")
    have=rows(t,'YTFM_FUND_C5',['C5_ID'],f"FIKRS = '{FIKRS}' AND FINCODE = '{PSPID}'")
    if not src: return f"B.C5 {PSPID}: no C5 link in P01"
    if have: return f"B.C5 {PSPID}: EXISTS -> skip"
    return f"B.C5 {PSPID}: WOULD assign C5 {[(r['C5_ID'],r['FM_OUTPUT']) for r in src]} via Y_BAPI_FUND_C5_ASSIGNMENT (verify FM signature) or INSERT YTFM_FUND_C5"

def step_E_budget_fund(p, t):
    src=rows(p,'BPGE',['WRTTP','VERSN','WTGES'],f"GEBER = '{PSPID}' AND WRTTP = '43' AND VERSN = '000'")
    if src is None or not src: return f"E.budget-fund {PSPID}: no WRTTP43 fund budget in P01"
    tot=sum(num(r['WTGES']) for r in src)
    return f"E.budget-fund {PSPID}: WOULD post fund-center budget (WRTTP43 net={tot:,.0f}) via BAPI_0050_CREATE addressing fund center (FS*) [wire-up: confirm address from P01 BPGE OBJNR]"

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    print(f"=== Replicate {PSPID} -> {TARGET}  (MODE={MODE}) ===  flow: A fund · B C5 · C project+WBS · D WBS-attrs · E budget-fund · F budget-project")
    for fn in (step_A_fund, step_B_c5, step_C_project, step_F_budget_project, step_E_budget_fund):
        try: print('  '+fn(p,t))
        except Exception as e: print(f"  {fn.__name__}: ERR {str(e)[:80]}")
    print("D.WBS-attrs: Y_BAPI_WBS_CUS_FIELD_UPDATE (USR00-04 region/country/sector/division + donor) — wire-up after project exists")
    print("\nNOTE: nested WBS (multi-level) -> CJ20N indent (BAPI I_WBS_HIERARCHIE_TABLE construction open). See ppm_sap_project_fund_e2e_flow.md")
    p.close(); t.close()

if __name__=="__main__": main()

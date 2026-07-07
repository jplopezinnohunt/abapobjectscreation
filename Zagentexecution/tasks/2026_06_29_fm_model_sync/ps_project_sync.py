"""
GOOD PROCESS — replicate a PS project + WBS hierarchy  P01 -> <TARGET>  via BAPI_PROJECT_MAINTAIN.
Usage: python ps_project_sync.py <TARGET> <PROJECT> [RESP_OVERRIDE] [APPL_OVERRIDE]

DESIGN PRINCIPLES (learned the hard way s093):
  1. **REFNUMBER = the row index WITHIN the object's OWN data table** — NOT a global sequence.
     ProjectDefinition -> 000001 (row 1 of I_PROJECT_DEFINITION); each WBS -> its 1-based index in
     I_WBS_ELEMENT_TABLE; Save -> 000000. Numbering globally (def=1,wbs=2,3,...) makes the LAST WBS point
     past its table and SAP reports "WBS element X already exists" (the #1 red herring this session).
  2. RESPONSIBLE_NO -> validated vs TCJ04 ; APPLICANT_NO -> validated vs TCJ05 (different tables). P01 HR
     numbers usually don't exist in the target -> pass valid target values (override args).
  3. Copy the FULL def (profiles/object class/calendar) — most are PROJECT_PROFILE-defaulted, but pass them
     anyway. Dates (START/FINISH/FCST_*) are deliberately NOT copied: P01 finish dates are in the past and
     would block a 2026 test posting -> leave open.
  4. BAPI auto-commits the Save (no TESTRUN). Verify by re-read, never by return code alone.
  5. NEVER iterate with METHOD='Delete' to "retry" — a failed delete sets the deletion flag (system status
     DLFL/I0076), which has NO clean RFC reset (only CJ20N 'reset deletion indicator'). Fix the input and
     re-run the single clean call on a project that does NOT yet exist in the target.
KNOWN LIMITATION — WBS HIERARCHY NESTING (unsolved by RFC, s093):
  Flat / single-level-1 create works once REFNUMBER is correct. But **nesting children under a parent
  does NOT work via this BAPI by RFC**: with no coding mask (MASK_ID empty) the POSID dots don't auto-nest,
  and I_WBS_HIERARCHIE_TABLE (UP/DOWN) is NOT honored at create -> "Several WBS elements on level 1 not
  allowed". Verified across one-call / incremental / UP-only / UP+DOWN. For a multi-level WBS structure,
  do the INDENT in **CJ20N (Project Builder)** after this script creates the def + root. The def, root,
  profiles, responsible/applicant and release are all done correctly here; only the child indent is manual.
PRECONDITION: PROJECT must NOT already exist in the target (PROJ/PRPS empty). If it exists in a bad state,
  reset its deletion flag + delete it in CJ20N first, then run this clean.
"""
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET=sys.argv[1] if len(sys.argv)>1 else "D01"
PROJ  =sys.argv[2] if len(sys.argv)>2 else "504PAK1000"
RESP  =sys.argv[3] if len(sys.argv)>3 else None   # valid TCJ04 person in target
APPL  =sys.argv[4] if len(sys.argv)>4 else None   # valid TCJ05 person in target

def errs(r): return [(m['MESSAGE_ID'],m['MESSAGE_TEXT']) for m in r.get('E_MESSAGE_TABLE',[]) if m['MESSAGE_TYPE'] in 'EAX']
def parent_of(posid):
    return posid.rsplit('.',1)[0] if '.' in posid else ''

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    # PRECONDITION guard
    ex=t.call('RFC_READ_TABLE',QUERY_TABLE='PRPS',FIELDS=[{'FIELDNAME':'POSID'}],OPTIONS=[{'TEXT':f"POSID LIKE '{PROJ}%'"}],ROWCOUNT=1)
    if ex['DATA']:
        print(f"ABORT: {PROJ} already has WBS in {TARGET}. Clean it in CJ20N (reset deletion flag + delete) before a clean run."); return
    pd=p.call('BAPI_PROJECTDEF_GETDETAIL',CURRENTEXTERNALPROJE=PROJ)['PROJECT_DEFINITION_STRU']
    resp=RESP or pd.get('RESPONSIBLE_NO',''); appl=APPL or pd.get('APPLICANT_NO','')
    # FAITHFUL: copy ALL populated def fields that exist in the create struct (dates, calendar, all
    # profiles: budget/plan/network/int/wbs_sched/cash, objectclass, time unit, SLWID, FCST dates...)
    DEF_FIELDS=['PROJECT_DEFINITION','DESCRIPTION','MASK_ID','RESPONSIBLE_NO','APPLICANT_NO','COMP_CODE',
      'BUS_AREA','CONTROLLING_AREA','PROFIT_CTR','PROJECT_CURRENCY','PROJECT_CURRENCY_ISO','NETWORK_ASSIGNMENT',
      'PLANT','CALENDAR','PLAN_BASIC','PLAN_FCST','TIME_UNIT','TIME_UNIT_ISO','NETWORK_PROFILE',
      'PROJECT_PROFILE','BUDGET_PROFILE','PROJECT_STOCK','OBJECTCLASS','STATISTICAL','TAXJURCODE','INT_PROFILE',
      'WBS_SCHED_PROFILE','CSH_BDGT_PROFILE','PLAN_PROFILE','FUNC_AREA','SLWID']
    # NOTE: dates (START/FINISH/FCST_*) intentionally NOT copied — P01's finish dates are in the past
    # (504PAK1000=2024, 000CRP9000=2020); copying them would block 2026 test postings. Left OPEN.
    idef={k:pd[k] for k in DEF_FIELDS if pd.get(k) and str(pd[k]).strip() not in ('','00000000')}
    idef['PROJECT_DEFINITION']=PROJ; idef['RESPONSIBLE_NO']=resp; idef['APPLICANT_NO']=appl
    res=p.call('RFC_READ_TABLE',QUERY_TABLE='PRPS',FIELDS=[{'FIELDNAME':x} for x in ['POSID','STUFE','PRART','POST1']],
               OPTIONS=[{'TEXT':f"POSID LIKE '{PROJ}%'"}],ROWCOUNT=0)
    m=res['FIELDS']
    wbs=sorted(({x['FIELDNAME']:r['WA'][int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m} for r in res['DATA']),
               key=lambda w:(w['POSID'].count('.'), w['POSID']))  # parents before children
    pos=[w['POSID'] for w in wbs]
    iwbs=[{'WBS_ELEMENT':w['POSID'],'PROJECT_DEFINITION':PROJ,'DESCRIPTION':w['POST1'] or w['POSID'],
        'COMP_CODE':idef['COMP_CODE'],'BUS_AREA':idef['BUS_AREA'],'CO_AREA':idef['CONTROLLING_AREA'],
        'PROJ_TYPE':w['PRART'],'CURRENCY':idef['PROJECT_CURRENCY'],
        'WBS_ACCOUNT_ASSIGNMENT_ELEMENT':'X','WBS_PLANNING_ELEMENT':'X','RESPONSIBLE_NO':resp,'APPLICANT_NO':appl} for w in wbs]
    # explicit hierarchy: UP = parent (by POSID mask)
    hier=[{'WBS_ELEMENT':w,'PROJECT_DEFINITION':PROJ,'UP':parent_of(w)} for w in pos]
    # CRITICAL: REFNUMBER = the row index WITHIN the object's OWN data table (NOT a global sequence).
    # ProjectDefinition -> row 1 of I_PROJECT_DEFINITION ; each WBS -> its 1-based index in I_WBS_ELEMENT_TABLE.
    # Numbering globally (def=1, wbs=2,3,..) makes the LAST WBS point past the table -> "WBS already exists".
    meth=[{'REFNUMBER':'000001','OBJECTTYPE':'ProjectDefinition','METHOD':'Create','OBJECTKEY':PROJ}]
    for i,w in enumerate(pos,1): meth.append({'REFNUMBER':f'{i:06d}','OBJECTTYPE':'WBS-Element','METHOD':'Create','OBJECTKEY':w})
    meth.append({'REFNUMBER':'000000','OBJECTTYPE':'','METHOD':'Save','OBJECTKEY':''})
    print(f"{PROJ}: {len(pos)} WBS, profile={idef['PROJECT_PROFILE']}, resp={resp}/appl={appl}")
    r=t.call('BAPI_PROJECT_MAINTAIN',I_PROJECT_DEFINITION=idef,I_WBS_ELEMENT_TABLE=iwbs,
             I_WBS_HIERARCHIE_TABLE=hier,I_METHOD_PROJECT=meth)
    e=errs(r)
    if e: print('CREATE errors:',e[:5]); t.call('BAPI_TRANSACTION_ROLLBACK'); return
    t.call('BAPI_TRANSACTION_COMMIT',WAIT='X'); print('CREATE ok')
    # release all
    rk=[{'WBS_ELEMENT':w,'PROJECT_DEFINITION':PROJ} for w in pos]
    rm=[{'REFNUMBER':f'{i:06d}','OBJECTTYPE':'WBS-Element','METHOD':'Release','OBJECTKEY':w} for i,w in enumerate(pos,1)]+[{'REFNUMBER':'000000','OBJECTTYPE':'','METHOD':'Save','OBJECTKEY':''}]
    r2=t.call('BAPI_PROJECT_MAINTAIN',I_WBS_ELEMENT_TABLE=rk,I_METHOD_PROJECT=rm)
    e2=errs(r2)
    if e2: print('RELEASE errors:',e2[:5]); t.call('BAPI_TRANSACTION_ROLLBACK')
    else: t.call('BAPI_TRANSACTION_COMMIT',WAIT='X'); print('RELEASE ok')
    chk=t.call('RFC_READ_TABLE',QUERY_TABLE='PRPS',FIELDS=[{'FIELDNAME':'POSID'}],OPTIONS=[{'TEXT':f"POSID LIKE '{PROJ}%'"}],ROWCOUNT=0)
    print(f'{PROJ} WBS now in {TARGET}: {len(chk["DATA"])}')
    p.close(); t.close()

if __name__=="__main__": main()

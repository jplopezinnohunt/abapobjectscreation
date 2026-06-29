"""
Replicate PS project + WBS structure  P01 -> <TARGET>  via BAPI_PROJECT_MAINTAIN (create + release).
Usage: python ps_project_sync.py <TARGET> <PROJECT>     e.g.  D01 504PAK1000
VERIFIED recipe (s093):
  CREATE: I_PROJECT_DEFINITION (incl. RESPONSIBLE_NO/APPLICANT_NO — profile-mandatory) +
          I_WBS_ELEMENT_TABLE (WBS_ACCOUNT_ASSIGNMENT_ELEMENT=X, WBS_PLANNING_ELEMENT=X) +
          I_METHOD_PROJECT [Create ProjectDefinition, Create WBS-Element*, Save (REFNUMBER=000000)]
  RELEASE: I_WBS_ELEMENT_TABLE (keys) + I_METHOD_PROJECT [Release WBS-Element*, Save]
  GOTCHAS: BAPI auto-commits (rollback does NOT undo); method table must be consistent with data tables;
           REFNUMBER is NUMC (Save row = 000000); read source via BAPI_PROJECTDEF_GETDETAIL + PRPS(POSID LIKE).
"""
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET=sys.argv[1] if len(sys.argv)>1 else "D01"
PROJ  =sys.argv[2] if len(sys.argv)>2 else "504PAK1000"
RESP_OVERRIDE=sys.argv[3] if len(sys.argv)>3 else None  # use a valid D01 TCJ04 person if P01's is absent

def errs(r): return [(m['MESSAGE_ID'],m['MESSAGE_TEXT']) for m in r.get('E_MESSAGE_TABLE',[]) if m['MESSAGE_TYPE'] in 'EAX']

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    pd=p.call('BAPI_PROJECTDEF_GETDETAIL',CURRENTEXTERNALPROJE=PROJ)['PROJECT_DEFINITION_STRU']
    idef={'PROJECT_DEFINITION':PROJ,'DESCRIPTION':pd['DESCRIPTION'],'COMP_CODE':pd['COMP_CODE'],
          'BUS_AREA':pd.get('BUS_AREA',''),'CONTROLLING_AREA':pd['CONTROLLING_AREA'],
          'PROJECT_CURRENCY':pd.get('PROJECT_CURRENCY','USD'),'PROJECT_PROFILE':pd['PROJECT_PROFILE'],
          'RESPONSIBLE_NO':RESP_OVERRIDE or pd.get('RESPONSIBLE_NO',''),'APPLICANT_NO':pd.get('APPLICANT_NO','')}
    res=p.call('RFC_READ_TABLE',QUERY_TABLE='PRPS',
        FIELDS=[{'FIELDNAME':x} for x in ['POSID','STUFE','BELKZ','PLAKZ','PRART','POST1']],
        OPTIONS=[{'TEXT':f"POSID LIKE '{PROJ}%'"}],ROWCOUNT=0)
    m=res['FIELDS']
    wbs=sorted(({x['FIELDNAME']:r['WA'][int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip() for x in m} for r in res['DATA']), key=lambda w:w['POSID'])
    print(f"{PROJ}: profile={idef['PROJECT_PROFILE']} CC={idef['COMP_CODE']} | {len(wbs)} WBS")
    iwbs=[{'WBS_ELEMENT':w['POSID'],'PROJECT_DEFINITION':PROJ,'DESCRIPTION':w['POST1'] or w['POSID'],
        'COMP_CODE':idef['COMP_CODE'],'BUS_AREA':idef['BUS_AREA'],'CO_AREA':idef['CONTROLLING_AREA'],
        'PROJ_TYPE':w['PRART'],'CURRENCY':idef['PROJECT_CURRENCY'],
        'WBS_ACCOUNT_ASSIGNMENT_ELEMENT':w['BELKZ'] or 'X','WBS_PLANNING_ELEMENT':w['PLAKZ'] or 'X',
        'RESPONSIBLE_NO':idef['RESPONSIBLE_NO']} for w in wbs]
    # CREATE
    meth=[{'REFNUMBER':'000001','OBJECTTYPE':'ProjectDefinition','METHOD':'Create','OBJECTKEY':PROJ}]
    for i,w in enumerate(iwbs,2):
        meth.append({'REFNUMBER':f'{i:06d}','OBJECTTYPE':'WBS-Element','METHOD':'Create','OBJECTKEY':w['WBS_ELEMENT']})
    meth.append({'REFNUMBER':'000000','OBJECTTYPE':'','METHOD':'Save','OBJECTKEY':''})
    r=t.call('BAPI_PROJECT_MAINTAIN',I_PROJECT_DEFINITION=idef,I_WBS_ELEMENT_TABLE=iwbs,I_METHOD_PROJECT=meth)
    e=errs(r)
    if e and not any('already exists' in x[1] for x in e):
        print('CREATE errors:',e[:5]); t.call('BAPI_TRANSACTION_ROLLBACK'); p.close(); t.close(); return
    t.call('BAPI_TRANSACTION_COMMIT',WAIT='X'); print(f'CREATE ok ({len(iwbs)} WBS) [or already existed]')
    # RELEASE (all WBS)
    rmeth=[{'REFNUMBER':f'{i:06d}','OBJECTTYPE':'WBS-Element','METHOD':'Release','OBJECTKEY':w['WBS_ELEMENT']} for i,w in enumerate(iwbs,1)]
    rmeth.append({'REFNUMBER':'000000','OBJECTTYPE':'','METHOD':'Save','OBJECTKEY':''})
    rkeys=[{'WBS_ELEMENT':w['WBS_ELEMENT'],'PROJECT_DEFINITION':PROJ} for w in iwbs]
    r2=t.call('BAPI_PROJECT_MAINTAIN',I_WBS_ELEMENT_TABLE=rkeys,I_METHOD_PROJECT=rmeth)
    e2=errs(r2)
    if e2: print('RELEASE errors:',e2[:5]); t.call('BAPI_TRANSACTION_ROLLBACK')
    else: t.call('BAPI_TRANSACTION_COMMIT',WAIT='X'); print('RELEASE ok (all WBS -> REL)')
    # verify
    chk=t.call('RFC_READ_TABLE',QUERY_TABLE='PRPS',FIELDS=[{'FIELDNAME':'POSID'}],OPTIONS=[{'TEXT':f"POSID LIKE '{PROJ}%'"}],ROWCOUNT=0)
    print(f'D01 PRPS for {PROJ}: {len(chk["DATA"])} WBS present')
    p.close(); t.close()

if __name__=="__main__": main()

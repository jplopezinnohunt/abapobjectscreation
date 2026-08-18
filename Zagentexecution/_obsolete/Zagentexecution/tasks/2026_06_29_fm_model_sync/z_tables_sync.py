"""
UNESCO Z (custom) FM tables sync  P01 -> <TARGET>  via direct INSERT (RFC_ABAP_INSTALL_AND_RUN).
Own Z objects -> direct INSERT is the correct channel (proven GL pattern).
Usage: python z_tables_sync.py <TARGET> <which>   which = output | fundc5 | cpl | all

Source = P01 LIVE (gold CPL is missing ENDDA/BEGDA -> never gold for write source).
Scope: fundc5 -> C5_ID='43'; cpl -> funds in the active C5/43 set; output -> full difference.
NOTE: YTFM_OUTPUT_T.ODESC is a STRING field -> excluded from INSERT (set empty).
"""
import sys, sqlite3, time
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
TARGET = sys.argv[1] if len(sys.argv) > 1 else "D01"
WHICH  = sys.argv[2] if len(sys.argv) > 2 else "all"
GOLD = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"

SPEC = {
  'YTFM_OUTPUT':   {'cols':['FM_OUTPUT','ZZSECT','ORANK','OTYPE'],          'key':['FM_OUTPUT'],            'where':''},
  'YTFM_OUTPUT_T': {'cols':['SPRSL','FM_OUTPUT','ONAME','OTEXT'],            'key':['SPRSL','FM_OUTPUT'],    'where':''},
  'YTFM_FUND_C5':  {'cols':['FIKRS','FINCODE','C5_ID','C5_SEL','FM_OUTPUT'], 'key':['FIKRS','FINCODE','C5_ID'], 'where':"C5_ID = '43'"},
  'YTFM_FUND_CPL': {'cols':['FIKRS','FINCODE','ENDDA','BEGDA','ALINE','NONIBF'],'key':['FIKRS','FINCODE','ENDDA'],'where':''},
}

def read_rows(c, tab, cols, where):
    res=c.call('RFC_READ_TABLE',QUERY_TABLE=tab,FIELDS=[{'FIELDNAME':f} for f in cols],
               OPTIONS=[{'TEXT':where}] if where else [],ROWCOUNT=0)
    m=res['FIELDS']; out=[]
    for row in res['DATA']:
        wa=row['WA']; out.append({f['FIELDNAME']:wa[int(f['OFFSET']):int(f['OFFSET'])+int(f['LENGTH'])].strip() for f in m})
    return out

def build_insert(tab, cols, rows):
    abap=['REPORT Z_FMZ_SYNC.', f'DATA ls TYPE {tab.lower()}.', 'DATA n TYPE i.']
    for r in rows:
        abap.append('CLEAR ls.'); abap.append('ls-mandt = sy-mandt.')
        for f in cols:
            v=str(r.get(f,'')).replace("'","''")
            line=f"ls-{f.lower()} = '{v}'."
            if len(line)<=72: abap.append(line)
        abap += [f'INSERT {tab.lower()} FROM ls.', 'IF sy-subrc = 0. n = n + 1. ENDIF.']
    abap += ['COMMIT WORK.', "WRITE: / 'INSERTED', n."]
    return abap

def sync_table(p, t, tab):
    sp=SPEC[tab]; cols=sp['cols']; key=sp['key']
    # scope CPL to active C5/43 fund set
    extra=''
    if tab=='YTFM_FUND_CPL':
        g=sqlite3.connect(GOLD)
        active=set((a.strip(),b.strip()) for a,b in g.execute("SELECT DISTINCT FIKRS,FINCODE FROM ytfm_fund_c5 WHERE C5_ID='43'")); g.close()
    src=read_rows(p, tab, cols, sp['where'])
    if tab=='YTFM_FUND_CPL':
        src=[r for r in src if (r['FIKRS'],r['FINCODE']) in active]
    tgt=read_rows(t, tab, key, sp['where'])
    have=set(tuple(r[k] for k in key) for r in tgt)
    missing=[r for r in src if tuple(r[k] for k in key) not in have]
    print(f"[{tab}] P01={len(src)} {TARGET}-have={len(have)} -> to INSERT={len(missing)}")
    created=0
    for i in range(0,len(missing),12):
        batch=missing[i:i+12]
        src_abap=[{'LINE':l[:72]} for l in build_insert(tab,cols,batch)]
        res=t.call('RFC_ABAP_INSTALL_AND_RUN', PROGRAM=src_abap)
        for w in res.get('WRITES',[]):
            if 'INSERTED' in w.get('ZEILE',''): created+=int(w['ZEILE'].split()[-1])
        time.sleep(0.5)
    # verify
    tgt2=read_rows(t, tab, key, sp['where'])
    have2=set(tuple(r[k] for k in key) for r in tgt2)
    gap=len([r for r in src if tuple(r[k] for k in key) not in have2])
    print(f"[{tab}] inserted={created}  remaining gap={gap}")

def main():
    p=get_connection('P01'); t=get_connection(TARGET)
    order=['YTFM_OUTPUT','YTFM_OUTPUT_T','YTFM_FUND_C5','YTFM_FUND_CPL']
    todo = order if WHICH=='all' else {
        'output':['YTFM_OUTPUT','YTFM_OUTPUT_T'],'fundc5':['YTFM_FUND_C5'],'cpl':['YTFM_FUND_CPL']}[WHICH]
    for tab in todo: sync_table(p,t,tab)
    p.close(); t.close()

if __name__=="__main__": main()

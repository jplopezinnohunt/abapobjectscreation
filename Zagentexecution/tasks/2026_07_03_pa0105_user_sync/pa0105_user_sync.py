"""
Replicate PA0105 subtype 0001 (SAP system user link PERNR->BNAME) from P01 (source of truth)
into a TARGET system (D01/V01) for employees that HAVE a SAP user in P01 but are MISSING it in target.

Fixes the "SaveFormData writes only if it finds the user" gap in the staff-time-distribution upload:
the lookup PERNR->SAP user fails when PA0105-0001 is absent in D01/V01.

Write path = STANDARD BAPI (never direct table insert on HR infotypes):
   BAPI_EMPLOYEE_ENQUEUE -> BAPI_EMPLCOMM_CREATE(SUBTYPE=0001, COMMUNICATIONID=<P01 USRID>,
   VALIDITYBEGIN=<P01 BEGDA>, VALIDITYEND=99991231, NOCOMMIT=X) -> BAPI_TRANSACTION_COMMIT -> DEQUEUE.
Idempotent (skips PERNRs that already have PA0105-0001). Every write verified by re-read.

Usage:
   python pa0105_user_sync.py <D01|V01> golden            # the 12 golden PERNRs (validation)
   python pa0105_user_sync.py <D01|V01> test:5            # first 5 of the gap (dry validation)
   python pa0105_user_sync.py <D01|V01> all               # the full gap
   python pa0105_user_sync.py <D01|V01> dry               # compute + print the gap, write nothing
   python pa0105_user_sync.py <D01|V01> 10001250,10001977 # explicit list
Append ' commit' as a 3rd arg to actually WRITE; without it, runs dry (plan only).
"""
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import get_connection
from pyrfc import ABAPApplicationError

GOLD = ['10152932','10110932','10148032','10149186','91036937','10001250',
        '10001977','10002139','10002259','10004022','10005507','10006039']

TGT  = sys.argv[1] if len(sys.argv) > 1 else "D01"
MODE = sys.argv[2] if len(sys.argv) > 2 else "dry"
COMMIT = (len(sys.argv) > 3 and sys.argv[3] == "commit") or MODE == "dry" and False

def reader(c):
    def read(tab, fl, where):
        try:
            res = c.call('RFC_READ_TABLE', QUERY_TABLE=tab,
                         FIELDS=[{'FIELDNAME': x} for x in fl],
                         OPTIONS=[{'TEXT': where}] if where else [], ROWCOUNT=0)
        except ABAPApplicationError:
            return None
        m = res['FIELDS']
        return [{x['FIELDNAME']: r['WA'][int(x['OFFSET']):int(x['OFFSET'])+int(x['LENGTH'])].strip()
                 for x in m} for r in res['DATA']]
    return read

def main():
    p = get_connection('P01'); rp = reader(p)
    t = get_connection(TGT);   rt = reader(t)

    # ---- source of truth: P01 PERNR -> (USRID, BEGDA) ----
    p01 = {r['PERNR']: (r['USRID'] or r['USRID_LONG'], r['BEGDA'])
           for r in rp('PA0105', ['PERNR','USRID','USRID_LONG','BEGDA','ENDDA'],
                       "SUBTY = '0001' AND ENDDA = '99991231'") if (r['USRID'] or r['USRID_LONG'])}

    # ---- target state ----
    emp = {e['PERNR'] for e in rt('PA0001', ['PERNR'], "ENDDA = '99991231'")}
    has = {u['PERNR'] for u in rt('PA0105', ['PERNR'], "SUBTY = '0001' AND ENDDA = '99991231'")}

    # ---- pick scope ----
    if MODE == 'golden':
        scope = [x for x in GOLD]
    elif MODE.startswith('test:'):
        n = int(MODE.split(':')[1]); scope = None; _n = n
    elif MODE in ('all', 'dry'):
        scope = None
    else:
        scope = [x.strip() for x in MODE.split(',')]

    # full gap = P01-has-user AND exists-in-target AND missing-in-target
    gap = [pn for pn in p01 if pn in emp and pn not in has]
    gap.sort()
    if scope is not None:
        work = [pn for pn in scope if pn in p01 and pn in emp and pn not in has]
        skipped_nouser = [pn for pn in scope if pn not in p01]
        skipped_hasit  = [pn for pn in scope if pn in has]
        skipped_noemp  = [pn for pn in scope if pn not in emp and pn in p01]
    else:
        work = gap
        if MODE.startswith('test:'):
            work = gap[:_n]
        skipped_nouser = skipped_hasit = skipped_noemp = []

    print(f"=== PA0105-0001 sync  P01 -> {TGT}  mode={MODE} commit={COMMIT} ===")
    print(f"P01 with user: {len(p01)} | {TGT} employees: {len(emp)} | {TGT} already have link: {len(has)}")
    print(f"Full gap ({TGT}): {len(gap)} | this run will process: {len(work)}")
    if skipped_nouser: print(f"  skip (no P01 user): {skipped_nouser}")
    if skipped_hasit:  print(f"  skip (already has link): {skipped_hasit}")
    if skipped_noemp:  print(f"  skip (not an employee in {TGT}): {skipped_noemp}")

    if not COMMIT:
        print("\nDRY — no writes. Sample of work:")
        for pn in work[:15]:
            print(f"   {pn} -> {p01[pn][0]} (begda {p01[pn][1]})")
        p.close(); t.close(); return

    ok = err = 0; errors = []
    for i, pn in enumerate(work, 1):
        usrid, begda = p01[pn]
        try:
            t.call('BAPI_EMPLOYEE_ENQUEUE', NUMBER=pn)
            r = t.call('BAPI_EMPLCOMM_CREATE', EMPLOYEENUMBER=pn, SUBTYPE='0001',
                       COMMUNICATIONID=usrid, VALIDITYBEGIN=begda, VALIDITYEND='99991231',
                       NOCOMMIT='X')
            ret = r.get('RETURN', {})
            if ret and ret.get('TYPE') in ('E','A','X'):
                t.call('BAPI_TRANSACTION_ROLLBACK'); err += 1
                errors.append((pn, ret.get('MESSAGE','')[:60]))
            else:
                t.call('BAPI_TRANSACTION_COMMIT', WAIT='X'); ok += 1
        except Exception as e:
            try: t.call('BAPI_TRANSACTION_ROLLBACK')
            except Exception: pass
            err += 1; errors.append((pn, str(e)[:60]))
        finally:
            try: t.call('BAPI_EMPLOYEE_DEQUEUE', NUMBER=pn)
            except Exception: pass
        if i % 50 == 0 or i == len(work):
            print(f"   ...{i}/{len(work)}  ok={ok} err={err}")

    # ---- verify by re-read ----
    has2 = {u['PERNR'] for u in rt('PA0105', ['PERNR'], "SUBTY = '0001' AND ENDDA = '99991231'")}
    verified = sum(1 for pn in work if pn in has2)
    print(f"\nDONE: created ok={ok} err={err} | verified present after: {verified}/{len(work)}")
    if errors[:10]:
        print("errors (first 10):")
        for pn, msg in errors[:10]: print(f"   {pn}: {msg}")
    p.close(); t.close()

if __name__ == "__main__":
    main()

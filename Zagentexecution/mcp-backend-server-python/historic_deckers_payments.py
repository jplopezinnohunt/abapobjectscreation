"""Find the 2 historical F110 runs that paid Imprimerie Deckers → BNP Paribas factor in D01."""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=200):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# 1. BSAK details — Imprimerie Deckers (0000302983) docs with EMPFB
print("\n=== BSAK for 0000302983 (Imprimerie Deckers Druk Snoec) with EMPFB ===")
a = rd("BSAK", ["LIFNR = '0000302983'", "AND EMPFB <> ' '"],
       ["BUKRS","BELNR","GJAHR","BUZEI","EMPFB","AUGDT","AUGBL"], n=50)
b = rd("BSAK", ["LIFNR = '0000302983'", "AND EMPFB <> ' '"],
       ["BUKRS","BELNR","WAERS","ZLSCH","HBKID"], n=50)

for ra, rb in zip(a, b):
    print(f"  {ra['BUKRS']}/{ra['BELNR']}/{ra['GJAHR']}/{ra['BUZEI']} EMPFB={ra['EMPFB']} AUGDT={ra['AUGDT']} AUGBL={ra['AUGBL']} WAERS={rb['WAERS']} ZLSCH='{rb['ZLSCH'].strip()}' HBKID={rb['HBKID']}")

# Filter to BNP Paribas (0000701556) only
print(f"\n=== Only BNP Paribas factor pair ===")
bnp_docs = [(ra,rb) for ra,rb in zip(a,b) if ra['EMPFB'].strip() == '0000701556']
for ra, rb in bnp_docs:
    augbl = ra['AUGBL'].strip()
    augdt = ra['AUGDT'].strip()
    print(f"\n  Doc {ra['BUKRS']}/{ra['BELNR']}/{ra['GJAHR']} → Clearing doc AUGBL={augbl} AUGDT={augdt}")

    # Look up the payment doc in REGUH (the clearing doc = payment doc)
    if augbl and augbl != '0000000000':
        # AUGBL is the payment doc number → find in REGUH by VBLNR
        regh = rd("REGUH", [f"VBLNR = '{augbl}'", "AND ZBUKR = 'UNES'"],
                  ["LAUFD","LAUFI","ZBUKR","LIFNR","VBLNR","XVORL"], n=10)
        for r in regh:
            print(f"    F110 run found: LAUFD={r['LAUFD']} LAUFI={r['LAUFI']} ZBUKR={r['ZBUKR']} LIFNR={r['LIFNR']} XVORL='{r['XVORL']}'")
            # Get RZAWE + HBKID/HKTID + EMPFG from REGUH
            try:
                rzawe_rows = rd("REGUH",
                                [f"LAUFD = '{r['LAUFD']}'", f"AND LAUFI = '{r['LAUFI']}'",
                                 f"AND ZBUKR = '{r['ZBUKR']}'", f"AND LIFNR = '{r['LIFNR']}'"],
                                ["RZAWE","HBKID","HKTID"], n=5)
                for rr in rzawe_rows:
                    print(f"      RZAWE='{rr['RZAWE'].strip()}' HBKID={rr['HBKID']} HKTID={rr['HKTID']}")
                emp_rows = rd("REGUH",
                              [f"LAUFD = '{r['LAUFD']}'", f"AND LAUFI = '{r['LAUFI']}'",
                               f"AND ZBUKR = '{r['ZBUKR']}'", f"AND LIFNR = '{r['LIFNR']}'"],
                              ["EMPFG","UBNKS","UBNKL"], n=5)
                for rr in emp_rows:
                    print(f"      EMPFG='{rr['EMPFG'].strip()}' UBNKS={rr['UBNKS']} UBNKL={rr['UBNKL'].strip()}")
            except Exception as e:
                print(f"      err: {e}")

            # DFPAYG for this run = the FORMI
            dfpg = rd("DFPAYG",
                      [f"LAUFD = '{r['LAUFD']}'", f"AND LAUFI = '{r['LAUFI']}'", f"AND ZBUKR = '{r['ZBUKR']}'"],
                      ["FORMI","GRPNO","HBKID","HKTID","ANZ_ERZ","ANZ_ERL"], n=10)
            for g in dfpg:
                print(f"      DFPAYG: FORMI={g['FORMI'].strip()} GRPNO={g['GRPNO'].strip()} HBKID={g['HBKID']} ANZ_ERZ={g['ANZ_ERZ'].strip()} ANZ_ERL={g['ANZ_ERL'].strip()}")

# Also: Fortis Commercial Finance pair
print(f"\n\n=== Fortis Commercial Finance (0000304728) pair ===")
fortis_docs = [(ra,rb) for ra,rb in zip(a,b) if ra['EMPFB'].strip() == '0000304728']
for ra, rb in fortis_docs:
    augbl = ra['AUGBL'].strip()
    print(f"\n  Doc {ra['BUKRS']}/{ra['BELNR']}/{ra['GJAHR']} → Clearing doc AUGBL={augbl}")
    if augbl and augbl != '0000000000':
        regh = rd("REGUH", [f"VBLNR = '{augbl}'", "AND ZBUKR = 'UNES'"],
                  ["LAUFD","LAUFI","ZBUKR","LIFNR","XVORL"], n=10)
        for r in regh:
            print(f"    F110 run: LAUFD={r['LAUFD']} LAUFI={r['LAUFI']} LIFNR={r['LIFNR']}")
            dfpg = rd("DFPAYG",
                      [f"LAUFD = '{r['LAUFD']}'", f"AND LAUFI = '{r['LAUFI']}'", f"AND ZBUKR = '{r['ZBUKR']}'"],
                      ["FORMI","GRPNO","HBKID"], n=5)
            for g in dfpg:
                print(f"      DFPAYG: FORMI={g['FORMI'].strip()} GRPNO={g['GRPNO'].strip()} HBKID={g['HBKID']}")

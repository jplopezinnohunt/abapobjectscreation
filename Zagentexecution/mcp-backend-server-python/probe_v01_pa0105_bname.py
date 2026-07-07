"""READ-ONLY live V01 extract: PA0105 subty 0001 (SY-UNAME -> BNAME) for the
105 usable V01 GEF employees (the CRP 'posibles creadores').
RFC_READ_TABLE only. No SAP writes. Does NOT touch the golden DB (one-writer rule).
Output: PERNR -> BNAME mapping written to unescrparalell as CSV + printed.
"""
import os, sys, csv, datetime
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from rfc_helpers import get_connection

PERNR_FILE = os.path.join(
    r"C:\Users\jp_lopez\AppData\Local\Temp\claude",
    r"C--Users-jp-lopez-projects-unescrparalell",
    r"7de9707a-e216-4a9b-9747-6960f7383402", "scratchpad", "v01_pernrs.txt")
OUT_CSV = r"C:\Users\jp_lopez\projects\unescrparalell\v01_pernr_bname.csv"

with open(PERNR_FILE) as f:
    f.readline()  # count line
    pernrs = [p.strip() for p in f.readline().strip().split(",") if p.strip()]
print("PERNRs to resolve:", len(pernrs))


def split_options(where):
    """RFC_READ_TABLE OPTIONS: each WA <= 72 chars, break only at spaces."""
    opts, cur = [], ""
    for tok in where.split(" "):
        add = (tok if not cur else " " + tok)
        if len(cur) + len(add) > 72:
            opts.append({"TEXT": cur})
            cur = tok
        else:
            cur += add
    if cur:
        opts.append({"TEXT": cur})
    return opts


def read_pa0105_all(conn, subty):
    """One call: all PA0105 rows for a subtype (short WHERE, no IN-list)."""
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE="PA0105", DELIMITER="|",
                    ROWCOUNT=0,
                    FIELDS=[{"FIELDNAME": x} for x in ("PERNR", "SUBTY", "ENDDA", "USRID", "USRID_LONG")],
                    OPTIONS=[{"TEXT": "SUBTY = '%s'" % subty}])
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return out


c = get_connection("V01")
info = c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
print("Connected V01: SYSID=%s HOST=%s CLIENT=%s\n" % (
    info.get("RFCSYSID"), info.get("RFCHOST"), os.getenv("SAP_V01_CLIENT")))

want = set(p.lstrip("0") for p in pernrs)
allrows = read_pa0105_all(c, "0001")
print("total PA0105 subty 0001 rows on V01:", len(allrows))

# best (latest ENDDA) subty-0001 row per wanted PERNR
best = {}
for r in allrows:
    pk = r["PERNR"].lstrip("0")
    if pk not in want:
        continue
    bname = r.get("USRID") or r.get("USRID_LONG")
    prev = best.get(pk)
    if prev is None or r.get("ENDDA", "") > prev[1]:
        best[pk] = (bname, r.get("ENDDA", ""))
print("matched wanted PERNRs:", len(best))

c.close()

resolved = 0
with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["PERNR", "BNAME", "ENDDA"])
    for p in pernrs:
        pk = p.lstrip("0")
        bname, endda = best.get(pk, ("", ""))
        if bname:
            resolved += 1
        w.writerow([p, bname, endda])

print("\n=== RESULT ===")
print("resolved %d / %d  (missing %d)" % (resolved, len(pernrs), len(pernrs) - resolved))
print("CSV ->", OUT_CSV)
print("(READ-ONLY. No SAP writes. Golden DB untouched.)")

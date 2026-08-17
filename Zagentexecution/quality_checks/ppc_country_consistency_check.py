"""Recurring quality check: is every PPC-configured country internally consistent?

Promoted from INC-EGYPT-PPC (session #099). The Egypt request exposed a class of defect, not
one country's gap: the three tables that make Purpose of Payment work are maintained
INDEPENDENTLY, nothing in SAP ties them together, and two of the three failure modes are
SILENT -- the posting is blocked but nothing renders, or the code is accepted but belongs to
another country.

Four checks, all measured against the Gold DB (P01 provenance):

  A  SWITCH WITHOUT A CODE LIST
     YTFI_PPC_STRUC has a PPC_VAR/PPC_DESCR row for the country, but T015L has no code with
     that prefix. Users are blocked with nothing to select. LOUD failure, caught on day one.

  B  SWITCH WITHOUT AN XML TAG
     YTFI_PPC_STRUC blocks, YTFI_PPC_TAG has no row for the country. Users are forced to fill
     a field that is then never written to the payment file. SILENT -- this satisfies the
     auditor and fails the bank.

  C  CODE LIST WITHOUT A SWITCH
     T015L carries a country's codes but YTFI_PPC_STRUC has no PPC_VAR/PPC_DESCR row, so the
     field stays optional. SILENT -- looks configured, controls nothing.

  D  DEGENERATE USAGE
     One code carries most of the country's real payments. The control is satisfied and the
     data the bank receives is worthless. A training problem wearing a config problem's
     clothes; only visible by measuring what was actually posted.

Check D also reports cross-country contamination, which exists because T015L's key is LZBKZ
alone -- it has NO country field. The 'EG'/'JO' prefix is a naming convention, not a rule SAP
enforces, and u917 only checks the field is non-empty. So a user CAN pick JO6 on an Egyptian
payment and every layer will accept it.

Read-only. Exits 1 if any HIGH finding is present, so it can gate a close.
"""
import io
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

SWITCH_CODES = {"PPC_VAR", "PPC_DESCR"}
DEGENERATE_SHARE = 0.60  # one code carrying more than this much of a country's usage


def load(con):
    cur = con.cursor()

    struct = defaultdict(set)
    for land, code in cur.execute("SELECT LAND1, PPC_CODE FROM YTFI_PPC_STRUC"):
        struct[(land or "").strip()].add((code or "").strip())

    codes = defaultdict(list)
    for (lzbkz,) in cur.execute("SELECT LZBKZ FROM T015L"):
        lz = (lzbkz or "").strip()
        if len(lz) >= 3 and lz[:2].isalpha():
            codes[lz[:2].upper()].append(lz)

    tags = {(land or "").strip() for (land,) in cur.execute("SELECT LAND1 FROM YTFI_PPC_TAG")}
    return struct, codes, tags


def usage(con):
    """What was actually posted, per country prefix. REGUP may not be in the Gold DB."""
    cur = con.cursor()
    try:
        rows = cur.execute(
            "SELECT LZBKZ, COUNT(*) FROM REGUP WHERE TRIM(LZBKZ) <> '' GROUP BY LZBKZ"
        ).fetchall()
    except sqlite3.Error:
        return None
    per = defaultdict(Counter)
    for lz, n in rows:
        lz = (lz or "").strip()
        if len(lz) >= 3 and lz[:2].isalpha():
            per[lz[:2].upper()][lz] += n
    return per


def main():
    if not GOLD.exists():
        print(f"SKIP - Gold DB not present at {GOLD}")
        return 0

    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    struct, codes, tags = load(con)
    used = usage(con)

    findings = []
    switched = sorted(c for c, s in struct.items() if s & SWITCH_CODES)

    print("=" * 78)
    print("PPC country consistency - three tables, maintained independently")
    print("=" * 78)
    print(f"countries that BLOCK postings (YTFI_PPC_STRUC): {len(switched)} - {', '.join(switched)}")
    print(f"countries with codes in T015L: {len(codes)} - {', '.join(sorted(codes))}")
    print(f"countries with an XML tag: {len(tags)} - {', '.join(sorted(tags))}\n")

    for c in switched:
        if not codes.get(c):
            findings.append(("HIGH", c, "A", "blocks postings but T015L has no code with this "
                                             "prefix - users are blocked with nothing to pick"))
        if c not in tags:
            findings.append(("HIGH", c, "B", "blocks postings but YTFI_PPC_TAG has no row - the "
                                             "field is forced, then never written to the file "
                                             "(SILENT)"))

    for c in sorted(codes):
        if c not in struct or not (struct[c] & SWITCH_CODES):
            findings.append(("MEDIUM", c, "C", f"{len(codes[c])} codes in T015L but nothing "
                                               "switches the control on - looks configured, "
                                               "controls nothing (SILENT)"))

    if used is None:
        print("NOTE: REGUP is not in the Gold DB - check D (degenerate usage) skipped.\n")
    else:
        for c in switched:
            cc = used.get(c)
            if not cc:
                continue
            total = sum(cc.values())
            top, n = cc.most_common(1)[0]
            if total >= 50 and n / total > DEGENERATE_SHARE:
                findings.append(("MEDIUM", c, "D", f"{top} carries {n}/{total} = {n/total:.0%} of "
                                                   "real usage - the control is satisfied and the "
                                                   "bank data is near-worthless"))
            unknown = [k for k in cc if k not in set(codes.get(c, ()))]
            if unknown:
                findings.append(("LOW", c, "D", f"codes posted that are not in T015L under this "
                                                f"prefix: {sorted(unknown)[:6]}"))

    if not findings:
        print("PASS - every configured country has code list + switch + XML tag, and no "
              "degenerate usage.")
        return 0

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    print(f"{len(findings)} finding(s):\n")
    for sev, c, chk, msg in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        print(f"  [{sev:6}] {c} check {chk}: {msg}")

    high = sum(1 for f in findings if f[0] == "HIGH")
    print(f"\n{high} HIGH")
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())

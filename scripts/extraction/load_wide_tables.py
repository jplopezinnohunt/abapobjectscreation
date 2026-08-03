"""FIRST LOAD of tables the golden does not have yet — including WIDE ones.

WHY THIS EXISTS SEPARATELY FROM gold_refresh.py
    gold_refresh.py is the registry-driven DELTA engine: it maintains tables the golden
    already holds. This does the first load, and it solves the one problem that blocks it:
    RFC_READ_TABLE returns a flat 512-character work area, so a table wider than that
    cannot be read in one call, and the P01 wrapper rejects ROWSKIPS so it cannot be paged
    either.

THE CHUNKING RULE THAT MATTERS
    Wide tables are read in several passes and the passes are merged ON THE KEY, never on
    row position. Position merging is the obvious shortcut and it is wrong: two reads of
    the same table are only in the same order by luck, and when they are not, every field
    in the second chunk lands on the wrong row — silently, producing a table that looks
    perfectly well-formed and is scrambled. Repeating the key columns in every chunk costs
    a few bytes per row and makes the merge verifiable.

PROVENANCE
    Source is P01, read-only, over SNC/SSO. Bare table names in the golden mean P01, which
    is the standing convention, so these load under their real SAP names.

USAGE
    python scripts/extraction/load_wide_tables.py SETHEADER SETNODE SETLEAF
    python scripts/extraction/load_wide_tables.py --all
"""
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# RFC_READ_TABLE's work area is 512 characters. Leave room rather than discover the edge.
MAX_WIDTH = 460
FIKRS = ["UNES", "IIEP", "ICTP", "UIS", "UIL", "IBE", "UBO", "MGIE", "ICBA"]

# What to load, and how to keep each read under the ceiling. `partition` names a column to
# split on when one read would return too much; None means the table is small enough whole.
PLAN = {
    "SETHEADER":  {"partition": None, "why": "set master — which hierarchies and groups exist"},
    "SETNODE":    {"partition": None, "why": "set structure — a set that contains another set"},
    "SETLEAF":    {"partition": None, "why": "set contents — the actual values in each group"},
    "SETHEADERT": {"partition": None, "why": "set names in language"},
    # The derivation-tool strategy tables. MEASURED EMPTY in P01 and loaded anyway: an
    # empty table that was checked is evidence, and the next session must not have to
    # rediscover that it is empty.
    "T811C":      {"partition": None, "why": "derivation-tool STRATEGY header — measured EMPTY"},
    "T811S":      {"partition": None, "why": "derivation-tool STEPS — measured EMPTY"},
    "T811K":      {"partition": None, "why": "derivation-tool step key fields — measured EMPTY"},
    "T811X":      {"partition": None, "why": "which derivation POINTS are registered — 4, and FMDERIVE is not one"},
    "T811I":      {"partition": None, "why": "derivation-tool field metadata"},
    # The mechanism actually in use: classic FM account-assignment derivation.
    "TABADRSF":   {"partition": None, "why": "CLASSIC FM derivation — the rule rows actually in use"},
    "TABADRS":    {"partition": None, "why": "classic FM derivation strategies"},
    "TABADRST":   {"partition": None, "why": "classic FM derivation strategy texts"},
    "TABADRH":    {"partition": None, "why": "classic FM derivation headers"},
    "TABADRX":    {"partition": None, "why": "classic FM derivation assignment"},
    "TABADRPCONF": {"partition": None, "why": "classic FM derivation process config"},
    # THE BUDGET-RATE SHADOW LEDGER. The BR solution does not convert amounts in place —
    # it maintains a PARALLEL set of tables keyed like the standard ones, holding the
    # fixed-rate valuation of every FM line. None of it was in the golden, so the entire
    # mechanism was unmeasurable.
    "YTFM_BR_FMIFIIT": {"partition": "GJAHR", "values": ["2024", "2025", "2026"],
                        "why": "BR shadow of FM ACTUAL line items — fixed-rate ZFKBTR/ZTRBTR"},
    "YTFM_BR_FMIOI":   {"partition": "GJAHR", "values": ["2024", "2025", "2026"],
                        "why": "BR shadow of FM COMMITMENTS — the fund reservations"},
    "YTFM_BR_FM_POS":  {"partition": None,
                        "why": "BR encumbrance positions, carrying BETRG_BEFORE — the before/after trail"},
    "YTFM_BR_PAYPI":   {"partition": None, "why": "BR PAYROLL items — the personnel path"},
    "YTFM_BR_PAYPH":   {"partition": None, "why": "BR payroll header"},
    "YTFM_BR_PAYPER":  {"partition": None, "why": "BR payroll period control"},
    "YTFM_BR_REP_H":   {"partition": None, "why": "BR report header"},
    "YTFM_BR_REP_D":   {"partition": "GJAHR", "values": ["2024", "2025", "2026"],
                        "why": "BR report detail"},
    # RE-PULL WITH ALL FIELDS. These tables are already in the golden as narrow extracts
    # that dropped every custom column. The loader reads the whole dictionary definition, so
    # re-pulling them is how the custom fields become measurable at all.
    "PRPS":       {"partition": None,
                   "why": "WBS element — 12 custom fields: donor, agencies, and the five PSC percentages"},
    "PROJ":       {"partition": None, "why": "project definition — re-pull for any custom fields"},
    "FMFINCODE":  {"partition": "FIKRS", "values": FIKRS,
                   "why": "fund master — carries ZZOUTPUT (native C/5 link) and ZZIBF"},
    "FMFUNDTYPE": {"partition": None,
                   "why": "fund type — carries ZZFIX_RATE, the flag gating the budget-rate perimeter"},
    "T001":       {"partition": None, "why": "company code — carries YYORGEH"},
    "T003":       {"partition": None, "why": "document type — carries YYBLART_GRP"},
    "T003T":      {"partition": None, "why": "document type text — carries YYNAME"},
    "YTHR_SORG_RULE": {"partition": None, "why": "custom HR org rule — carries ZZSECT"},
    # The COMMITMENT lines. The golden holds a 13-column extract without VRGNG, BTART or
    # TWAER — precisely the fields that identify a purchase-order reduction, which is the
    # one budget-rate baseline we could not evaluate.
    "FMIOI":      {"partition": "GJAHR", "values": ["2024", "2025", "2026"],
                   "why": "FM commitments — re-pull with all fields for the EKBE baseline"},
    # HR organisational assignment. Feature YYCDR — the personnel budget-rate perimeter —
    # is evaluated against PERSG, GSBER and WERKS on this infotype, and no HR table was in
    # the golden at all.
    "PA0001":     {"partition": None, "why": "HR org assignment — the fields feature YYCDR decides on"},
    # The transport record at source. cts_transports was built without as4text, and the
    # text is what says WHY a transport exists — the difference between a fix and a data move.
    "E070":       {"partition": None, "why": "transport headers — status, type, owner, date"},
    "E07T":       {"partition": None, "why": "transport TEXTS — the field cts_transports left empty"},
    # THE PAYROLL CALCULATION LAYER. Read live this session and not persisted — which meant
    # every payroll question needed a live P01 connection. This is the layer that computes
    # staff cost and none of it was held.
    "T52C0":      {"partition": None, "why": "payroll schema steps — the engine"},
    "T52C1":      {"partition": None, "why": "client-specific schemas, >30 custom"},
    "T52C5":      {"partition": None, "why": "payroll RULE lines — 166,453 of them"},
    "T512T":      {"partition": None, "why": "wage-type texts — where BR for Staff surfaced"},
    "T512W":      {"partition": None, "why": "wage-type processing classes"},
    "T549D":      {"partition": None, "why": "feature directory — each compiles to a readable program"},
    "T549B":      {"partition": None, "why": "feature decision-tree nodes"},
    "T52EL":      {"partition": None, "why": "wage type to symbolic account — measured EMPTY for UN"},
    # THE PAYROLL-TO-FM BRIDGE, and it is CUSTOM. Symbolic account x employee grouping ->
    # company code, business area, cost centre, FUND CENTRE and FUND. Not a GL mapping —
    # an FM account assignment, which is why the search through T030 could never find it.
    # THE ANSWER TO THE ACCOUNT DETERMINATION, and it is not a config table: the posting
    # document ITEMS carry the symbolic account AND the resolved GL account on the same row.
    "PPDHD":      {"partition": None, "why": "payroll posting document headers — run to document"},
    "PPDIT":      {"partition": "BUKRS", "values": ["UNES","IIEP","ICTP","UIS","UIL","IBE","UBO","MGIE","ICBA"],
                   "why": "payroll posting ITEMS — KTOSL and HKONT together, the resolved assignment"},
    "PPDIX":      {"partition": None, "why": "posting run index — run to document line"},
    "T9POST":     {"partition": None, "why": "payroll symbolic account -> FM account assignment (custom)"},
    "T9FUND":     {"partition": None, "why": "payroll symbolic account -> fund (custom)"},
    "T030B":      {"partition": None, "why": "payroll account determination — symbolic account to GL, the last link"},
    "T52EZ":      {"partition": None, "why": "payroll posting: symbolic account by employee grouping"},
    "T52EK":      {"partition": None, "why": "symbolic account to transaction key — measured EMPTY"},
    # The enhancement registry: what is hooked where. Read live to find the ZFIX family.
    "ENHOBJ":     {"partition": None, "why": "enhancement to hooked object"},
    "ENHINCINX":  {"partition": None, "why": "enhancement to its generated include"},
    "TSTC":       {"partition": None, "why": "transaction to program — resolves a tcode to what it runs"},
    # Scope rule: 2024-2026 only. RYEAR is in the key, so it partitions cleanly.
    # Loaded under a DIFFERENT golden name and swapped in one step at the end: bkpf is read
    # by other processes and must never be visible half-replaced.
    "BKPF_FULL":  {"partition": "GJAHR", "values": ["2024", "2025", "2026"], "sap_table": "BKPF",
                   "why": "FI header with ALL fields — WWERT, the translation date, decides which rate a document used"},
    "FMIT":       {"partition": "RYEAR", "values": ["2024", "2025", "2026"],
                   "why": "FM TOTALS — the report leg the golden has never held"},
}


class Session(object):
    """P01 drops after roughly a dozen calls. A dropped call is not an answer, so retry it
    — but only for the transport failure. A real error is a real answer and must surface."""

    def __init__(self):
        self.c = get_connection("P01")
        self.calls = 0
        self.reconnects = 0

    def call(self, fm, **kw):
        for attempt in range(4):
            try:
                r = self.c.call(fm, **kw)
                self.calls += 1
                return r
            except Exception as e:
                m = str(e)
                if "COMMUNICATION_FAILURE" not in m and "not reached" not in m:
                    raise
                self.reconnects += 1
                time.sleep(2 + attempt * 3)
                self.c = get_connection("P01")
        raise RuntimeError("P01 unreachable after retries")


def sap_name(t):
    """The SAP table to READ. Lets a load land under a different golden name so a live
    table is never left half-replaced — build beside it, swap once, atomically."""
    return PLAN.get(t, {}).get("sap_table", t)


def fields_of(s, table):
    r = s.call("DDIF_FIELDINFO_GET", TABNAME=table, ALL_TYPES="X")
    out = []
    for f in r.get("DFIES_TAB") or []:
        # Long/string columns cannot be read through RFC_READ_TABLE at all on this system.
        if f.get("INTTYPE") in ("g", "y") or (f.get("DATATYPE") or "") in ("STRG", "RSTR"):
            continue
        out.append({"name": f["FIELDNAME"], "len": int(f.get("LENG") or 0),
                    "key": f.get("KEYFLAG") == "X"})
    return out


def chunks_for(fields):
    """Split into reads that fit, with the KEY repeated in every one so the merge is by key."""
    keys = [f for f in fields if f["key"]]
    rest = [f for f in fields if not f["key"]]
    kw = sum(f["len"] for f in keys)
    if kw >= MAX_WIDTH:
        raise RuntimeError("the key alone exceeds the work area — needs a different reader")
    out, cur, w = [], [], kw
    for f in rest:
        if w + f["len"] > MAX_WIDTH and cur:
            out.append(keys + cur)
            cur, w = [], kw
        cur.append(f)
        w += f["len"]
    out.append(keys + cur)
    return out, [f["name"] for f in keys]


def parse(res):
    meta = res.get("FIELDS", [])
    rows = []
    for row in res.get("DATA", []):
        wa = row.get("WA", "")
        rows.append({f["FIELDNAME"]: wa[int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
                     for f in meta})
    return rows


def read_table(s, table, plan):
    fields = fields_of(s, sap_name(table))
    if not fields:
        return None, "no readable fields", None
    groups, keys = chunks_for(fields)
    parts = plan.get("values") if plan.get("partition") else [None]

    merged = {}
    order = []
    for gi, grp in enumerate(groups):
        for pv in parts:
            opt = ("%s = '%s'" % (plan["partition"], pv)) if pv else ""
            try:
                res = s.call("RFC_READ_TABLE", QUERY_TABLE=sap_name(table),
                             FIELDS=[{"FIELDNAME": f["name"]} for f in grp],
                             OPTIONS=([{"TEXT": opt}] if opt else []), ROWCOUNT=0)
            except Exception as e:
                m = str(e)
                if "TABLE_WITHOUT_DATA" in m:
                    continue
                return None, "%s%s: %s" % (table, (" " + pv) if pv else "", m[:110]), fields
            for row in parse(res):
                k = tuple(row.get(x, "") for x in keys)
                if k not in merged:
                    merged[k] = {}
                    order.append(k)
                merged[k].update(row)
        print("      chunk %d/%d  filas acumuladas %d" % (gi + 1, len(groups), len(merged)))
    return [merged[k] for k in order], None, fields


def write(con, table, rows, fields=None, append=False, slice_col=None, slice_val=None):
    """Write the table — INCLUDING when it came back empty.

    An empty table that was actually read is evidence, and dropping it on the floor means
    the next session cannot tell "we checked and it is empty" from "we never looked". That
    distinction is the whole point of measuring a configuration table.
    """
    if not rows:
        if not fields:
            return 0
        cur = con.cursor()
        cur.execute('DROP TABLE IF EXISTS "%s"' % table)
        cur.execute('CREATE TABLE "%s" (%s)'
                    % (table, ",".join('"%s" TEXT' % f["name"] for f in fields)))
        con.commit()
        return 0
    # Build the replacement BESIDE the original and swap only once it is complete. The
    # obvious order — DROP, CREATE, INSERT — destroys the existing extract the moment
    # anything fails afterwards, and these re-pulls are precisely the case where a table we
    # already hold is being replaced by a wider version of itself.
    cols = list(rows[0].keys())
    tmp = "%s__loading" % table
    cur = con.cursor()
    cur.execute('DROP TABLE IF EXISTS "%s"' % tmp)
    cur.execute('CREATE TABLE "%s" (%s)' % (tmp, ",".join('"%s" TEXT' % c for c in cols)))
    cur.executemany('INSERT INTO "%s" VALUES (%s)' % (tmp, ",".join("?" * len(cols))),
                    [[r.get(c, "") for c in cols] for r in rows])
    con.commit()
    if append:
        # A sliced load adds one partition; dropping the table would discard the others.
        # It must also be IDEMPOTENT: delete the slice before inserting it, or a retry
        # after a failure that got as far as the INSERT silently doubles the partition.
        # That is not hypothetical — it happened, and the duplicate looked like a clean load.
        cols_sql = ",".join('"%s" TEXT' % c for c in cols)
        cur.execute('CREATE TABLE IF NOT EXISTS "%s" (%s)' % (table, cols_sql))
        if slice_col and slice_val is not None:
            cur.execute('DELETE FROM "%s" WHERE trim("%s")=?' % (table, slice_col), (slice_val,))
        cur.execute('INSERT INTO "%s" SELECT * FROM "%s"' % (table, tmp))
        con.commit()
        cur.execute('DROP TABLE IF EXISTS "%s"' % tmp)
    else:
        cur.execute('DROP TABLE IF EXISTS "%s"' % table)
        cur.execute('ALTER TABLE "%s" RENAME TO "%s"' % (tmp, table))
    con.commit()
    return len(rows)


def main(argv):
    # A partitioned table can exceed any single run. --year narrows the partition so a big
    # table is loaded one slice at a time and a dropped connection costs one slice, not all.
    year = None
    if "--year" in argv:
        year = argv[argv.index("--year") + 1]
        argv = [a for a in argv if a != "--year" and a != year]
    want = [a for a in argv if not a.startswith("--")]
    if "--all" in argv or not want:
        want = list(PLAN)
    unknown = [t for t in want if t not in PLAN]
    if unknown:
        print("no estan en el plan: %s" % ", ".join(unknown))
        return 2

    if year:
        for t in want:
            if PLAN[t].get("values"):
                PLAN[t] = dict(PLAN[t], values=[year], _sliced=True)
    s = Session()
    con = sqlite3.connect(str(GOLD))
    print("CARGA INICIAL desde P01 (solo lectura) -> golden")
    print("=" * 70)
    done, failed = [], []
    for t in want:
        print("\n%s  — %s" % (t, PLAN[t]["why"]))
        rows, err, flds = read_table(s, t, PLAN[t])
        if err:
            print("   FALLO: %s" % err)
            failed.append((t, err))
            continue
        n = write(con, t, rows, flds, append=bool(year),
                  slice_col=PLAN[t].get("partition"), slice_val=year)
        print("   escritas %d filas" % n)
        done.append((t, n))
    con.close()
    print("\n%s" % ("=" * 70))
    for t, n in done:
        print("   %-14s %8d filas" % (t, n))
    for t, e in failed:
        print("   %-14s FALLO  %s" % (t, e[:70]))
    print("   llamadas RFC %d, reconexiones %d" % (s.calls, s.reconnects))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

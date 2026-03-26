"""
bdc_full_inventory.py — Complete BDC Session Inventory + Transaction Resolution
================================================================================
Covers ALL session types (no top-10 limit) for last 90 days.
Resolves every session to a transaction code or business process.

Key facts from probe run:
  - PROGID='MSSY1' on numeric sessions → MSS = Message Server System Y1
    Y1 is the SAP SYSTEM ID (SID) of the source system sending BDC via ALE/tRFC
    → These are NOT Allos sessions. They originate from SAP system Y1.
    → MSSY1 = Logical System "MSSY1" (SAP HCM Y1 production = payroll system)
  - FORMID = '2026' → year of payroll run
  - Session name = PERNR + payroll-area-code + run-counter
    Example: 10155259V901 = PERNR=10155259, V9=payroll-area, 01=run number
  - These are PAYROLL POSTING sessions (FI posting from HCM payroll results)
    Transaction behind: PC00_M99_CIPE or direct FI posting

Usage:
    python bdc_full_inventory.py               # Full inventory, P01, 90 days
    python bdc_full_inventory.py --creator GAMA-BERNA
    python bdc_full_inventory.py --creator COLLOCA
    python bdc_full_inventory.py --extended    # includes DESTSYS + PROGID detail
    python bdc_full_inventory.py --json > bdc_full_$(date '+%Y%m%d').json
"""

import os, sys, json, argparse, re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

import pyrfc


def rfc_connect():
    params = {
        "ashost": env("SAP_P01_ASHOST", default="172.16.4.100"),
        "sysnr":  env("SAP_P01_SYSNR",  default="00"),
        "client": env("SAP_P01_CLIENT", default="350"),
    }
    snc_mode = env("SAP_P01_SNC_MODE")
    snc_pn   = env("SAP_P01_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"]        = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"]         = env("SAP_P01_SNC_QOP", default="9")
    else:
        params["user"]   = env("SAP_P01_USER", "SAP_USER")
        params["passwd"] = env("SAP_P01_PASSWORD", "SAP_P01_PASSWD")
    return pyrfc.Connection(**params)


def parse_fixed(wa, fields):
    result = {}; p = 0
    for f in fields:
        w = int(f.get("LENGTH", 10))
        result[f["FIELDNAME"]] = wa[p:p+w].strip() if p < len(wa) else ""
        p += w + 1
    return result


def rfc_table(conn, table, field_names, where_clauses, max_rows=5000):
    """Safe RFC_READ_TABLE call. where_clauses = list of WHERE text strings."""
    fields = [{"FIELDNAME": f} for f in field_names]
    options = [{"TEXT": t} for t in where_clauses]
    r = conn.call("RFC_READ_TABLE",
        QUERY_TABLE=table,
        FIELDS=fields,
        OPTIONS=options,
        ROWCOUNT=max_rows,
    )
    schema = r.get("FIELDS", [])
    return [parse_fixed(row["WA"], schema) for row in r.get("DATA", [])], schema


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTION DECODER
# ─────────────────────────────────────────────────────────────────────────────

QSTATE_MAP = {" ": "NEW", "": "NEW", "E": "ERROR", "P": "PROCESSING",
              "F": "DONE", "Z": "BG_QUEUE", "2": "PROCESSED", "S": "PROCESSED",
              "C": "PROCESSED"}

TCODE_DESC = {
    "PA30": "HR: Maintain HR Master Data (infotype)",
    "PA40": "HR: Personnel Actions",
    "PA20": "HR: Display HR Master Data",
    "PR05": "Travel: Expense Report",
    "TRIP": "Travel: Business Trip",
    "FMBB": "FM: Transfer Budget",
    "FB01": "FI: Post Document",
    "FB60": "FI: Vendor Invoice",
    "PC00_M99_CIPE": "Payroll: International Posting to FI",
    "PCP0": "Payroll: Payroll Posting",
    "F110": "FI: Payment Run",
    "ME21N": "MM: Create Purchase Order",
}

# Known PROGID → what system/process creates these sessions
PROGID_INTEL = {
    "MSSY1": {
        "description": "SAP System Y1 (HCM Payroll Backend) → sends payroll posting BDC via tRFC/ALE",
        "tcode":       "PC00_M99_CIPE / PCP0 (Payroll-to-FI posting)",
        "process":     "PAYROLL POSTING: After payroll run on Y1, results are posted to FI via BDC",
        "source":      "SAP Payroll system (not Allos — this is system-to-system automation)",
    },
    "MSS": {
        "description": "SAP Manager Self Service system",
        "tcode":       "PA30 / PA40",
        "process":     "HR action originating from MSS portal",
        "source":      "MSS portal → BDC",
    },
    "SY1": {
        "description": "SAP System Y1 (another system, ALE/IDoc queue processor)",
        "tcode":       "PR05 / TRIP (Travel Management)",
        "process":     "Travel expense posting from HR system via ALE",
        "source":      "Inter-system ALE (explains TRIP_MODIFY 1180 sessions)",
    },
    "R0": {
        "description": "RPRAMASS0 / PRAAUNESC_SC creator — standard PA mass update report",
        "tcode":       "PA30 / PA40",
        "process":     "Personnel master data mass update (Allos-generated)",
        "source":      "Allos Excel VBA macro → SAP BDC",
    },
}

def decode_session_name(groupid: str, progid: str, creator: str) -> dict:
    """Resolve a session name to its transaction and business process."""
    gid = groupid.strip().upper()
    pid = progid.strip().upper()
    cre = creator.strip().upper()

    # ── Known named sessions ──────────────────────────────────────────────────
    named_patterns = {
        "PRAAUNESC_SC": ("PA30/PA40", "Personnel Admin — infotype update", "Allos"),
        "PRAAUNESU_SC": ("PA30",      "Personnel Admin — individual employee", "Allos"),
        "PRAAUNESU_ST": ("PA30",      "Personnel Admin — time infotypes", "Allos"),
        "TRIP_MODIFY":  ("PR05/TRIP", "Travel expense modification", "ALE from Y1"),
        "OBBATCH":      ("OB52/FB01", "FI period open/close or batch posting", "Automated"),
        "HUNUPSR0":     ("PA30/PA40", "HCM mass infotype update (HUNUPSR0 standard)", "HR batch"),
        "SUPPORT COST": ("FMBB/FB01", "FM support cost allocation", "Finance automation"),
    }
    if gid in named_patterns:
        tc, proc, src = named_patterns[gid]
        return {"tcode": tc, "process": proc, "source": src, "confidence": "HIGH"}

    # ── PROGID-based resolution ───────────────────────────────────────────────
    if pid in PROGID_INTEL:
        intel = PROGID_INTEL[pid]
        return {
            "tcode":      intel["tcode"],
            "process":    intel["process"],
            "source":     intel["source"],
            "confidence": "HIGH",
        }

    # ── Numeric pattern: [PERNR][PAYROLL-AREA][RUN] → payroll posting ─────────
    # e.g. 63178940U101 = PERNR=63178940, Payroll-area variant U1, run 01
    #      10155259V901 = PERNR=10155259, Payroll-area V9, run 01
    if re.match(r'^\d{6,10}[A-Z]\d{2,4}$', gid):
        m = re.match(r'^(\d{6,10})([A-Z])(\d{2,4})$', gid)
        if m:
            pernr_part  = m.group(1)
            payroll_var = m.group(2)
            run_id      = m.group(3)
            # V/U = payroll variant letters used in UNESCO payroll areas
            payroll_area = f"{payroll_var}{run_id[:2]}"
            return {
                "tcode":   "PC00_M99_CIPE / PCP0",
                "process": f"PAYROLL POSTING to FI — PERNR {pernr_part}, "
                           f"Payroll-area variant '{payroll_var}', run {run_id}",
                "source":  f"SAP Y1 payroll system → BDC to P01 FI (via {pid})",
                "confidence": "HIGH",
                "pernr":   pernr_part,
                "payroll_area": payroll_area,
            }

    # ── Creator-based hints ───────────────────────────────────────────────────
    if "BATCH" in cre or "BBATCH" in cre:
        return {"tcode": "PA30", "process": "Automated PA batch (BBATCH service user)",
                "source": "Allos or scheduled ABAP", "confidence": "MEDIUM"}

    return {"tcode": "?", "process": f"Unknown — PROGID={pid}", "source": creator,
            "confidence": "LOW"}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN INVENTORY
# ─────────────────────────────────────────────────────────────────────────────

def fetch_full_inventory(conn, days=90, creator_filter=None):
    """Fetch ALL sessions from APQI for the last N days, optionally filtered by creator."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    where = [f"CREDATE >= '{cutoff}'"]
    if creator_filter:
        # Exact match — RFC_READ_TABLE does not support OR in single query
        safe = creator_filter.replace("'", "").upper()
        where.append(f"AND CREATOR LIKE '%{safe}%'")

    try:
        rows, _ = rfc_table(conn, "APQI",
            ["GROUPID", "QID", "CREATOR", "CREDATE", "CRETIME",
             "QSTATE", "PROGID", "FORMID", "DESTSYS", "DESTAPP", "TRANSCNT"],
            where,
            max_rows=5000,
        )
    except Exception as ex:
        print(f"  [APQI fetch error: {ex}]")
        return []

    for r in rows:
        r["QSTATE_DESC"] = QSTATE_MAP.get(r.get("QSTATE", ""), r.get("QSTATE", ""))

    return rows


def build_group_report(all_rows):
    """Aggregate APQI rows into per-GROUPID intelligence."""
    by_group = defaultdict(list)
    for r in all_rows:
        by_group[r.get("GROUPID", "?").strip()].append(r)

    groups = []
    for gid, members in sorted(by_group.items(), key=lambda x: -len(x[1])):
        states    = Counter(m["QSTATE_DESC"] for m in members)
        creators  = Counter(m.get("CREATOR", "?").strip() for m in members)
        progids   = Counter(m.get("PROGID", "").strip() for m in members)
        formids   = Counter(m.get("FORMID", "").strip() for m in members)
        destsyss  = Counter(m.get("DESTSYS", "").strip() for m in members)

        top_creator = creators.most_common(1)[0][0]
        top_progid  = progids.most_common(1)[0][0]

        decode = decode_session_name(gid, top_progid, top_creator)

        groups.append({
            "groupid":       gid,
            "total":         len(members),
            "states":        dict(states),
            "top_creator":   top_creator,
            "all_creators":  dict(creators.most_common(5)),
            "progid":        top_progid,
            "formid":        formids.most_common(1)[0][0] if formids else "",
            "destsys":       destsyss.most_common(1)[0][0] if destsyss else "",
            "tcode":         decode["tcode"],
            "process":       decode["process"],
            "source":        decode["source"],
            "confidence":    decode["confidence"],
            "pernr":         decode.get("pernr", ""),
            "payroll_area":  decode.get("payroll_area", ""),
        })

    return groups


# ─────────────────────────────────────────────────────────────────────────────
# EXTENDED: Resolve MSSY1 + check PA0001 for one sample PERNR
# ─────────────────────────────────────────────────────────────────────────────

def resolve_mssy1(conn):
    """Check logical system tables to confirm what MSSY1 is."""
    print("\n  [MSSY1 Resolution]")

    # Try TBDLS — logical system name table
    for tbl in ["TBDLS", "TBDLT", "BD54"]:
        try:
            rows, _ = rfc_table(conn, tbl,
                ["LOGSYS", "STEXT"] if tbl in ("TBDLS","BD54") else ["LOGSYS"],
                ["LOGSYS LIKE 'MSSY%' OR LOGSYS LIKE 'Y1%'"],
            )
            if rows:
                print(f"    {tbl} → {rows[:5]}")
        except:
            pass

    # Try RFCDES — RFC destinations
    try:
        rows, _ = rfc_table(conn, "RFCDES",
            ["RFCDEST", "RFCTYPE", "RFCSYSID", "RFCHOST"],
            ["RFCDEST LIKE 'MSSY%' OR RFCDEST LIKE 'Y1%'"],
            max_rows=20,
        )
        if rows:
            print(f"    RFC Destinations matching Y1/MSSY1:")
            for r in rows:
                print(f"      {r}")
    except Exception as ex:
        print(f"    RFCDES: {str(ex)[:60]}")

    # Try to read program MSSY1 source
    for prog in ["MSSY1", "PC00_M99_CIPE", "RPCIPEU0", "RPCIPE99"]:
        try:
            r = conn.call("RFC_READ_REPORT", PROGRAM=prog)
            lines = r.get("QTAB", [])
            if lines:
                print(f"    Program '{prog}' found — {len(lines)} lines")
                for l in [x.get("LINE","") for x in lines[:10]]:
                    print(f"      {l}")
                break
        except:
            pass


def check_pernr_in_pa0001(conn, pernr: str):
    """Verify if a numeric string is a real UNESCO personnel number."""
    try:
        rows, schema = rfc_table(conn, "PA0001",
            ["PERNR", "ENAME", "ORGEH", "PLANS", "BEGDA"],
            [f"PERNR = '{pernr.zfill(8)}'", "AND ENDDA >= '20260101'"],
            max_rows=1,
        )
        if rows:
            return rows[0]
    except:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PRINT
# ─────────────────────────────────────────────────────────────────────────────

CONFIDENCE_ICON = {"HIGH": "✅", "MEDIUM": "🔎", "LOW": "❓"}

def print_full_inventory(groups, verify_pernr=False, conn=None):

    # Summary table — ALL sessions
    print(f"\n{'═'*100}")
    print(f"  COMPLETE BDC SESSION INVENTORY — LAST 90 DAYS")
    print(f"  Total distinct session types: {len(groups)} | "
          f"Total sessions: {sum(g['total'] for g in groups)}")
    print(f"{'═'*100}")
    print(f"  {'#':>3}  {'Session Type':<28}  {'Vol':>5}  {'Transaction':<28}  "
          f"{'Creator':<18}  {'Conf'}  Business Process")
    print(f"  {'─'*3}  {'─'*28}  {'─'*5}  {'─'*28}  {'─'*18}  {'─'*4}  {'─'*40}")

    for i, g in enumerate(groups, 1):
        conf_icon = CONFIDENCE_ICON.get(g["confidence"], "❓")
        short_proc = g["process"][:50]
        print(f"  {i:>3}  {g['groupid']:<28}  {g['total']:>5}  "
              f"{g['tcode']:<28}  {g['top_creator']:<18}  {conf_icon}    "
              f"{short_proc}")

    # ── By source type ─────────────────────────────────────────────────────
    print(f"\n\n{'═'*80}")
    print(f"  GROUPED BY SOURCE / ORIGIN")
    print(f"{'═'*80}")

    by_source = defaultdict(list)
    for g in groups:
        src = g["source"]
        if "Allos" in src:
            by_source["🔴  ALLOS (Excel VBA → BDC)"].append(g)
        elif "payroll" in src.lower() or "Payroll" in src or "Y1" in src:
            by_source["🟠  PAYROLL SYSTEM (SAP Y1 → BDC)"].append(g)
        elif "ALE" in src:
            by_source["🔵  ALE/tRFC (System Integration)"].append(g)
        elif "batch" in src.lower() or "Batch" in src or "HR batch" in src:
            by_source["🟡  ABAP BATCH (Scheduled Programs)"].append(g)
        else:
            by_source["⚪  OTHER / UNKNOWN"].append(g)

    total_by_source = {}
    for source_label, items in sorted(by_source.items()):
        vol = sum(i["total"] for i in items)
        total_by_source[source_label] = vol
        print(f"\n  {source_label}  [{vol} sessions in 90d]")
        for g in sorted(items, key=lambda x: -x["total"]):
            pernr_note = f" (PERNR:{g['pernr']})" if g.get("pernr") else ""
            print(f"    {g['groupid']:<30}  ×{g['total']:>5}  "
                  f"{g['tcode']:<25}  {g['top_creator']}{pernr_note}")

    # ── Creator breakdown ──────────────────────────────────────────────────
    print(f"\n\n{'═'*80}")
    print(f"  CREATOR / USER BREAKDOWN (Who is creating BDC sessions?)")
    print(f"{'═'*80}")
    all_creators = Counter()
    for g in groups:
        for creator, cnt in g.get("all_creators", {}).items():
            all_creators[creator] += cnt

    for creator, total in all_creators.most_common(25):
        flag = ""
        if "_" in creator or "BATCH" in creator.upper(): flag = " ← SERVICE/AUTOMATED"
        elif creator.upper() in ("COLLOCA", "GAMA-BERNA", "TOUFFAHI"): flag = " ← Allos user"
        print(f"    {creator:<25}  {total:>5} sessions{flag}")

    # ── Verify PERNR ──────────────────────────────────────────────────────
    if verify_pernr and conn:
        print(f"\n\n{'═'*80}")
        print(f"  PERNR VERIFICATION — Are numeric session names = employee numbers?")
        print(f"{'═'*80}")
        checked = set()
        for g in groups:
            if g.get("pernr") and g["pernr"] not in checked:
                checked.add(g["pernr"])
                emp = check_pernr_in_pa0001(conn, g["pernr"])
                if emp:
                    print(f"  ✅ {g['pernr']} → {emp.get('ENAME','?'):30}  "
                          f"Org:{emp.get('ORGEH','?')}  Pos:{emp.get('PLANS','?')}")
                else:
                    print(f"  ❌ {g['pernr']} → Not found in PA0001")
                if len(checked) >= 5:
                    break

    # ── Replacement roadmap ────────────────────────────────────────────────
    print(f"\n\n{'═'*80}")
    print(f"  ALLOS REPLACEMENT ROADMAP")
    print(f"{'═'*80}")
    allos_sessions = [g for g in groups if "Allos" in g.get("source","")]
    if allos_sessions:
        total_allos = sum(g["total"] for g in allos_sessions)
        print(f"  Allos-generated BDC sessions (last 90d): {total_allos}")
        print(f"  {'Session':<28}  {'Volume':>6}  Transaction     → Replacement BAPI")
        print(f"  {'─'*28}  {'─'*6}  {'─'*14}    {'─'*35}")
        bapi_map = {
            "PA30": "BAPI_EMPLOYEE_ENQUEUE + HR_INFOTYPE_OPERATION",
            "PA40": "BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA",
            "PA30/PA40": "BAPI_EMPLOYEE_ENQUEUE",
            "FMBB/FB01": "BAPI_ACC_COMMITMENT_CREATE",
        }
        for g in sorted(allos_sessions, key=lambda x: -x["total"]):
            bapi = bapi_map.get(g["tcode"], "Research needed")
            print(f"  {g['groupid']:<28}  {g['total']:>6}  {g['tcode']:<14}  → {bapi}")
    else:
        print("  No sessions classified as Allos (check --creator filters)")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Complete BDC session inventory — ALL sessions, last 90 days")
    parser.add_argument("--days",      type=int, default=90)
    parser.add_argument("--creator",   type=str, default=None,
        help="Filter by creator substring (e.g. GAMA-BERNA, COLLOCA, BBATCH)")
    parser.add_argument("--extended",  action="store_true",
        help="Run MSSY1 + PERNR verification")
    parser.add_argument("--pernr",     action="store_true",
        help="Verify if numeric prefixes are real personnel numbers in PA0001")
    parser.add_argument("--json",      action="store_true",
        help="Output as JSON")
    args = parser.parse_args()

    print(f"\n{'═'*80}")
    print(f"  BDC COMPLETE INVENTORY — UNESCO P01 Production")
    print(f"  Period: Last {args.days} days (3 months)  |  "
          f"{'Creator: ' + args.creator if args.creator else 'ALL creators'}")
    print(f"{'═'*80}")

    conn = rfc_connect()
    print(f"  ✅ Connected to P01")

    # If no creator filter, run passes for common creators separately (OR workaround)
    if not args.creator:
        print(f"\n  Reading all APQI sessions (no creator filter)...")
        all_rows = fetch_full_inventory(conn, days=args.days)

        # Also fetch by creator substrings that might not match otherwise
        # (GAMA-BERNA has a hyphen that sometimes gets truncated in fixed-width)
        for extra_creator in ["GAMA-BERNA", "GAMA_BERNA"]:
            extra = fetch_full_inventory(conn, days=args.days,
                                          creator_filter=extra_creator)
            # Merge (avoid duplicates by QID)
            existing_qids = {r.get("QID","") for r in all_rows}
            for r in extra:
                if r.get("QID","") not in existing_qids:
                    all_rows.append(r)
    else:
        all_rows = fetch_full_inventory(conn, days=args.days,
                                         creator_filter=args.creator)

    print(f"  Total APQI records: {len(all_rows)}")

    if not all_rows:
        print("  No sessions found.")
        conn.close()
        return

    groups = build_group_report(all_rows)

    if args.extended:
        resolve_mssy1(conn)

    if args.json:
        print(json.dumps(groups, indent=2, ensure_ascii=False, default=str))
        conn.close()
        return

    print_full_inventory(groups, verify_pernr=args.pernr, conn=conn)

    print(f"\n{'═'*80}")
    print(f"  Run with --pernr to verify employee numbers")
    print(f"  Run with --extended for MSSY1/RFC destination resolution")
    print(f"  Run with --json to export for Brain import")
    print(f"{'═'*80}\n")

    conn.close()


if __name__ == "__main__":
    main()

"""
bdc_deep_analysis.py — Deep Batch Input (BDC) Session Intelligence
===================================================================

Goes BELOW the APQI header level to extract:
  A) Which ABAP PROGRAM creates each BDC session   (APQI.PROGID / .FORMID)
  B) For sessions still in ERROR state: APQD records still exist → read them
  C) From APQD: TCODE, DYNPRO screen numbers, FNAM/FVAL field data
  D) Decode session naming patterns to identify the business process

This is a SEPARATE tool from sap_system_monitor.py.
The monitor shows HIGH-LEVEL counts.
This tool does the DEEP FORENSIC ANALYSIS of individual BDC sessions.

Key insight about APQD availability:
  - QSTATE=' '/NEW   → APQD still exists (session not yet processed)
  - QSTATE='E'/ERROR → APQD still exists (processing failed, data preserved)
  - QSTATE='F'/DONE  → APQD is DELETED (SAP purges it after successful run)
  - QSTATE='2'       → Processed/consumed (APQD deleted)

Strategy:
  1. Focus on ERROR sessions first (APQD guaranteed to exist)
  2. Then decode PROGID to find the ABAP program that creates the BDC
  3. Read that ABAP program's source to see which TCODE it drives

Usage:
    python bdc_deep_analysis.py                     # last 90 days, P01
    python bdc_deep_analysis.py --session PRAAUNESC_SC
    python bdc_deep_analysis.py --state E           # ERROR sessions only
    python bdc_deep_analysis.py --top 10 --sample 10
    python bdc_deep_analysis.py --json > bdc_intel_$(date +%Y%m%d).json

System: Always runs against P01 (production data). Use --system D01 for dev.

Author: Antigravity / UNESCO SAP Intelligence
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter


# ──────────────────────────────────────────────────────────────────────────────
# CONNECTION
# ──────────────────────────────────────────────────────────────────────────────

def load_config():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    def env(*keys, default=""):
        for k in keys:
            v = os.getenv(k)
            if v:
                return v
        return default

    return {
        "D01": {
            "host":    env("SAP_ASHOST",     default="172.16.4.66"),
            "sysnr":   env("SAP_SYSNR",      default="00"),
            "client":  env("SAP_CLIENT",     default="350"),
            "user":    env("SAP_USER"),
            "passwd":  env("SAP_PASSWD", "SAP_PASSWORD"),
            "snc_mode":        env("SAP_SNC_MODE"),
            "snc_partnername": env("SAP_SNC_PARTNERNAME"),
            "snc_qop":         env("SAP_SNC_QOP"),
        },
        "P01": {
            "host":    env("SAP_P01_ASHOST", default="172.16.4.100"),
            "sysnr":   env("SAP_P01_SYSNR",  default="00"),
            "client":  env("SAP_P01_CLIENT", default="350"),
            "user":    env("SAP_P01_USER", "SAP_USER"),
            "passwd":  env("SAP_P01_PASSWORD", "SAP_P01_PASSWD"),
            "snc_mode":        env("SAP_P01_SNC_MODE"),
            "snc_partnername": env("SAP_P01_SNC_PARTNERNAME"),
            "snc_qop":         env("SAP_P01_SNC_QOP"),
        },
    }


def rfc_connect(cfg: dict):
    import pyrfc
    params = {
        "ashost": cfg["host"],
        "sysnr":  cfg["sysnr"],
        "client": cfg["client"],
    }
    if cfg.get("snc_mode") and cfg.get("snc_partnername"):
        params["snc_mode"]        = cfg["snc_mode"]
        params["snc_partnername"] = cfg["snc_partnername"]
        params["snc_qop"]         = cfg.get("snc_qop", "9")
    else:
        params["user"]   = cfg.get("user", "")
        params["passwd"] = cfg.get("passwd", "")
    import pyrfc
    return pyrfc.Connection(**params)


def parse_fixed_width(row_wa: str, fields: list) -> dict:
    """
    Parse a RFC_READ_TABLE WA string using the FIELDS metadata.
    Each field has FIELDNAME and LENGTH. Fields are separated by a single space.
    """
    result = {}
    p = 0
    for f in fields:
        name = f["FIELDNAME"]
        w    = int(f.get("LENGTH", 10))
        val  = row_wa[p:p+w] if p + w <= len(row_wa) else row_wa[p:]
        result[name] = val.strip()
        p += w + 1  # +1 for the separator space
    return result


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1: Read APQI headers — correctly parsed
# ──────────────────────────────────────────────────────────────────────────────

QSTATE_MAP = {
    " ": "NEW",
    "":  "NEW",
    "E": "ERROR",
    "P": "PROCESSING",
    "F": "DONE",
    "Z": "BG_QUEUE",
    "2": "PROCESSED",
    "C": "PROCESSED",
}

def fetch_apqi(conn, days: int = 90, session_filter: str = None,
               state_filter: str = None, max_rows: int = 2000) -> list[dict]:
    """
    Read APQI batch input queue index.
    Returns list of dicts with: GROUPID, CREATOR, CREDATE, QSTATE, QID, PROGID, FORMID
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # Build WHERE clauses — RFC_READ_TABLE uses AND-chained rows
    where = [{"TEXT": f"CREDATE >= '{cutoff}'"}]
    if session_filter:
        safe = session_filter.replace("'", "").upper()
        where.append({"TEXT": f" AND GROUPID = '{safe}'"})
    if state_filter:
        safe_st = state_filter.replace("'", "").upper()
        where.append({"TEXT": f" AND QSTATE = '{safe_st}'"})

    result = conn.call("RFC_READ_TABLE",
        QUERY_TABLE="APQI",
        FIELDS=[
            {"FIELDNAME": "GROUPID"},
            {"FIELDNAME": "QID"},
            {"FIELDNAME": "CREATOR"},
            {"FIELDNAME": "CREDATE"},
            {"FIELDNAME": "CRETIME"},
            {"FIELDNAME": "QSTATE"},
            {"FIELDNAME": "PROGID"},
            {"FIELDNAME": "FORMID"},
        ],
        OPTIONS=where,
        ROWCOUNT=max_rows,
    )

    fields = result.get("FIELDS", [])
    rows   = []
    for row in result.get("DATA", []):
        d = parse_fixed_width(row["WA"], fields)
        d["QSTATE_DESC"] = QSTATE_MAP.get(d.get("QSTATE", ""), d.get("QSTATE", "?"))
        rows.append(d)
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2: APQD — Read BDC detail records (only available for non-processed sessions)
# ──────────────────────────────────────────────────────────────────────────────

def fetch_apqd(conn, qid: str) -> list[dict]:
    """
    Read APQD BDC data records for a single QID.
    Returns list of screen/field records.
    Returns empty list if APQD has been purged (processed sessions).
    """
    try:
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="APQD",
            FIELDS=[
                {"FIELDNAME": "QID"},
                {"FIELDNAME": "DSATZ"},
                {"FIELDNAME": "TCODE"},
                {"FIELDNAME": "DYNBEGIN"},
                {"FIELDNAME": "DYNPRO"},
                {"FIELDNAME": "FNAM"},
                {"FIELDNAME": "FVAL"},
            ],
            OPTIONS=[{"TEXT": f"QID = '{qid}'"}],
            ROWCOUNT=5000,
        )
        fields = result.get("FIELDS", [])
        rows   = []
        for row in result.get("DATA", []):
            rows.append(parse_fixed_width(row["WA"], fields))
        return rows
    except Exception:
        return []  # TABLE_WITHOUT_DATA — session processed, APQD purged


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3: Parse APQD into structured screen flow
# ──────────────────────────────────────────────────────────────────────────────

def parse_screen_flow(apqd_rows: list[dict]) -> dict:
    """
    Converts raw APQD field rows into a structured session:
    {
      "tcode": "PA30",
      "screens": [
        {"dynpro": "0100", "fields": [{"name": "PA0008-TRFKZ", "value": "05"}, ...]},
        ...
      ]
    }
    """
    tcode = ""
    screens = []
    current = None

    for row in apqd_rows:
        if row.get("TCODE"):
            tcode = row["TCODE"].strip()
        if row.get("DYNBEGIN") == "X":
            if current:
                screens.append(current)
            current = {"dynpro": row.get("DYNPRO", "").strip(), "fields": []}
        elif current is not None:
            fn = row.get("FNAM", "").strip()
            fv = row.get("FVAL", "").strip()
            if fn:
                current["fields"].append({"name": fn, "value": fv})

    if current:
        screens.append(current)

    return {"tcode": tcode, "screens": screens}


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4: Get ABAP program source for PROGID → find embedded TCODE
# ──────────────────────────────────────────────────────────────────────────────

def find_tcode_in_program(conn, progid: str) -> list[str]:
    """
    Read ABAP program source and extract BDC transaction codes.
    Looks for patterns like: TCODE = 'PA30', 'Call Transaction'
    """
    if not progid or len(progid) < 3:
        return []
    try:
        result = conn.call("RFC_READ_REPORT",
            PROGRAM=progid,
            INCLUDE="",
        )
        lines = [l.get("LINE", "") for l in result.get("QTAB", [])]
        tcodes = []
        import re
        for line in lines:
            line_u = line.upper()
            # Pattern 1: CALL TRANSACTION 'PA30'
            m = re.findall(r"CALL\s+TRANSACTION\s+'([A-Z0-9_]+)'", line_u)
            tcodes.extend(m)
            # Pattern 2: BDC_INSERT ... with 'TCODE' = 'PA30'
            m2 = re.findall(r"TCODE\s*[=:]\s*'([A-Z0-9_]+)'", line_u)
            tcodes.extend([t for t in m2 if t not in ("", "BDC")])
            # Pattern 3: BDC_OPEN_GROUP with TCODE
            m3 = re.findall(r"OPEN_GROUP.*TCODE\s*=\s*'([A-Z0-9_]+)'", line_u)
            tcodes.extend(m3)
        return list(set(tcodes))
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5: Check BDCP (BDC change pointer) — another angle
# ──────────────────────────────────────────────────────────────────────────────

def fetch_bdcp_sample(conn, days: int = 90) -> list[dict]:
    """
    BDCP = BDC Change Pointers. These survive after BDC processing.
    Can reveal which object types / table names are being updated.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d%H%M%S")
    try:
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="BDCP",
            FIELDS=[
                {"FIELDNAME": "TABNAME"},
                {"FIELDNAME": "TABKEY"},
                {"FIELDNAME": "FLDNAME"},
                {"FIELDNAME": "CRETIME"},
                {"FIELDNAME": "USRNAME"},
            ],
            ROWCOUNT=100,
        )
        fields = result.get("FIELDS", [])
        rows   = []
        for row in result.get("DATA", []):
            rows.append(parse_fixed_width(row["WA"], fields))
        return rows
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6: Decode session name patterns
# ──────────────────────────────────────────────────────────────────────────────

SESSION_PATTERN_INTELLIGENCE = {
    # UNESCO HCM Personnel Admin
    "PRAAUNESC_SC": {
        "likely_tcode":  ["PA30", "PA40"],
        "business":      "UNESCO Personnel Admin — PA infotype update (Allos → PA30 via BDC)",
        "owner":         "_COLLOCA / _GAMA-BERNA (automated Allos users)",
        "replacement":   "Custom Fiori HCM app with BAPI_EMPLOYEE_ENQUEUE / HRPAD00INFTY",
    },
    "PRAAUNESU_SC": {
        "likely_tcode":  ["PA30"],
        "business":      "UNESCO Personnel Admin variant 2 (same pattern, different scope)",
        "owner":         "automated",
        "replacement":   "Same as PRAAUNESC_SC",
    },
    "PRAAUNESU_ST": {
        "likely_tcode":  ["PA30"],
        "business":      "UNESCO Personnel Admin — Time-related infotypes",
        "owner":         "automated",
        "replacement":   "Fiori Time Management app",
    },
    "TRIP_MODIFY": {
        "likely_tcode":  ["PR05", "TRIP"],
        "business":      "Travel expense modification — users submitting/modifying trip reports",
        "owner":         "individual users (NOT automated — real users via Fiori)",
        "replacement":   "Already likely Fiori — investigate if standard app is used",
    },
    "OBBATCH": {
        "likely_tcode":  ["OB52", "FS00", "FB01"],
        "business":      "FI period open/close automation or batch posting",
        "owner":         "OBBATCH background job user",
        "replacement":   "Custom Fiori period management or BAPI_ACC_DOCUMENT_POST",
    },
    "HUNUPSR0": {
        "likely_tcode":  ["PA30", "PA40"],
        "business":      "HCM infotype mass update program (RPUAUD00/similar)",
        "owner":         "automated HR process",
        "replacement":   "BAPI_EMPLOYEE_ENQUEUE + infotype BAPI",
    },
    "SUPPORT COST": {
        "likely_tcode":  ["FMBB", "FI01", "FB01"],
        "business":      "Support Cost allocation — FM budget entry automation",
        "owner":         "automated budget process",
        "replacement":   "Custom Fiori Budget Upload app with BAPI_ACC_COMMITMENT_CREATE",
    },
}

def decode_session_name(groupid: str) -> dict:
    """Try to decode a session name against known patterns."""
    groupid_upper = groupid.upper().strip()

    # Exact match
    if groupid_upper in SESSION_PATTERN_INTELLIGENCE:
        return SESSION_PATTERN_INTELLIGENCE[groupid_upper]

    # Numeric pattern: e.g. '63178940U101', '10155259V901'
    import re
    if re.match(r'^\d+[A-Z]\d+$', groupid_upper):
        return {
            "likely_tcode":  ["unknown — decode from numeric ID"],
            "business":      f"Numeric session ID — likely from automated ABAP job. Pattern: {groupid_upper}",
            "owner":         "automated background job",
            "replacement":   "Investigate ABAP program that creates this session",
            "notes":         "Pattern: [sequence][suffix-code][client] — common in payroll/HR batch",
        }

    return {
        "likely_tcode":  ["unknown"],
        "business":      f"Unknown pattern: {groupid}",
        "owner":         "unknown",
        "replacement":   "Need APQD data or program source analysis",
    }


# ──────────────────────────────────────────────────────────────────────────────
# TCODE descriptions
# ──────────────────────────────────────────────────────────────────────────────

TCODE_DESC = {
    "PA30": "HR: Maintain HR Master Data (infotype change via screen)",
    "PA40": "HR: Personnel Actions (hiring, org change, termination)",
    "PA20": "HR: Display HR Master Data",
    "PA10": "HR: Personnel File",
    "PA03": "HR: Payroll Control Record",
    "PR05": "Travel: Travel Expense Manager",
    "TRIP": "Travel: Trip — create/modify business trip",
    "PR10": "Travel: Travel Request",
    "FMBB": "FM: Transfer Budget (Funds Reservation)",
    "FMRP": "FM: Budget Report",
    "OB52": "FI: Maintain Accounting Period",
    "FB01": "FI: Post Document",
    "FB60": "FI: Enter Vendor Invoice",
    "F-02": "FI: General Posting",
    "FBV0": "FI: Post Parked Documents",
    "ME21N": "MM: Create Purchase Order",
    "ME22N": "MM: Change Purchase Order",
    "CATS": "Cross Application Time Sheet",
    "PT50": "Time: Quota Overview",
    "HUNUPSR0": "HR: Mass Update — recurring infotype update program",
}

def describe(tcode: str) -> str:
    return TCODE_DESC.get(tcode, "— (research needed)")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN REPORT
# ──────────────────────────────────────────────────────────────────────────────

def run_analysis(conn, days: int, top: int, sample: int,
                 session_filter: str, state_filter: str,
                 verbose: bool, raw_json: bool) -> list[dict]:

    results = []

    # ── 1. Get APQI headers ──────────────────────────────────────────────────
    print(f"\n  [1/4] Reading APQI session headers (last {days} days)...")
    headers = fetch_apqi(conn, days=days, session_filter=session_filter,
                         state_filter=state_filter)

    if not headers:
        print("  → No BDC sessions found.")
        return []

    print(f"  → Found {len(headers)} total session records")

    # Group by GROUPID
    by_group = defaultdict(list)
    for h in headers:
        gid = h.get("GROUPID", "?").strip()
        by_group[gid].append(h)

    # Sort by frequency
    sorted_groups = sorted(by_group.items(), key=lambda x: len(x[1]), reverse=True)
    if session_filter:
        sorted_groups = [(g, v) for g, v in sorted_groups
                         if session_filter.upper() in g.upper()]
    groups_to_analyse = sorted_groups[:top]

    print(f"\n  Session types found: {len(sorted_groups)}")
    print(f"  Analysing top {len(groups_to_analyse)}:")
    print(f"\n  {'Session Name':<30}  {'Total':>6}  {'NEW':>5}  {'ERROR':>6}  {'DONE':>5}  Creator(s)")
    print(f"  {'-'*30}  {'-'*6}  {'-'*5}  {'-'*6}  {'-'*5}  {'-'*20}")
    for gid, members in sorted_groups[:20]:
        states = Counter(m["QSTATE_DESC"] for m in members)
        creators = Counter(m.get("CREATOR", "?") for m in members)
        top_creator = creators.most_common(1)[0][0] if creators else "?"
        print(f"  {gid:<30}  {len(members):>6}  "
              f"{states.get('NEW',0):>5}  {states.get('ERROR',0):>6}  "
              f"{states.get('DONE',0):>5}  {top_creator}")

    # ── 2. PROGID → ABAP program source (find TCODEs in code) ────────────────
    print(f"\n  [2/4] Extracting ABAP program source for PROGID identification...")
    progid_tcode_cache = {}
    all_progids = {m.get("PROGID", "").strip()
                   for _, members in groups_to_analyse
                   for m in members
                   if m.get("PROGID", "").strip()}
    for progid in list(all_progids)[:20]:
        if progid and progid not in progid_tcode_cache:
            tcodes = find_tcode_in_program(conn, progid)
            progid_tcode_cache[progid] = tcodes
            if tcodes:
                print(f"    PROGID {progid:<20} → TCODEs: {tcodes}")

    # ── 3. APQD drill-down for ERROR/NEW sessions (APQD still alive) ─────────
    print(f"\n  [3/4] Drilling into APQD (ERROR/NEW sessions only — DONE sessions purged)...")

    for gid, members in groups_to_analyse:
        # Find sessions where APQD likely still exists
        active_sessions = [m for m in members
                           if m.get("QSTATE_DESC") in ("NEW", "ERROR", "PROCESSING")]
        sample_sessions = active_sessions[:sample]

        apqd_flows = []
        all_tcodes = Counter()
        all_screens = Counter()
        all_fields = Counter()

        if sample_sessions:
            print(f"\n    '{gid}': {len(active_sessions)} ERROR/NEW sessions → sampling {len(sample_sessions)}")
            for session in sample_sessions:
                qid = session.get("QID", "").strip()
                if not qid:
                    continue
                apqd_rows = fetch_apqd(conn, qid)
                if not apqd_rows:
                    continue
                flow = parse_screen_flow(apqd_rows)
                apqd_flows.append(flow)
                if flow["tcode"]:
                    all_tcodes[flow["tcode"]] += 1
                for screen in flow["screens"]:
                    all_screens[screen["dynpro"]] += 1
                    for field in screen["fields"]:
                        fn = field["name"]
                        if fn not in ("BDC_CURSOR", "BDC_OKCODE"):
                            all_fields[fn] += 1
        else:
            print(f"\n    '{gid}': No ERROR/NEW sessions → using pattern intelligence + PROGID analysis")

        # ── 4. Aggregate result for this group ────────────────────────────────
        pattern = decode_session_name(gid)

        # Merge PROGID-found TCODEs with APQD-found TCODEs
        progid_tcodes = []
        for m in members[:5]:
            pid = m.get("PROGID", "").strip()
            if pid in progid_tcode_cache:
                progid_tcodes.extend(progid_tcode_cache[pid])

        # Determine final tcode intelligence
        confirmed_tcodes = dict(all_tcodes)
        inferred_tcodes  = list(set(progid_tcodes)) if not confirmed_tcodes else []

        # Creator breakdown
        creators = Counter(m.get("CREATOR", "?").strip() for m in members)
        state_breakdown = Counter(m["QSTATE_DESC"] for m in members)

        result = {
            "groupid":          gid,
            "total_sessions":   len(members),
            "state_breakdown":  dict(state_breakdown),
            "top_creators":     dict(creators.most_common(5)),
            "progids":          list({m.get("PROGID","").strip() for m in members if m.get("PROGID","").strip()}),
            "formids":          list({m.get("FORMID","").strip() for m in members if m.get("FORMID","").strip()})[:3],
            "apqd_sampled":     len(apqd_flows),
            "confirmed_tcodes": confirmed_tcodes,
            "inferred_tcodes":  inferred_tcodes,
            "pattern_intel":    pattern,
            "top_screens":      dict(all_screens.most_common(15)) if all_screens else {},
            "top_fields":       dict(all_fields.most_common(25)) if all_fields else {},
            "sample_flows":     apqd_flows[:2] if verbose else [],
        }
        results.append(result)

    # ── Check BDCP ────────────────────────────────────────────────────────────
    print(f"\n  [4/4] Checking BDCP change pointer table...")
    bdcp_rows = fetch_bdcp_sample(conn, days=days)
    if bdcp_rows:
        tables = Counter(r.get("TABNAME", "?") for r in bdcp_rows)
        print(f"    BDCP has {len(bdcp_rows)} rows. Top tables changed:")
        for tbl, cnt in tables.most_common(10):
            print(f"      {tbl:<20}  ×{cnt}")
    else:
        print("    BDCP: No rows accessible")

    return results


# ──────────────────────────────────────────────────────────────────────────────
# REPORT PRINTER
# ──────────────────────────────────────────────────────────────────────────────

def print_report(results: list[dict], verbose: bool = False):

    for r in results:
        gid   = r["groupid"]
        total = r["total_sessions"]
        states = r["state_breakdown"]
        creators = r["top_creators"]
        pattern  = r["pattern_intel"]
        conf_tc  = r["confirmed_tcodes"]
        inf_tc   = r["inferred_tcodes"]
        progids  = r["progids"]
        sampled  = r["apqd_sampled"]

        print(f"\n{'═'*72}")
        print(f"  SESSION: {gid}")
        print(f"  Last 90d: {total} sessions  │  "
              f"States: {states}  │  "
              f"APQD sampled: {sampled}")
        print(f"{'─'*72}")

        # Confirmed transactions (from live APQD)
        print(f"\n  [TRANSACTIONS — CONFIRMED via APQD]")
        if conf_tc:
            for tc, cnt in sorted(conf_tc.items(), key=lambda x: -x[1]):
                print(f"    ✅ {tc:<10}  (in {cnt} of {sampled} samples)  {describe(tc)}")
        else:
            print(f"    (All sessions processed — APQD purged.)")

        # Inferred from PROGID source code
        print(f"\n  [TRANSACTIONS — INFERRED from ABAP Source (PROGID)]")
        if inf_tc:
            for tc in inf_tc:
                print(f"    🔎 {tc:<10}  {describe(tc)}")
        elif progids:
            print(f"    PROGID(s): {progids}  → source scan returned no TCODEs")
        else:
            print(f"    No PROGID available in this session type.")

        # Pattern intelligence
        print(f"\n  [PATTERN INTELLIGENCE]")
        pat_tcodes = pattern.get("likely_tcode", [])
        print(f"    Business process  : {pattern.get('business', '?')}")
        print(f"    Likely TCODEs     : {', '.join(pat_tcodes)}")
        print(f"    Owner/creator     : {pattern.get('owner', '?')}")
        print(f"    Replacement path  : {pattern.get('replacement', '?')}")
        if pattern.get("notes"):
            print(f"    Notes             : {pattern['notes']}")

        # Top creators
        print(f"\n  [TOP CREATORS]")
        for creator, cnt in list(creators.items())[:5]:
            flag = " ← AUTOMATED (service user?)" if "_" in creator or cnt > 50 else ""
            print(f"    {creator:<25}  ×{cnt}{flag}")

        # ABAP programs involved
        if progids:
            print(f"\n  [ABAP PROGRAMS (PROGID — what generates this BDC)]")
            for pid in progids[:5]:
                print(f"    {pid}")

        # Screens and fields (if available)
        if r.get("top_screens"):
            print(f"\n  [SCREENS VISITED (DYNPRO)]")
            for scr, cnt in list(r["top_screens"].items())[:10]:
                print(f"    Dynpro {scr:<10}  ×{cnt}")

        if r.get("top_fields"):
            print(f"\n  [FIELDS PROCESSED (business data)]")
            print(f"    {'Field Name':<40}  Count")
            print(f"    {'-'*40}  -----")
            for fn, cnt in list(r["top_fields"].items())[:20]:
                print(f"    {fn:<40}  {cnt}")

        # Verbose: show one full sample flow
        if verbose and r.get("sample_flows"):
            flow = r["sample_flows"][0]
            print(f"\n  [SAMPLE SESSION WALKTHROUGH]")
            print(f"    Transaction: {flow.get('tcode','?')}")
            for i, scr in enumerate(flow.get("screens", [])[:20]):
                print(f"    Screen {i+1}: Dynpro {scr.get('dynpro','?')}")
                for fld in scr.get("fields", [])[:15]:
                    if fld["name"] not in ("BDC_CURSOR",):
                        print(f"      {fld['name']:<40} = '{fld['value']}'")


def print_summary(results: list[dict]):
    print(f"\n\n{'═'*72}")
    print(f"  ALLOS/BDC REPLACEMENT ROADMAP SUMMARY")
    print(f"{'═'*72}")
    print(f"  {'Priority':<10}  {'Session':<25}  {'Sessions':>8}  "
          f"{'Transaction(s)':<25}  {'Creator'}")
    print(f"  {'-'*10}  {'-'*25}  {'-'*8}  {'-'*25}  {'-'*20}")

    for r in sorted(results, key=lambda x: x["total_sessions"], reverse=True):
        gid    = r["groupid"][:24]
        total  = r["total_sessions"]
        conf   = list(r["confirmed_tcodes"].keys())
        infer  = r["inferred_tcodes"]
        pat    = r["pattern_intel"].get("likely_tcode", [])
        tcodes = (conf or infer or pat)[:3]
        tc_str = ", ".join(tcodes) if tcodes else "?"
        creator = list(r["top_creators"].keys())[0] if r["top_creators"] else "?"

        if total >= 100:  priority = "🔴 CRITICAL"
        elif total >= 20: priority = "🟡 HIGH    "
        elif total >= 5:  priority = "🟢 MEDIUM  "
        else:             priority = "🔵 LOW     "

        print(f"  {priority}  {gid:<25}  {total:>8}  {tc_str:<25}  {creator}")

    print(f"\n  Key insight: APQD records are PURGED after successful processing.")
    print(f"  Use --state E to focus on ERROR sessions (APQD data still live).")
    print(f"  Pattern intelligence fills the gap for processed sessions.")


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BDC Deep Analysis — APQD transaction and field intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bdc_deep_analysis.py
      Top 10 session types, last 90 days (P01)

  python bdc_deep_analysis.py --session PRAAUNESC_SC --verbose
      Full drill-down on PRAAUNESC_SC with field walkthrough

  python bdc_deep_analysis.py --state E --sample 10
      Focus only on ERROR sessions (APQD data guaranteed present)

  python bdc_deep_analysis.py --json > bdc_intelligence.json
      Export full JSON for brain import or further processing

  python bdc_deep_analysis.py --top 20
      Analyse top 20 session types (wider coverage)
""")
    parser.add_argument("--system",  default="P01", choices=["D01", "P01"])
    parser.add_argument("--days",    type=int, default=90,
        help="Lookback window in days (default: 90 = 3 months)")
    parser.add_argument("--top",     type=int, default=10,
        help="Analyse top N session types by frequency")
    parser.add_argument("--sample",  type=int, default=10,
        help="Max sessions to sample per group for APQD drill-down")
    parser.add_argument("--session", type=str, default=None,
        help="Filter to a specific GROUPID (e.g., PRAAUNESC_SC)")
    parser.add_argument("--state",   type=str, default=None,
        help="Filter by QSTATE: E=ERROR, F=DONE, ' '=NEW")
    parser.add_argument("--verbose", action="store_true",
        help="Print full screen-by-screen field walkthrough for one example")
    parser.add_argument("--json",    action="store_true",
        help="Output results as JSON (for brain import)")
    args = parser.parse_args()

    cfg_all = load_config()
    cfg     = cfg_all.get(args.system.upper(), cfg_all["P01"])

    print(f"\n{'═'*72}")
    print(f"  BDC DEEP ANALYSIS — Transaction & Field Intelligence")
    print(f"  System  : {args.system}  {cfg['host']}  client={cfg['client']}")
    print(f"  SNC/SSO : {'YES' if cfg.get('snc_mode') else 'NO'}")
    print(f"  Window  : Last {args.days} days (3 months)")
    print(f"  Focus   : Top {args.top} session types, sampling {args.sample} each")
    print(f"{'═'*72}")

    try:
        conn = rfc_connect(cfg)
        print(f"  ✅ Connected to {args.system}")
    except Exception as ex:
        print(f"  ❌ Connection failed: {ex}")
        sys.exit(1)

    try:
        results = run_analysis(
            conn,
            days=args.days,
            top=args.top,
            sample=args.sample,
            session_filter=args.session,
            state_filter=args.state,
            verbose=args.verbose,
            raw_json=args.json,
        )
    finally:
        conn.close()

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        return

    print_report(results, verbose=args.verbose)
    print_summary(results)

    print(f"\n{'═'*72}")
    print(f"  Done. Add --verbose for field-level walkthrough.")
    print(f"  Add --state E to focus on live ERROR sessions.")
    print(f"  Add --json > bdc_intelligence.json to save for Brain.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()

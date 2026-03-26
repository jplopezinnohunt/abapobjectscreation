"""
sap_system_monitor.py — SAP System Intelligence Dashboard
==========================================================

Answers the key operational questions:
  - WHO is connected right now? (active users, sessions)
  - WHAT transactions are being used?
  - WHICH programs/objects are obsolete or unused?
  - WHAT batch inputs / BDC sessions exist? (SM35 — Allos replacement discovery)
  - WHAT background jobs are scheduled? (SM37)
  - WHAT errors/dumps are happening? (ST22)
  - HOW is the workload distributed? (SM50/SM66 equivalent)

Uses BOTH channels:
  - Python RFC (SNC, no password) → SM04, SM35, SM37, workload, user stats
  - ADT REST (HTTP, Basic Auth)   → Runtime dumps, usage references, object last change

Usage:
    python sap_system_monitor.py --report all
    python sap_system_monitor.py --report users
    python sap_system_monitor.py --report transactions
    python sap_system_monitor.py --report obsolete
    python sap_system_monitor.py --report dumps
    python sap_system_monitor.py --report bdc        # Batch input/SM35 discovery
    python sap_system_monitor.py --report jobs       # Background jobs SM37
"""

import os
import sys
import argparse
from datetime import datetime, timedelta


def load_config():
    """Load env vars inside function to avoid heap crash."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # ══ TWO-SYSTEM ARCHITECTURE ════════════════════════════════════
    # D01 (Development)  ← code deploy, BSP extract, ADT API
    # P01 (Production)   ← data, monitoring, BDC, users, obsolete
    # ══════════════════════════════════════════════════════════════
    def env(*keys, default=""):
        for k in keys:
            v = os.getenv(k)
            if v:
                return v
        return default

    return {
        # D01 — development / ADT
        "D01": {
            "host":    env("SAP_ASHOST", default="172.16.4.66"),
            "sysnr":   env("SAP_SYSNR",  default="00"),
            "client":  env("SAP_CLIENT", default="350"),
            "user":    env("SAP_USER"),
            "passwd":  env("SAP_PASSWD", "SAP_PASSWORD"),
            "snc_mode":     env("SAP_SNC_MODE"),
            "snc_partnername": env("SAP_SNC_PARTNERNAME"),
            "snc_qop":      env("SAP_SNC_QOP"),
            "adt_host": env("SAP_HOST", default="HQ-SAP-D01.HQ.INT.UNESCO.ORG"),
            "adt_port": env("SAP_ADT_PORT", default="80"),
        },
        # P01 — production / data / monitoring
        "P01": {
            "host":    env("SAP_P01_ASHOST", default="172.16.4.100"),
            "sysnr":   env("SAP_P01_SYSNR",  default="00"),
            "client":  env("SAP_P01_CLIENT", default="350"),
            "user":    env("SAP_P01_USER", "SAP_USER"),
            "passwd":  env("SAP_P01_PASSWORD", "SAP_P01_PASSWD"),
            "snc_mode":     env("SAP_P01_SNC_MODE"),
            "snc_partnername": env("SAP_P01_SNC_PARTNERNAME"),
            "snc_qop":      env("SAP_P01_SNC_QOP"),
            "adt_host": env("SAP_P01_HOST", default="172.16.4.100"),
            "adt_port": env("SAP_P01_ADT_PORT", default="8000"),
        },
    }


def get_system_cfg(config: dict, system_id: str) -> dict:
    """Get config for a specific system (D01 or P01)."""
    return config.get(system_id.upper(), config["D01"])


def rfc_connect(cfg: dict):
    """
    Connect via RFC. Supports both password auth and SNC (SSO).
    cfg = one system's config dict (e.g. config['P01']).
    """
    import pyrfc
    params = {
        "ashost": cfg["host"],
        "sysnr":  cfg["sysnr"],
        "client": cfg["client"],
        "user":   cfg["user"],
    }
    # SNC (SSO) takes precedence over password
    if cfg.get("snc_mode") and cfg.get("snc_partnername"):
        params["snc_mode"]        = cfg["snc_mode"]
        params["snc_partnername"] = cfg["snc_partnername"]
        params["snc_qop"]         = cfg.get("snc_qop", "9")
        # Remove user/passwd for SNC trust login
        params.pop("user", None)
    elif cfg.get("passwd"):
        params["passwd"] = cfg["passwd"]
    else:
        # No password, no SNC — try without (will likely fail)
        pass

    return pyrfc.Connection(**params)


def rfc_connect_indirect(d01_cfg: dict, p01_dest: str = "P01CLNT350"):
    """
    Indirect access: connect to D01, then reach P01 via RFC destination
    (SM59 RFC destination, e.g. 'P01CLNT350'). Returns D01 connection
    plus the dest name to pass as DEST= in RFC calls.

    Usage:
        conn, dest = rfc_connect_indirect(config['D01'])
        conn.call('RFC_READ_TABLE', QUERY_TABLE='APQI', ...,
                  DESTINATION=dest)   # executes on P01 via SM59
    """
    conn = rfc_connect(d01_cfg)
    return conn, p01_dest


def adt_get(cfg: dict, path: str):
    """Raw ADT GET for a system config dict. Returns (status, text)."""
    import urllib.request, base64
    user   = cfg.get("user", "")
    passwd = cfg.get("passwd", "")
    client = cfg.get("client", "350")
    host   = cfg.get("adt_host", "")
    port   = cfg.get("adt_port", "80")
    auth   = "Basic " + base64.b64encode(f"{user}:{passwd}".encode()).decode()
    url    = f"http://{host}:{port}{path}?sap-client={client}"
    req    = urllib.request.Request(url, headers={"Authorization": auth, "Accept": "application/xml"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as ex:
        return 0, str(ex)


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 1: ACTIVE USERS & SESSIONS (SM04 equivalent)
# ══════════════════════════════════════════════════════════════════════════════

def report_active_users(cfg):
    """
    Who is connected RIGHT NOW.
    
    Data sources:
      RFC: TH_USER_LIST → active dialog sessions
      RFC: RFC_READ_TABLE on USR02 → last login dates
    """
    print("\n" + "="*65)
    print("  📊 ACTIVE USERS & SESSIONS")
    print("="*65)

    try:
        conn = rfc_connect(cfg)

        # SM04 equivalent: get active work processes
        try:
            result = conn.call("TH_USER_LIST")
            users = result.get("USRLIST", [])
            print(f"\n  Active Sessions: {len(users)}\n")
            seen = set()
            for u in sorted(users, key=lambda x: x.get("BNAME", "")):
                key = (u.get("BNAME",""), u.get("TCODE",""))
                if key not in seen:
                    seen.add(key)
                    print(f"  User: {u.get('BNAME','?'):15}  "
                          f"TCode: {u.get('TCODE','?'):10}  "
                          f"Terminal: {u.get('TERMINAL','?'):15}  "
                          f"Type: {u.get('TYPE','?')}")
        except Exception as ex:
            print(f"  [TH_USER_LIST failed: {ex}]")
            # Fallback: query USR02 for recent logins
            try:
                import pyrfc
                cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                result = conn.call("RFC_READ_TABLE",
                    QUERY_TABLE="USR02",
                    FIELDS=[{"FIELDNAME":"BNAME"},{"FIELDNAME":"TRDAT"},
                             {"FIELDNAME":"LTIME"},{"FIELDNAME":"UFLAG"}],
                    OPTIONS=[{"TEXT": f"TRDAT >= '{cutoff}'"}],
                    ROWCOUNT=50
                )
                rows = [r["WA"].split() for r in result.get("DATA", [])]
                fields = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
                print(f"\n  Users logged in last 30 days:")
                for row in result.get("DATA", []):
                    wa = row["WA"]
                    print(f"    {wa[:80]}")
            except Exception as ex2:
                print(f"  [USR02 fallback failed: {ex2}]")

        conn.close()

    except Exception as ex:
        print(f"  [RFC Connection failed: {ex}]")
        print("  → Trying ADT for user info...")
        status, body = adt_get(cfg, "/sap/bc/adt/system/users")
        print(f"  ADT /system/users: HTTP {status}")
        if status == 200:
            print(body[:800])


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 2: TRANSACTION USAGE (Which transactions are being used)
# ══════════════════════════════════════════════════════════════════════════════

def report_transaction_usage(cfg):
    """
    Which transactions are actively used vs. dead/obsolete.
    
    Data sources:
      RFC: RFC_READ_TABLE on TSTC → all Z-transactions
      RFC: RFC_READ_TABLE on TSTCT → transaction descriptions
      ADT: /informationsystem/usageReferences → who calls what
    """
    print("\n" + "="*65)
    print("  📋 TRANSACTION USAGE ANALYSIS")
    print("="*65)

    try:
        conn = rfc_connect(cfg)

        # Get all Z-custom transactions
        print("\n  [1] Custom Transactions (Z/Y prefix):")
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="TSTC",
            FIELDS=[{"FIELDNAME":"TCODE"},{"FIELDNAME":"PGMNA"},{"FIELDNAME":"CINFO"}],
            OPTIONS=[{"TEXT": "TCODE LIKE 'Z%' OR TCODE LIKE 'Y%'"}],
            ROWCOUNT=200
        )
        fields = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        tcodes = []
        for row in result.get("DATA", []):
            wa = row["WA"]
            # Parse fixed-width
            parts = wa.split()
            if parts:
                tcodes.append({"tcode": parts[0], "program": parts[1] if len(parts) > 1 else ""})

        print(f"  Found {len(tcodes)} custom transactions")
        for t in tcodes[:30]:
            print(f"    {t['tcode']:20}  → Program: {t['program']}")
        if len(tcodes) > 30:
            print(f"    ... ({len(tcodes)-30} more)")

        # SM20 security audit for usage — read SWFVARBIND or use workload
        print("\n  [2] SM50/SM66 Work Process Overview:")
        try:
            wl = conn.call("TH_WPINFO")
            procs = wl.get("WPLIST", [])
            print(f"  Work Processes: {len(procs)}")
            for p in procs[:15]:
                print(f"    PID:{p.get('WP_PID','?'):6}  "
                      f"Type:{p.get('WP_TYP','?'):4}  "
                      f"Status:{p.get('WP_STATUS','?'):10}  "
                      f"TCode:{p.get('WP_TCODE','?'):10}  "
                      f"User:{p.get('WP_UNAME','?')}")
        except Exception as ex:
            print(f"  [TH_WPINFO: {ex}]")

        conn.close()

    except Exception as ex:
        print(f"  [RFC failed: {ex}]")

    # ADT: usage references
    print("\n  [3] ADT Object Usage References:")
    status, body = adt_get(cfg, "/sap/bc/adt/repository/informationsystem/objecttypes")
    print(f"  Object type registry: HTTP {status}")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 3: OBSOLETE / UNUSED PROGRAMS DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def report_obsolete_programs(cfg, months_unused: int = 12):
    """
    Which custom programs have NOT been changed or likely not used recently.
    Uses REPOSRC (last change date) as the primary signal.
    TADIR is queried separately per object type to avoid its authorization block.
    """
    print("\n" + "="*65)
    print(f"  [OBSOLETE] Programs not changed in {months_unused}+ months")
    print("="*65)

    cutoff = (datetime.now() - timedelta(days=30*months_unused)).strftime("%Y%m%d")

    try:
        conn = rfc_connect(cfg)

        # REPOSRC: source code repository — has PROGNAME + UDATE (last change)
        print(f"\n  REPOSRC: Z-programs not changed since {cutoff[:4]}-{cutoff[4:6]}-{cutoff[6:]}...")
        try:
            result_rs = conn.call("RFC_READ_TABLE",
                QUERY_TABLE="REPOSRC",
                FIELDS=[{"FIELDNAME":"PROGNAME"},{"FIELDNAME":"UDATE"},
                        {"FIELDNAME":"UNAM"}],
                OPTIONS=[
                    {"TEXT": f"PROGNAME LIKE 'Z%' AND UDATE < '{cutoff}'"}
                ],
                ROWCOUNT=200
            )
            old_progs = result_rs.get("DATA", [])
            fields = result_rs.get("FIELDS", [])
            widths = [int(f.get("LENGTH", 30)) for f in fields]

            print(f"  Programs stale (not changed since cutoff): {len(old_progs)}")
            print(f"\n  {'Program':<40}  {'Last Changed':<12}  {'Changed By'}")
            print(f"  {'-'*40}  {'-'*12}  {'-'*12}")

            pos = 0
            for row in old_progs[:50]:
                wa = row["WA"]
                parts = []
                p = 0
                for w in widths:
                    parts.append(wa[p:p+w].strip())
                    p += w + 1   # +1 for separator
                prog  = parts[0] if len(parts) > 0 else "?"
                udate = parts[1] if len(parts) > 1 else "?"
                unam  = parts[2] if len(parts) > 2 else "?"
                fmt_date = f"{udate[:4]}-{udate[4:6]}-{udate[6:]}" if len(udate)==8 else udate or "NEVER"
                print(f"  {prog:<40}  {fmt_date:<12}  {unam}")

            if len(old_progs) > 50:
                print(f"  ... ({len(old_progs)-50} more). Run with --months to adjust threshold.")
        except Exception as ex:
            print(f"  [REPOSRC query: {ex}]")

        conn.close()

    except Exception as ex:
        print(f"  [RFC failed: {ex}]")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 6: BATCH INPUTS / SM35 — ALLOS REPLACEMENT DISCOVERY
# ══════════════════════════════════════════════════════════════════════════════

def report_batch_inputs(cfg, days: int = 90):
    """
    Discover which Batch Input (BDC) sessions are being created — key intelligence
    for identifying what the 'Allos' Excel/VBA tool is automating in SAP.

    The Allos tool generates BDC sessions that map to specific transactions.
    These sessions are prime candidates for replacement by custom Fiori/ABAP apps.

    Data sources:
      RFC: RFC_READ_TABLE on APQI → Batch input session queue index (SM35 backing)
      RFC: RFC_READ_TABLE on TBTCO → Scheduled background jobs (SM37)

    Key fields in APQI:
      GROUPID   - Session name (often reflects the business purpose)
      CREATOR   - User who created it (look for service user = likely Allos)
      CREDATE   - Creation date
      QSTATE    - Status: ' '=new, 'E'=error, 'P'=in process, 'F'=done
      DYNNR     - Transaction/screen being driven
    """
    print("\n" + "="*65)
    print(f"  [BATCH INPUT] SM35 Sessions & Allos Discovery (last {days} days)")
    print("="*65)

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    try:
        conn = rfc_connect(cfg)

        # --- APQI: Batch Input Queue Index (SM35 sessions) ---
        print("\n  [1] Batch Input Sessions (APQI — SM35):")
        try:
            result = conn.call("RFC_READ_TABLE",
                QUERY_TABLE="APQI",
                FIELDS=[
                    {"FIELDNAME": "GROUPID"},   # Session name
                    {"FIELDNAME": "CREATOR"},   # Who created it
                    {"FIELDNAME": "CREDATE"},   # Creation date
                    {"FIELDNAME": "QSTATE"},    # Status
                    {"FIELDNAME": "QID"},        # Queue ID
                ],
                OPTIONS=[{"TEXT": f"CREDATE >= '{cutoff}'"}],
                ROWCOUNT=500
            )
            sessions = result.get("DATA", [])
            fields   = result.get("FIELDS", [])
            widths   = [int(f.get("LENGTH", 20)) for f in fields]

            status_map = {" ": "NEW", "E": "ERROR", "P": "PROCESSING",
                          "F": "DONE", "Z": "BACKGROUND"}

            print(f"  Total BDC sessions last {days} days: {len(sessions)}")

            # Group by session name to spot patterns
            from collections import Counter
            session_names = []
            creators = []
            for row in sessions:
                wa = row["WA"]
                p  = 0
                parts = []
                for w in widths:
                    parts.append(wa[p:p+w].strip())
                    p += w + 1
                session_names.append(parts[0] if parts else "?")
                creators.append(parts[1] if len(parts) > 1 else "?")

            print(f"\n  Top Session Names (likely Allos/automated processes):")
            for name, count in Counter(session_names).most_common(20):
                print(f"    {name:<40}  x{count}")

            print(f"\n  Top Creators (who is generating BDC sessions?):")
            for creator, count in Counter(creators).most_common(15):
                flag = "  <-- AUTOMATED? (check if Allos user)" if count > 5 else ""
                print(f"    {creator:<20}  x{count}{flag}")

            print(f"\n  Detail (last 20 sessions):")
            print(f"  {'Session Name':<40}  {'Creator':<15}  {'Date':<10}  Status")
            print(f"  {'-'*40}  {'-'*15}  {'-'*10}  ------")
            for row in sessions[-20:]:
                wa = row["WA"]
                p  = 0
                parts = []
                for w in widths:
                    parts.append(wa[p:p+w].strip())
                    p += w + 1
                sname   = parts[0] if len(parts) > 0 else "?"
                creator = parts[1] if len(parts) > 1 else "?"
                credate = parts[2] if len(parts) > 2 else "?"
                qstate  = status_map.get(parts[3], parts[3]) if len(parts) > 3 else "?"
                fmt_date = f"{credate[:4]}-{credate[4:6]}-{credate[6:]}" if len(credate)==8 else credate
                print(f"  {sname:<40}  {creator:<15}  {fmt_date:<10}  {qstate}")

        except Exception as ex:
            print(f"  [APQI query failed: {ex}]")
            print(f"  Hint: Table may be APQR or BDC_TAB in some releases")

        # --- TBTCO: Background Jobs (SM37) ---
        print("\n  [2] Background Jobs (TBTCO — SM37):")
        try:
            result_j = conn.call("RFC_READ_TABLE",
                QUERY_TABLE="TBTCO",
                FIELDS=[
                    {"FIELDNAME": "JOBNAME"},
                    {"FIELDNAME": "SDLSTRTDT"},   # Scheduled start date
                    {"FIELDNAME": "STATUS"},       # A=active, F=finished, S=scheduled, P=running
                    {"FIELDNAME": "JOBCOUNT"},
                    {"FIELDNAME": "AUTHCKNAM"},    # Owner user
                ],
                OPTIONS=[{"TEXT": f"SDLSTRTDT >= '{cutoff}' AND JOBNAME LIKE 'Z%'"}],
                ROWCOUNT=200
            )
            jobs = result_j.get("DATA", [])
            fields_j = result_j.get("FIELDS", [])
            widths_j = [int(f.get("LENGTH", 20)) for f in fields_j]

            from collections import Counter
            job_names = []
            for row in jobs:
                wa = row["WA"]
                p  = 0
                parts = []
                for w in widths_j:
                    parts.append(wa[p:p+w].strip())
                    p += w + 1
                job_names.append(parts[0] if parts else "?")

            print(f"  Custom background jobs last {days} days: {len(jobs)}")
            print(f"\n  Top Job Names:")
            for name, count in Counter(job_names).most_common(20):
                print(f"    {name:<50}  x{count}")

        except Exception as ex:
            print(f"  [TBTCO query: {ex}]")

        conn.close()

    except Exception as ex:
        print(f"  [RFC failed: {ex}]")

    # --- Allos Replacement Strategy ---
    print("\n" + "-"*65)
    print("  [ALLOS REPLACEMENT STRATEGY]")
    print("-"*65)
    print("")
    print("  The Allos tool creates BDC sessions via Excel macros. Replace with:")
    print("")
    print("  Pattern 1: Data Upload (Excel → SAP table update)")
    print("    → Custom Fiori Upload App + BAPI/Function Module backend")
    print("    → File upload UI → ABAP parsing → BAPI call → result in UI")
    print("")
    print("  Pattern 2: Mass Transaction Execution (BDC batch replay)")
    print("    → Identify the target transaction from APQI.GROUPID name")
    print("    → Replace BDC with direct BAPI/RFC calls (no screen scraping)")
    print("    → Result Excel → replaced by Fiori table with Excel download")
    print("")
    print("  Pattern 3: Cross-system data extraction")
    print("    → Replace Excel macros with OData service + Fiori app")
    print("    → Our RFC/ADT toolkit already extracts any table/class")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 7: BACKGROUND JOBS (SM37 standalone)
# ══════════════════════════════════════════════════════════════════════════════

def report_jobs(cfg, days: int = 7):
    """List all custom background jobs scheduled/run recently (SM37)."""
    print("\n" + "="*65)
    print(f"  [JOBS] Background Job Overview (SM37, last {days} days)")
    print("="*65)
    report_batch_inputs.__wrapped_jobs = True  # reuse TBTCO logic above
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    try:
        conn = rfc_connect(cfg)
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="TBTCO",
            FIELDS=[{"FIELDNAME": "JOBNAME"},{"FIELDNAME": "STATUS"},
                    {"FIELDNAME": "SDLSTRTDT"},{"FIELDNAME": "AUTHCKNAM"}],
            OPTIONS=[{"TEXT": f"SDLSTRTDT >= '{cutoff}'"}],
            ROWCOUNT=300
        )
        jobs = result.get("DATA", [])
        fields = result.get("FIELDS", [])
        widths = [int(f.get("LENGTH", 20)) for f in fields]

        status_map = {"A": "ACTIVE", "F": "FINISHED", "S": "SCHEDULED",
                      "P": "RUNNING", "Z": "RELEASED"}
        from collections import Counter
        job_names, statuses = [], []
        for row in jobs:
            wa = row["WA"]; p = 0; parts = []
            for w in widths:
                parts.append(wa[p:p+w].strip()); p += w + 1
            job_names.append(parts[0] if parts else "?")
            statuses.append(status_map.get(parts[1], parts[1]) if len(parts) > 1 else "?")

        print(f"  Total jobs: {len(jobs)}")
        print(f"  Status breakdown: {dict(Counter(statuses))}")
        print(f"\n  {'Job Name':<50}  Status")
        print(f"  {'-'*50}  ------")
        for name, status in sorted(zip(job_names, statuses))[:40]:
            print(f"  {name:<50}  {status}")
        conn.close()
    except Exception as ex:
        print(f"  [RFC failed: {ex}]")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 4: RUNTIME DUMPS & ERRORS (ST22 equivalent)
# ══════════════════════════════════════════════════════════════════════════════

def report_runtime_dumps(cfg, days: int = 7):
    """
    Recent ABAP short dumps and errors.
    
    Data sources:
      ADT: /sap/bc/adt/runtime/dumps
      RFC: RFC_READ_TABLE on SNAP → ABAP dump header table
    """
    print("\n" + "="*65)
    print(f"  💥 RUNTIME DUMPS (last {days} days)")
    print("="*65)

    # ADT approach
    print("\n  [1] Via ADT runtime/dumps:")
    status, body = adt_get(cfg, "/sap/bc/adt/runtime/dumps")
    print(f"  HTTP {status}")
    if status == 200:
        import re
        dumps_found = re.findall(r'<[^>]+dump[^>]+>', body[:5000])
        print(f"  Dump entries found in response: {len(dumps_found)}")
        print(f"  Response preview: {body[:600]}")

    # RFC: query SNAP table directly
    print("\n  [2] Via RFC (SNAP table — ST22 backing store):")
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    try:
        conn = rfc_connect(cfg)
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="SNAP",
            FIELDS=[{"FIELDNAME":"DATUM"},{"FIELDNAME":"UZEIT"},
                    {"FIELDNAME":"MANDT"},{"FIELDNAME":"UNAME"},
                    {"FIELDNAME":"REPID"},{"FIELDNAME":"ERRMSG"}],
            OPTIONS=[{"TEXT": f"DATUM >= '{cutoff}'"}],
            ROWCOUNT=50
        )
        snaps = result.get("DATA", [])
        print(f"  SNAP entries last {days} days: {len(snaps)}")
        for row in snaps[:20]:
            print(f"    {row['WA'][:120]}")
        conn.close()
    except Exception as ex:
        print(f"  [RFC SNAP failed: {ex}]")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 5: SYSTEM HEALTH OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def report_system_health(cfg):
    """
    Quick system health overview: system info, landscape, buffer stats.
    """
    print("\n" + "="*65)
    print("  🏥 SYSTEM HEALTH OVERVIEW")
    print("="*65)

    try:
        conn = rfc_connect(cfg)

        # System info
        try:
            info = conn.call("RFC_SYSTEM_INFO")
            print(f"\n  System ID   : {info.get('RFCSYSID','?')}")
            print(f"  Client      : {info.get('RFCCLIENT','?')}")
            print(f"  Language    : {info.get('RFCLANG','?')}")
            print(f"  Hostname    : {info.get('RFCHOST','?')}")
            print(f"  Kernel      : {info.get('RFCPROTO','?')}")
            si = info.get("RFCSYSINFO","")
            if si:
                print(f"  SAP Release : {si}")
        except Exception as ex:
            print(f"  [RFC_SYSTEM_INFO: {ex}]")

        # Number of custom Z* objects by type
        print("\n  Custom Object Counts by Type:")
        for obj_type in ["PROG", "CLAS", "FUGR", "TRAN", "TABL", "DTEL", "WAPA"]:
            try:
                result = conn.call("RFC_READ_TABLE",
                    QUERY_TABLE="TADIR",
                    FIELDS=[{"FIELDNAME":"OBJ_NAME"}],
                    OPTIONS=[{"TEXT": f"OBJECT = '{obj_type}' AND OBJ_NAME LIKE 'Z%'"}],
                    ROWCOUNT=1000
                )
                count = len(result.get("DATA", []))
                bar = "█" * min(count // 10, 40)
                print(f"  {obj_type:<6}: {count:>5}  {bar}")
            except:
                pass

        conn.close()

    except Exception as ex:
        print(f"  [RFC failed: {ex}]")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="SAP System Intelligence Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
System routing rules:
  --system D01  Development: ADT, code deploy, BSP extraction
  --system P01  Production : data, monitoring, BDC, users, dumps (DEFAULT for monitoring)

Report defaults:
  health, users, transactions, obsolete, dumps, bdc, jobs  → default: P01
  (override with --system D01 to inspect dev system instead)
""")
    parser.add_argument("--report", default="all",
        choices=["all","users","transactions","obsolete","dumps","health","bdc","jobs"],
        help="Which report to run (bdc=batch input/SM35 discovery, jobs=SM37)")
    parser.add_argument("--system", default="P01",
        choices=["D01","P01"],
        help="SAP system to connect to (default: P01 for production data)")
    parser.add_argument("--months", type=int, default=12,
        help="Months threshold for obsolete programs (default: 12)")
    parser.add_argument("--days", type=int, default=7,
        help="Days back for dumps/bdc/jobs reports (default: 7)")
    args = parser.parse_args()

    all_config = load_config()
    cfg = get_system_cfg(all_config, args.system)

    print(f"\n{'='*65}")
    print(f"  SAP SYSTEM INTELLIGENCE MONITOR")
    print(f"  System: {args.system}  Host: {cfg['host']}  Client: {cfg['client']}")
    print(f"  SNC   : {'YES (SSO)' if cfg.get('snc_mode') else 'NO (password)'}")
    print(f"  Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print(f"  [ROUTING] D01=development(code/deploy)  P01=production(data/monitoring)")
    print(f"  [ROUTING] This run: --> {args.system} <-- {'(change with --system D01)' if args.system=='P01' else '(change with --system P01 for prod data)'}")
    print(f"{'='*65}")

    if args.report in ("all", "health"):
        report_system_health(cfg)

    if args.report in ("all", "users"):
        report_active_users(cfg)

    if args.report in ("all", "transactions"):
        report_transaction_usage(cfg)

    if args.report in ("all", "obsolete"):
        report_obsolete_programs(cfg, months_unused=args.months)

    if args.report in ("all", "dumps"):
        report_runtime_dumps(cfg, days=args.days)

    if args.report in ("all", "bdc"):
        report_batch_inputs(cfg, days=max(args.days, 90))

    if args.report == "jobs":
        report_jobs(cfg, days=args.days)

    print(f"\n{'='*65}")
    print(f"  Report complete. Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()

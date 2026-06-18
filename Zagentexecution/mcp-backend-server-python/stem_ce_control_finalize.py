"""
stem_ce_control_finalize.py — STEM cost-element control adjustment.

Source decision matrix
----------------------
Zagentexecution/STEM_SKB1_not_in_MGIE_CSKB_2026-04-15.xlsx
  264 Balance accounts  → no action (correct as-is, CSKB not needed)
   31 Delete-flagged    → 5 actually present in D01 STEM SKB1 → DELETE
   12 P&L need CE       → 2 actually present in D01 STEM SKB1 → INSERT CSKB

Resolved doubts (locked)
------------------------
DOUBT #1 DATAB        : Mirror KOKRS=UNES per KSTAR (both KSTARs → 20141231)
DOUBT #2 Scope        : Only the 2 P&L SAKNRs with matching SKB1 in STEM today
DOUBT #3 Delete mode  : Physical DELETE FROM skb1 (user reaffirmed)
DOUBT #4 Transport    : Probe D01K9B0CBG live, abort if not modifiable

Operations against D01
----------------------
Phase B — CSKB INSERT 2 rows for KOKRS=STEM (copy from KOKRS=UNES, change only KOKRS)
          + TR_APPEND_TO_COMM CBG with 2 E071K keys
Phase C — SKB1 DELETE 5 rows where BUKRS=STEM
          + TR_APPEND_TO_COMM CBG with 5 E071K keys

Modes
-----
    python stem_ce_control_finalize.py --mode=dryrun    (default — JSON plan, no write)
    python stem_ce_control_finalize.py --mode=test      (1 INSERT + 1 DELETE, then abort)
    python stem_ce_control_finalize.py --mode=execute   (full 2 INSERTs + 5 DELETEs)

Safety rails
------------
- TARGET_SYSTEM hardcoded D01; abort if guard.system_id mismatch
- Source rows for CSKB inserts read LIVE from D01 KOKRS=UNES (not Gold DB)
- SKB1 delete targets re-validated LIVE against D01 BUKRS=STEM before write
- E070 TRSTATUS probed; abort if TRKORR not in (D, L)
- 72-char ABAP line cap asserted before RFC_ABAP_INSTALL_AND_RUN
- COMMIT WORK per phase
- test mode runs exactly 1 op per phase and exits

Related
-------
- stem_align_to_mgie_skb1.py / stem_align_to_mgie_cskb.py — April 14 reference scripts
- .agents/skills/sap_master_data_sync/SKILL.md
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa: E402

# ---------------------------------------------------------------- safety rails
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be D01 (P01 is read-only).")

TRANSPORT = "D01K9B0CBG"
MANDT = "350"
SRC_KOKRS = "UNES"      # source controlling area we clone from
TGT_KOKRS = "STEM"      # target controlling area for the 2 inserts
TGT_BUKRS = "STEM"      # target company code for the 5 deletes

# Phase B — KSTARs to copy from KOKRS=UNES into KOKRS=STEM (CSKB only).
# CSKA + CSKU already exist at chart UNES — no chart-level write needed.
CE_TO_CREATE = [
    "0006012218",  # Service Contract Salaries HQ        (DATAB=20141231 in UNES)
    "0006012219",  # Service Contract Social Charges HQ  (DATAB=20141231 in UNES)
]

# Phase C — SAKNRs to physically DELETE from D01 SKB1 BUKRS=STEM.
# Each is a Balance Sheet account (XBILK=X) flagged Delete in the Excel matrix
# and verified present in D01 STEM SKB1 (Gold DB 2026-05-12, re-verified live below).
SKB1_TO_DELETE = [
    "0001044714",  # CLOSED BK COMMERCIAL BK OF ETHIOPIA-UNES ICB ETB  (SKA1.XLOEV=X)
    "0001144714",  # CLOSED S-BK COMMERCIAL BK OF ETHIOPIA-ICB ETB     (SKA1.XLOEV=X)
    "0001700715",  # CLOSED TS/RP IICBA
    "0004043012",  # BLOCKED Other investments
    "0005098018",  # (Balance, flagged Delete in Excel)
]

THROTTLE_SEC = 2.0
DRYRUN_PATH = HERE / "stem_ce_control_finalize_dryrun.json"
LOG_PATH = HERE.parent.parent / "knowledge" / "configuration_retros" / "STEM_ce_control_2026-05-26.md"

# CSKB columns we will copy (KOKRS will be overwritten to STEM)
CSKB_COLS = [
    "KOKRS", "KSTAR", "DATBI", "KATYP", "DATAB",
    "LOEVM", "MGEFL", "ERSDA", "USNAM",
]
CSKB_NON_KEY = ["KATYP", "DATAB", "LOEVM", "MGEFL"]   # ERSDA/USNAM set to sy-* at insert


# ----------------------------------------------------------------- helpers
def esc(s) -> str:
    return (str(s) if s is not None else "").replace("'", "''")


def read_transport_status(guard, trkorr: str) -> dict:
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="E070",
        FIELDS=[{"FIELDNAME": "TRSTATUS"}, {"FIELDNAME": "AS4USER"},
                {"FIELDNAME": "AS4DATE"}, {"FIELDNAME": "STRKORR"}],
        OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}'"}],
        DELIMITER="|", ROWCOUNT=1,
    )
    data = res.get("DATA") or []
    if not data:
        raise SystemExit(f"Transport {trkorr} not found in D01 E070.")
    wa = data[0]["WA"].split("|")
    return {"TRSTATUS": wa[0].strip(), "AS4USER": wa[1].strip(),
            "AS4DATE": wa[2].strip(), "STRKORR": wa[3].strip()}


def read_cskb_unes_for(guard, kstars: list[str]) -> list[dict]:
    """Read CSKB rows for KOKRS=UNES for the given KSTARs — these are the templates."""
    in_clause = ",".join(f"'{k}'" for k in kstars)
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="CSKB",
        FIELDS=[{"FIELDNAME": c} for c in CSKB_COLS],
        OPTIONS=[{"TEXT": f"KOKRS = '{SRC_KOKRS}' AND KSTAR IN ({in_clause})"}],
        DELIMITER="|", ROWCOUNT=100,
    )
    rows = []
    for d in res.get("DATA", []):
        parts = d["WA"].split("|")
        rows.append({c: parts[i].strip() for i, c in enumerate(CSKB_COLS)})
    return rows


def read_cskb_stem(guard) -> set[tuple[str, str]]:
    """Read existing CSKB keys for KOKRS=STEM. Returns set of (KSTAR, DATBI)."""
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="CSKB",
        FIELDS=[{"FIELDNAME": "KSTAR"}, {"FIELDNAME": "DATBI"}],
        OPTIONS=[{"TEXT": f"KOKRS = '{TGT_KOKRS}'"}],
        DELIMITER="|", ROWCOUNT=5000,
    )
    out = set()
    for d in res.get("DATA", []):
        kstar, datbi = d["WA"].split("|")
        out.add((kstar.strip(), datbi.strip()))
    return out


def read_skb1_stem_present(guard, saknrs: list[str]) -> list[str]:
    """Return the subset of saknrs that currently exist in D01 SKB1 BUKRS=STEM."""
    in_clause = ",".join(f"'{s}'" for s in saknrs)
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="SKB1",
        FIELDS=[{"FIELDNAME": "SAKNR"}],
        OPTIONS=[{"TEXT": f"BUKRS = '{TGT_BUKRS}' AND SAKNR IN ({in_clause})"}],
        DELIMITER="|", ROWCOUNT=100,
    )
    return sorted({d["WA"].strip() for d in res.get("DATA", [])})


def read_cska_present(guard, kstars: list[str]) -> set[str]:
    """Confirm CSKA exists at chart UNES for each KSTAR (precondition for CSKB)."""
    in_clause = ",".join(f"'{k}'" for k in kstars)
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="CSKA",
        FIELDS=[{"FIELDNAME": "KSTAR"}],
        OPTIONS=[{"TEXT": f"KTOPL = 'UNES' AND KSTAR IN ({in_clause})"}],
        DELIMITER="|", ROWCOUNT=100,
    )
    return {d["WA"].strip() for d in res.get("DATA", [])}


def read_cbg_keys(guard, trkorr: str, objname: str) -> set[str]:
    res = guard.call(
        "RFC_READ_TABLE", QUERY_TABLE="E071K",
        FIELDS=[{"FIELDNAME": "TABKEY"}],
        OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}' AND OBJNAME = '{objname}'"}],
        DELIMITER="|", ROWCOUNT=5000,
    )
    return {d["WA"].strip() for d in res.get("DATA", [])}


# ----------------------------------------------------------------- ABAP emit
def build_cskb_insert_abap(rows: list[dict]) -> list[str]:
    """Emit ABAP that inserts each row into CSKB with KOKRS=STEM and attaches the key to CBG."""
    lines = [
        "REPORT Z_STEM_CSKB_INS.",
        "DATA: ls TYPE cskb, lv_ok TYPE i, lv_ko TYPE i,",
        "      ls_e071 TYPE e071, ls_e071k TYPE e071k,",
        "      lt_e071k TYPE TABLE OF e071k.",
        "",
    ]
    for r in rows:
        kstar = esc(r["KSTAR"])
        datbi = esc(r["DATBI"])
        datab = esc(r["DATAB"])
        katyp = esc(r["KATYP"])
        loevm = esc(r.get("LOEVM", ""))
        mgefl = esc(r.get("MGEFL", ""))
        lines += [
            "CLEAR ls.",
            "ls-mandt = sy-mandt.",
            f"ls-kokrs = '{TGT_KOKRS}'.",
            f"ls-kstar = '{kstar}'.",
            f"ls-datbi = '{datbi}'.",
            f"ls-datab = '{datab}'.",
            f"ls-katyp = '{katyp}'.",
            f"ls-loevm = '{loevm}'.",
            f"ls-mgefl = '{mgefl}'.",
            "ls-ersda = sy-datum.",
            "ls-usnam = sy-uname.",
            "INSERT cskb FROM ls.",
            "IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "ELSE. ADD 1 TO lv_ko. ENDIF.",
            "",
        ]
        tabkey = f"{MANDT}{TGT_KOKRS}{kstar}{datbi}"
        lines += [
            "CLEAR: ls_e071, ls_e071k. REFRESH lt_e071k.",
            "ls_e071-pgmid = 'R3TR'.",
            "ls_e071-object = 'TABU'.",
            "ls_e071-obj_name = 'CSKB'.",
            "ls_e071k-pgmid = 'R3TR'.",
            "ls_e071k-object = 'TABU'.",
            "ls_e071k-objname = 'CSKB'.",
            "ls_e071k-mastertype = 'TABU'.",
            "ls_e071k-mastername = 'CSKB'.",
            f"ls_e071k-tabkey = '{tabkey}'.",
            "APPEND ls_e071k TO lt_e071k.",
            "CALL FUNCTION 'TR_APPEND_TO_COMM'",
            f"  EXPORTING pi_korrnum           = '{TRANSPORT}'",
            "            wi_e071              = ls_e071",
            "            wi_suppress_key_check = 'X'",
            "  TABLES    wt_e071k             = lt_e071k",
            "  EXCEPTIONS OTHERS              = 8.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'INSERT_OK:', lv_ok, '  INSERT_KO:', lv_ko.",
    ]
    return lines


def build_skb1_delete_abap(saknrs: list[str]) -> list[str]:
    """Emit ABAP that DELETEs each SKB1 row for BUKRS=STEM and attaches the key to CBG."""
    lines = [
        "REPORT Z_STEM_SKB1_DEL.",
        "DATA: lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i,",
        "      ls_e071 TYPE e071, ls_e071k TYPE e071k,",
        "      lt_e071k TYPE TABLE OF e071k.",
        "",
    ]
    for s in saknrs:
        saknr = esc(s)
        lines += [
            f"DELETE FROM skb1 WHERE bukrs = '{TGT_BUKRS}'",
            f"  AND saknr = '{saknr}'.",
            "IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "ELSEIF sy-subrc = 4. ADD 1 TO lv_mi.",
            "ELSE. ADD 1 TO lv_ko. ENDIF.",
            "",
        ]
        tabkey = f"{MANDT}{TGT_BUKRS}{saknr}"
        lines += [
            "CLEAR: ls_e071, ls_e071k. REFRESH lt_e071k.",
            "ls_e071-pgmid = 'R3TR'.",
            "ls_e071-object = 'TABU'.",
            "ls_e071-obj_name = 'SKB1'.",
            "ls_e071k-pgmid = 'R3TR'.",
            "ls_e071k-object = 'TABU'.",
            "ls_e071k-objname = 'SKB1'.",
            "ls_e071k-mastertype = 'TABU'.",
            "ls_e071k-mastername = 'SKB1'.",
            f"ls_e071k-tabkey = '{tabkey}'.",
            "APPEND ls_e071k TO lt_e071k.",
            "CALL FUNCTION 'TR_APPEND_TO_COMM'",
            f"  EXPORTING pi_korrnum           = '{TRANSPORT}'",
            "            wi_e071              = ls_e071",
            "            wi_suppress_key_check = 'X'",
            "  TABLES    wt_e071k             = lt_e071k",
            "  EXCEPTIONS OTHERS              = 8.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'DELETE_OK:', lv_ok,",
        "       '  DELETE_KO:', lv_ko,",
        "       '  MISSING:',  lv_mi.",
    ]
    return lines


# ----------------------------------------------------------------- runner
def run_batch(guard, abap_lines: list[str]) -> dict:
    for i, line in enumerate(abap_lines):
        if len(line) > 72:
            raise SystemExit(f"ABAP line {i} overflows 72 chars ({len(line)}): {line!r}")
    src = [{"LINE": line[:72]} for line in abap_lines]
    result = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    writes = result.get("WRITES", [])
    err = result.get("ERRORMESSAGE", "")
    output = " ".join(w.get("ZEILE", "") for w in writes)
    ok = ko = mi = 0
    m = re.search(r"(INSERT|DELETE)_OK:\s*(\d+)", output)
    if m:
        ok = int(m.group(2))
    m = re.search(r"(INSERT|DELETE)_KO:\s*(\d+)", output)
    if m:
        ko = int(m.group(2))
    m = re.search(r"MISSING:\s*(\d+)", output)
    if m:
        mi = int(m.group(1))
    return {"ok": ok, "ko": ko, "mi": mi, "output": output, "error": err}


# ----------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dryrun", "test", "execute"], default="dryrun")
    args = ap.parse_args(argv)

    print("=" * 60)
    print(f"  STEM CE control finalize  |  mode={args.mode}  |  target=D01")
    print(f"  Transport: {TRANSPORT}")
    print("=" * 60)

    print(f"\n[CONNECT] {TARGET_SYSTEM}")
    guard = get_connection(TARGET_SYSTEM)
    sid = getattr(guard, "system_id", None)
    if sid != TARGET_SYSTEM:
        raise SystemExit(f"guard sid {sid!r} != {TARGET_SYSTEM!r}")

    print(f"\n[PROBE] transport {TRANSPORT}...")
    ts = read_transport_status(guard, TRANSPORT)
    print(f"        TRSTATUS={ts['TRSTATUS']}  user={ts['AS4USER']}  date={ts['AS4DATE']}")
    if ts["TRSTATUS"] not in ("D", "L"):
        raise SystemExit(f"Transport {TRANSPORT} is not modifiable "
                         f"(TRSTATUS={ts['TRSTATUS']}). Aborting.")

    # --- Phase B preflight: live source rows from KOKRS=UNES + chart presence + STEM gaps
    print(f"\n[READ] D01 CSKA chart={SRC_KOKRS} for {len(CE_TO_CREATE)} KSTARs...")
    cska_found = read_cska_present(guard, CE_TO_CREATE)
    missing_in_cska = [k for k in CE_TO_CREATE if k not in cska_found]
    if missing_in_cska:
        raise SystemExit(f"CSKA missing for: {missing_in_cska}. Cannot create CSKB.")
    print(f"        CSKA present: {len(cska_found)}/{len(CE_TO_CREATE)} OK")

    print(f"\n[READ] D01 CSKB KOKRS={SRC_KOKRS} (source rows)...")
    source_rows = read_cskb_unes_for(guard, CE_TO_CREATE)
    if len(source_rows) != len(CE_TO_CREATE):
        raise SystemExit(f"Expected {len(CE_TO_CREATE)} CSKB rows in KOKRS={SRC_KOKRS}, "
                         f"got {len(source_rows)}.")
    for r in source_rows:
        print(f"        SRC  {r['KSTAR']}  DATAB={r['DATAB']}  DATBI={r['DATBI']}  KATYP={r['KATYP']}")

    print(f"\n[READ] D01 CSKB KOKRS={TGT_KOKRS} (existing targets)...")
    stem_cskb = read_cskb_stem(guard)
    print(f"        STEM CSKB currently: {len(stem_cskb)} rows")

    # Skip any KSTAR already present in STEM for the same DATBI
    inserts = []
    skipped_already_present = []
    for r in source_rows:
        key = (r["KSTAR"], r["DATBI"])
        if key in stem_cskb:
            skipped_already_present.append(key)
            continue
        new = dict(r)
        new["KOKRS"] = TGT_KOKRS   # the ONLY field that changes
        inserts.append(new)
    print(f"        INSERTs needed: {len(inserts)}   already-present skip: {len(skipped_already_present)}")

    # --- Phase C preflight: live re-validate SKB1 delete targets
    print(f"\n[READ] D01 SKB1 BUKRS={TGT_BUKRS} for {len(SKB1_TO_DELETE)} delete targets...")
    present = read_skb1_stem_present(guard, SKB1_TO_DELETE)
    absent = [s for s in SKB1_TO_DELETE if s not in present]
    print(f"        present: {len(present)}   absent (skip): {len(absent)}")
    if absent:
        for s in absent:
            print(f"          absent: {s}")

    # --- Phase B/C transport key visibility
    cbg_cskb_keys = read_cbg_keys(guard, TRANSPORT, "CSKB")
    cbg_skb1_keys = read_cbg_keys(guard, TRANSPORT, "SKB1")
    print(f"\n[READ] CBG keys: CSKB={len(cbg_cskb_keys)}  SKB1={len(cbg_skb1_keys)}")

    # --- Dryrun plan
    plan = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_system": TARGET_SYSTEM,
        "transport": TRANSPORT,
        "transport_status": ts,
        "phase_b_cskb_insert": {
            "source_kokrs": SRC_KOKRS, "target_kokrs": TGT_KOKRS,
            "ce_planned": CE_TO_CREATE,
            "inserts_to_perform": [
                {"KOKRS": r["KOKRS"], "KSTAR": r["KSTAR"],
                 "DATBI": r["DATBI"], "DATAB": r["DATAB"], "KATYP": r["KATYP"]}
                for r in inserts
            ],
            "skipped_already_present": [list(k) for k in skipped_already_present],
        },
        "phase_c_skb1_delete": {
            "target_bukrs": TGT_BUKRS,
            "saknrs_planned": SKB1_TO_DELETE,
            "saknrs_to_delete_live": present,
            "saknrs_skipped_absent": absent,
        },
        "cbg_keys_before": {
            "CSKB": len(cbg_cskb_keys), "SKB1": len(cbg_skb1_keys),
        },
        "cbg_keys_after_estimate": {
            "CSKB": len(cbg_cskb_keys) + len(inserts),
            "SKB1": len(cbg_skb1_keys) + len(present),
        },
    }
    DRYRUN_PATH.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"\n[DRYRUN] Plan written: {DRYRUN_PATH}")
    print(json.dumps(plan["phase_b_cskb_insert"], indent=2))
    print(json.dumps(plan["phase_c_skb1_delete"], indent=2))

    if args.mode == "dryrun":
        guard.close()
        print("\n[DRYRUN] No writes performed. Re-run with --mode=test, then --mode=execute.")
        return 0

    # --- TEST mode: 1 op per phase
    if args.mode == "test":
        print("\n" + "=" * 60)
        print("  TEST MODE — 1 INSERT + 1 DELETE")
        print("=" * 60)
        totals = {}
        if inserts:
            r = run_batch(guard, build_cskb_insert_abap(inserts[:1]))
            print(f"  CSKB insert[1]  ok={r['ok']} ko={r['ko']}  {r['output'][:200]}")
            totals["test_cskb"] = r
        if present:
            r = run_batch(guard, build_skb1_delete_abap(present[:1]))
            print(f"  SKB1 delete[1] ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
            totals["test_skb1"] = r
        guard.close()
        print("\n[TEST] done. Verify in SE16N + SE09 (CBG), then re-run --mode=execute.")
        return 0

    # --- EXECUTE mode
    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase B INSERT {len(inserts)} CSKB rows (KOKRS={TGT_KOKRS})")
    print("=" * 60)
    total = {"b_ok": 0, "b_ko": 0, "c_ok": 0, "c_ko": 0, "c_mi": 0}
    if inserts:
        r = run_batch(guard, build_cskb_insert_abap(inserts))
        total["b_ok"] = r["ok"]; total["b_ko"] = r["ko"]
        print(f"  Phase B  ok={r['ok']} ko={r['ko']}  {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase C DELETE {len(present)} SKB1 rows (BUKRS={TGT_BUKRS})")
    print("=" * 60)
    if present:
        r = run_batch(guard, build_skb1_delete_abap(present))
        total["c_ok"] = r["ok"]; total["c_ko"] = r["ko"]; total["c_mi"] = r["mi"]
        print(f"  Phase C  ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    # --- Verify
    print("\n[VERIFY] Re-reading STEM state...")
    stem_cskb_after = read_cskb_stem(guard)
    skb1_remaining = read_skb1_stem_present(guard, SKB1_TO_DELETE)
    cbg_cskb_after = read_cbg_keys(guard, TRANSPORT, "CSKB")
    cbg_skb1_after = read_cbg_keys(guard, TRANSPORT, "SKB1")

    cskb_inserted_ok = sum(
        1 for r in inserts if (r["KSTAR"], r["DATBI"]) in stem_cskb_after
    )
    print(f"  CSKB STEM after: {len(stem_cskb_after)} rows  (added {cskb_inserted_ok}/{len(inserts)})")
    print(f"  SKB1 STEM delete targets still present: {len(skb1_remaining)} of {len(present)}")
    print(f"  CBG CSKB keys after: {len(cbg_cskb_after)}  (delta +{len(cbg_cskb_after)-len(cbg_cskb_keys)})")
    print(f"  CBG SKB1 keys after: {len(cbg_skb1_after)}  (delta +{len(cbg_skb1_after)-len(cbg_skb1_keys)})")

    guard.close()

    # --- Retro log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write("# STEM Cost Element Control finalize\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d')}  \n")
        f.write(f"**Target:** D01 ({TRANSPORT})  \n")
        f.write(f"**Mode:** execute  \n")
        f.write(f"**Source matrix:** Zagentexecution/STEM_SKB1_not_in_MGIE_CSKB_2026-04-15.xlsx\n\n")
        f.write("## Phase B — CSKB inserts (KOKRS=STEM, copied from KOKRS=UNES)\n\n")
        for r in inserts:
            f.write(f"- {r['KSTAR']}  DATAB={r['DATAB']}  DATBI={r['DATBI']}  KATYP={r['KATYP']}\n")
        f.write(f"\n**Result:** ok={total['b_ok']}  ko={total['b_ko']}\n\n")
        f.write("## Phase C — SKB1 physical deletes (BUKRS=STEM)\n\n")
        for s in present:
            f.write(f"- {s}\n")
        if absent:
            f.write(f"\n**Skipped (already absent):** {absent}\n")
        f.write(f"\n**Result:** ok={total['c_ok']}  ko={total['c_ko']}  missing={total['c_mi']}\n\n")
        f.write("## CBG transport keys\n\n")
        f.write(f"- CSKB: {len(cbg_cskb_keys)} → {len(cbg_cskb_after)}\n")
        f.write(f"- SKB1: {len(cbg_skb1_keys)} → {len(cbg_skb1_after)}\n")
    print(f"\n[LOG] {LOG_PATH}")

    print(f"\nFINAL: {total}")
    return 0 if total["b_ko"] == 0 and total["c_ko"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""
stem_finalize_skb1_cskb.py — STEM SKB1 + CSKB final alignment to Final List.

Source of truth
---------------
  Excel: Zagentexecution/STEM_SKB1_not_in_MGIE_CSKB_2026-04-15.xlsx
  Tab:   "Final LIst" — 540 SAKNRs (MGIEP G/L account)

Live state read 2026-05-26 (D01 RFC)
------------------------------------
  D01 SKB1 BUKRS=STEM:  639 rows
  D01 CSKB KOKRS=STEM:  362 rows

Action matrix (all 3 phases, single transport D01K9B0CBG)
---------------------------------------------------------
  Phase A — CSKB INSERT 12   P&L in Final List missing CSKB in STEM
                              → clone from KOKRS=UNES, change only KOKRS
                              → TR_APPEND_TO_COMM 12 keys to CBG
  Phase B — CSKB DELETE 37   8 BAL orphans + 29 obsolete P&L not in FL
                              → DELETE FROM cskb + TR_APPEND_TO_COMM
  Phase C — SKB1 DELETE 99   Extras in STEM SKB1 not in Final List
                              → DELETE FROM skb1 + TR_APPEND_TO_COMM

Phase order rationale
---------------------
  A before B/C: ensure new CEs exist before any deletion side-effect ripples.
  B before C:   remove cost elements before removing the GL row they reference.

Modes
-----
    python stem_finalize_skb1_cskb.py --mode=dryrun    (default — JSON plan, no write)
    python stem_finalize_skb1_cskb.py --mode=test      (1 row per phase, then abort)
    python stem_finalize_skb1_cskb.py --mode=execute   (full A=12, B=37, C=99)

Safety rails
------------
- TARGET_SYSTEM hardcoded D01; abort if guard.system_id mismatch
- E070 TRSTATUS probed; abort if TRKORR not in (D, L)
- All action lists loaded from Zagentexecution/stem_actions_LIVE_2026-05-26.json
- Source CSKB rows for inserts read LIVE from D01 KOKRS=UNES (not Gold DB)
- 72-char ABAP line cap asserted before RFC_ABAP_INSTALL_AND_RUN
- COMMIT WORK per batch (small batches: 6 inserts, 8 deletes per call)
- Test mode runs 1 op per phase and exits
- Live verification at end: re-read SKB1 + CSKB and report drift vs target
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
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

# ---------------------------------------------------------------- safety rails
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be D01.")

TRANSPORT = "D01K9B0CBG"
MANDT = "350"
SRC_KOKRS = "UNES"   # source controlling area to clone CSKB rows from
TGT_KOKRS = "STEM"
TGT_BUKRS = "STEM"

MATRIX_PATH = HERE.parent / "stem_actions_LIVE_2026-05-26.json"
DRYRUN_PATH = HERE / "stem_finalize_skb1_cskb_dryrun.json"
LOG_PATH = HERE.parent.parent / "knowledge" / "configuration_retros" / "STEM_skb1_cskb_finalize_2026-05-26.md"

BATCH_INSERT = 6
BATCH_DELETE = 8
THROTTLE_SEC = 2.0

CSKB_COLS = ["KOKRS", "KSTAR", "DATBI", "KATYP", "DATAB",
             "LOEVM", "MGEFL", "ERSDA", "USNAM"]


def esc(s) -> str:
    return (str(s) if s is not None else "").replace("'", "''")


# ----------------------------------------------------------------- live reads
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
        raise SystemExit(f"Transport {trkorr} not found.")
    wa = data[0]["WA"].split("|")
    return {"TRSTATUS": wa[0].strip(), "AS4USER": wa[1].strip(),
            "AS4DATE": wa[2].strip(), "STRKORR": wa[3].strip()}


def read_cskb_template(guard, kstars: list[str]) -> dict:
    """Read CSKB rows for KOKRS=UNES for the given KSTARs (read all then filter)."""
    rows = rfc_read_paginated(
        guard._conn, "CSKB", CSKB_COLS,
        [{"TEXT": f"KOKRS = '{SRC_KOKRS}'"}],
        batch_size=2000, throttle=0.5,
    )
    wanted = set(kstars)
    return {r["KSTAR"]: r for r in rows if r["KSTAR"] in wanted}


def read_live_state(guard) -> tuple[set[str], set[str]]:
    """Return (live STEM SKB1 SAKNRs, live STEM CSKB KSTARs)."""
    skb1 = rfc_read_paginated(
        guard._conn, "SKB1", ["SAKNR"],
        [{"TEXT": f"BUKRS = '{TGT_BUKRS}'"}],
        batch_size=2000, throttle=0.5,
    )
    cskb = rfc_read_paginated(
        guard._conn, "CSKB", ["KSTAR"],
        [{"TEXT": f"KOKRS = '{TGT_KOKRS}'"}],
        batch_size=2000, throttle=0.5,
    )
    return {r["SAKNR"] for r in skb1}, {r["KSTAR"] for r in cskb}


# ----------------------------------------------------------------- ABAP emit
def build_cskb_insert_abap(batch: list[dict]) -> list[str]:
    """For each row (UNES template), INSERT into CSKB with KOKRS=STEM + TR_APPEND."""
    lines = [
        "REPORT Z_STEM_CSKB_INS.",
        "DATA: ls TYPE cskb, lv_ok TYPE i, lv_ko TYPE i,",
        "      ls_e071 TYPE e071, ls_e071k TYPE e071k,",
        "      lt_e071k TYPE TABLE OF e071k.",
        "",
    ]
    for r in batch:
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


def build_cskb_delete_abap(kstars_with_datbi: list[tuple[str, str]]) -> list[str]:
    """DELETE FROM cskb for each (KSTAR, DATBI) where KOKRS=STEM + TR_APPEND."""
    lines = [
        "REPORT Z_STEM_CSKB_DEL.",
        "DATA: lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i,",
        "      ls_e071 TYPE e071, ls_e071k TYPE e071k,",
        "      lt_e071k TYPE TABLE OF e071k.",
        "",
    ]
    for kstar, datbi in kstars_with_datbi:
        ks = esc(kstar); db = esc(datbi)
        lines += [
            f"DELETE FROM cskb WHERE kokrs = '{TGT_KOKRS}'",
            f"  AND kstar = '{ks}' AND datbi = '{db}'.",
            "IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "ELSEIF sy-subrc = 4. ADD 1 TO lv_mi.",
            "ELSE. ADD 1 TO lv_ko. ENDIF.",
            "",
        ]
        tabkey = f"{MANDT}{TGT_KOKRS}{ks}{db}"
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
        "WRITE: / 'DELETE_OK:', lv_ok,",
        "       '  DELETE_KO:', lv_ko,",
        "       '  MISSING:',  lv_mi.",
    ]
    return lines


def build_skb1_delete_abap(saknrs: list[str]) -> list[str]:
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
    output = " ".join(w.get("ZEILE", "") for w in writes)
    ok = ko = mi = 0
    m = re.search(r"(INSERT|DELETE)_OK:\s*(\d+)", output)
    if m: ok = int(m.group(2))
    m = re.search(r"(INSERT|DELETE)_KO:\s*(\d+)", output)
    if m: ko = int(m.group(2))
    m = re.search(r"MISSING:\s*(\d+)", output)
    if m: mi = int(m.group(1))
    return {"ok": ok, "ko": ko, "mi": mi, "output": output}


def chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ----------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dryrun", "test", "execute"], default="dryrun")
    args = ap.parse_args(argv)

    print("=" * 60)
    print(f"  STEM finalize SKB1+CSKB  |  mode={args.mode}  |  target=D01")
    print(f"  Transport: {TRANSPORT}")
    print("=" * 60)

    # Load action matrix
    with MATRIX_PATH.open() as f:
        matrix = json.load(f)
    cskb_inserts_kstars = matrix["cskb"]["insert"]
    cskb_deletes_kstars = matrix["cskb"]["final_deletes"]
    skb1_deletes = matrix["skb1"]["delete"]
    print(f"\n[MATRIX] {MATRIX_PATH.name}")
    print(f"  Phase A — CSKB INSERT: {len(cskb_inserts_kstars)} KSTARs")
    print(f"  Phase B — CSKB DELETE: {len(cskb_deletes_kstars)} KSTARs")
    print(f"  Phase C — SKB1 DELETE: {len(skb1_deletes)} SAKNRs")

    # Connect
    print(f"\n[CONNECT] {TARGET_SYSTEM}")
    guard = get_connection(TARGET_SYSTEM)
    if guard.system_id != TARGET_SYSTEM:
        raise SystemExit(f"guard sid mismatch: {guard.system_id}")

    # Probe transport
    print(f"\n[PROBE] {TRANSPORT}")
    ts = read_transport_status(guard, TRANSPORT)
    print(f"  TRSTATUS={ts['TRSTATUS']}  user={ts['AS4USER']}  date={ts['AS4DATE']}")
    if ts["TRSTATUS"] not in ("D", "L"):
        raise SystemExit(f"Transport {TRANSPORT} not modifiable (TRSTATUS={ts['TRSTATUS']}).")

    # Read source CSKB templates from KOKRS=UNES
    print(f"\n[READ] D01 CSKB KOKRS={SRC_KOKRS} (template rows for inserts)...")
    template = read_cskb_template(guard, cskb_inserts_kstars)
    print(f"  Templates found: {len(template)} / {len(cskb_inserts_kstars)}")
    missing = [k for k in cskb_inserts_kstars if k not in template]
    if missing:
        raise SystemExit(f"Missing CSKB template in KOKRS={SRC_KOKRS} for: {missing}")

    # Read CSKB rows in STEM that we will delete (need DATBI for the key)
    print(f"\n[READ] D01 CSKB KOKRS={TGT_KOKRS} (for delete keys)...")
    stem_cskb_rows = rfc_read_paginated(
        guard._conn, "CSKB", ["KSTAR", "DATBI"],
        [{"TEXT": f"KOKRS = '{TGT_KOKRS}'"}],
        batch_size=2000, throttle=0.5,
    )
    stem_cskb_map = {r["KSTAR"]: r["DATBI"] for r in stem_cskb_rows}
    delete_keys = [(k, stem_cskb_map[k]) for k in cskb_deletes_kstars if k in stem_cskb_map]
    delete_missing = [k for k in cskb_deletes_kstars if k not in stem_cskb_map]
    if delete_missing:
        print(f"  WARN: {len(delete_missing)} CSKB-to-delete not in live STEM: {delete_missing[:5]}...")
    print(f"  Will delete {len(delete_keys)} CSKB rows.")

    # Live state before any write
    live_skb1, live_cskb = read_live_state(guard)
    print(f"\n[BEFORE] live D01 STEM SKB1={len(live_skb1)}  CSKB={len(live_cskb)}")

    # Build inserts payload (clone from template, override KOKRS)
    inserts = []
    for k in cskb_inserts_kstars:
        new = dict(template[k]); new["KOKRS"] = TGT_KOKRS
        inserts.append(new)

    # Dryrun summary
    plan = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transport": TRANSPORT, "transport_status": ts,
        "before": {"skb1": len(live_skb1), "cskb": len(live_cskb)},
        "phase_a_cskb_insert": {"count": len(inserts), "kstars": cskb_inserts_kstars},
        "phase_b_cskb_delete": {"count": len(delete_keys),
                                "kstars": [k for k, _ in delete_keys]},
        "phase_c_skb1_delete": {"count": len(skb1_deletes), "saknrs": skb1_deletes},
        "expected_after": {
            "skb1": len(live_skb1) - len(skb1_deletes),
            "cskb": len(live_cskb) + len(inserts) - len(delete_keys),
        },
    }
    DRYRUN_PATH.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"\n[DRYRUN] {DRYRUN_PATH}")
    print(json.dumps({k: v for k, v in plan.items() if k != "phase_c_skb1_delete"}, indent=2))

    if args.mode == "dryrun":
        guard.close()
        print("\n[DRYRUN] No writes. Re-run with --mode=test (1 op/phase) or --mode=execute (full).")
        return 0

    if args.mode == "test":
        print("\n" + "=" * 60); print("  TEST MODE — 1 op per phase"); print("=" * 60)
        if inserts:
            r = run_batch(guard, build_cskb_insert_abap(inserts[:1]))
            print(f"  A[1] CSKB insert ok={r['ok']} ko={r['ko']}  {r['output'][:200]}")
        if delete_keys:
            r = run_batch(guard, build_cskb_delete_abap(delete_keys[:1]))
            print(f"  B[1] CSKB delete ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        if skb1_deletes:
            r = run_batch(guard, build_skb1_delete_abap(skb1_deletes[:1]))
            print(f"  C[1] SKB1 delete ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        guard.close()
        print("\n[TEST] done. Verify in SE16N + SE09, then --mode=execute.")
        return 0

    # EXECUTE
    total = {"a_ok": 0, "a_ko": 0, "b_ok": 0, "b_ko": 0, "b_mi": 0,
             "c_ok": 0, "c_ko": 0, "c_mi": 0}

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase A INSERT {len(inserts)} CSKB rows")
    print("=" * 60)
    for i, b in enumerate(chunk(inserts, BATCH_INSERT), 1):
        r = run_batch(guard, build_cskb_insert_abap(b))
        total["a_ok"] += r["ok"]; total["a_ko"] += r["ko"]
        print(f"  [A b{i:02d}] {len(b)} rows  ok={r['ok']} ko={r['ko']}")
        if r["ko"]: print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase B DELETE {len(delete_keys)} CSKB rows")
    print("=" * 60)
    for i, b in enumerate(chunk(delete_keys, BATCH_DELETE), 1):
        r = run_batch(guard, build_cskb_delete_abap(b))
        total["b_ok"] += r["ok"]; total["b_ko"] += r["ko"]; total["b_mi"] += r["mi"]
        print(f"  [B b{i:02d}] {len(b)} rows  ok={r['ok']} ko={r['ko']} mi={r['mi']}")
        if r["ko"]: print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase C DELETE {len(skb1_deletes)} SKB1 rows")
    print("=" * 60)
    for i, b in enumerate(chunk(skb1_deletes, BATCH_DELETE), 1):
        r = run_batch(guard, build_skb1_delete_abap(b))
        total["c_ok"] += r["ok"]; total["c_ko"] += r["ko"]; total["c_mi"] += r["mi"]
        print(f"  [C b{i:02d}] {len(b)} rows  ok={r['ok']} ko={r['ko']} mi={r['mi']}")
        if r["ko"]: print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    # Verify
    print("\n[VERIFY]")
    skb1_after, cskb_after = read_live_state(guard)
    print(f"  SKB1 STEM after: {len(skb1_after)}  (expected {len(live_skb1)-len(skb1_deletes)})")
    print(f"  CSKB STEM after: {len(cskb_after)}  (expected {len(live_cskb)+len(inserts)-len(delete_keys)})")
    guard.close()

    # Log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write("# STEM SKB1 + CSKB finalize against Final List\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d')}  \n")
        f.write(f"**Target:** D01 ({TRANSPORT})  \n")
        f.write(f"**Source:** Excel Final LIst tab (540 MGIEP SAKNRs)\n\n")
        f.write(f"## Before\n- SKB1 STEM: {len(live_skb1)}\n- CSKB STEM: {len(live_cskb)}\n\n")
        f.write(f"## Counters\n")
        for k, v in total.items(): f.write(f"- {k}: {v}\n")
        f.write(f"\n## After\n- SKB1 STEM: {len(skb1_after)}\n- CSKB STEM: {len(cskb_after)}\n")
    print(f"\n[LOG] {LOG_PATH}")
    print(f"\nFINAL: {total}")
    return 0 if (total["a_ko"] == 0 and total["b_ko"] == 0 and total["c_ko"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())

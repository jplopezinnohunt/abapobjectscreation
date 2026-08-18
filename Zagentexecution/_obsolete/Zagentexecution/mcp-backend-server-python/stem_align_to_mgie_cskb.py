"""
stem_align_to_mgie_cskb.py — Clone MGIE CSKB into STEM in D01 + attach keys to CBG.

Purpose
-------
Make transport D01K9B0CBG also carry STEM cost elements (CSKB) aligned to
MGIE. STEM currently has 2 CSKB rows in D01; MGIE has 362. All 2 STEM rows
match MGIE. Delta: 360 pure INSERTs. Transport CBG does not yet list
R3TR TABU CSKB — TR_APPEND_TO_COMM creates the E071 header on first call.

Scope (verified 2026-04-14 live against D01)
--------------------------------------------
- STEM CSKB rows:  2
- MGIE CSKB rows:  362
- Common (identical): 2 — no-op
- MGIE-only:  360 → INSERT into D01 as KOKRS=STEM, all other fields copied
                    from MGIE → attach 360 E071K keys to CBG.

CSKB key: MANDT + KOKRS + KSTAR + DATBI (25-char TABKEY)
CSKB cols (19): MANDT, KOKRS, KSTAR, DATBI, DATAB, KATYP, ERSDA, USNAM,
                EIGEN, PLAZU, PLAOR, PLAUS, KOSTL, AUFNR, MGEFL, MSEHI,
                DEAKT, LOEVM, RECID

Modes
-----
    python stem_align_to_mgie_cskb.py --mode=dryrun    (default)
    python stem_align_to_mgie_cskb.py --mode=test      (run ONE insert)
    python stem_align_to_mgie_cskb.py --mode=execute   (full 360)

Related
-------
- stem_align_to_mgie_skb1.py — same pattern, SKB1 alignment
- .agents/skills/sap_master_data_sync/SKILL.md
- Session #031 retro: CSKB=0 STEM gap discovery
"""

from __future__ import annotations

import argparse
import io
import json
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

# --- safety ---
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be D01.")

TRANSPORT = "D01K9B0CBG"
SRC_KOKRS = "MGIE"
TGT_KOKRS = "STEM"
MANDT = "350"

BATCH_ROWS = 8
THROTTLE_SEC = 2.0
DRYRUN_PATH = HERE / "stem_align_to_mgie_cskb_dryrun.json"
LOG_PATH = HERE.parent.parent / "knowledge" / "configuration_retros" / "STEM_cskb_align_2026-04-14.md"

CSKB_COLS = [
    "KOKRS", "KSTAR", "DATBI", "DATAB", "KATYP", "ERSDA", "USNAM",
    "EIGEN", "PLAZU", "PLAOR", "PLAUS", "KOSTL", "AUFNR", "MGEFL",
    "MSEHI", "DEAKT", "LOEVM", "RECID",
]
KEY_COLS = {"KOKRS", "KSTAR", "DATBI"}
NON_KEY = [c for c in CSKB_COLS if c not in KEY_COLS]


def esc(s):
    return (str(s) if s is not None else "").replace("'", "''")


def read_cskb(guard, kokrs: str) -> list[dict]:
    where = [{"TEXT": f"KOKRS = '{kokrs}'"}]
    rows = rfc_read_paginated(guard._conn, "CSKB", CSKB_COLS, where,
                              batch_size=2000, throttle=1.0)
    return rows


def read_transport_status(guard, trkorr: str) -> dict:
    res = guard.call("RFC_READ_TABLE", QUERY_TABLE="E070",
                     FIELDS=[{"FIELDNAME": "TRSTATUS"}, {"FIELDNAME": "AS4USER"},
                             {"FIELDNAME": "AS4DATE"}],
                     OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}'"}],
                     DELIMITER="|", ROWCOUNT=1)
    data = res.get("DATA") or []
    if not data:
        raise SystemExit(f"Transport {trkorr} not found.")
    wa = data[0]["WA"].split("|")
    return {"TRSTATUS": wa[0].strip(), "AS4USER": wa[1].strip(), "AS4DATE": wa[2].strip()}


def read_cbg_cskb_keys(guard, trkorr: str) -> set[str]:
    res = guard.call("RFC_READ_TABLE", QUERY_TABLE="E071K",
                     FIELDS=[{"FIELDNAME": "TABKEY"}],
                     OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}' AND OBJNAME = 'CSKB'"}],
                     DELIMITER="|", ROWCOUNT=5000)
    return {d["WA"].strip() for d in res.get("DATA", [])
            if d["WA"].strip()[3:7] == TGT_KOKRS}


def compute_delta(mgie_rows: list[dict], stem_rows: list[dict]):
    # key tuple: (KSTAR, DATBI)
    def key(r): return (r["KSTAR"], r["DATBI"])
    mgie = {key(r): r for r in mgie_rows}
    stem = {key(r): r for r in stem_rows}
    common = sorted(set(mgie) & set(stem))
    mgie_only = sorted(set(mgie) - set(stem))
    stem_only = sorted(set(stem) - set(mgie))

    updates, inserts = [], []
    for k in common:
        src = dict(mgie[k]); src["KOKRS"] = TGT_KOKRS
        updates.append(src)
    for k in mgie_only:
        src = dict(mgie[k]); src["KOKRS"] = TGT_KOKRS
        inserts.append(src)
    return updates, inserts, common, mgie_only, stem_only


def _emit_assignments(row: dict) -> list[str]:
    out = []
    for col in NON_KEY:
        val = esc(row.get(col, ""))
        line = f"ls-{col.lower()} = '{val}'."
        if len(line) > 72:
            raise RuntimeError(f"{col} value too long for ABAP literal: {val!r}")
        out.append(line)
    return out


def build_update_abap(batch):
    lines = [
        "REPORT Z_STEM_CSKB_UPD.",
        "DATA: ls TYPE cskb, lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for r in batch:
        kstar = esc(r["KSTAR"]); datbi = esc(r["DATBI"])
        lines += [
            "CLEAR ls.",
            f"SELECT SINGLE * FROM cskb INTO ls WHERE kokrs = '{TGT_KOKRS}'",
            f"  AND kstar = '{kstar}' AND datbi = '{datbi}'.",
            "IF sy-subrc = 0.",
        ]
        for ln in _emit_assignments(r):
            lines.append(f"  {ln}")
        lines += [
            "  UPDATE cskb FROM ls.",
            "  IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "  ELSE. ADD 1 TO lv_ko. ENDIF.",
            "ELSE. ADD 1 TO lv_mi. ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'UPDATE_OK:', lv_ok,",
        "       '  UPDATE_KO:', lv_ko,",
        "       '  MISSING:',  lv_mi.",
    ]
    return lines


def build_insert_abap(batch, attach_transport: bool):
    lines = [
        "REPORT Z_STEM_CSKB_INS.",
        "DATA: ls TYPE cskb, lv_ok TYPE i, lv_ko TYPE i,",
        "      ls_e071 TYPE e071, ls_e071k TYPE e071k,",
        "      lt_e071k TYPE TABLE OF e071k.",
        "",
    ]
    for r in batch:
        kstar = esc(r["KSTAR"]); datbi = esc(r["DATBI"])
        lines += [
            "CLEAR ls.",
            "ls-mandt = sy-mandt.",
            f"ls-kokrs = '{TGT_KOKRS}'.",
            f"ls-kstar = '{kstar}'.",
            f"ls-datbi = '{datbi}'.",
        ]
        for ln in _emit_assignments(r):
            lines.append(ln)
        lines += [
            "INSERT cskb FROM ls.",
            "IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "ELSE. ADD 1 TO lv_ko. ENDIF.",
            "",
        ]
        if attach_transport:
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


def run_batch(guard, abap_lines):
    for i, line in enumerate(abap_lines):
        if len(line) > 72:
            raise SystemExit(f"ABAP line {i} overflow ({len(line)}): {line!r}")
    src = [{"LINE": l[:72]} for l in abap_lines]
    result = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    writes = result.get("WRITES", [])
    output = " ".join(w.get("ZEILE", "") for w in writes)
    import re
    ok = ko = mi = 0
    m = re.search(r"(UPDATE|INSERT)_OK:\s*(\d+)", output);  ok = int(m.group(2)) if m else 0
    m = re.search(r"(UPDATE|INSERT)_KO:\s*(\d+)", output);  ko = int(m.group(2)) if m else 0
    m = re.search(r"MISSING:\s*(\d+)", output);             mi = int(m.group(1)) if m else 0
    return {"ok": ok, "ko": ko, "mi": mi, "output": output}


def chunk(s, n):
    for i in range(0, len(s), n): yield s[i:i+n]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dryrun", "test", "execute"], default="dryrun")
    args = ap.parse_args(argv)

    print("=" * 60)
    print(f"  STEM CSKB ← MGIE clone  |  mode={args.mode}  |  target=D01")
    print("=" * 60)

    guard = get_connection(TARGET_SYSTEM)
    if guard.system_id != TARGET_SYSTEM:
        raise SystemExit("guard sid mismatch")

    ts = read_transport_status(guard, TRANSPORT)
    print(f"[PROBE] {TRANSPORT}  TRSTATUS={ts['TRSTATUS']} user={ts['AS4USER']} date={ts['AS4DATE']}")
    if ts["TRSTATUS"] not in ("D", "L"):
        raise SystemExit("Transport not modifiable.")

    mgie_rows = read_cskb(guard, SRC_KOKRS)
    stem_rows = read_cskb(guard, TGT_KOKRS)
    print(f"[READ] MGIE CSKB: {len(mgie_rows)}   STEM CSKB: {len(stem_rows)}")

    cbg_keys = read_cbg_cskb_keys(guard, TRANSPORT)
    print(f"[READ] CBG STEM CSKB keys currently: {len(cbg_keys)}")

    updates, inserts, common, mgie_only, stem_only = compute_delta(mgie_rows, stem_rows)
    print(f"[DELTA] common={len(common)}  mgie_only={len(mgie_only)}  stem_only={len(stem_only)}")

    plan = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transport": TRANSPORT, "transport_status": ts,
        "scope": {"MGIE": len(mgie_rows), "STEM": len(stem_rows),
                  "common": len(common), "mgie_only_INSERT": len(mgie_only),
                  "stem_only": len(stem_only)},
        "operations": {"updates_on_common": len(updates),
                       "inserts": len(inserts),
                       "new_keys_added_to_CBG": len(inserts)},
        "cbg_cskb_stem_keys_current": len(cbg_keys),
        "cbg_cskb_stem_keys_after": len(cbg_keys) + len(inserts),
        "stem_only_keys": [f"{k}/{d}" for k, d in stem_only],
    }
    DRYRUN_PATH.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"[DRYRUN] Plan -> {DRYRUN_PATH}")
    print(json.dumps(plan["scope"], indent=2))
    print(json.dumps(plan["operations"], indent=2))

    if args.mode == "dryrun":
        guard.close()
        return 0

    if args.mode == "test":
        print("\n-- TEST MODE: 1 INSERT --")
        if inserts:
            r = run_batch(guard, build_insert_abap(inserts[:1], attach_transport=True))
            print(f"  insert[1]  ok={r['ok']} ko={r['ko']}  {r['output'][:200]}")
        if updates:
            r = run_batch(guard, build_update_abap(updates[:1]))
            print(f"  update[1]  ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        guard.close()
        return 0

    # execute
    total = {"p1_ok": 0, "p1_ko": 0, "p1_mi": 0, "p2_ok": 0, "p2_ko": 0}
    print(f"\n-- Phase 1 UPDATE {len(updates)} --")
    for i, b in enumerate(chunk(updates, BATCH_ROWS), 1):
        r = run_batch(guard, build_update_abap(b))
        total["p1_ok"] += r["ok"]; total["p1_ko"] += r["ko"]; total["p1_mi"] += r["mi"]
        if i % 10 == 0 or r["ko"]:
            print(f"  [P1 b{i:03d}] {len(b)} rows  ok={r['ok']} ko={r['ko']} mi={r['mi']}")
        time.sleep(THROTTLE_SEC)

    print(f"\n-- Phase 2 INSERT + TR_APPEND_TO_COMM {len(inserts)} --")
    for i, b in enumerate(chunk(inserts, BATCH_ROWS), 1):
        r = run_batch(guard, build_insert_abap(b, attach_transport=True))
        total["p2_ok"] += r["ok"]; total["p2_ko"] += r["ko"]
        if i % 5 == 0 or r["ko"]:
            print(f"  [P2 b{i:03d}] {len(b)} rows  ok={r['ok']} ko={r['ko']}")
        if r["ko"]:
            print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    # verify
    print("\n-- Verify --")
    stem_after = read_cskb(guard, TGT_KOKRS)
    cbg_after = read_cbg_cskb_keys(guard, TRANSPORT)
    print(f"  STEM CSKB after: {len(stem_after)}  (was {len(stem_rows)})")
    print(f"  CBG STEM keys after: {len(cbg_after)}  (was {len(cbg_keys)}, +{len(cbg_after)-len(cbg_keys)})")

    # Compute drift
    drift = 0
    mset = {(r["KSTAR"], r["DATBI"]): r for r in mgie_rows}
    sset = {(r["KSTAR"], r["DATBI"]): r for r in stem_after}
    missing = [k for k in mset if k not in sset]
    print(f"  MGIE→STEM keys still missing: {len(missing)}")
    for k in mset:
        if k in sset:
            src, tgt = mset[k], sset[k]
            for c in NON_KEY:
                if (src.get(c) or "") != (tgt.get(c) or ""):
                    drift += 1
                    break
    print(f"  MGIE→STEM value drift rows: {drift}")

    guard.close()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write("# STEM CSKB ← MGIE alignment\n\n")
        f.write(f"**Date:** 2026-04-14  \n**Target:** D01 ({TRANSPORT})\n\n")
        for k, v in total.items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n- STEM after: {len(stem_after)}\n")
        f.write(f"- CBG keys after: {len(cbg_after)} (+{len(cbg_after)-len(cbg_keys)})\n")
        f.write(f"- drift: {drift}\n")
    print(f"\n[LOG] {LOG_PATH}")
    return 0 if all(v == 0 for k, v in total.items() if k.endswith("_ko")) else 1


if __name__ == "__main__":
    sys.exit(main())

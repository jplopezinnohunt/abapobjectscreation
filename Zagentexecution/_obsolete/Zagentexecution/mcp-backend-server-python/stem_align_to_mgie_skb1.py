"""
stem_align_to_mgie_skb1.py — Clone MGIE SKB1 into STEM in D01 + attach keys to CBG.

Purpose
-------
Make transport D01K9B0CBG carry a field-for-field copy of MGIE's SKB1 rows
as STEM, closing the FIPOS gap that blocks budget posting for STEM GLs.

Scope (verified 2026-04-14 against Gold DB mtime 2026-04-14 15:39)
------------------------------------------------------------------
- 533 common SAKNRs  → UPDATE STEM rows in D01 with MGIE field values
                       (fills FIPOS on 530 rows + XOPVW on 1 row)
- 98 MGIE-only SAKNRs → INSERT into D01 SKB1 as BUKRS=STEM with MGIE values
                        AND attach each key to transport D01K9B0CBG
-   8 STEM-only SAKNRs → UPDATE FIPOS only, using unanimous cross-institute
                         value (BANK×7, BALANCE×1).  No delete.

Phase ordering (data before transport)
--------------------------------------
Phase 1  UPDATE 533 common
Phase 2  INSERT 98 new + TR_OBJECTS_INSERT the 98 keys into CBG
Phase 3  UPDATE 8 STEM-only (FIPOS only)
Phase 4  Re-extract D01 SKB1 for STEM → verify zero drift vs MGIE

Modes
-----
    python stem_align_to_mgie_skb1.py --mode=dryrun    (default, writes JSON, no write)
    python stem_align_to_mgie_skb1.py --mode=test      (runs ONE SAKNR through each phase)
    python stem_align_to_mgie_skb1.py --mode=execute   (runs the full bulk)

Safety rails
------------
- TARGET_SYSTEM hardcoded to D01
- Transport D01K9B0CBG open-status probed via E070 before any write
- Every ABAP line asserted ≤ 72 chars
- COMMIT WORK per batch
- Test mode must pass + user re-invoke with --mode=execute for bulk

Related
-------
- .agents/skills/sap_master_data_sync/SKILL.md
- Zagentexecution/mcp-backend-server-python/h29_skat_update.py  (reference pattern)
- Session #031 retro: FMCI=0 / CSKB=0 critical discovery (FIPOS gap is same class)
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

# ---------------------------------------------------------------- safety rails
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be D01 (P01 is read-only).")

TRANSPORT = "D01K9B0CBG"
SRC_BUKRS = "MGIE"
TGT_BUKRS = "STEM"
MANDT = "350"

# Fixed STEM-only fipos overrides (from cross-institute lookup)
STEM_ONLY_FIPOS = {
    "0001044711": "BANK",
    "0001044714": "BANK",
    "0001044715": "BANK",
    "0001144711": "BANK",
    "0001144714": "BANK",
    "0001144715": "BANK",
    "0001700715": "BALANCE",
    "0001900754": "BANK",
}

BATCH_ROWS = 6              # SKB1 has 38 cols, keep ABAP below 72-char & 1000-line limits
THROTTLE_SEC = 2.0
DRYRUN_PATH = HERE / "stem_align_to_mgie_skb1_dryrun.json"
LOG_PATH = HERE.parent.parent / "knowledge" / "configuration_retros" / "STEM_skb1_align_2026-04-14.md"

SKB1_COLS = [
    "BUKRS", "SAKNR", "WAERS", "XSALH", "KDFSL", "BEWGP", "MWSKZ", "XMWNO",
    "MITKZ", "XOPVW", "XKRES", "ZUAWA", "BEGRU", "BUSAB", "FSTAG", "XINTB",
    "XNKON", "XMITK", "FDLEV", "XGKON", "FIPOS", "HBKID", "HKTID", "VZSKZ",
    "ZINDT", "ZINRT", "DATLZ", "XLOEB", "XSPEB", "XLGCLR", "MCAKEY", "ALTKT",
    "TOGRU", "INFKY", "WMETH", "RECID", "FDGRV", "STEXT",
]
KEY_COLS = {"BUKRS", "SAKNR"}
NON_KEY = [c for c in SKB1_COLS if c not in KEY_COLS]


def esc(s):
    if s is None:
        return ""
    return str(s).replace("'", "''")


# ----------------------------------------------------------------- live reads
def read_skb1(guard, bukrs: str) -> list[dict]:
    """Read D01 SKB1 for a single company code live (no Gold DB)."""
    where = [{"TEXT": f"BUKRS = '{bukrs}'"}]
    rows = rfc_read_paginated(
        guard._conn, "SKB1", SKB1_COLS, where,
        batch_size=2000, throttle=1.0,
    )
    return rows


def read_transport_status(guard, trkorr: str) -> str:
    """Return E070.TRSTATUS (D=modifiable, R=released, O=consolidated)."""
    res = guard.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="E070",
        FIELDS=[{"FIELDNAME": "TRSTATUS"}, {"FIELDNAME": "AS4USER"},
                {"FIELDNAME": "AS4DATE"}],
        OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}'"}],
        DELIMITER="|", ROWCOUNT=1,
    )
    data = res.get("DATA") or []
    if not data:
        raise SystemExit(f"Transport {trkorr} not found in D01 E070.")
    wa = data[0]["WA"].split("|")
    return {"TRSTATUS": wa[0].strip(), "AS4USER": wa[1].strip(), "AS4DATE": wa[2].strip()}


def read_cbg_skb1_keys(guard, trkorr: str) -> set[str]:
    """Return set of SAKNRs currently registered in CBG for TABU SKB1."""
    res = guard.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="E071K",
        FIELDS=[{"FIELDNAME": "TABKEY"}],
        OPTIONS=[
            {"TEXT": f"TRKORR = '{trkorr}' AND OBJNAME = 'SKB1'"},
        ],
        DELIMITER="|", ROWCOUNT=10000,
    )
    out = set()
    for d in res.get("DATA", []):
        tk = d["WA"].strip()
        if len(tk) >= 17 and tk[:3] == MANDT and tk[3:7] == TGT_BUKRS:
            out.add(tk[7:17])
    return out


# ----------------------------------------------------------------- delta calc
def compute_delta(mgie_rows: list[dict], stem_rows: list[dict]):
    mgie = {r["SAKNR"]: r for r in mgie_rows}
    stem = {r["SAKNR"]: r for r in stem_rows}
    common = sorted(set(mgie) & set(stem))
    mgie_only = sorted(set(mgie) - set(stem))
    stem_only = sorted(set(stem) - set(mgie))

    updates = []     # 533 — rebuild STEM rows from MGIE values
    inserts = []     # 98  — new STEM rows from MGIE values
    stem_fix = []    # 8   — FIPOS fill from STEM_ONLY_FIPOS

    for s in common:
        src = dict(mgie[s])
        src["BUKRS"] = TGT_BUKRS
        updates.append(src)
    for s in mgie_only:
        src = dict(mgie[s])
        src["BUKRS"] = TGT_BUKRS
        inserts.append(src)
    for s in stem_only:
        target_fipos = STEM_ONLY_FIPOS.get(s, "")
        if not target_fipos:
            continue
        current = dict(stem[s])
        if (current.get("FIPOS") or "") != target_fipos:
            current["FIPOS"] = target_fipos
            stem_fix.append(current)
    return updates, inserts, stem_fix, common, mgie_only, stem_only


# ----------------------------------------------------------------- ABAP emit
def _emit_assignments(row: dict) -> list[str]:
    """Emit `ls-<col> = '<val>'.` for every non-key col, max 72 chars/line."""
    lines = []
    for col in NON_KEY:
        val = esc(row.get(col, ""))
        line = f"ls-{col.lower()} = '{val}'."
        if len(line) > 72:
            # very long STEXT — truncate conservatively; STEXT max is 50 chars in DDIC
            raise RuntimeError(f"{col} value too long for ABAP literal: {val!r}")
        lines.append(line)
    return lines


def build_update_abap(batch: list[dict]) -> list[str]:
    lines = [
        "REPORT Z_STEM_SKB1_UPD.",
        "DATA: ls TYPE skb1, lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for row in batch:
        saknr = esc(row["SAKNR"])
        lines += [
            "CLEAR ls.",
            f"SELECT SINGLE * FROM skb1 INTO ls WHERE bukrs = '{TGT_BUKRS}'",
            f"  AND saknr = '{saknr}'.",
            "IF sy-subrc = 0.",
        ]
        for ln in _emit_assignments(row):
            lines.append(f"  {ln}")
        lines += [
            "  UPDATE skb1 FROM ls.",
            "  IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "  ELSE. ADD 1 TO lv_ko. ENDIF.",
            "ELSE.",
            "  ADD 1 TO lv_mi.",
            "ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'UPDATE_OK:', lv_ok,",
        "       '  UPDATE_KO:', lv_ko,",
        "       '  MISSING:',  lv_mi.",
    ]
    return lines


def build_insert_abap(batch: list[dict], attach_transport: bool) -> list[str]:
    lines = [
        "REPORT Z_STEM_SKB1_INS.",
        "DATA: ls TYPE skb1, lv_ok TYPE i, lv_ko TYPE i,",
        "      ls_e071 TYPE e071, lt_e071k TYPE TABLE OF e071k,",
        "      ls_e071k TYPE e071k.",
        "",
    ]
    for row in batch:
        saknr = esc(row["SAKNR"])
        lines += [
            "CLEAR ls.",
            "ls-mandt = sy-mandt.",
            f"ls-bukrs = '{TGT_BUKRS}'.",
            f"ls-saknr = '{saknr}'.",
        ]
        for ln in _emit_assignments(row):
            lines.append(ln)
        lines += [
            "INSERT skb1 FROM ls.",
            "IF sy-subrc = 0. ADD 1 TO lv_ok.",
            "ELSE. ADD 1 TO lv_ko. ENDIF.",
            "",
        ]
        if attach_transport:
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
        "WRITE: / 'INSERT_OK:', lv_ok, '  INSERT_KO:', lv_ko.",
    ]
    return lines


def build_fipos_fix_abap(batch: list[dict]) -> list[str]:
    """Update FIPOS only on 8 STEM-only rows."""
    lines = [
        "REPORT Z_STEM_SKB1_FIX.",
        "DATA: ls TYPE skb1, lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for row in batch:
        saknr = esc(row["SAKNR"])
        fipos = esc(row["FIPOS"])
        lines += [
            "CLEAR ls.",
            f"SELECT SINGLE * FROM skb1 INTO ls WHERE bukrs = '{TGT_BUKRS}'",
            f"  AND saknr = '{saknr}'.",
            "IF sy-subrc = 0.",
            f"  ls-fipos = '{fipos}'.",
            "  UPDATE skb1 FROM ls.",
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
    import re
    ok = ko = mi = 0
    m = re.search(r"(UPDATE|INSERT)_OK:\s*(\d+)", output)
    if m:
        ok = int(m.group(2))
    m = re.search(r"(UPDATE|INSERT)_KO:\s*(\d+)", output)
    if m:
        ko = int(m.group(2))
    m = re.search(r"MISSING:\s*(\d+)", output)
    if m:
        mi = int(m.group(1))
    return {"ok": ok, "ko": ko, "mi": mi, "output": output, "error": err}


def chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ----------------------------------------------------------------- dry-run
def write_dryrun(updates, inserts, fipos_fix, common, mgie_only, stem_only,
                 transport_status, cbg_keys):
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_bukrs": SRC_BUKRS,
        "target_bukrs": TGT_BUKRS,
        "transport": TRANSPORT,
        "transport_status": transport_status,
        "scope": {
            "MGIE_total": len(common) + len(mgie_only),
            "STEM_total": len(common) + len(stem_only),
            "common": len(common),
            "mgie_only__insert": len(mgie_only),
            "stem_only__fipos_fix": len(stem_only),
        },
        "operations": {
            "phase1_updates_on_common": len(updates),
            "phase2_inserts": len(inserts),
            "phase2_new_keys_added_to_CBG": len(inserts),
            "phase3_fipos_fix": len(fipos_fix),
        },
        "cbg_skb1_stem_keys_current": len(cbg_keys),
        "cbg_skb1_stem_keys_after": len(cbg_keys) + len(inserts),
        "stem_only_fipos_map": STEM_ONLY_FIPOS,
        "mgie_only_first20": mgie_only[:20],
        "stem_only": stem_only,
    }
    DRYRUN_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\n[DRYRUN] Plan written to {DRYRUN_PATH}")
    print(json.dumps(payload["scope"], indent=2))
    print(json.dumps(payload["operations"], indent=2))
    print(f"Transport {TRANSPORT} status: {transport_status}")


# ----------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dryrun", "test", "execute"], default="dryrun")
    args = ap.parse_args(argv)

    print("=" * 60)
    print(f"  STEM SKB1 ← MGIE clone  |  mode={args.mode}  |  target=D01")
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
                         f"(TRSTATUS={ts['TRSTATUS']}).")

    print(f"\n[READ] D01 SKB1 live for BUKRS={SRC_BUKRS}...")
    mgie_rows = read_skb1(guard, SRC_BUKRS)
    print(f"        MGIE rows: {len(mgie_rows)}")
    print(f"[READ] D01 SKB1 live for BUKRS={TGT_BUKRS}...")
    stem_rows = read_skb1(guard, TGT_BUKRS)
    print(f"        STEM rows: {len(stem_rows)}")

    print(f"\n[READ] CBG SKB1 keys in E071K for STEM...")
    cbg_keys = read_cbg_skb1_keys(guard, TRANSPORT)
    print(f"        CBG currently holds {len(cbg_keys)} STEM SKB1 keys.")

    updates, inserts, fipos_fix, common, mgie_only, stem_only = compute_delta(
        mgie_rows, stem_rows
    )
    print(f"\n[DELTA]")
    print(f"  common SAKNRs (UPDATE to MGIE values): {len(updates)}")
    print(f"  MGIE-only (INSERT + attach to CBG):    {len(inserts)}")
    print(f"  STEM-only FIPOS fix:                   {len(fipos_fix)}")

    write_dryrun(updates, inserts, fipos_fix, common, mgie_only, stem_only,
                 ts, cbg_keys)

    if args.mode == "dryrun":
        print("\n[DRYRUN] No writes performed. Re-run with --mode=test to run 1 row.")
        guard.close()
        return 0

    # === TEST mode: one row per phase ===
    if args.mode == "test":
        print("\n" + "=" * 60)
        print("  TEST MODE — running ONE row per phase")
        print("=" * 60)
        if updates:
            r = run_batch(guard, build_update_abap(updates[:1]))
            print(f"  P1 update[1]  ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        if inserts:
            r = run_batch(guard, build_insert_abap(inserts[:1], attach_transport=True))
            print(f"  P2 insert[1]  ok={r['ok']} ko={r['ko']}  {r['output'][:200]}")
        if fipos_fix:
            r = run_batch(guard, build_fipos_fix_abap(fipos_fix[:1]))
            print(f"  P3 fix[1]     ok={r['ok']} ko={r['ko']} mi={r['mi']}  {r['output'][:200]}")
        guard.close()
        print("\n[TEST] done. Verify manually in SE16N + SE09, then re-run with --mode=execute.")
        return 0

    # === EXECUTE mode ===
    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase 1 UPDATE {len(updates)} common")
    print("=" * 60)
    total = {"p1_ok": 0, "p1_ko": 0, "p1_mi": 0,
             "p2_ok": 0, "p2_ko": 0,
             "p3_ok": 0, "p3_ko": 0, "p3_mi": 0}
    for i, b in enumerate(chunk(updates, BATCH_ROWS), 1):
        r = run_batch(guard, build_update_abap(b))
        total["p1_ok"] += r["ok"]; total["p1_ko"] += r["ko"]; total["p1_mi"] += r["mi"]
        if i % 10 == 0 or r["ko"]:
            print(f"  [P1 b{i:03d}] {len(b)} rows  ok={r['ok']} ko={r['ko']} mi={r['mi']}")
        if r["ko"]:
            print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase 2 INSERT {len(inserts)} + TR_OBJECTS_INSERT")
    print("=" * 60)
    for i, b in enumerate(chunk(inserts, BATCH_ROWS), 1):
        r = run_batch(guard, build_insert_abap(b, attach_transport=True))
        total["p2_ok"] += r["ok"]; total["p2_ko"] += r["ko"]
        print(f"  [P2 b{i:03d}] {len(b)} rows  ok={r['ok']} ko={r['ko']}")
        if r["ko"]:
            print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    print("\n" + "=" * 60)
    print(f"  EXECUTE — Phase 3 FIPOS fix {len(fipos_fix)}")
    print("=" * 60)
    for i, b in enumerate(chunk(fipos_fix, BATCH_ROWS), 1):
        r = run_batch(guard, build_fipos_fix_abap(b))
        total["p3_ok"] += r["ok"]; total["p3_ko"] += r["ko"]; total["p3_mi"] += r["mi"]
        print(f"  [P3 b{i:03d}] {len(b)} rows  ok={r['ok']} ko={r['ko']} mi={r['mi']}")
        if r["ko"]:
            print(f"       {r['output'][:200]}")
        time.sleep(THROTTLE_SEC)

    # Verify
    print("\n[VERIFY] Re-reading STEM SKB1 + CBG keys from D01...")
    stem_after = read_skb1(guard, TGT_BUKRS)
    cbg_after = read_cbg_skb1_keys(guard, TRANSPORT)
    # quick drift recompute
    updates2, inserts2, fipos2, _, _, _ = compute_delta(mgie_rows, stem_after)
    # In aligned state: inserts2 should be 0, updates2 (with any value drift) should be 0.
    # But updates2 logic rebuilds row payload not diff. Use field drift:
    drift = 0
    for src in mgie_rows:
        saknr = src["SAKNR"]
        tgt = next((x for x in stem_after if x["SAKNR"] == saknr), None)
        if tgt is None:
            drift += 1
            continue
        for c in NON_KEY:
            if (src.get(c) or "") != (tgt.get(c) or ""):
                drift += 1
                break
    print(f"  STEM rows after: {len(stem_after)}")
    print(f"  CBG STEM SKB1 keys after: {len(cbg_after)}  (delta: +{len(cbg_after)-len(cbg_keys)})")
    print(f"  MGIE→STEM drift rows remaining: {drift}")

    guard.close()

    # Log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write("# STEM SKB1 ← MGIE alignment\n\n")
        f.write(f"**Date:** 2026-04-14  \n")
        f.write(f"**Target:** D01 (transport {TRANSPORT})  \n")
        f.write(f"**Mode:** execute  \n\n")
        f.write(f"## Counters\n\n")
        for k, v in total.items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n- STEM rows after: {len(stem_after)} (was {len(stem_rows)})\n")
        f.write(f"- CBG SKB1/STEM keys after: {len(cbg_after)} (was {len(cbg_keys)})\n")
        f.write(f"- MGIE→STEM drift remaining: {drift}\n")
    print(f"\n[LOG] {LOG_PATH}")
    print(f"\nFINAL: {total}")
    return 0 if all(v == 0 for k, v in total.items() if k.endswith("_ko")) else 1


if __name__ == "__main__":
    sys.exit(main())

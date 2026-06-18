#!/usr/bin/env python
"""
Claim verifier — Layer 3 of the brain (the self-challenge that replaces the
human's constant manual challenge).

A claim is only TRUSTWORTHY if its evidence can be RE-DERIVED on demand. Most
claims today carry prose evidence (not runnable), so they are NOT machine-
verifiable. This harness:
  1. Re-runs every claim that has a structured `verification` block against the
     Gold DB, and reports CONFIRMED / DRIFT / ERROR.
  2. Reports how many claims have NO check at all — the honest measure of how
     much of what the brain "knows" is actually verifiable today.
  3. Writes the result back onto each claim (verification_status, last_verified,
     verified_value) so brain_state can surface trust, and flags DRIFT for review.

A `verification` block on a claim:
  "verification": {
     "source": "gold_db",
     "query":  "SELECT COUNT(*) FROM t030h WHERE ...",   # must be a SELECT
     "expect": {"op": "==", "value": 2},                  # see _check()
     "note":   "optional human note"
  }
Ops: ==, !=, >, >=, <, <=, nonzero, between [a,b], approx {value, tol}, contains.

Usage:
  python brain_v2/verify_claims.py            # run + write statuses back
  python brain_v2/verify_claims.py --dry-run  # report only, do not write
"""
import json, io, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "brain_v2" / "claims" / "claims.json"
GOLD = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"


def _check(actual, expect):
    """Return (ok: bool, human_expect: str)."""
    op = expect.get("op")
    v = expect.get("value")
    try:
        if op == "==":      return actual == v or str(actual) == str(v), f"== {v}"
        if op == "!=":      return str(actual) != str(v), f"!= {v}"
        if op == ">":       return float(actual) > v, f"> {v}"
        if op == ">=":      return float(actual) >= v, f">= {v}"
        if op == "<":       return float(actual) < v, f"< {v}"
        if op == "<=":      return float(actual) <= v, f"<= {v}"
        if op == "nonzero": return float(actual) != 0, "!= 0"
        if op == "between": return v[0] <= float(actual) <= v[1], f"in [{v[0]},{v[1]}]"
        if op == "approx":  return abs(float(actual) - v) <= expect.get("tol", 0.01), f"~= {v} (±{expect.get('tol',0.01)})"
        if op == "contains":return str(v) in str(actual), f"contains '{v}'"
    except (TypeError, ValueError):
        return False, f"{op} {v} (uncomparable actual={actual!r})"
    return False, f"unknown op {op}"


def run(write=True):
    claims = json.load(io.open(CLAIMS, encoding="utf-8"))
    con = sqlite3.connect(str(GOLD))
    rows = {"CONFIRMED": [], "DRIFT": [], "ERROR": [], "NO_CHECK": []}
    for c in claims:
        cid = c.get("id")
        v = c.get("verification")
        if not v or v.get("source") != "gold_db":
            rows["NO_CHECK"].append(cid)
            continue
        q = (v.get("query") or "").strip()
        if not q.lower().startswith("select"):
            rows["ERROR"].append((cid, "query is not a SELECT"))
            c["verification_status"] = "ERROR"
            continue
        # PROVENANCE GUARD — the line is CODE vs DATA, not P01 vs D01.
        # A claim about REALITY/DATA (balance, document count, who-posted, job ran)
        # must be checked against P01 (bare-named Gold DB tables). A claim about
        # CODE/structure (tcode->program, a table's fields) is system-invariant and
        # may use a d01_/v01_ table — the claim opts in with system_invariant=true,
        # which means "this is a CODE fact, not a reality fact". Reading a d01_ table
        # WITHOUT that flag = a reality-claim being checked against non-P01 data = ERROR.
        import re as _re
        cross = _re.findall(r"\b(d01_\w+|v01_\w+)\b", q.lower())
        if cross and not v.get("system_invariant"):
            rows["ERROR"].append((cid, f"provenance: P01 claim checked against {cross} (set system_invariant=true if SAP-standard)"))
            c["verification_status"] = "ERROR"
            c["needs_review"] = True
            continue
        try:
            r = con.execute(q).fetchone()
            actual = r[0] if r else None
            ok, exp = _check(actual, v["expect"])
            status = "CONFIRMED" if ok else "DRIFT"
            rows[status].append((cid, f"actual={actual} | expect {exp}"))
            c["verification_status"] = status
            c["last_verified"] = "s079"
            c["verified_value"] = actual
            if status == "DRIFT":
                c["needs_review"] = True
        except Exception as e:
            rows["ERROR"].append((cid, str(e)[:90]))
            c["verification_status"] = "ERROR"
    con.close()

    if write:
        json.dump(claims, io.open(CLAIMS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ---- trust dashboard ----
    total = len(claims)
    verifiable = total - len(rows["NO_CHECK"])
    print("=" * 64)
    print("CLAIM VERIFIER — Layer 3 trust dashboard")
    print("=" * 64)
    print(f"  Total claims:              {total}")
    print(f"  Machine-verifiable (have a check): {verifiable}  ({round(100*verifiable/total)}%)")
    print(f"  No check (prose-only):     {len(rows['NO_CHECK'])}")
    print(f"  ---- of the verifiable ----")
    print(f"  CONFIRMED:                 {len(rows['CONFIRMED'])}")
    print(f"  DRIFT (needs review):      {len(rows['DRIFT'])}")
    print(f"  ERROR:                     {len(rows['ERROR'])}")
    for status in ("CONFIRMED", "DRIFT", "ERROR"):
        if rows[status]:
            print(f"\n  {status}:")
            for cid, detail in rows[status]:
                print(f"    claim {cid}: {detail}")
    print()
    print(f"  Honest read: only {verifiable}/{total} claims can be checked by machine today.")
    print(f"  The other {len(rows['NO_CHECK'])} rely on prose evidence — a human must trust them.")
    print(f"  Every NEW claim should carry a `verification` block so this number climbs.")
    return rows


if __name__ == "__main__":
    run(write="--dry-run" not in sys.argv)

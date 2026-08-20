"""
CLAIMS-HEALTH GATE (change #2, 2026-06-22) — systematize what caught claim #232 by escalation.
A claim with <2 INDEPENDENT evidence sources is WEAK; a WEAK + TIER_1 claim is the dangerous kind
(high-confidence, thin evidence) — exactly what #232 was (1 source = a raw count → wrong conclusion).
This gate scans claims.json, scores evidence health, and emits the verification worklist (the WEAK TIER_1
claims that should each get a verifier chip). Run it at session close; queue a chip per weak high-tier claim.

"Independent" = distinct evidence TYPE (empirical / production_data / source_code / config) — two of the same
type is corroboration, not independence.

Run:  python brain_v2/claims_health.py
"""

# REGLAS QUE APLICAN AQUI (citadas para que existan en su punto de uso, no solo en el JSON):
#   feedback_claims_health_gate_at_close
#     -> el momento es medir la salud de los claims: este script ES esa medida
import io, json, os

CLAIMS = os.path.join(os.path.dirname(__file__), "claims", "claims.json")


def _ev_types(claim):
    types = set()
    for ev in (claim.get("evidence_for") or []):
        if isinstance(ev, dict):
            t = ev.get("type") or ev.get("evidence_type") or "unknown"
            types.add(t)
        elif isinstance(ev, str) and ev.strip():
            types.add("legacy_text")
    return types


def health(claim):
    ts = _ev_types(claim)
    n = len(ts)
    if n >= 2:   return "STRONG"      # >=2 independent types
    if n == 1:   return "WEAK"        # single source/type
    # fall back to legacy text fields
    if claim.get("evidence_legacy_text_for") or claim.get("evidence_count_for", 0):
        return "WEAK"
    return "UNSUPPORTED"


def main():
    c = json.load(io.open(CLAIMS, encoding="utf-8"))
    claims = c if isinstance(c, list) else c.get("claims", [])
    buckets = {"STRONG": 0, "WEAK": 0, "UNSUPPORTED": 0}
    worklist = []
    for cl in claims:
        if str(cl.get("status", "active")).startswith("supersed"):
            continue  # superseded claims are not live
        h = health(cl)
        buckets[h] += 1
        tier = cl.get("tier") or cl.get("evidence_tier") or "?"
        if h in ("WEAK", "UNSUPPORTED") and str(tier).upper() in ("TIER_1", "1", "TIER1"):
            cid = cl.get("id") or cl.get("claim_id")
            txt = (cl.get("statement") or cl.get("claim") or cl.get("text") or "")[:90]
            worklist.append((cid, tier, h, sorted(_ev_types(cl)), txt))
    live = sum(buckets.values())
    verif_rate = round(100 * buckets["STRONG"] / max(live, 1), 1)
    print(f"=== CLAIMS-HEALTH GATE — {live} live claims ===")
    print(f"  STRONG (>=2 independent types): {buckets['STRONG']}  ({verif_rate}%)")
    print(f"  WEAK   (1 source):              {buckets['WEAK']}")
    print(f"  UNSUPPORTED (0):                {buckets['UNSUPPORTED']}")
    print(f"  *** VERIFICATION RATE = {verif_rate}% of live claims have >=2 independent sources ***")
    print(f"\n  VERIFICATION WORKLIST — WEAK/UNSUPPORTED TIER_1 claims (queue a verifier chip each): {len(worklist)}")
    for cid, tier, h, types, txt in worklist[:15]:
        print(f"    #{cid} [{h:11}] types={types or 'none'} :: {txt}")
    # emit for the meta-capability scorer (change #5)
    out = os.path.join(os.path.dirname(__file__), "claims_health.json")
    json.dump({"live": live, "buckets": buckets, "verification_rate": verif_rate,
               "weak_tier1_worklist": [{"id": w[0], "tier": w[1], "health": w[2], "types": w[3], "stmt": w[4]} for w in worklist]},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print(f"\n  emitted: {out}  (feeds the meta-capability VERIFY dimension)")


if __name__ == "__main__":
    main()

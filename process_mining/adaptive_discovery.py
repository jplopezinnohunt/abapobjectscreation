"""
SELF-ADAPTING process discovery (per user 2026-06-21: "a process mining discovery that self-adapts
with what it learns"). Instead of a human hand-adding FM->process patterns, the engine AUTO-RESOLVES each
unknown call from the brain — its FUNCTION GROUP (tfdir_custom: SAPLY_PS_BAPI -> PS, SAPLY_FM_BAPI -> PSM,
SAPLZHRBK -> HCM) + naming + APP_DOMAIN — then LEARNS it (persists to learned_rules.json) and RE-CLASSIFIES.
It loops until coverage converges; each run it explains more with zero hand-coding. What it cannot resolve
(no TFDIR entry / no signal) it surfaces for human review = the genuine frontier.

Run:  python process_mining/adaptive_discovery.py
Learns into: process_mining/learned_rules.json (grows every run).
"""
import os, sys, json, sqlite3
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import rfc_process_classifier as base  # reuse the base patterns + classify()

GOLD = r"Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
LEARNED = os.path.join(os.path.dirname(__file__), "learned_rules.json")
MIN_VOL = 50  # only auto-learn FMs above this call volume (avoid noise)

# Auto-resolver: keyword over {FM name + function group + app domain} -> process. The function group
# encodes the SAP domain (SAP naming convention) — this is what lets the engine teach itself.
FG_RULES = [
    ("PS-Project",     ["_PS_", "PROJ", "WBS", "PRPS", "SAPLY_PS"]),
    ("PSM-Budget/FM",  ["_FM_", "FUND", "FMKU", "BCS", "FMRESERV", "SAPLY_FM"]),
    ("HCM",            ["HRBK", "HRCA", "_HR_", "PERNR", "PAYROLL", "RHAK", "PA00", "TRV", "TRIP"]),
    ("MDM-Vendor",     ["VEND", "KRED", "LFA1"]),
    ("MDM-Bank",       ["BNKA", "BANK"]),
    ("P2P",            ["_MM_", "_PO_", "_PR_", "PURCH", "REQUIS", "GOODSMVT", "INVOICE", "ENTRYSHEET", "EKKO"]),
    ("FI",             ["_FI_", "_GL_", "ACCT", "BKPF", "BSEG", "SAKO"]),
    ("Payment/Bank",   ["PAYM", "PAYR", "DMEE", "FEB", "_BNK"]),
    ("Identity/Role",  ["USER", "ROLE", "_AGR", "AUTH"]),
    ("Address/Util",   ["ADDRESS", "POSTAL", "_SX0", "NORMAL"]),
]


def auto_resolve(fm, fg, app):
    hay = f"{fm} {fg or ''} {app or ''}".upper()
    for proc, kws in FG_RULES:
        if any(k in hay for k in kws):
            return proc, f"func_group={fg or app or '?'}"
    return None, None


def main():
    c = sqlite3.connect(GOLD, timeout=10)
    fgmap = {fn: (fg or pn, ap) for fn, pn, fg, ap in
             c.execute("SELECT FUNCNAME, PNAME, FUNC_GROUP, APP_DOMAIN FROM tfdir_custom")}
    rows = c.execute("SELECT PARAM3, SLGUSER, COUNT(*) FROM rsau_audit_history "
                     "WHERE TXSUBCLSID='RFC Function Call' AND PARAM3<>'' GROUP BY PARAM3, SLGUSER").fetchall()
    fmvol = defaultdict(int)                       # business FM -> volume (excl. ours/technical)
    for fm, user, n in rows:
        b, _ = base.classify(fm, user)
        if b in ("KNOWN", "UNKNOWN"):
            fmvol[fm] += n
    learned = json.load(open(LEARNED)) if os.path.exists(LEARNED) else {}

    def resolved(fm):
        b, proc = base.classify(fm, "")
        if b == "KNOWN": return proc
        return learned[fm]["process"] if fm in learned else None

    biz = sum(fmvol.values())
    progression, learned_this_run = [], []
    for _ in range(6):                              # adaptive loop until converged
        cov = round(100 * sum(n for fm, n in fmvol.items() if resolved(fm)) / biz, 1)
        progression.append(cov)
        new = 0
        for fm, n in sorted(fmvol.items(), key=lambda x: -x[1]):
            if resolved(fm) or n < MIN_VOL:
                continue
            fg, ap = fgmap.get(fm, (None, None))
            proc, ev = auto_resolve(fm, fg, ap)
            if proc:
                learned[fm] = {"process": proc, "evidence": ev, "vol": n}
                learned_this_run.append((fm, proc, ev, n)); new += 1
        if not new:
            break
    json.dump(learned, open(LEARNED, "w"), indent=1)

    final = round(100 * sum(n for fm, n in fmvol.items() if resolved(fm)) / biz, 1)
    print(f"=== SELF-ADAPTING DISCOVERY ===")
    print(f"  coverage progression (auto-learned): {progression} -> {final}%")
    print(f"  learned rules persisted: {len(learned)}  (+{len(learned_this_run)} this run, zero hand-coding)")
    print("  what it taught itself this run (top):")
    for fm, proc, ev, n in sorted(learned_this_run, key=lambda x: -x[3])[:10]:
        print(f"    {n:>8,}  {fm:34} -> {proc:16} [{ev}]")
    rem = [(fm, n) for fm, n in fmvol.items() if not resolved(fm)]
    rem_vol = sum(n for _, n in rem)
    print(f"\n  FRONTIER (cannot self-resolve — human review): {len(rem)} FMs, {rem_vol:,} calls "
          f"({round(100*rem_vol/biz,1)}%)")
    for fm, n in sorted(rem, key=lambda x: -x[1])[:8]:
        print(f"    {n:>7,}  {fm:34} (in tfdir={fm in fgmap})")


if __name__ == "__main__":
    main()

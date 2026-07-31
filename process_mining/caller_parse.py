"""caller_parse.py — parse the audit caller string, and repair SAP's truncation (s097).

Shared by interface_boundary (F1) and derive_satellites (F2). Both parsed `PARAMX`
independently, and both inherited the same defect — which is the argument for one
implementation: the alias bug in this project appeared three times for exactly that reason.

**The truncation is in the DATA, not in the regex.** I recorded the failure mode as "the
destination parse truncates names" and that was wrong about the cause. `PARAMX` is a fixed
length field and SAP cuts the caller string when it does not fit:

    caller: host=HQ-SAP-P01_P01_00, dest=HQ-SAP-P01-1_P01_01, user=SMTMSBP   <- complete
    caller: host=HQ-SAP-P01_P01_00, dest=HQ-SAP-P01-1_P01_                   <- cut

The regex extracts exactly what is there. A better pattern cannot recover a character the
source never stored.

**So the repair is reconciliation, not parsing.** A value that is a strict PREFIX of a
longer observed value, and appears nowhere else as a complete name, is the same entity cut
short. `HQ-SAP-P01-1_P01_` is `HQ-SAP-P01-1_P01_01`; `328a121d-ba7a-4b84-b` is
`328a121d-ba7a-4b84-b2ae-b3a427c53727`.

**Conservative on purpose.** Two rules keep this from merging genuinely different entities:
a fragment must be strictly shorter, and it must have exactly ONE longer candidate. A
fragment matching two different full names is ambiguous and is left alone — merging it
would invent a fact, and a wrong merge is worse than a duplicate.
"""
import re

DEST = re.compile(r"dest=\s*([^\s,;]+)")
HOST = re.compile(r"host=\s*([^\s,;]+)")
USER = re.compile(r"user=\s*([^\s,;]+)")

MIN_FRAGMENT = 8       # shorter than this, a prefix match means nothing


def parse(paramx):
    """caller string -> (dest, host, user). Any may be None."""
    px = paramx or ""
    d, h, u = DEST.search(px), HOST.search(px), USER.search(px)
    return (d.group(1).strip() if d else None,
            h.group(1).strip() if h else None,
            u.group(1).strip() if u else None)


def build_truncation_map(names):
    """fragment -> full name, for values SAP cut short.

    Returns only UNAMBIGUOUS repairs: a fragment with two possible completions is left
    unmapped, because choosing one would invent a fact.
    """
    names = {n for n in names if n}
    ordered = sorted(names, key=len, reverse=True)
    repair, ambiguous = {}, set()

    for frag in names:
        if len(frag) < MIN_FRAGMENT:
            continue
        cands = [n for n in ordered if len(n) > len(frag) and n.startswith(frag)]
        if len(cands) == 1:
            repair[frag] = cands[0]
        elif len(cands) > 1:
            # several completions share this prefix — genuinely ambiguous
            ambiguous.add(frag)
    return repair, ambiguous


def canonical(name, repair):
    """Resolve a possibly-truncated name to its full form, following one hop."""
    seen = set()
    cur = name
    while cur in repair and cur not in seen:
        seen.add(cur)
        cur = repair[cur]
    return cur


if __name__ == "__main__":
    import sqlite3
    from pathlib import Path
    GOLD = (Path(__file__).resolve().parent.parent / "Zagentexecution" /
            "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db")
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    rows = con.execute("SELECT DISTINCT PARAMX FROM rsau_audit_history "
                       "WHERE PARAMX IS NOT NULL AND PARAMX <> ''").fetchall()
    con.close()
    dests, hosts = set(), set()
    for (px,) in rows:
        d, h, _ = parse(px)
        if d:
            dests.add(d)
        if h:
            hosts.add(h)
    rep, amb = build_truncation_map(dests | hosts)
    print(f"{len(dests)} destinations, {len(hosts)} hosts observed")
    print(f"truncated values repaired: {len(rep)} · left ambiguous: {len(amb)}")
    for frag, full in sorted(rep.items())[:12]:
        print(f"    {frag:34s} -> {full}")

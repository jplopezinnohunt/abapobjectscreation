"""KEEP ONLY THE PAYROLL RUNS THAT ACTUALLY POSTED. Simulations are deleted.

WHY THIS EXISTS
    A payroll posting run produces documents whether or not it is real. A simulation writes
    PPDHD, PPDIT, PPDIX and PPOIX rows that are STRUCTURALLY IDENTICAL to a real posting —
    same document numbers, same amounts, same account assignments. Nothing in the row says
    which it is.

    That is not a theoretical hazard. Measured on the 2026 load: 1,828 of 2,316 runs never
    reached accounting, and summing the Constant Dollar impact without filtering them gave
    USD 20.5 million when the real figure is USD 1.98 million. NINE TIMES too high, from a
    query that looked perfectly reasonable.

    The fix is not a rule to remember. It is to make the wrong answer unavailable: the
    simulations come out of the golden, so no later analysis can count them.

THE DISCRIMINATOR, AND WHY IT IS TRUSTWORTHY
    BKPF-AWKEY = PPDHD-DOCNUM for AWTYP 'HRPAY'. A run either transfers WHOLE or not at all —
    measured across 2,316 runs, ZERO are partial, which is what makes the run (not the
    document) the right unit. And of the 89,420 documents from unposted runs, NOT ONE appears
    in BKPF under any AWTYP at all.

    The ratio is ~10-14% in every month of 2026 and in 2024 and 2025 alike, so this is
    structural rather than a backlog of transfers not yet made.

WHAT IS KEPT AND WHAT IS NOT
    PPDIT, PPDIX and PPOIX are purged to posted runs only — they are the detail, and the
    detail is what gets summed by mistake.

    PPDHD IS KEPT WHOLE, deliberately. It is the record that the simulations existed at all,
    which is how the ratio above is measurable; deleting it would erase the evidence for the
    rule. It also spans 2007-2026 while BKPF in the golden covers 2024-2026 only, so the
    discriminator CANNOT judge a run outside that window — purging PPDHD by it would silently
    destroy every pre-2024 run as if it were a simulation.

    That window limit applies to any future use of this script: it is only valid where BKPF
    coverage exists.

USAGE
    python scripts/extraction/purge_simulation_runs.py            # report only
    python scripts/extraction/purge_simulation_runs.py --apply    # delete
"""
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Detail tables and how each one reaches a run. PPDHD is absent on purpose — see the header.
TARGETS = [
    ("ppdix", "RUNID in (select RUNID from payroll_runs_posted)"),
    ("ppoix", "RUNID in (select RUNID from payroll_runs_posted)"),
    ("ppdit", "DOCNUM in (select DOCNUM from ppdhd "
              "where RUNID in (select RUNID from payroll_runs_posted))"),
]


def main(argv):
    apply = "--apply" in argv
    con = sqlite3.connect(str(GOLD))
    con.execute("DROP VIEW IF EXISTS payroll_runs_posted")
    con.execute("""CREATE VIEW payroll_runs_posted AS
     SELECT DISTINCT h.RUNID FROM ppdhd h
     JOIN bkpf k ON k.AWKEY = h.DOCNUM AND k.AWTYP = 'HRPAY'""")
    con.commit()
    runs = con.execute("select count(*) from payroll_runs_posted").fetchone()[0]
    print("runs con documento contable: %d" % runs)
    print("=" * 74)
    for t, keep in TARGETS:
        tot = con.execute('select count(*) from "%s"' % t).fetchone()[0]
        k = con.execute('select count(*) from "%s" where %s' % (t, keep)).fetchone()[0]
        print("   %-6s total %9d  final %8d  simulacion %9d  (%.1f%%)"
              % (t, tot, k, tot - k, 100.0 * (tot - k) / tot if tot else 0))
        if apply and tot > k:
            con.execute('DELETE FROM "%s" WHERE NOT (%s)' % (t, keep))
            con.commit()
            print("      borradas %d filas, quedan %d"
                  % (tot - k, con.execute('select count(*) from "%s"' % t).fetchone()[0]))
    if not apply:
        print("\n   (informe. Anade --apply para borrar)")
    else:
        # Leave the rule where the next reader of the table will trip over it, not only in
        # this file. A comment in a script nobody opens is not a guarantee.
        con.execute("DROP VIEW IF EXISTS payroll_detail_is_posted_runs_only")
        con.execute("""CREATE VIEW payroll_detail_is_posted_runs_only AS
         SELECT 'ppdit, ppdix and ppoix contain ONLY runs that produced an FI document. '
                || 'Simulation runs were deleted s098 because summing them overstated the '
                || 'Constant Dollar impact ninefold. PPDHD is NOT purged: it is the record '
                || 'that the simulations existed.' AS note""")
        con.commit()
        print("\n   base purgada. Vista payroll_detail_is_posted_runs_only deja la regla escrita.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

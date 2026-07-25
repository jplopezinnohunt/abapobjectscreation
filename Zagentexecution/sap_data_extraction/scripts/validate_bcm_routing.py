"""
validate_bcm_routing.py
========================
Tests the causal hypothesis for BCM routing now that REGUH has the full schema.

Hypotheses:
  H1 (LEGACY, likely wrong):
      LAUFI suffix 'B' <-> BCM batch exists
      (100% correlation observed, but this is naming convention, not rule)

  H2 (CAUSAL, to prove):
      REGUH.RZAWE (payment method) joined to T042Z.ZLSCH where some flag
      (XBKKT / XSTRA / XEINZ / XCRED / ...) marks BCM-enabled methods
      <-> BCM batch exists via BNK_BATCH_ITEM join

  H3 (alternative):
      T042E.ZBUKR+ZLSCH combination has a BCM activation marker, not T042Z

Outputs a Markdown report: reports/bcm_routing_validation.md
"""

import os
import sys
import sqlite3

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPTS_DIR, "..", "sqlite", "p01_gold_master_data.db")
REPORT_PATH = os.path.join(SCRIPTS_DIR, "..", "reports", "bcm_routing_validation.md")
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)


def q(conn, sql, *params):
    return conn.execute(sql, params).fetchall()


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    out = []
    out.append("# BCM Routing Causal Validation\n")
    out.append(f"_Generated: {os.path.basename(__file__)}_\n")

    # ----- Schema snapshot -----
    out.append("\n## 1. REGUH_FULL schema\n")
    cols = c.execute("PRAGMA table_info(REGUH_FULL)").fetchall()
    out.append(f"{len(cols)} columns: {', '.join(r[1] for r in cols)}\n")

    out.append("\n## 2. REGUH_FULL coverage\n")
    tot = c.execute("SELECT COUNT(*) FROM REGUH_FULL").fetchone()[0]
    runs = c.execute("SELECT COUNT(DISTINCT LAUFD||LAUFI) FROM REGUH_FULL").fetchone()[0]
    mn, mx = c.execute("SELECT MIN(LAUFD), MAX(LAUFD) FROM REGUH_FULL WHERE LAUFD!=''").fetchone()
    out.append(f"- rows={tot:,}  distinct runs (LAUFD+LAUFI)={runs:,}  range={mn}..{mx}\n")

    # ----- H1 legacy test -----
    out.append("\n## 3. H1 — LAUFI suffix B rule (legacy)\n")
    rows = c.execute("""
        WITH r AS (SELECT DISTINCT LAUFD, LAUFI, substr(LAUFI,-1,1) s FROM REGUH_FULL)
        SELECT r.s,
               COUNT(*) runs,
               SUM(CASE WHEN b.LAUFI IS NOT NULL THEN 1 ELSE 0 END) bcm_linked,
               printf('%.1f%%', 100.0 * SUM(CASE WHEN b.LAUFI IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*)) pct
        FROM r LEFT JOIN (SELECT DISTINCT LAUFD, LAUFI FROM BNK_BATCH_HEADER) b
               ON b.LAUFD=r.LAUFD AND b.LAUFI=r.LAUFI
        GROUP BY r.s ORDER BY runs DESC
    """).fetchall()
    out.append("| suffix | runs | with_bcm | pct |\n|---|---|---|---|\n")
    for s, runs, bcm, pct in rows:
        out.append(f"| `{s}` | {runs:,} | {bcm:,} | {pct} |\n")

    # ----- H2 causal test: RZAWE vs BCM -----
    out.append("\n## 4. H2 — RZAWE (payment method) rule (causal candidate)\n")
    rows = c.execute("""
        WITH r AS (SELECT DISTINCT LAUFD, LAUFI, RZAWE FROM REGUH_FULL)
        SELECT r.RZAWE,
               COUNT(*) runs,
               SUM(CASE WHEN b.LAUFI IS NOT NULL THEN 1 ELSE 0 END) bcm_linked,
               printf('%.1f%%', 100.0 * SUM(CASE WHEN b.LAUFI IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*)) pct
        FROM r LEFT JOIN (SELECT DISTINCT LAUFD, LAUFI FROM BNK_BATCH_HEADER) b
               ON b.LAUFD=r.LAUFD AND b.LAUFI=r.LAUFI
        GROUP BY r.RZAWE ORDER BY runs DESC
    """).fetchall()
    out.append("| RZAWE (ZLSCH) | runs | with_bcm | pct |\n|---|---|---|---|\n")
    for z, runs, bcm, pct in rows:
        out.append(f"| `{z}` | {runs:,} | {bcm:,} | {pct} |\n")

    # ----- T042Z flag enumeration for BCM-linked methods -----
    out.append("\n## 5. Which T042Z flag discriminates BCM-enabled PMs?\n")
    # Flags to test — those found in T042Z schema
    flags = ["XBKKT", "XSTRA", "XEINZ", "XCRED", "XDEBT", "XSKRL", "XINKS", "XAUSZ"]
    t042z_cols = [r[1] for r in c.execute("PRAGMA table_info(T042Z_FULL)").fetchall()]
    flags = [f for f in flags if f in t042z_cols]

    # For each country+ZLSCH in BCM-linked RZAWEs, check which flag is set
    out.append("\n### Flag profile for BCM-linked payment methods\n")
    out.append("(ZLSCH values whose runs have 100% BCM linkage vs 0%)\n\n")

    # Find BCM-yes and BCM-no RZAWEs
    bcm_yes_pms = {z for z, runs, bcm, _ in rows if bcm > 0 and bcm == runs}
    bcm_partial_pms = {z for z, runs, bcm, _ in rows if 0 < bcm < runs}
    bcm_no_pms = {z for z, runs, bcm, _ in rows if bcm == 0}

    out.append(f"- **BCM-yes PMs (100%):** {sorted(bcm_yes_pms)}\n")
    out.append(f"- **BCM-partial PMs:**  {sorted(bcm_partial_pms)}\n")
    out.append(f"- **BCM-no PMs (0%):**  {sorted(bcm_no_pms)}\n")

    # Show T042Z flag settings per ZLSCH
    if flags:
        out.append(f"\n### T042Z flag settings per ZLSCH (flags tested: {flags})\n")
        flag_sql = ", ".join(flags)
        # Group by ZLSCH across countries — show if flags are consistent
        rows2 = c.execute(f"""
            SELECT ZLSCH, {", ".join(f'GROUP_CONCAT(DISTINCT {f})' for f in flags)},
                   COUNT(DISTINCT LAND1) countries
            FROM T042Z_FULL
            GROUP BY ZLSCH ORDER BY ZLSCH
        """).fetchall()
        out.append(f"| ZLSCH | {' | '.join(flags)} | countries | BCM class |\n")
        out.append("|---" * (len(flags) + 3) + "|\n")
        for row in rows2:
            zlsch = row[0]
            flag_vals = row[1:1+len(flags)]
            ctrys = row[-1]
            cls = ("BCM-yes" if zlsch in bcm_yes_pms else
                   "BCM-partial" if zlsch in bcm_partial_pms else
                   "BCM-no" if zlsch in bcm_no_pms else "?")
            out.append(f"| `{zlsch}` | " + " | ".join(f"`{v}`" for v in flag_vals) + f" | {ctrys} | **{cls}** |\n")

    # ----- H3 T042E-side test -----
    out.append("\n## 6. H3 — T042E per-BUKRS activation\n")
    t042e_cols = [r[1] for r in c.execute("PRAGMA table_info(T042E_FULL)").fetchall()]
    out.append(f"T042E_FULL columns: {t042e_cols}\n")

    # ----- Final conclusion generator -----
    out.append("\n## 7. Interpretation checklist\n")
    out.append("- [ ] Does any single T042Z flag perfectly split BCM-yes from BCM-no PMs?\n")
    out.append("- [ ] Is the sufijo-B pattern a convention caused by ZLSCH naming upstream?\n")
    out.append("- [ ] Do BCM-partial PMs show a company-code (ZBUKR) gradient in T042E?\n")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("".join(out))
    print(f"Report written: {REPORT_PATH}")
    print(f"{len(out)} sections")

    conn.close()


if __name__ == "__main__":
    main()

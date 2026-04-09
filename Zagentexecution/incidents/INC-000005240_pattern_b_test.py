"""
INC-000005240 — Pattern B empirical test
=========================================
Uses DA_ENGONGA (field user, Y_USERFO='DAK', Dakar) invoices cleared by
C_LOPEZ / L_HANGI / JOBBATCH (HQ central users / system) to test the
structural-risk hypothesis:

  - Does the substitution at invoice time write the INVOICE POSTER's office
    (e.g., 'DAK' for DA_ENGONGA's invoices)?
  - Does the substitution at payment/clearing time OVERWRITE those values
    with the CLEARING USER's office (e.g., 'HQ' for C_LOPEZ)?
  - Or are both sides carrying the same value?

If invoice XREF = DAK and clearing XREF = HQ → mis-attribution proven.
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")

# Pairs: (invoice BELNR, invoice TCODE, clearing BELNR, clearing USNAM, clearing TCODE)
TEST_CASES = [
    ("5100004414", "MIRO",  "0002003771", "C_LOPEZ",  "F110"),
    ("5100004419", "MIRO",  "0002003771", "C_LOPEZ",  "F110"),
    ("5100004424", "MIRO",  "0002003828", "C_LOPEZ",  "F110"),
    ("6400003609", "FB60",  "0100024070", "L_HANGI",  "FB1K"),
    ("6400003617", "FB01",  "0100020974", "JOBBATCH", "FB1K"),
    ("6400003560", "FB01",  "0100020514", "JOBBATCH", "FB1K"),
]

def fetch_bsak(guard, belnr):
    """Read all BSAK rows for a document (vendor cleared items)."""
    rows = rfc_read_paginated(
        guard, table="BSAK",
        fields=["BUKRS", "GJAHR", "BELNR", "BUZEI",
                "XREF1", "XREF2", "XREF3", "ZUONR",
                "HKONT", "LIFNR", "BSCHL",
                "AUGBL", "AUGDT", "DMBTR", "SHKZG", "BLART"],
        where=f"BUKRS = 'UNES' AND BELNR = '{belnr}' AND GJAHR = '2026'",
        batch_size=500,
    )
    return rows


def fetch_bsis(guard, belnr):
    """Read all BSIS rows (GL open items) for a document."""
    rows = rfc_read_paginated(
        guard, table="BSIS",
        fields=["BUKRS", "GJAHR", "BELNR", "BUZEI",
                "XREF1", "XREF2", "XREF3", "ZUONR",
                "HKONT", "BSCHL", "DMBTR", "SHKZG"],
        where=f"BUKRS = 'UNES' AND BELNR = '{belnr}' AND GJAHR = '2026'",
        batch_size=500,
    )
    return rows


def show_lines(label, rows):
    print(f"\n  {label}: {len(rows)} lines")
    for r in rows:
        partner = (r.get('LIFNR') or '').strip() or '-'
        print(
            f"    L{str(r.get('BUZEI','?')).strip():>3s} "
            f"HKONT={str(r.get('HKONT','')).strip():10s} "
            f"LIFNR={partner:<10} "
            f"BSCHL={str(r.get('BSCHL','')).strip() or '-':3s} "
            f"XREF1={str(r.get('XREF1','')).strip()!r:12s} "
            f"XREF2={str(r.get('XREF2','')).strip()!r:12s} "
            f"XREF3={str(r.get('XREF3','')).strip()!r:12s} "
            f"ZUONR={str(r.get('ZUONR','')).strip()!r}"
        )


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    results = []
    for (inv_belnr, inv_tcode, clr_belnr, clr_user, clr_tcode) in TEST_CASES:
        print("=" * 100)
        print(f"PAIR: invoice {inv_belnr}/2026 ({inv_tcode}) by DA_ENGONGA")
        print(f"      cleared by  {clr_belnr}/2026 ({clr_tcode}) by {clr_user}")
        print("=" * 100)

        inv_bsak = fetch_bsak(guard, inv_belnr)
        clr_bsak = fetch_bsak(guard, clr_belnr)
        clr_bsis = fetch_bsis(guard, clr_belnr)

        show_lines(f"Invoice {inv_belnr} BSAK vendor lines", inv_bsak)
        show_lines(f"Clearing {clr_belnr} BSAK vendor lines", clr_bsak)
        show_lines(f"Clearing {clr_belnr} BSIS GL lines", clr_bsis)

        # Aggregate
        inv_xref2 = sorted({str(r.get('XREF2','')).strip() for r in inv_bsak})
        clr_xref2 = sorted({str(r.get('XREF2','')).strip() for r in clr_bsak})
        print(f"\n  Invoice XREF2 distinct values:  {inv_xref2}")
        print(f"  Clearing XREF2 distinct values: {clr_xref2}")

        verdict = "?"
        if inv_xref2 == clr_xref2 and inv_xref2:
            verdict = f"SAME ({inv_xref2[0]})"
        elif inv_xref2 and clr_xref2 and inv_xref2 != clr_xref2:
            verdict = f"MISMATCH — invoice={inv_xref2} clearing={clr_xref2}"
        elif not inv_xref2 or not clr_xref2:
            verdict = "at least one side empty"
        print(f"  VERDICT: {verdict}\n")

        results.append({
            "invoice": inv_belnr, "invoice_tcode": inv_tcode,
            "clearing": clr_belnr, "clearing_user": clr_user, "clearing_tcode": clr_tcode,
            "invoice_bsak": inv_bsak,
            "clearing_bsak": clr_bsak,
            "clearing_bsis": clr_bsis,
            "invoice_xref2": inv_xref2,
            "clearing_xref2": clr_xref2,
            "verdict": verdict,
        })

    # Also pull USR05 Y_USERFO for the clearing users we haven't checked
    print("\n" + "=" * 100)
    print("USR05 Y_USERFO for clearing users")
    print("=" * 100)
    for u in ["C_LOPEZ", "L_HANGI", "JOBBATCH", "DA_ENGONGA"]:
        try:
            usr05 = rfc_read_paginated(
                guard, table="USR05",
                fields=["BNAME", "PARID", "PARVA"],
                where=f"BNAME = '{u}' AND PARID = 'Y_USERFO'",
                batch_size=10,
            )
            pv = usr05[0]["PARVA"].strip() if usr05 else "(no row)"
            print(f"  {u:15s} Y_USERFO = {pv!r}")
        except Exception as e:
            print(f"  {u:15s} read failed: {e}")

    OUT.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults written to: {OUT}")


if __name__ == "__main__":
    main()

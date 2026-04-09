"""
uba01_gl_full_compare.py
=========================
Compare SKA1, SKB1, SKAT for ALL 4 UBA01 G/L accounts across D01, V01, P01.
Field-by-field comparison.
"""
import sys, os, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

BUKRS = "UNES"
KTOPL = "UNES"
GLS = ["0001065421", "0001165421", "0001065424", "0001165424"]
SYSTEMS = ["D01", "V01", "P01"]

SKA1_FIELDS = ["SAKNR", "KTOKS", "XBILK", "BILKT", "GVTYP", "XLOEV",
               "FUNC_AREA", "XSPEA", "XSPEB", "XSPEP"]
SKB1_FIELDS = ["SAKNR", "WAERS", "FDLEV", "ZUAWA", "XKRES", "XGKON",
               "FIPOS", "FSTAG", "XOPVW", "HBKID", "HKTID", "XINTB",
               "MITKZ", "XNKON", "XMITK", "BEWGP", "MWSKZ", "BUSAB",
               "VZSKZ", "BEGRU", "ALTKT", "TOGRU", "STEXT"]
SKAT_FIELDS = ["SPRAS", "TXT20", "TXT50"]


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=100, throttle=0.3)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            return None
        # Field not available — try fewer fields
        if "FIELD_NOT_EXIST" in str(e) or "NOT_SUPPORTED" in str(e):
            return None
        raise


def read_gl_data(conn, system, gl):
    """Read SKA1 + SKB1 + SKAT for one GL."""
    result = {"system": system, "gl": gl}

    # SKA1
    ska1 = safe_read(conn, "SKA1", SKA1_FIELDS,
                     f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
    if ska1:
        result["ska1"] = {k: str(v).strip() if v else "" for k, v in ska1[0].items()}
    else:
        result["ska1"] = None

    # SKB1 — try full field list, fall back if needed
    skb1 = safe_read(conn, "SKB1", SKB1_FIELDS,
                     f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'")
    if skb1 is None:
        # Retry with core fields only
        core = ["SAKNR", "WAERS", "FDLEV", "ZUAWA", "XKRES", "XGKON",
                "FIPOS", "FSTAG", "XOPVW", "HBKID", "HKTID", "XINTB"]
        skb1 = safe_read(conn, "SKB1", core,
                         f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'")
    if skb1:
        result["skb1"] = {k: str(v).strip() if v else "" for k, v in skb1[0].items()}
    else:
        result["skb1"] = None

    # SKAT
    skat = safe_read(conn, "SKAT", ["SPRAS", "SAKNR", "TXT20", "TXT50"],
                     f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
    if skat:
        result["skat"] = {}
        for row in skat:
            lang = str(row.get("SPRAS", "")).strip()
            result["skat"][lang] = {
                "TXT20": str(row.get("TXT20", "")).strip(),
                "TXT50": str(row.get("TXT50", "")).strip(),
            }
    else:
        result["skat"] = None

    return result


def run():
    # Collect data
    all_data = {}  # {gl: {system: data}}
    conns = {}

    for system in SYSTEMS:
        print(f"  Connecting to {system}...")
        try:
            conns[system] = get_connection(system)
        except Exception as e:
            print(f"  ERROR {system}: {e}")

    for gl in GLS:
        all_data[gl] = {}
        for system in SYSTEMS:
            if system in conns:
                all_data[gl][system] = read_gl_data(conns[system], system, gl)

    for system in conns:
        conns[system].close()

    # Compare and print
    for gl in GLS:
        sig = gl.lstrip('0')
        gl_type = "bank (10*)" if sig.startswith('10') else "clearing (11*)"

        print(f"\n{'='*90}")
        print(f"  G/L {gl} — {gl_type}")
        print(f"{'='*90}")

        data = all_data[gl]

        # SKA1
        print(f"\n  --- SKA1 (Chart of Accounts) ---")
        ska1_all = {s: data[s]["ska1"] for s in SYSTEMS if s in data}

        if all(v is None for v in ska1_all.values()):
            print(f"  NOT FOUND in any system")
        else:
            # Collect all fields
            all_fields = set()
            for s, d in ska1_all.items():
                if d:
                    all_fields.update(d.keys())
            all_fields.discard("SAKNR")

            for field in sorted(all_fields):
                values = {}
                for s in SYSTEMS:
                    d = ska1_all.get(s)
                    if d is None:
                        values[s] = "(MISSING)"
                    else:
                        values[s] = d.get(field, "")

                unique = set(values.values())
                marker = "MATCH" if len(unique) == 1 else "DIFF"
                if marker == "MATCH":
                    val = list(unique)[0]
                    print(f"  {field:15s} [ALL]  {val or '(empty)'}")
                else:
                    print(f"  {field:15s} ** DIFF **")
                    for s in SYSTEMS:
                        print(f"    {s}: {values[s] or '(empty)'}")

        # SKB1
        print(f"\n  --- SKB1 (Company Code) ---")
        skb1_all = {s: data[s]["skb1"] for s in SYSTEMS if s in data}

        if all(v is None for v in skb1_all.values()):
            print(f"  NOT FOUND in any system")
        else:
            all_fields = set()
            for s, d in skb1_all.items():
                if d:
                    all_fields.update(d.keys())
            all_fields.discard("SAKNR")

            for field in sorted(all_fields):
                values = {}
                for s in SYSTEMS:
                    d = skb1_all.get(s)
                    if d is None:
                        values[s] = "(MISSING)"
                    else:
                        values[s] = d.get(field, "")

                unique = set(values.values())
                marker = "MATCH" if len(unique) == 1 else "DIFF"
                if marker == "MATCH":
                    val = list(unique)[0]
                    print(f"  {field:15s} [ALL]  {val or '(empty)'}")
                else:
                    print(f"  {field:15s} ** DIFF **")
                    for s in SYSTEMS:
                        print(f"    {s}: {values[s] or '(empty)'}")

        # SKAT
        print(f"\n  --- SKAT (Texts) ---")
        skat_all = {s: data[s]["skat"] for s in SYSTEMS if s in data}

        if all(v is None for v in skat_all.values()):
            print(f"  NOT FOUND in any system")
        else:
            all_langs = set()
            for s, d in skat_all.items():
                if d:
                    all_langs.update(d.keys())

            for lang in sorted(all_langs):
                for txt_field in ["TXT20", "TXT50"]:
                    values = {}
                    for s in SYSTEMS:
                        d = skat_all.get(s)
                        if d is None or lang not in d:
                            values[s] = "(MISSING)"
                        else:
                            values[s] = d[lang].get(txt_field, "")

                    unique = set(values.values())
                    marker = "MATCH" if len(unique) == 1 else "DIFF"
                    label = f"{lang}/{txt_field}"
                    if marker == "MATCH":
                        val = list(unique)[0]
                        print(f"  {label:15s} [ALL]  {val or '(empty)'}")
                    else:
                        print(f"  {label:15s} ** DIFF **")
                        for s in SYSTEMS:
                            print(f"    {s}: {values[s]}")

    # Final summary
    print(f"\n{'='*90}")
    print(f"  SUMMARY")
    print(f"{'='*90}")

    total_diffs = 0
    for gl in GLS:
        data = all_data[gl]
        gl_diffs = []

        # SKA1 diffs
        for field in set().union(*(d["ska1"].keys() for s, d in data.items() if d.get("ska1"))):
            if field == "SAKNR":
                continue
            vals = set()
            for s in SYSTEMS:
                d = data.get(s, {}).get("ska1")
                vals.add(d.get(field, "") if d else "(MISSING)")
            if len(vals) > 1:
                gl_diffs.append(f"SKA1.{field}")

        # SKB1 diffs
        for field in set().union(*(d["skb1"].keys() for s, d in data.items() if d.get("skb1"))):
            if field == "SAKNR":
                continue
            vals = set()
            for s in SYSTEMS:
                d = data.get(s, {}).get("skb1")
                vals.add(d.get(field, "") if d else "(MISSING)")
            if len(vals) > 1:
                gl_diffs.append(f"SKB1.{field}")

        # SKAT diffs
        all_langs = set()
        for s in SYSTEMS:
            d = data.get(s, {}).get("skat")
            if d:
                all_langs.update(d.keys())
        for lang in all_langs:
            for tf in ["TXT20", "TXT50"]:
                vals = set()
                for s in SYSTEMS:
                    d = data.get(s, {}).get("skat")
                    if d and lang in d:
                        vals.add(d[lang].get(tf, ""))
                    else:
                        vals.add("(MISSING)")
                if len(vals) > 1:
                    gl_diffs.append(f"SKAT.{lang}.{tf}")

        if gl_diffs:
            total_diffs += len(gl_diffs)
            print(f"\n  {gl} ({len(gl_diffs)} diffs): {', '.join(gl_diffs)}")
        else:
            print(f"\n  {gl}: IDENTICAL across D01/V01/P01")

    print(f"\n  Total field-level differences: {total_diffs}")


if __name__ == "__main__":
    run()

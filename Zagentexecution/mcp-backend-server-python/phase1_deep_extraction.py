"""phase1_deep_extraction.py — extract everything else accessible without human input.

Wave 1 — SAP std country dispatcher classes (the actual address-to-REF mapping):
  - CL_IDFI_CGI_CALL05_FR (most relevant - French SEPA addresses)
  - CL_IDFI_CGI_CALL05_DE (Germany)
  - CL_IDFI_CGI_CALL05_IT (Italy)
  - CL_IDFI_CGI_CALL05_GB (Great Britain)
  - CL_IDFI_CGI_CALL05_GENERIC (fallback)
  - CL_IDFI_CGI_CALL05_FACTORY (dispatch)
  - IF_IDFI_CGI_CALL05 interface

Wave 2 — UNESCO Z-exits (1 node each, mentioned in MP_EXIT_FUNC counts):
  - Z_DMEE_EXIT_TAX_NUMBER
  - ZDMEE_EXIT_SEPA_21

Wave 3 — Live data probes:
  - T012 (house bank UNESCO co codes)
  - T012K (house bank account)
  - BNKA sample for CGI CdtrAgt banks (NG/KR/GB)
  - LFB1 alt-payee for CITI Worldlink vendors
  - OBPM4 events all (00..08) for 4 trees

Output: extracted_code/FI/DMEE_full_inventory/ + knowledge/domains/Payment/phase0/dmee_full/
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

REPO = HERE.parent.parent
CODE_OUT = REPO / "extracted_code" / "FI" / "DMEE_full_inventory"
DATA_OUT = REPO / "knowledge" / "domains" / "Payment" / "phase0" / "dmee_full"
CODE_OUT.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)


def read_program(conn, name):
    try:
        r = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=name, WITH_LOWERCASE="X")
        lines = r.get("SOURCE_EXTENDED", []) or r.get("SOURCE", [])
        return "\n".join(l.get("LINE", "") if isinstance(l, dict) else l for l in lines)
    except Exception as e:
        return None


def extract_class_includes(conn, classname, suffixes=None):
    if suffixes is None:
        suffixes = ["CCDEF", "CCIMP", "CCMAC", "CP", "CO", "CU", "CI",
                    "CM001", "CM002", "CM003", "CM004", "CM005", "CM006", "CM007",
                    "CM008", "CM009", "CM010"]
    padded = classname.ljust(30, "=")
    extracted = {}
    for suffix in suffixes:
        inc_name = f"{padded}{suffix}"
        src = read_program(conn, inc_name)
        if src and src.strip() and not src.startswith("[ERR"):
            out = CODE_OUT / f"{classname}_{suffix}.abap"
            out.write_text(src, encoding="utf-8")
            non_empty = sum(1 for l in src.split("\n") if l.strip() and not l.strip().startswith("*"))
            extracted[suffix] = (len(src), non_empty)
            print(f"    {suffix}: {len(src)} chars, {non_empty} non-comment lines")
    return extracted


def wave1_sap_classes(conn):
    print("\n=== WAVE 1: SAP std country dispatcher classes ===")
    targets = [
        "CL_IDFI_CGI_CALL05_FR",
        "CL_IDFI_CGI_CALL05_DE",
        "CL_IDFI_CGI_CALL05_IT",
        "CL_IDFI_CGI_CALL05_GB",
        "CL_IDFI_CGI_CALL05_GENERIC",
        "CL_IDFI_CGI_CALL05_FACTORY",
    ]
    for cls in targets:
        print(f"\n  -- {cls} --")
        extract_class_includes(conn, cls)


def wave1b_interface(conn):
    print("\n=== WAVE 1b: IF_IDFI_CGI_CALL05 interface ===")
    # Interface includes are different — typically just CU (declaration)
    # try as program
    for nm in ["IF_IDFI_CGI_CALL05", "IF_IDFI_CGI_DMEE_COUNTRIES"]:
        print(f"\n  -- {nm} --")
        for suffix in ["CU", "CCDEF", "CO"]:
            padded = nm.ljust(30, "=")
            inc = f"{padded}{suffix}"
            src = read_program(conn, inc)
            if src and not src.startswith("[ERR"):
                out = CODE_OUT / f"{nm}_{suffix}.abap"
                out.write_text(src, encoding="utf-8")
                non_empty = sum(1 for l in src.split("\n") if l.strip() and not l.strip().startswith("*"))
                print(f"    {suffix}: {len(src)} chars, {non_empty} non-comment lines")


def wave2_z_exits(conn):
    print("\n=== WAVE 2: UNESCO Z-exits ===")
    targets = ["Z_DMEE_EXIT_TAX_NUMBER", "ZDMEE_EXIT_SEPA_21"]
    for fm in targets:
        print(f"\n  -- {fm} (FM) --")
        try:
            r = conn.call("RPY_FUNCTIONMODULE_READ", FUNCTIONNAME=fm)
            lines = r.get("SOURCE", [])
            src = "\n".join(l.get("LINE", "") if isinstance(l, dict) else l for l in lines)
            if src:
                out = CODE_OUT / f"{fm}.abap"
                out.write_text(src, encoding="utf-8")
                non_empty = sum(1 for l in src.split("\n") if l.strip() and not l.strip().startswith("*"))
                print(f"    saved {out.name} ({len(src)} chars, {non_empty} non-comment lines)")
        except Exception as e:
            # Try as program (some Z-exits are reports)
            src = read_program(conn, fm)
            if src and not src.startswith("[ERR"):
                out = CODE_OUT / f"{fm}_program.abap"
                out.write_text(src, encoding="utf-8")
                print(f"    saved as program ({len(src)} chars)")
            else:
                print(f"    not found: {e}")


def wave3a_house_bank(conn):
    print("\n=== WAVE 3a: T012 + T012K house bank for UNESCO co codes ===")
    co_codes = ["UNES", "IIEP", "UIL", "UBO", "UIS", "ICTP", "MGIE"]
    where_co = " OR ".join(f"BUKRS = '{c}'" for c in co_codes)

    for tbl, fields in [
        ("T012", ["BUKRS", "HBKID", "BANKS", "BANKL", "BNKA1", "BNKA2", "BNKA3", "BNKA4"]),
        ("T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "BKONT", "WAERS"]),
    ]:
        print(f"\n  -- {tbl} --")
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE=tbl, DELIMITER="|",
                          ROWCOUNT=200,
                          OPTIONS=[{"TEXT": where_co}],
                          FIELDS=[{"FIELDNAME": f} for f in fields])
            data = r.get("DATA", [])
            print(f"    {len(data)} rows")
            with open(DATA_OUT / f"{tbl.lower()}_unesco.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(fields)
                for d in data:
                    vals = [v.strip() for v in d.get("WA", "").split("|")]
                    w.writerow(vals)
            print(f"    saved {tbl.lower()}_unesco.csv")
        except Exception as e:
            print(f"    err: {e}")


def wave3b_bnka_sample(conn):
    print("\n=== WAVE 3b: BNKA sample for CGI banks (NG/KR/GB - countries with unstructured CdtrAgt today) ===")
    for cty in ["NG", "KR", "GB", "FR", "BR", "MG", "TN"]:
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE="BNKA", DELIMITER="|", ROWCOUNT=10,
                          OPTIONS=[{"TEXT": f"BANKS = '{cty}'"}],
                          FIELDS=[{"FIELDNAME": f} for f in
                                  ["BANKS", "BANKL", "BANKA", "STRAS", "ORT01", "PSTLZ", "BNKLZ"]])
            data = r.get("DATA", [])
            if data:
                print(f"\n  {cty}: {len(data)} sample banks")
                for d in data[:3]:
                    vals = [v.strip() for v in d.get("WA", "").split("|")]
                    print(f"    {dict(zip(['BANKS','BANKL','BANKA','STRAS','ORT01','PSTLZ','BNKLZ'], vals))}")
        except Exception as e:
            print(f"  {cty} err: {e}")


def wave3c_obpm4_full(conn):
    print("\n=== WAVE 3c: OBPM4 events 00..08 for our 4 trees ===")
    trees = ["/SEPA_CT_UNES", "/CITI/XML/UNESCO/DC_V3_01", "/CGI_XML_CT_UNESCO", "/CGI_XML_CT_UNESCO_1"]
    where = " OR ".join(f"FORMI = '{t}'" for t in trees)
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFPM042FB", DELIMITER="|",
                      OPTIONS=[{"TEXT": where}],
                      FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
        rows = []
        for d in r.get("DATA", []):
            vals = [v.strip() for v in d.get("WA", "").split("|")]
            rec = dict(zip(["FORMI", "EVENT", "FNAME"], vals))
            rows.append(rec)
            print(f"    {rec}")
        with open(DATA_OUT / "obpm4_events_full.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["FORMI", "EVENT", "FNAME"])
            for rec in rows:
                w.writerow([rec["FORMI"], rec["EVENT"], rec["FNAME"]])
    except Exception as e:
        print(f"  err: {e}")


def wave3d_lfb1_altpayee(conn):
    print("\n=== WAVE 3d: LFB1 alternative payee sample (PAYEE field) ===")
    for cocd in ["UNES", "UIS", "UBO"]:
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE="LFB1", DELIMITER="|", ROWCOUNT=20,
                          OPTIONS=[{"TEXT": f"BUKRS = '{cocd}' AND LNRZB <> ''"}],
                          FIELDS=[{"FIELDNAME": "BUKRS"}, {"FIELDNAME": "LIFNR"}, {"FIELDNAME": "LNRZB"}, {"FIELDNAME": "ZWELS"}])
            data = r.get("DATA", [])
            if data:
                print(f"\n  {cocd}: {len(data)} vendors with LNRZB (alt-payee) set")
                for d in data[:5]:
                    vals = [v.strip() for v in d.get("WA", "").split("|")]
                    print(f"    {dict(zip(['BUKRS','LIFNR','LNRZB','ZWELS'], vals))}")
        except Exception as e:
            print(f"  {cocd} err: {e}")


def main():
    conn = get_connection("P01")
    try:
        wave1_sap_classes(conn)
        wave1b_interface(conn)
        wave2_z_exits(conn)
        wave3a_house_bank(conn)
        wave3b_bnka_sample(conn)
        wave3c_obpm4_full(conn)
        wave3d_lfb1_altpayee(conn)
    finally:
        conn.close()
    print("\n=== Done ===")


if __name__ == "__main__":
    main()

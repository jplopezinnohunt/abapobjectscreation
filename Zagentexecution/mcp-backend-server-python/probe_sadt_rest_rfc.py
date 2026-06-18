"""
probe_sadt_rest_rfc.py — Verify SADT_REST_RFC_ENDPOINT exists in D01
and test downloading ABAP source code via RFC (no HTTP/CSRF needed).

Based on openadt/AdtRestRfcClient.java pattern.
"""
import os, sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    from pyrfc import Connection, ABAPApplicationError, RFCError
except ImportError:
    print("ERROR: pyrfc not installed")
    sys.exit(1)

def get_conn():
    return Connection(
        ashost=os.getenv("SAP_ASHOST"),
        sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"),
        user=os.getenv("SAP_USER"),
        passwd=os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD"),
        lang="EN"
    )

def check_fm_exists(conn, fm_name):
    """Check if an FM exists via TFDIR."""
    try:
        result = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="TFDIR",
            FIELDS=[{"FIELDNAME": "FUNCNAME"}],
            OPTIONS=[{"TEXT": f"FUNCNAME = '{fm_name}'"}],
            ROWCOUNT=1
        )
        return len(result["DATA"]) > 0
    except Exception as e:
        return False

def call_adt_via_rfc(conn, method, uri, headers=None, body=b""):
    """
    Call SAP ADT REST endpoint via SADT_REST_RFC_ENDPOINT.
    No CSRF tokens, no cookie jars, no urllib — pure RFC.
    """
    header_fields = []
    if headers:
        for name, value in headers.items():
            header_fields.append({"NAME": name, "VALUE": value})

    result = conn.call("SADT_REST_RFC_ENDPOINT",
        REQUEST={
            "REQUEST_LINE": {
                "METHOD": method,
                "URI": uri,
                "VERSION": "HTTP/1.1"
            },
            "HEADER_FIELDS": header_fields,
            "MESSAGE_BODY": body
        }
    )
    response = result["RESPONSE"]
    status_code = int(response["STATUS_LINE"]["STATUS_CODE"])
    reason = response["STATUS_LINE"]["REASON_PHRASE"]
    body_bytes = response["MESSAGE_BODY"]

    resp_headers = {}
    for row in response.get("HEADER_FIELDS", []):
        resp_headers[row["NAME"]] = row["VALUE"]

    return status_code, reason, resp_headers, body_bytes

def main():
    print("=" * 60)
    print("SADT_REST_RFC_ENDPOINT Probe — D01")
    print("=" * 60)

    print("\n[1] Connecting to D01...")
    try:
        conn = get_conn()
        print(f"    Connected: {os.getenv('SAP_ASHOST')}:{os.getenv('SAP_SYSNR')}")
    except Exception as e:
        print(f"    ERROR: {e}")
        sys.exit(1)

    print("\n[2] Checking if SADT_REST_RFC_ENDPOINT exists in TFDIR...")
    exists = check_fm_exists(conn, "SADT_REST_RFC_ENDPOINT")
    print(f"    Exists: {exists}")

    if not exists:
        print("\n    Searching similar ADT RFCs...")
        try:
            result = conn.call("RFC_READ_TABLE",
                QUERY_TABLE="TFDIR",
                FIELDS=[{"FIELDNAME": "FUNCNAME"}],
                OPTIONS=[{"TEXT": "FUNCNAME LIKE 'SADT%'"}],
                ROWCOUNT=20
            )
            for row in result["DATA"]:
                print(f"    Found: {row['WA'].strip()}")
        except Exception as e:
            print(f"    Search error: {e}")
        conn.close()
        return

    print("\n[3] Calling ADT discovery endpoint via RFC...")
    try:
        status, reason, headers, body = call_adt_via_rfc(
            conn, "GET", "/sap/bc/adt/discovery",
            headers={"Accept": "application/xml"}
        )
        print(f"    Status: {status} {reason}")
        print(f"    Body length: {len(body)} bytes")
        if body:
            text = body.decode("utf-8", errors="replace")
            print(f"    Body preview: {text[:300]}")
    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n[4] Downloading ABAP class source via RFC (ZCL_FI_ACCOUNT_SUBST)...")
    try:
        uri = "/sap/bc/adt/oo/classes/ZCL_FI_ACCOUNT_SUBST/source/main"
        status, reason, headers, body = call_adt_via_rfc(
            conn, "GET", uri,
            headers={"Accept": "text/plain"}
        )
        print(f"    Status: {status} {reason}")
        if body:
            src = body.decode("utf-8", errors="replace")
            print(f"    Source length: {len(src)} chars")
            print(f"    First 400 chars:")
            print("    " + src[:400].replace("\n", "\n    "))
        else:
            print("    Empty body")
    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n[5] Downloading a known program source (SAPF100) via RFC...")
    try:
        uri = "/sap/bc/adt/programs/programs/SAPF100/source/main"
        status, reason, headers, body = call_adt_via_rfc(
            conn, "GET", uri,
            headers={"Accept": "text/plain"}
        )
        print(f"    Status: {status} {reason}")
        if body:
            src = body.decode("utf-8", errors="replace")
            print(f"    Source length: {len(src)} chars")
            print(f"    First 200 chars: {src[:200]}")
        else:
            print("    Empty body")
    except Exception as e:
        print(f"    ERROR: {e}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()

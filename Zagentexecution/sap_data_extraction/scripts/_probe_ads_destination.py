"""
_probe_ads_destination.py — READ-ONLY probe of the Adobe Document Services (ADS) channel in P01.

Born from INC-000016471 (2026-08-26): "Create PDF Agreement" in the Internship Agreement app
fails with `500 Internal Server Error / ADS: SOAP Runtime Exception: CSoapExceptionTransport
:(100101)`. That string is emitted by the ABAP-side ADS client when the HTTP call to Adobe
Document Services does not come back — i.e. it is a TRANSPORT failure on a destination, not a
form-logic failure.

Reads only. RFC_READ_TABLE over SNC/SSO against P01. No writes anywhere.

Usage:  python Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "mcp-backend-server-python"))
if MCP not in sys.path:
    sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard  # noqa: E402


def main():
    g = ConnectionGuard("P01")
    g.connect()

    def rt(tab, fields, where=None, rc=200):
        kw = dict(QUERY_TABLE=tab, ROWCOUNT=rc, DELIMITER="|",
                  FIELDS=[{"FIELDNAME": f} for f in fields])
        if where:
            kw["OPTIONS"] = [{"TEXT": w} for w in where]
        try:
            r = g.call("RFC_READ_TABLE", **kw)
            return [d["WA"] for d in r.get("DATA", [])]
        except Exception as e:
            return ["!!ERR %s: %s" % (type(e).__name__, e)]

    print("=== RFCDES: HTTP destinations (type G = HTTP to ext server, H = HTTP to ABAP) ===")
    for row in rt("RFCDES", ["RFCDEST", "RFCTYPE"], ["RFCTYPE = 'G' OR RFCTYPE = 'H'"]):
        print(row)

    print()
    print("=== RFCDES: any destination whose name carries ADS ===")
    for row in rt("RFCDES", ["RFCDEST", "RFCTYPE"], ["RFCDEST LIKE '%ADS%'"], rc=50):
        print(row)

    print()
    print("=== RFCDOC: description text of the ADS destinations ===")
    for row in rt("RFCDOC", ["RFCDEST", "RFCDOC1"], ["RFCDEST LIKE '%ADS%'"], rc=20):
        print(row)

    g.close()
    print("DONE")


if __name__ == "__main__":
    main()

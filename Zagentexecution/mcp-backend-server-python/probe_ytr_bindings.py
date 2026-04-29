"""Dig into YTR0/YTR1/YTR2/YTR2_HR TCODE definitions (CINFO, TSTCA, TSTCC)."""
from __future__ import annotations
import os, sys, io
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
from pyrfc import Connection

c = Connection(
    ashost=os.getenv("SAP_ASHOST"),
    sysnr=os.getenv("SAP_SYSNR"),
    client=os.getenv("SAP_CLIENT"),
    user=os.getenv("SAP_USER"),
    lang="EN",
    snc_mode=os.getenv("SAP_SNC_MODE","1"),
    snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"),
    snc_qop=os.getenv("SAP_SNC_QOP","9"),
)

for tc in ("YTR0","YTR1","YTR2","YTR2_HR","YTR3"):
    print(f"\n=== TCODE {tc} ===")
    # Get all TSTC columns
    r = c.call("RFC_READ_TABLE",
        QUERY_TABLE="TSTC",
        DELIMITER="|",
        OPTIONS=[{"TEXT": f"TCODE = '{tc}'"}],
        FIELDS=[],  # all fields
    )
    flds = [f["FIELDNAME"] for f in r.get("FIELDS",[])]
    print("FIELDS:", flds)
    for row in r.get("DATA",[]):
        wa = row.get("WA","")
        parts = wa.split("|")
        for f,v in zip(flds, parts):
            v = v.strip()
            if v:
                print(f"  {f} = {v}")
    # Also read TSTCT texts
    r2 = c.call("RFC_READ_TABLE",
        QUERY_TABLE="TSTCT",
        DELIMITER="|",
        OPTIONS=[{"TEXT": f"TCODE = '{tc}' AND SPRSL = 'E'"}],
        FIELDS=[{"FIELDNAME":"TTEXT"}],
    )
    for row in r2.get("DATA",[]):
        print(f"  TITLE = {row.get('WA','')}")

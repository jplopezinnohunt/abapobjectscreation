"""Probe TSTC for TCODE bindings for the bank-recon program family."""
from __future__ import annotations
import os, sys, io, json
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, errors="replace", encoding="utf-8")
from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
from pyrfc import Connection

PROGS = [
    "YTBAE001","YTBAE001_HR","YTBAE002",
    "YTBAI001","YTBAM001","YTBAM002","YTBAM002_HR","YTBAM002_HR_UBO",
    "YTBAM003","YTBAM003_HR","YTBAM004","YTBAM004_HR",
    "YFI_BANK_RECONCILIATION","YFI_BANK_RECONCILIATION_DATA","YFI_BANK_RECONCILIATION_SEL",
]

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
print("Connected P01 via SNC")

# Any TCODE starting with YTR, YFI_BANK, YBANK, YBAE, YBAM, YBAI
for prefix in ["YTR","YFI_BANK","YBAE","YBAM","YBAI","YTB"]:
    print(f"\n=== TCODE LIKE {prefix}* ===")
    try:
        r = c.call("RFC_READ_TABLE",
            QUERY_TABLE="TSTC",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"TCODE LIKE '{prefix}%'"}],
            FIELDS=[{"FIELDNAME":"TCODE"},{"FIELDNAME":"PGMNA"}],
        )
        for row in r.get("DATA",[]) or []:
            print("  ",row.get("WA",""))
    except Exception as e:
        print("  [ERR]",str(e)[:200])

# Also confirm bindings for each program
for p in PROGS:
    try:
        r = c.call("RFC_READ_TABLE",
            QUERY_TABLE="TSTC",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"PGMNA = '{p}'"}],
            FIELDS=[{"FIELDNAME":"TCODE"},{"FIELDNAME":"PGMNA"}],
        )
        rows = r.get("DATA",[]) or []
        if rows:
            for row in rows:
                print(f"[BINDING] {p} -> TCODE: {row.get('WA','')}")
    except Exception as e:
        pass

"""Quick connectivity test before full extraction."""
import os
import sys
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(key, default=None):
    return os.getenv(f"SAP_D01_{key}") or os.getenv(f"SAP_{key}") or default

params = {
    "ashost": env("ASHOST"),
    "sysnr":  env("SYSNR"),
    "client": env("CLIENT"),
    "user":   env("USER"),
    "passwd": env("PASSWD") or env("PASSWORD"),
    "lang":   "EN",
}

print("Connecting with params:", {k: v for k, v in params.items() if k != "passwd"})

try:
    conn = Connection(**params)
    print("Connected OK!")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# List files in ZHROFFBOARDING
for app in ["ZHROFFBOARDING", "YHR_OFFBOARDEMP"]:
    try:
        r = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="O2PAGDIR",
            OPTIONS=[{"TEXT": f"APPLNAME = '{app}'"}],
            FIELDS=[{"FIELDNAME": "PAGENAME"}],
            ROWCOUNT=5,
            DELIMITER="|",
        )
        rows = r.get("DATA", [])
        print(f"\n{app}: {len(rows)} rows (sample):")
        for row in rows:
            print(f"  {row['WA'].strip()}")
    except Exception as e:
        print(f"\n{app}: ERROR — {e}")

conn.close()
print("\nTest complete.")

import sys, os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv()
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"]="1"; p["snc_partnername"]=os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"]=os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

conn = get_conn()
cls = "ZCL_Z_CRP_SRV_DPC_EXT"
method = "CRPCERTIFICATESET_GET_ENTITY"

print(f"Finding CM include for {cls}->{method}")

# We can find this by reading the 'Methods' virtual include if it exists, 
# or by searching for entries in SEOMETAREL or similar.
# Since SEOIMPLEM was not available, let's try reading the 'include methods.' content from the class pool's perspective.
# Actually, let's try reading and searching the CP include more thoroughly.

# Another way: RFC_READ_TABLE on WDY_WB_VC_USE or similar? No.
# Let's try to list ALL reports starting with ZCL_Z_CRP_SRV_DPC_EXT=========

r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TRDIR", DELIMITER="|",
              OPTIONS=[{"TEXT": f"NAME LIKE '{cls}==============%'"}],
              FIELDS=[{"FIELDNAME":"NAME"}])

for row in r.get("DATA", []):
    print(row['WA'])

conn.close()

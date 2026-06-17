import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection
try:
    c = get_connection("D01")
    info=c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
    print("D01 UP:", info.get("RFCSYSID"), info.get("RFCHOST"))
except Exception as e:
    print("D01 DOWN:", str(e)[:80]); sys.exit()
# try reading a CITIPMW FM source
for fm in ("/CITIPMW/V3_GET_CDTR_BLDG","/CITIPMW/V3_CGI_CRED_STREET"):
    try:
        r=c.call("RPY_FUNCTIONMODULE_READ", FUNCNAME=fm)
        src=r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
        print(f"\n=== {fm} ({len(src)} líneas) ===")
        for line in src[:25]:
            t=line.get("LINE","") if isinstance(line,dict) else str(line)
            if t.strip(): print("  ",t.rstrip())
    except Exception as e:
        print(f"  {fm}: RPY ERR {str(e)[:60]}")
c.close()

"""
Generic BSP Extractor
=====================
Extracts ALL source files of any SAP BSP application to disk.

Usage:
    python extract_bsp_generic.py <APP_NAME>
    python extract_bsp_generic.py ZHROFFBOARDING
    python extract_bsp_generic.py YHR_OFFBOARDEMP
    python extract_bsp_generic.py <APP_NAME> --system P01   (target system)
    python extract_bsp_generic.py <APP_NAME> --out ./my_output
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# --------------------------------------------------------------------------- #
#  Connection (mirrors query_table.py / sap_utils.py)
# --------------------------------------------------------------------------- #

def get_conn(system_id="D01"):
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    prefix = f"SAP_{system_id}_"

    def env(key, default=None):
        return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

    params = {
        "ashost": env("ASHOST"),
        "sysnr":  env("SYSNR"),
        "client": env("CLIENT"),
        "user":   env("USER"),
        "passwd": env("PASSWD") or env("PASSWORD"),
        "lang":   env("LANG", "EN"),
    }
    if env("SNC_MODE") == "1":
        params["snc_mode"]        = "1"
        params["snc_partnername"] = env("SNC_PARTNERNAME")
        params["snc_qop"]         = env("SNC_QOP", "9")

    return Connection(**params)

# --------------------------------------------------------------------------- #
#  Core extraction helpers
# --------------------------------------------------------------------------- #

def list_files(conn, app_name):
    """Return list of {name, mime} dicts from O2PAGDIR."""
    result = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="O2PAGDIR",
        OPTIONS=[{"TEXT": f"APPLNAME = '{app_name}'"}],
        FIELDS=[{"FIELDNAME": "PAGENAME"}, {"FIELDNAME": "MIMETYPE"}],
        ROWCOUNT=5000,
        DELIMITER="|",
    )
    files = []
    for row in result.get("DATA", []):
        parts = row["WA"].split("|")
        name = parts[0].strip()
        mime = parts[1].strip() if len(parts) > 1 else ""
        if name and not name.startswith("UI5"):   # skip binary fingerprint blobs
            files.append({"name": name, "mime": mime})
    return files


def fetch_content(conn, app_name, page_name):
    """Fetch raw text content of a BSP page from O2PAGCON."""
    result = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="O2PAGCON",
        OPTIONS=[{"TEXT": f"APPLNAME = '{app_name}' AND PAGENAME = '{page_name}'"}],
        FIELDS=[{"FIELDNAME": "PAGELINE"}],
        ROWCOUNT=999999,
        DELIMITER="\x01",   # unlikely to appear in source code
    )
    lines = []
    for row in result.get("DATA", []):
        line = row["WA"]
        if line.endswith("\x01"):
            line = line[:-1]
        lines.append(line)
    return "\n".join(lines)


def save(out_dir: Path, page_name: str, content: str) -> Path:
    safe = page_name.replace("/", os.sep).lstrip(os.sep)
    target = out_dir / safe
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", errors="replace")
    return target

# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #

def extract(app_name: str, system_id: str, out_base: Path):
    print(f"\n{'='*60}")
    print(f"  BSP EXTRACTION: {app_name}  (system: {system_id})")
    print(f"{'='*60}\n")

    conn = get_conn(system_id)
    print(f"Connected to SAP {system_id}.\n")

    # 1. List files
    files = list_files(conn, app_name)
    if not files:
        print(f"ERROR: No files found in O2PAGDIR for '{app_name}'.")
        conn.close()
        return

    print(f"Files to extract ({len(files)}):")
    for f in files:
        print(f"  {f['name']}")

    out_dir = out_base / f"BSP_{app_name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {out_dir}\n")

    # 2. Extract each file
    ok = failed = empty = 0
    for i, f in enumerate(files, 1):
        name = f["name"]
        print(f"  [{i:3d}/{len(files)}] {name} ... ", end="", flush=True)
        try:
            content = fetch_content(conn, app_name, name)
            if content.strip():
                saved = save(out_dir, name, content)
                print(f"OK  ({len(content):,} chars)")
                ok += 1
            else:
                save(out_dir, name, f"/* empty — {name} */")
                print(f"EMPTY")
                empty += 1
        except RFCError as e:
            print(f"RFC ERROR: {e}")
            save(out_dir, name + ".ERROR", str(e))
            failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            save(out_dir, name + ".ERROR", str(e))
            failed += 1

    conn.close()

    print(f"\n{'='*60}")
    print(f"  DONE: {app_name}")
    print(f"  Output : {out_dir}")
    print(f"  OK     : {ok}")
    print(f"  Empty  : {empty}")
    print(f"  Failed : {failed}")
    print(f"  Total  : {len(files)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generic SAP BSP Extractor")
    parser.add_argument("app", help="BSP application name (e.g. ZHROFFBOARDING)")
    parser.add_argument("--system", default="D01", help="SAP system ID (default: D01)")
    parser.add_argument("--out", default=None, help="Output base directory")
    args = parser.parse_args()

    base = Path(args.out) if args.out else Path(__file__).parent / "extracted_code"
    extract(args.app, args.system, base)

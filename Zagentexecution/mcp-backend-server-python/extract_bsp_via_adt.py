"""
extract_bsp_via_adt.py — SAP BSP / UI5 Extractor via ADT File Store
====================================================================

CORRECT APPROACH (discovered 2026-03-12):
  BSP/UI5 apps in SAP ADT are exposed via the FILE STORE endpoint:

  LISTING:  GET /sap/bc/adt/filestore/ui5-bsp/objects/{APP}/content
  CONTENT:  GET /sap/bc/adt/filestore/ui5-bsp/objects/{APP}%2f{PATH}/content

  The listing returns an Atom XML feed with:
    <atom:category term="file"/>   → download via /content suffix
    <atom:category term="folder"/> → recurse via /content suffix

CONFIRMED WORKING:
  URL:    http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80
  Client: 350
  Auth:   HTTP Basic (jp_lopez / password from .env SAP_PASSWORD)

Usage:
    python extract_bsp_via_adt.py ZHROFFBOARDING
    python extract_bsp_via_adt.py YHR_OFFBOARDEMP
    python extract_bsp_via_adt.py ZHROFFBOARDING --system P01
    python extract_bsp_via_adt.py ZHROFFBOARDING --out ./my_folder
"""
import os
import sys
import argparse
import urllib.request
import urllib.parse
import urllib.error
import base64
import re
from pathlib import Path


BASE_URL = "http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80"


def main():
    parser = argparse.ArgumentParser(description="SAP BSP/UI5 Extractor via ADT File Store")
    parser.add_argument("app",      help="BSP application name (e.g. ZHROFFBOARDING)")
    parser.add_argument("--system", default="D01", help="SAP system ID (default: D01)")
    parser.add_argument("--out",    default=None,  help="Output base directory")
    args = parser.parse_args()

    # ── Load config (inside main to avoid Windows heap crash) ───────────────
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    sys_prefix = f"SAP_{args.system}_"
    def e(k, d=None):
        return os.getenv(sys_prefix + k) or os.getenv("SAP_" + k) or d

    host    = e("HOST") or e("ASHOST")
    port    = e("ADT_PORT", "80")
    https   = e("ADT_HTTPS", "false").lower() not in ("false", "0", "no")
    client  = e("CLIENT", "350")
    user    = e("USER")
    passwd  = e("PASSWD") or e("PASSWORD")
    scheme  = "https" if https else "http"
    base    = f"{scheme}://{host}:{port}"
    auth    = "Basic " + base64.b64encode(f"{user}:{passwd}".encode()).decode()

    app_name = args.app
    out_base = Path(args.out) if args.out else Path(__file__).parent / "extracted_code"
    out_dir  = out_base / f"BSP_{app_name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  BSP EXTRACTION (ADT File Store): {app_name}  [{args.system}]")
    print(f"  ADT: {base}  Client: {client}")
    print(f"  Out: {out_dir}")
    print(f"{'='*65}\n")

    # ── State ────────────────────────────────────────────────────────────────
    stats = {"ok": 0, "empty": 0, "failed": 0}

    # ── HTTP helper ──────────────────────────────────────────────────────────
    def adt_get(path_with_qs):
        """GET {base}{path_with_qs}. Returns (status, text). Path must include ?sap-client=N."""
        url = base + path_with_qs
        req = urllib.request.Request(url, headers={
            "Authorization": auth,
            "Accept": "application/xml, application/atom+xml, */*",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as ex:
            return ex.code, ex.read().decode("utf-8", errors="replace")
        except Exception as ex:
            return 0, str(ex)

    # ── Atom XML parser — extract entries ────────────────────────────────────
    def parse_entries(xml):
        """
        Returns list of dicts: {title, category, content_src}
        - title: e.g. "ZHROFFBOARDING/manifest.json" or "ZHROFFBOARDING/controller"
        - category: "file" or "folder"
        - content_src: relative src attribute from <atom:content src="..."/>
        """
        entries = []
        for block in re.findall(r'<atom:entry[^>]*>.*?</atom:entry>', xml, re.DOTALL):
            title_m    = re.search(r'<atom:title[^>]*>([^<]+)</atom:title>', block)
            cat_m      = re.search(r'<atom:category[^>]*term="([^"]+)"', block)
            content_m  = re.search(r'<atom:content[^>]*src="([^"]+)"', block)
            if title_m and cat_m and content_m:
                entries.append({
                    "title":       title_m.group(1).strip(),
                    "category":    cat_m.group(1).strip(),
                    "content_src": content_m.group(1).strip(),
                })
        return entries

    # ── Recursive traversal & download ───────────────────────────────────────
    def traverse(content_src, depth=0):
        """
        content_src: relative path like "./ZHROFFBOARDING%2fcontroller/content"
        We convert to absolute: /sap/bc/adt/filestore/ui5-bsp/objects/{content_src}
        """
        abs_path = f"/sap/bc/adt/filestore/ui5-bsp/objects/{content_src}?sap-client={client}"
        status, body = adt_get(abs_path)

        if status != 200:
            print(f"  {'  '*depth}[FEED ERR] HTTP {status}: {content_src}")
            return

        entries = parse_entries(body)

        for entry in entries:
            title    = entry["title"]   # e.g. "ZHROFFBOARDING/view/Main.view.xml"
            category = entry["category"]
            src      = entry["content_src"]   # e.g. "./ZHROFFBOARDING%2fview%2fMain.view.xml/content"

            # Strip app prefix from title to get relative path
            rel_path = title
            if "/" in title:
                rel_path = title.split("/", 1)[1]   # "view/Main.view.xml"

            indent = "  " * depth

            if category == "file":
                print(f"  {indent}FILE  {rel_path} ... ", end="", flush=True)
                # Download file content
                file_path = f"/sap/bc/adt/filestore/ui5-bsp/objects/{src}?sap-client={client}"
                fstatus, content = adt_get(file_path)
                target = out_dir / rel_path.replace("/", os.sep)
                target.parent.mkdir(parents=True, exist_ok=True)
                if fstatus == 200 and content.strip():
                    target.write_text(content, encoding="utf-8", errors="replace")
                    print(f"OK ({len(content):,} chars)")
                    stats["ok"] += 1
                elif fstatus == 200:
                    target.write_text(f"/* EMPTY */", encoding="utf-8")
                    print(f"EMPTY")
                    stats["empty"] += 1
                else:
                    Path(str(target) + ".ERROR").write_text(
                        f"HTTP {fstatus}\n{file_path}\n\n{content}", encoding="utf-8"
                    )
                    print(f"HTTP {fstatus}")
                    stats["failed"] += 1

            elif category == "folder":
                print(f"  {indent}FOLDER {rel_path}/")
                traverse(src.lstrip("./"), depth + 1)

    # ── Start from app root ──────────────────────────────────────────────────
    print(f"Traversing file store for '{app_name}'...\n")
    root_src = f"{app_name}/content"
    traverse(root_src)

    print(f"\n{'='*65}")
    print(f"  DONE   : {app_name}")
    print(f"  Output : {out_dir}")
    print(f"  OK     : {stats['ok']}  |  Empty: {stats['empty']}  |  Failed: {stats['failed']}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()

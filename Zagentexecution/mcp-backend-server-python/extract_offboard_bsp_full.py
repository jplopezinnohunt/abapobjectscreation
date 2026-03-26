"""
Full BSP Extraction Script for HR Offboarding App
==================================================
1. Discovers the BSP application name from TADIR (WAPA objects related to offboarding)
2. Lists ALL files in the BSP (O2PAGDIR table)
3. Extracts the CONTENT of every file (O2PAGCON table)
4. Saves all files to: extracted_code/BSP_<APPNAME>/ preserving directory structure

Usage:
    python extract_offboard_bsp_full.py                              (auto-discover + extract)
    python extract_offboard_bsp_full.py --app HCMFAB_HR_OFFBOARD    (use specific app name)
    python extract_offboard_bsp_full.py --discover                   (only list candidates)
"""
import os
import sys
import argparse
from pathlib import Path
from sap_utils import get_sap_connection


def discover_bsp_candidates(conn, keywords=None):
    """Search TADIR for BSP (WAPA) objects related to offboarding."""
    if keywords is None:
        keywords = ['OFFBOARD', 'HCMFAB', 'ZHRF']

    print(f"\n=== STEP 1: Discovering BSP apps (WAPA) in TADIR ===\n")
    seen = set()
    candidates = []

    for kw in keywords:
        try:
            result = conn.call(
                'RFC_READ_TABLE',
                QUERY_TABLE='TADIR',
                OPTIONS=[{'TEXT': f"PGMID = 'R3TR' AND OBJECT = 'WAPA' AND OBJ_NAME LIKE '%{kw}%'"}],
                FIELDS=[{'FIELDNAME': 'OBJ_NAME'}, {'FIELDNAME': 'DEVCLASS'}],
                ROWCOUNT=100,
                DELIMITER='|'
            )
            for row in result.get('DATA', []):
                parts = row['WA'].split('|')
                name = parts[0].strip()
                if name and name not in seen:
                    seen.add(name)
                    candidates.append(name)
                    devclass = parts[1].strip() if len(parts) > 1 else ''
                    print(f"  Found BSP [{kw}]: {name}  (package: {devclass})")
        except Exception as e:
            print(f"  Warning scanning keyword '{kw}': {e}")

    if not candidates:
        print("  No BSP candidates found.")
    else:
        print(f"\n  Total unique candidates: {len(candidates)}")
    return candidates


def list_bsp_files(conn, app_name):
    """Return all file-page metadata for a BSP app from O2PAGDIR."""
    print(f"\n=== STEP 2: Listing all pages/files in BSP '{app_name}' (O2PAGDIR) ===\n")
    result = conn.call(
        'RFC_READ_TABLE',
        QUERY_TABLE='O2PAGDIR',
        OPTIONS=[{'TEXT': f"APPLNAME = '{app_name}'"}],
        FIELDS=[
            {'FIELDNAME': 'PAGEKEY'},
            {'FIELDNAME': 'PAGENAME'},
            {'FIELDNAME': 'MIMETYPE'},
        ],
        ROWCOUNT=5000,
        DELIMITER='|'
    )
    files = []
    for row in result.get('DATA', []):
        parts = row['WA'].split('|')
        name = parts[1].strip() if len(parts) > 1 else ''
        mime = parts[2].strip() if len(parts) > 2 else ''
        if name:
            files.append({'name': name, 'mime': mime})

    print(f"  Total files found: {len(files)}")
    for f in files:
        print(f"    [{f['mime'] or 'unknown':40s}] {f['name']}")
    return files


def fetch_page_content(conn, app_name, page_name):
    """Fetch the content of a specific BSP page from O2PAGCON."""
    result = conn.call(
        'RFC_READ_TABLE',
        QUERY_TABLE='O2PAGCON',
        OPTIONS=[{'TEXT': f"APPLNAME = '{app_name}' AND PAGENAME = '{page_name}'"}],
        FIELDS=[{'FIELDNAME': 'PAGELINE'}],
        ROWCOUNT=999999,
        DELIMITER='~'
    )
    lines = []
    for row in result.get('DATA', []):
        line = row['WA']
        # strip our delimiter
        if line.endswith('~'):
            line = line[:-1]
        lines.append(line)
    return '\n'.join(lines)


def save_file(output_dir: Path, page_name: str, content: str):
    """Save extracted BSP file content to disk, preserving directory structure."""
    safe_name = page_name.replace('/', os.sep).lstrip(os.sep)
    target = output_dir / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8', errors='replace')
    return target


def extract_full_bsp(conn, app_name: str, output_base: Path):
    """Main extraction routine."""
    files = list_bsp_files(conn, app_name)
    if not files:
        print(f"ERROR: No files found in BSP '{app_name}'. Check app name.")
        return None

    output_dir = output_base / f"BSP_{app_name}"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== STEP 3: Extracting content → {output_dir} ===\n")

    success = 0
    empty = 0
    errors = 0

    for i, f in enumerate(files, 1):
        page_name = f['name']
        print(f"  [{i:3d}/{len(files)}] {page_name} ... ", end='', flush=True)
        try:
            content = fetch_page_content(conn, app_name, page_name)
            if content.strip():
                saved = save_file(output_dir, page_name, content)
                print(f"OK ({len(content):,} chars)")
                success += 1
            else:
                saved = save_file(output_dir, page_name, f"/* EMPTY — {page_name} */")
                print(f"EMPTY (placeholder)")
                empty += 1
        except Exception as e:
            print(f"ERROR: {e}")
            # write error marker file
            try:
                save_file(output_dir, page_name + '.ERROR', str(e))
            except Exception:
                pass
            errors += 1

    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"  App     : {app_name}")
    print(f"  Output  : {output_dir}")
    print(f"  Success : {success}")
    print(f"  Empty   : {empty}")
    print(f"  Errors  : {errors}")
    print(f"  Total   : {len(files)}")
    print(f"{'='*60}\n")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description='Full BSP Extractor for HR Offboarding App')
    parser.add_argument('--app', default=None, help='BSP application name (e.g. HCMFAB_HR_OFFBOARD)')
    parser.add_argument('--discover', action='store_true', help='Only discover BSP app candidates, do not extract')
    parser.add_argument('--output', default=None, help='Output base directory')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_base = Path(args.output) if args.output else script_dir / 'extracted_code'
    output_base.mkdir(parents=True, exist_ok=True)

    print("Connecting to SAP...")
    conn = get_sap_connection()
    print("Connected.")

    # Step 1: Discover
    if args.app:
        app_name = args.app
        print(f"\nUsing specified app: {app_name}")
    else:
        candidates = discover_bsp_candidates(conn)
        if args.discover:
            conn.close()
            print(f"\nDiscovery complete. {len(candidates)} candidate(s) found above.")
            return
        if not candidates:
            conn.close()
            print("\nNo BSP candidates found. Use --app to specify one manually.")
            sys.exit(1)
        # Prefer offboard-specific ones first
        preferred = None
        priority_kw = ['OFFBOARD', 'HCMFAB_HR_OFFBOARD', 'ZHRF_OFFBOARD']
        for kw in priority_kw:
            for c in candidates:
                if kw in c.upper():
                    preferred = c
                    break
            if preferred:
                break
        app_name = preferred or candidates[0]
        print(f"\nAuto-selected app for extraction: {app_name}")

    # Step 2 + 3: Extract
    extract_full_bsp(conn, app_name, output_base)
    conn.close()


if __name__ == '__main__':
    main()

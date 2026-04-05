"""
h11_h14_h18_adt_extract.py — ADT extraction for 3 zombies shipping in #038

Session #038 · 2026-04-05

Targets:
  H18 — YCL_IDFI_CGI_DMEE_AE + YCL_IDFI_CGI_DMEE_BH (find XML <Purp><Cd> literal)
  H14 — YWFI package function modules (Z_GET_CERTIF_OFFICER_UNESDIR, siblings)
  H11 — Benefits BSP app (discover from ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT) + HCM Z-reports

Output layout:
  extracted_code/DMEE/YCL_IDFI_CGI_DMEE_AE.abap
  extracted_code/DMEE/YCL_IDFI_CGI_DMEE_BH.abap
  extracted_code/YWFI/<fm_name>.abap  (one file per FM in the YWFI package)
  extracted_code/HCM/ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT.abap (trace file)
  extracted_code/HCM/BSP/<bsp_name>/<page>.html  (if BSP discoverable)
  extracted_code/HCM/Z_Reports/<program_name>.abap (Z* programs in HCM namespace)

Direction: D01 READ-ONLY via ADT REST API. No writes.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, errors="replace", encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sap_adt_client import from_env  # noqa: E402

REPO = HERE.parent.parent
OUT = REPO / "extracted_code"
OUT.mkdir(parents=True, exist_ok=True)


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  [OUT] {path.relative_to(REPO)}  ({len(content)} chars)")


def extract_class(client, class_name: str, outdir: Path) -> str | None:
    """Extract a CLAS/OC class source. Returns the source or None if not found."""
    print(f"\n--- Extracting CLASS {class_name} ---")
    try:
        results = client.search_object(class_name, obj_type="CLAS/OC", max_results=5)
    except Exception as e:
        print(f"  [ERROR] search failed: {e}")
        return None
    if not results:
        print(f"  [NOT FOUND] {class_name}")
        return None
    hit = next((r for r in results if r["name"].upper() == class_name.upper()), results[0])
    uri = hit["uri"]
    print(f"  [FOUND] {hit['name']} type={hit['type']} uri={uri}")
    try:
        src = client.get_source(uri)
    except Exception as e:
        print(f"  [ERROR] get_source failed: {e}")
        return None
    safe_write(outdir / f"{class_name}.abap", src)
    return src


def extract_h18(client) -> dict:
    """H18: Read YCL_IDFI_CGI_DMEE_AE + YCL_IDFI_CGI_DMEE_BH, find <Purp><Cd> literal."""
    print("\n" + "=" * 60)
    print("  H18 — DMEE PPC XML Purp/Cd value")
    print("=" * 60)
    out = OUT / "DMEE"
    findings = {}
    for cls in ("YCL_IDFI_CGI_DMEE_AE", "YCL_IDFI_CGI_DMEE_BH"):
        src = extract_class(client, cls, out)
        if not src:
            findings[cls] = None
            continue
        # Hunt for Purp/Cd literal. Patterns:
        #   <Purp><Cd>XXX</Cd></Purp>
        #   'Purp' ... 'Cd' = '...'
        #   'AE5' / 'SAL' / similar 3-char codes near 'Purp' or 'Cd'
        hits = []
        for pat in [
            r"<Purp><Cd>([^<]+)</Cd></Purp>",
            r"<Purp>\s*<Cd>\s*([^<\s]+)\s*</Cd>\s*</Purp>",
            r"['\"]Purp['\"][^\n]*['\"]Cd['\"][^\n]*['\"]([A-Z0-9]{2,5})['\"]",
            r"cd\s*=\s*['\"]([A-Z0-9]{2,5})['\"]\s*.*Purp",
            r"Purp.*?cd\s*=\s*['\"]([A-Z0-9]{2,5})['\"]",
        ]:
            for m in re.finditer(pat, src, re.IGNORECASE | re.DOTALL):
                hits.append(m.group(1))
        # Also surface any 3-5 char code literals near "Purp"
        for m in re.finditer(r"([A-Za-z]*Purp[A-Za-z]*)[^\n]{0,200}?['\"]([A-Z][A-Z0-9]{2,4})['\"]", src):
            hits.append(f"{m.group(1)}/{m.group(2)}")
        findings[cls] = hits[:20]
        print(f"  [HITS] {cls}: {findings[cls] or '(no Purp/Cd literals matched patterns)'}")
        if not hits:
            # Dump first few lines containing 'Purp' or 'Cd' for manual inspection
            interesting = [
                (i, line) for i, line in enumerate(src.splitlines(), 1)
                if "purp" in line.lower() or "<cd>" in line.lower() or "purp" in line.lower()
            ]
            if interesting:
                print(f"  [MANUAL] {len(interesting)} lines mention Purp/Cd — first 10:")
                for i, line in interesting[:10]:
                    print(f"    line {i}: {line.strip()[:100]}")
    return findings


def extract_h14(client) -> dict:
    """H14: YWFI package — extract function modules + any classes."""
    print("\n" + "=" * 60)
    print("  H14 — YWFI package source")
    print("=" * 60)
    out = OUT / "YWFI"
    findings = {"fms": [], "missing": []}

    # Try known FM names first
    targets = [
        ("FUGR/FF", "Z_GET_CERTIF_OFFICER_UNESDIR"),
        ("FUGR/FF", "Z_WF_GET_CERTIFYING_OFFICER"),
    ]
    for obj_type, name in targets:
        print(f"\n--- Searching {obj_type} {name} ---")
        try:
            results = client.search_object(name, obj_type=obj_type, max_results=5)
        except Exception as e:
            print(f"  [ERROR] search failed: {e}")
            findings["missing"].append(name)
            continue
        if not results:
            # Try without type filter
            results = client.search_object(name, max_results=10)
        hit = next((r for r in results if r["name"].upper() == name.upper()), None)
        if not hit:
            print(f"  [NOT FOUND] {name}")
            findings["missing"].append(name)
            continue
        print(f"  [FOUND] {hit}")
        try:
            src = client.get_source(hit["uri"])
            safe_write(out / f"{name}.abap", src)
            findings["fms"].append({"name": name, "uri": hit["uri"], "size": len(src)})
        except Exception as e:
            print(f"  [ERROR] get_source failed: {e}")
            findings["missing"].append(name)

    # Discovery: search YWFI package content via wildcard Z_WF*
    print("\n--- Discovery: Z_WF* wildcard search ---")
    try:
        discoveries = client.search_object("Z_WF*", max_results=30)
        print(f"  Found {len(discoveries)} Z_WF* objects")
        for d in discoveries[:15]:
            print(f"    {d['name']:40s} type={d['type']:12s} uri={d['uri'][:60]}")
        findings["discovery_z_wf"] = discoveries
    except Exception as e:
        print(f"  [ERROR] discovery failed: {e}")

    return findings


def extract_h11(client) -> dict:
    """H11: Benefits BSP + HCM Z-reports.

    Strategy:
      1. Extract ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT source to find BSP references
      2. Search for BSP applications matching Z_HCMFAB* or Z_PT_*
      3. Discover HCM namespace programs (Z*HCM* or Z_HR*)
    """
    print("\n" + "=" * 60)
    print("  H11 — Benefits BSP + HCM Z-reports")
    print("=" * 60)
    findings = {}
    out_hcm = OUT / "HCM"

    # Step 1: extract the trace class
    src = extract_class(client, "ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT", out_hcm)
    findings["trace_class_src_len"] = len(src) if src else 0
    if src:
        # Look for BSP references in the source
        bsp_refs = set()
        for pat in [
            r"ZHCMFAB[_A-Z0-9]*",
            r"MYFAMILYME[_A-Z0-9]*",
            r"BSP_[A-Z_]+",
        ]:
            bsp_refs.update(re.findall(pat, src.upper()))
        findings["bsp_refs_in_trace"] = sorted(bsp_refs)[:20]
        print(f"  [TRACE] BSP-ish references in class: {list(bsp_refs)[:10]}")

    # Step 2: BSP search — try common HCM patterns
    print("\n--- BSP search ---")
    all_bsps = []
    for query in ("ZHCMFAB*", "Z_HCM*", "ZHR*", "ZMYFAMILYME*"):
        try:
            hits = client.search_object(query, obj_type="BSP/WA", max_results=20)
            if hits:
                print(f"  [{query}] {len(hits)} BSP apps")
                for h in hits[:5]:
                    print(f"    {h['name']}  uri={h['uri'][:70]}")
                all_bsps.extend(hits)
        except Exception as e:
            print(f"  [ERROR] BSP search {query}: {e}")
    findings["bsp_apps_found"] = len(all_bsps)
    if all_bsps:
        findings["bsp_names"] = sorted({b["name"] for b in all_bsps})

    # Step 3: HCM Z-reports — search by wildcard
    print("\n--- HCM Z-report discovery ---")
    all_progs = []
    for query in ("Z_HR*", "Z_HCM*", "ZHR_*", "Y_HR*", "YHR_*"):
        try:
            hits = client.search_object(query, obj_type="PROG/P", max_results=20)
            if hits:
                print(f"  [{query}] {len(hits)} programs")
                for h in hits[:5]:
                    print(f"    {h['name']}")
                all_progs.extend(hits)
        except Exception as e:
            print(f"  [ERROR] PROG search {query}: {e}")

    # Download up to first 15 discovered programs
    out_reports = out_hcm / "Z_Reports"
    extracted_count = 0
    seen = set()
    for p in all_progs:
        if p["name"] in seen:
            continue
        seen.add(p["name"])
        if extracted_count >= 15:
            break
        try:
            src = client.get_source(p["uri"])
            safe_write(out_reports / f"{p['name']}.abap", src)
            extracted_count += 1
        except Exception as e:
            print(f"  [SKIP] {p['name']}: {e}")
    findings["z_reports_extracted"] = extracted_count
    findings["z_reports_discovered"] = len(seen)

    return findings


def main() -> int:
    print("=" * 60)
    print("  H11/H14/H18 ADT Extraction — Session #038")
    print("=" * 60)

    print("\n[CONNECT] D01 ADT REST API...")
    client = from_env("D01")
    # Sanity ping
    try:
        client.fetch_csrf()
        print("[CONNECT] CSRF token fetched — ADT connection live")
    except Exception as e:
        print(f"[FATAL] ADT connection failed: {e}")
        return 1

    # Run all three in sequence
    results = {}
    try:
        results["H18"] = extract_h18(client)
    except Exception as e:
        print(f"[H18] raised: {e}")
        results["H18"] = {"error": str(e)}
    try:
        results["H14"] = extract_h14(client)
    except Exception as e:
        print(f"[H14] raised: {e}")
        results["H14"] = {"error": str(e)}
    try:
        results["H11"] = extract_h11(client)
    except Exception as e:
        print(f"[H11] raised: {e}")
        results["H11"] = {"error": str(e)}

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"\nH18 — DMEE classes:")
    for cls, hits in results["H18"].items():
        if hits is None:
            print(f"  {cls}: NOT FOUND")
        else:
            print(f"  {cls}: {len(hits)} Purp/Cd literal candidates: {hits[:5]}")
    print(f"\nH14 — YWFI package:")
    h14 = results["H14"]
    print(f"  FMs extracted: {len(h14.get('fms', []))}")
    for fm in h14.get("fms", []):
        print(f"    {fm['name']} ({fm['size']} chars)")
    print(f"  Missing: {h14.get('missing', [])}")
    print(f"  Z_WF* discoveries: {len(h14.get('discovery_z_wf', []))}")
    print(f"\nH11 — Benefits BSP + HCM Z-reports:")
    h11 = results["H11"]
    print(f"  ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT: {h11.get('trace_class_src_len', 0)} chars")
    print(f"  BSP apps found: {h11.get('bsp_apps_found', 0)}")
    if h11.get("bsp_names"):
        print(f"    names: {h11['bsp_names'][:10]}")
    print(f"  Z reports extracted: {h11.get('z_reports_extracted', 0)} / {h11.get('z_reports_discovered', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

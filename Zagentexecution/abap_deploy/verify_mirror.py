"""
verify_mirror.py — git-mirror 0-diff verifier (ported from CRP `unescrp/scripts/verify_mirror.py`).

READ-ONLY against D01 (GET active source only). Writes ONLY to the local git tree (with --adopt).
For each manifest object: fetch live D01 source -> normalize -> compare to the canonical git file.
Goal: 0-diff at session close (the mirror is git's review/audit trail; CRP uses pure ADT GET, NOT abapGit).

Usage:
  python verify_mirror.py                 # verify all manifest objects
  python verify_mirror.py --only NAME     # one object
  python verify_mirror.py --adopt-missing # write live->canonical where the local mirror is absent
  python verify_mirror.py --adopt NAME    # force-overwrite one canonical with live D01 source

Exit: 0 = all MATCH ; 1 = any DIFF/MISSING ; 2 = read error (e.g. 401 — HARD STOP, no retry).
"""
import os
import sys
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp-backend-server-python"))

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

from sap_adt_rfc_client import from_env, AdtRfcError

MANIFEST = os.path.join(HERE, "objects_manifest.yaml")


def normalize(src: str) -> str:
    lines = [ln.rstrip() for ln in src.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Verify git mirror == D01 active (read-only)")
    ap.add_argument("--only", help="verify a single object by name")
    ap.add_argument("--adopt-missing", action="store_true", help="seed canonical from D01 where local file absent")
    ap.add_argument("--adopt", help="force-overwrite one canonical with live D01 source")
    args = ap.parse_args()

    with open(MANIFEST, encoding="utf-8") as f:
        man = yaml.safe_load(f)

    objs = [o for o in man.get("objects", []) if o.get("tier") == "custom"]
    if args.only:
        objs = [o for o in objs if o["name"].upper() == args.only.upper()]
    if args.adopt:
        objs = [o for o in objs if o["name"].upper() == args.adopt.upper()]
    if not objs:
        sys.exit(f"No matching custom objects in manifest.")

    adt = from_env("D01")
    rc = 0
    for o in objs:
        name, otype, canon = o["name"], o.get("type", "CLASS"), os.path.join(HERE, o["canonical"])
        try:
            live = adt.read_source(otype, name)
        except AdtRfcError as e:
            if e.status in (401, 403):
                print(f"{name}: AUTH ERROR {e.status} — HARD STOP (no retry).")
                sys.exit(2)
            print(f"{name}: read error {e.status}")
            rc = 1
            continue

        if args.adopt or (args.adopt_missing and not os.path.exists(canon)):
            os.makedirs(os.path.dirname(canon), exist_ok=True)
            with open(canon, "w", encoding="utf-8") as f:
                f.write(normalize(live))
            print(f"{name}: ADOPTED -> {o['canonical']} ({len(live.splitlines())} lines)")
            continue

        if not os.path.exists(canon):
            print(f"{name}: MISSING canonical mirror ({o['canonical']}) — run --adopt-missing")
            rc = 1
            continue

        with open(canon, encoding="utf-8") as f:
            local = f.read()
        if normalize(local) == normalize(live):
            print(f"{name}: MATCH (0-diff)")
        else:
            print(f"{name}: DIFF — local mirror != D01 active")
            rc = 1

    print("\n" + ("ALL MATCH (mirror clean)" if rc == 0 else "MIRROR HAS DIFFS/MISSING — see above"))
    return rc


if __name__ == "__main__":
    sys.exit(main())

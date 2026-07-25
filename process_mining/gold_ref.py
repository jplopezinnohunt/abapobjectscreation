"""
gold_ref.py — resolve the golden DB through `golden_manifest.json`, never by a hardcoded path.

BEFORE (T5): 11 files under process_mining/ each embedded the literal
`Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`. 8 of them embedded it as a
RELATIVE string, so they only worked when cwd happened to be the repo root, and all 11 broke the
moment the hub moved a file. That path coupling is exactly what caps the hub's maturity: the
consumer had to know the physical layout.

AFTER: every consumer asks for (tenant_id, system_role) and the manifest answers. When D3/T7
retires the p01_/v01_ prefix, only the manifest builder changes — no file here.

    from gold_ref import GOLD          # module-level default: UNESCO / PROD, absolute
    from gold_ref import gold_db_path
    db = sqlite3.connect(gold_db_path("UNESCO", "VALIDATION"))

Returns a plain filesystem path (str) because several process_mining scripts WRITE their own
accumulation tables into the golden (e.g. accumulate_problems.py). For read-only access from
outside this package, prefer the `golden_query` MCP tool instead.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_HUB_DIR = REPO / "Zagentexecution" / "mcp-backend-server-python"

# Last-resort fallback, used ONLY if golden_manifest.json has not been built yet. Keeping it
# means no script here regresses; it is deliberately the single remaining literal in the package.
_LEGACY = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

DEFAULT_TENANT = "UNESCO"
DEFAULT_ROLE = "PROD"


def gold_db_path(tenant_id: str = DEFAULT_TENANT, system_role: str = DEFAULT_ROLE,
                 strict: bool = False) -> str:
    """(tenant_id, system_role) -> absolute path of that system's golden .db, via the manifest.

    strict=True raises if the manifest is missing/unbuilt instead of falling back.
    """
    if str(_HUB_DIR) not in sys.path:
        sys.path.insert(0, str(_HUB_DIR))
    try:
        import golden_hub  # stdlib-only module; no pyrfc/mcp import cost

        sysrec = golden_hub.resolve_system(tenant_id=tenant_id, system_role=system_role)
        p = sysrec.get("db_path_abs") or str(REPO / sysrec["db_path"])
        return str(Path(p))
    except Exception as e:  # manifest absent, unbuilt, or golden_hub missing
        if strict:
            raise
        sys.stderr.write(
            "[gold_ref] manifest resolution failed (%s: %s); falling back to the legacy path. "
            "Build it with: python scripts/extraction/build_golden_manifest.py\n"
            % (type(e).__name__, e)
        )
        return str(_LEGACY)


#: The golden DB for the default tenant/role. Absolute — cwd-independent (the old relative
#: literals silently pointed at nothing when a script ran from another directory).
GOLD = gold_db_path()


if __name__ == "__main__":
    print(GOLD)

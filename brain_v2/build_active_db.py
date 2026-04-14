"""
Build SQLite Active DB — agent-queryable database for filtering PMO, claims, sessions, incidents.
Generated from source files (not source of truth). Rebuildable anytime.

Usage: python brain_v2/build_active_db.py
"""
import json, os, re, sqlite3
from pathlib import Path
from glob import glob

PROJECT_ROOT = Path(__file__).parent.parent
CLAIMS_PATH = PROJECT_ROOT / "brain_v2" / "claims" / "claims.json"
PMO_PATH = PROJECT_ROOT / ".agents" / "intelligence" / "PMO_BRAIN.md"
ANNOTATIONS_PATH = PROJECT_ROOT / "brain_v2" / "annotations" / "annotations.json"
RETROS_DIR = PROJECT_ROOT / "knowledge" / "session_retros"
DB_PATH = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_active.db"


def create_schema(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS pmo_items;
        DROP TABLE IF EXISTS claims;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS incidents;

        CREATE TABLE pmo_items (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT,
            status TEXT NOT NULL,
            first_raised_session INTEGER,
            closed_session INTEGER,
            closed_reason TEXT,
            notes TEXT
        );
        CREATE INDEX idx_pmo_status ON pmo_items(status);
        CREATE INDEX idx_pmo_priority ON pmo_items(priority);

        CREATE TABLE claims (
            id INTEGER PRIMARY KEY,
            claim TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            confidence TEXT NOT NULL,
            evidence_for TEXT,                -- JSON-serialized list of {type, ref, cite, added_session}
            evidence_against TEXT,            -- JSON-serialized list (same schema) or NULL
            evidence_count_for INTEGER DEFAULT 0,    -- count of structured evidence items (CP-003: weakness detector)
            evidence_count_against INTEGER DEFAULT 0,
            evidence_legacy_text_for TEXT,    -- original pre-session-054 string (CP-001: preserve)
            evidence_legacy_text_against TEXT,
            related_objects TEXT,
            domain TEXT,
            created_session INTEGER,
            resolved_session INTEGER,
            status TEXT DEFAULT 'active'
        );
        CREATE INDEX idx_claims_type ON claims(claim_type);
        CREATE INDEX idx_claims_confidence ON claims(confidence);
        CREATE INDEX idx_claims_evidence_count_for ON claims(evidence_count_for);

        CREATE TABLE sessions (
            session_number INTEGER PRIMARY KEY,
            date TEXT,
            focus TEXT,
            deliverables_count INTEGER DEFAULT 0,
            items_added INTEGER DEFAULT 0,
            items_closed INTEGER DEFAULT 0,
            net INTEGER DEFAULT 0
        );

        CREATE TABLE incidents (
            id TEXT PRIMARY KEY,
            description TEXT,
            root_cause_objects TEXT,
            contributing_objects TEXT,
            session_discovered INTEGER,
            session_resolved INTEGER,
            status TEXT
        );
    """)


def load_claims(conn):
    if not CLAIMS_PATH.exists():
        print("  No claims.json found")
        return 0
    claims = json.load(open(CLAIMS_PATH, encoding="utf-8"))
    count = 0
    for c in claims:
        # Evidence is now a structured list (session #054 H42 migration).
        # Serialize to JSON for SQLite TEXT storage; keep a count column for
        # CP-003 weakness detection (claims with evidence_count_for < 2 are suspect).
        ef = c.get("evidence_for")
        ea = c.get("evidence_against")
        ef_json = json.dumps(ef, ensure_ascii=False) if ef is not None else None
        ea_json = json.dumps(ea, ensure_ascii=False) if ea is not None else None
        ef_count = len(ef) if isinstance(ef, list) else (1 if ef else 0)
        ea_count = len(ea) if isinstance(ea, list) else (1 if ea else 0)

        conn.execute("""INSERT OR REPLACE INTO claims
            (id, claim, claim_type, confidence,
             evidence_for, evidence_against,
             evidence_count_for, evidence_count_against,
             evidence_legacy_text_for, evidence_legacy_text_against,
             related_objects, domain, created_session, resolved_session, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (c["id"], c["claim"], c["claim_type"], c["confidence"],
             ef_json, ea_json,
             ef_count, ea_count,
             c.get("evidence_legacy_text_for"), c.get("evidence_legacy_text_against"),
             json.dumps(c.get("related_objects", [])),
             c.get("domain"), c.get("created_session"),
             c.get("resolved_session"), c.get("status", "active")))
        count += 1
    return count


def parse_pmo(conn):
    if not PMO_PATH.exists():
        print("  No PMO_BRAIN.md found")
        return 0
    text = open(PMO_PATH, encoding="utf-8").read()
    count = 0

    # Parse table rows: | ID | title | session | category/blocks | notes |
    # Detect struck-through items: ~~ID~~
    for line in text.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 4:
            continue

        # Find the ID cell (B1, H1, G1, etc.)
        id_cell = cells[1] if len(cells) > 1 else ""
        # Strip markdown formatting
        raw_id = re.sub(r"[~*]", "", id_cell).strip()

        # Match PMO item IDs
        m = re.match(r"^(B\d+|H\d+|G\d+)$", raw_id)
        if not m:
            continue

        item_id = m.group(1)
        is_struck = "~~" in id_cell

        title = re.sub(r"[~*]", "", cells[2]).strip() if len(cells) > 2 else ""
        session_text = re.sub(r"[~*]", "", cells[3]).strip() if len(cells) > 3 else ""

        # Parse session number
        sm = re.search(r"#(\d+)", session_text)
        first_session = int(sm.group(1)) if sm else None

        # Determine priority from section context
        if item_id.startswith("B"):
            priority = "BLOCKING"
        elif item_id.startswith("H"):
            priority = "HIGH"
        else:
            priority = "BACKLOG"

        status = "CLOSED" if is_struck else "OPEN"

        # Extract closed reason from notes
        notes = cells[5].strip() if len(cells) > 5 else cells[4].strip() if len(cells) > 4 else ""
        notes = re.sub(r"[~*]", "", notes)
        closed_reason = None
        if "KILLED" in notes:
            status = "KILLED"
            closed_reason = "killed"
        elif "Done" in notes or "DONE" in notes:
            closed_reason = "done"
        elif "MERGED" in notes:
            status = "MERGED"
            closed_reason = "merged"

        conn.execute("""INSERT OR REPLACE INTO pmo_items
            (id, title, priority, status, first_raised_session, closed_reason, notes)
            VALUES (?,?,?,?,?,?,?)""",
            (item_id, title[:200], priority, status, first_session, closed_reason, notes[:500]))
        count += 1

    return count


def parse_sessions(conn):
    """Parse session retro files for session metadata."""
    count = 0
    if not RETROS_DIR.exists():
        print("  No session_retros directory")
        return 0

    for retro_file in sorted(RETROS_DIR.glob("session_*_retro.md")):
        m = re.search(r"session_(\d+)_retro", retro_file.name)
        if not m:
            continue
        session_num = int(m.group(1))

        text = open(retro_file, encoding="utf-8", errors="replace").read()

        # Extract date
        dm = re.search(r"\*\*Date:\*\*\s*(\S+)", text)
        date = dm.group(1) if dm else ""

        # Extract focus from first ## heading or "What Happened"
        fm = re.search(r"## What Happened\s*\n(.+?)(?:\n|$)", text)
        focus = fm.group(1).strip()[:200] if fm else ""
        if not focus:
            fm = re.search(r"\*\*Focus:\*\*\s*(.+?)(?:\n|$)", text)
            focus = fm.group(1).strip()[:200] if fm else ""

        # Count deliverables
        dm = re.search(r"Deliverables?\s*\((\d+)\)", text)
        deliverables = int(dm.group(1)) if dm else 0

        # Count PMO additions/closures
        added = len(re.findall(r"NEW\)", text))
        closed = len(re.findall(r"Done|KILLED|CLOSED|Closed", text))

        conn.execute("""INSERT OR REPLACE INTO sessions
            (session_number, date, focus, deliverables_count, items_added, items_closed, net)
            VALUES (?,?,?,?,?,?,?)""",
            (session_num, date, focus, deliverables, added, closed, closed - added))
        count += 1

    return count


def parse_incidents(conn):
    """Extract incidents from annotations."""
    if not ANNOTATIONS_PATH.exists():
        return 0
    annotations = json.load(open(ANNOTATIONS_PATH, encoding="utf-8"))
    incidents = {}

    for obj_id, obj_data in annotations.items():
        for ann in obj_data.get("annotations", []):
            inc = ann.get("incident")
            if not inc:
                continue
            if inc not in incidents:
                incidents[inc] = {
                    "description": "",
                    "root_cause": [],
                    "contributing": [],
                    "session": ann.get("session", ""),
                }
            tag = ann.get("tag", "")
            if tag == "CRITICAL":
                incidents[inc]["root_cause"].append(obj_id)
                if not incidents[inc]["description"]:
                    incidents[inc]["description"] = ann.get("finding", "")[:200]
            else:
                incidents[inc]["contributing"].append(obj_id)

    count = 0
    for inc_id, data in incidents.items():
        sm = re.search(r"#(\d+)", data["session"])
        session_num = int(sm.group(1)) if sm else None
        conn.execute("""INSERT OR REPLACE INTO incidents
            (id, description, root_cause_objects, contributing_objects,
             session_discovered, status)
            VALUES (?,?,?,?,?,?)""",
            (inc_id, data["description"],
             json.dumps(data["root_cause"]),
             json.dumps(data["contributing"]),
             session_num, "OPEN"))
        count += 1

    return count


def build():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("Creating schema...")
    create_schema(conn)

    print("Loading claims...")
    n = load_claims(conn)
    print(f"  {n} claims loaded")

    print("Parsing PMO...")
    n = parse_pmo(conn)
    print(f"  {n} PMO items parsed")

    print("Parsing sessions...")
    n = parse_sessions(conn)
    print(f"  {n} sessions parsed")

    print("Parsing incidents...")
    n = parse_incidents(conn)
    print(f"  {n} incidents parsed")

    conn.commit()
    conn.close()
    print(f"\nActive DB saved: {DB_PATH}")


if __name__ == "__main__":
    build()

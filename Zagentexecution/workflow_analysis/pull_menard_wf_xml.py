"""
Phase 2 — pull workflow XML definitions for N_MENARD's 9 WS templates
and scan each for User Decision steps with outcome name 'Return'.

Approach: call RFC 'RH_WF_DEFINITION_LOAD' (returns ASC_LINES of the XML).
Fallback: read HRS1217 / HRS1222 directly.

Outcome detection: search for <STEP STEP_TYPE="UserDecision"> then nested
outcome/decision tags with OUTCOME_TEXT (or NAME) containing 'Return'.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
WS_IDS = [
    "98100016", "98100018", "98100019", "98100020",
    "98100021", "98100022", "98100023", "98100026", "98100027",
]

# Candidate RFC functions that return workflow definitions.
CANDIDATE_RFCS = [
    "RH_WF_DEFINITION_LOAD",
    "SWD_WFD_DEFINITION_READ",
    "RH_WF_DEFINITION_DOWNLOAD",
    "RH_WORKFLOW_DEFINITION_GET",
]


def discover_rfc(g):
    """Find which workflow-definition RFC exists in this system."""
    found = []
    for fn in CANDIDATE_RFCS:
        try:
            r = g.call(
                "RFC_READ_TABLE",
                QUERY_TABLE="TFDIR",
                DELIMITER="|",
                OPTIONS=[{"TEXT": f"FUNCNAME = '{fn}'"}],
                FIELDS=[{"FIELDNAME": "FUNCNAME"}, {"FIELDNAME": "PNAME"}],
                ROWCOUNT=1,
            )
            if r["DATA"]:
                found.append(fn)
        except Exception:
            pass
    return found


def try_rh_wf_load(g, objid):
    """Try RH_WF_DEFINITION_LOAD — returns tab of strings."""
    try:
        r = g.call(
            "RH_WF_DEFINITION_LOAD",
            OBJID=objid,
            OTYPE="WS",
        )
        return True, r
    except Exception as e:
        return False, str(e)


def scan_for_return(xml_text):
    """Find User Decision steps whose outcomes include a 'Return' label."""
    hits = []
    # Most XML variants use <step type="0121"> or STEP_TYPE="UserDecision"
    # Outcomes live under <outcome_text>...</outcome_text> or NAME attribute.
    # Be permissive: any tag/attribute whose value equals 'Return' near a decision step.
    # First pass: count raw 'Return' occurrences in outcome-labeled contexts.
    pattern_ud = re.compile(
        r"(STEP_TYPE\s*=\s*['\"]UserDecision['\"]|<step[^>]*type=['\"]0121['\"])",
        re.IGNORECASE,
    )
    if not pattern_ud.search(xml_text):
        return {"user_decision_steps": 0, "return_outcomes": 0, "hits": []}

    # Split into step blocks and inspect each.
    step_blocks = re.split(r"(?=(?:STEP_TYPE\s*=|<step\s))", xml_text, flags=re.IGNORECASE)
    ud_count = 0
    for block in step_blocks:
        if not pattern_ud.search(block):
            continue
        ud_count += 1
        # Look for outcome names = 'Return' (case-sensitive match on the literal label).
        m_outs = re.findall(
            r"(?:OUTCOME|NAME|outcome_text|OUTCOME_TEXT)\s*[=>:]\s*['\"]?Return['\"]?",
            block,
        )
        if m_outs:
            # Grab the step number if present
            m_step = re.search(
                r"(?:STEP_NUMBER|NODEID|step_number|nodeid|STEP)\s*[=:]\s*['\"]?(\d+)",
                block,
            )
            step_no = m_step.group(1) if m_step else "?"
            hits.append({"step": step_no, "return_markers": len(m_outs)})
    return {
        "user_decision_steps": ud_count,
        "return_outcomes": sum(h["return_markers"] for h in hits),
        "hits": hits,
    }


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        print("== discovering available RFCs ==")
        available = discover_rfc(g)
        print(f"  available: {available}")

        results = {}
        for wsid in WS_IDS:
            print(f"\n== WS {wsid} ==")
            ok, payload = try_rh_wf_load(g, wsid)
            if not ok:
                print(f"  RH_WF_DEFINITION_LOAD failed: {payload[:180]}")
                results[wsid] = {"error": payload[:500]}
                continue
            # Concatenate any table-of-strings payload into one text blob
            blob_parts = []
            for k, v in payload.items():
                if isinstance(v, list):
                    for row in v:
                        if isinstance(row, dict):
                            blob_parts.append(" ".join(str(x) for x in row.values()))
                        else:
                            blob_parts.append(str(row))
                elif isinstance(v, (str, bytes)):
                    blob_parts.append(v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else v)
            xml_text = "\n".join(blob_parts)
            scan = scan_for_return(xml_text)
            print(f"  XML chars: {len(xml_text)}")
            print(f"  UserDecision steps: {scan['user_decision_steps']}")
            print(f"  'Return' outcome hits: {scan['return_outcomes']}")
            for h in scan["hits"]:
                print(f"    step {h['step']}: {h['return_markers']} Return marker(s)")
            # Save the raw XML for offline inspection
            raw_path = os.path.join(OUT_DIR, f"WS{wsid}_raw.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(xml_text)
            results[wsid] = {
                "xml_chars": len(xml_text),
                "scan": scan,
                "raw_file": os.path.basename(raw_path),
            }

        summary_path = os.path.join(OUT_DIR, "menard_return_step_scan.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({"available_rfcs": available, "results": results},
                      f, indent=2, ensure_ascii=False)
        print(f"\nsummary: {summary_path}")
    finally:
        g.close()


if __name__ == "__main__":
    main()

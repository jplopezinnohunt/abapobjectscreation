"""Session #054 Chunk C: add 4 operational rules derived from CPs."""
import json
from pathlib import Path

RULES_PATH = Path("brain_v2/agent_rules/feedback_rules.json")

new_rules = [
    {
        "id": "feedback_retro_to_pmo_bridge",
        "rule": "At session close, every 'commitment', 'open follow-up', 'what's next', or 'consider building X' mentioned in the retro MUST have a corresponding PMO H-item before the session is closed. If a retro mentions N follow-up items, PMO must show N new/updated entries traceable to that retro.",
        "why": "Session #053 generated 16 follow-up items in retro sections §7/§11/§13 (Brain updates, Knowledge graph edges, skill sap_fm_avc_intelligence, ZFIX object promotions, table registrations). Only 3 were formalized (H38/H39/H40). The other 13 quietly disappeared — discovered only at session #054 audit by the user. This is a systemic trap: retros are written with flow-of-thought commitment language but PMO is the enforcement layer. Without a bridge check, velocity-mode sessions erode the knowledge base silently.",
        "how_to_apply": "Before marking a session closed, grep the retro for verbs of commitment (should, need to, must, will, consider, propose, promote, register) and for sections titled 'Open follow-ups', 'Brain updates needed', 'PMO updates', 'What's next'. For each unique action noun phrase, verify a matching H-item exists in PMO_BRAIN.md with session tag. If missing, either (a) add the H-item now, or (b) explicitly write 'DECIDED NOT TO TRACK: <reason>' in the retro so the absence is evidence of decision, not omission. When in doubt, formalize — a false-positive H-item can be killed; a false-negative follow-up is irreversible memory loss.",
        "severity": "CRITICAL",
        "derives_from_core_principle": "CP-001",
        "created_session": 54,
        "source_file": "knowledge/session_retros/session_053_retro.md",
        "evidence_of_violation": [
            {"session": 53, "items_committed_in_retro": 16, "items_formalized_in_pmo": 3, "gap_detected_session": 54}
        ]
    },
    {
        "id": "feedback_never_drop_columns",
        "rule": "When extending a table, DataFrame, SQLite schema, Excel sheet, or any tabular artifact, NEVER drop existing columns while adding new ones. Use a single canonical script that all queries extend; columns are append-only unless the user explicitly asks to remove one.",
        "why": "Session #053 retro §10 identified this as a 'did worse' pattern, observed twice in the same session: while building br_lines_FINAL.xlsx (INC-BUDGETRATE-EQG inventory), the agent added new analytical columns and silently dropped 3-4 existing ones the user had asked for. The user had to re-request and re-validate, which broke trust in the iteration. Root cause: agent was regenerating the whole DataFrame each iteration from a narrower column list instead of augmenting the existing one. Cost: loss of fidelity + wasted user time.",
        "how_to_apply": "Maintain a canonical column list variable at the top of the extraction/build script. When adding a new column: append to the list, never replace it. When tempted to simplify: don't — preserve every column the user has ever asked for. If a column is truly obsolete, ask the user explicitly before dropping. In Excel output: pd.concat([existing_df, new_cols], axis=1), not pd.DataFrame(new_data_only). In SQLite: ALTER TABLE ADD COLUMN, never DROP TABLE + CREATE TABLE. Verify column count is >= previous before saving.",
        "severity": "HIGH",
        "derives_from_core_principle": "CP-001",
        "created_session": 54,
        "source_file": "knowledge/session_retros/session_053_retro.md",
        "evidence_of_violation": [
            {"session": 53, "artifact": "Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx", "incident": "dropped columns twice during iteration"}
        ]
    },
    {
        "id": "feedback_sample_before_aggregating",
        "rule": "Before computing aggregates (sum, avg, count, groupby) on an unfamiliar table or data shape, ALWAYS read 3+ raw rows first to verify sign convention, units, scale, and duplicate semantics. Write the aggregation ONLY after the raw sample is understood.",
        "why": "Session #053 retro §10: the agent misinterpreted FMIOI sign convention twice — took absolute sums assuming all rows were positive, when in reality FMIOI WRTTP=81 rows for an FR include creation (positive), period-016 year-end reversal (negative), and period-000 carryforward-in (positive). Naive sum returned inflated commitment numbers. Same pattern with FMAVCT duplicates by RVERS/RPMAX. Root cause: the agent wrote the aggregation SQL before reading any raw row. For unfamiliar SAP tables with cluster or time-dependent semantics, this is guaranteed to produce wrong numbers.",
        "how_to_apply": "For any new SAP table the agent queries for the first time in a session: (1) SELECT * FROM table LIMIT 5 with all fields visible; (2) inspect sign patterns of amount fields (HSL*, WRBTR, FKBTR) for the same key across rows; (3) check for version/status columns (RVERS, RPMAX, WRTTP, STATUS); (4) document sign convention in a comment before the aggregation SQL. For FMIOI specifically: always filter by GJAHR + WRTTP and trace by BUDAT for carryforward interpretation. For FMAVCT: dedup by RVERS/RPMAX before summing. For cluster tables (BSEG, KBLE, KBLEW): use the appropriate wrapper FM, never raw RFC_READ_TABLE.",
        "severity": "MEDIUM",
        "derives_from_core_principle": "CP-003",
        "created_session": 54,
        "source_file": "knowledge/session_retros/session_053_retro.md",
        "evidence_of_violation": [
            {"session": 53, "artifact": "br_consumption_audit.py v1", "incident": "FMIOI absolute-sum bug, 2 iterations"}
        ]
    },
    {
        "id": "feedback_explicit_aggregation_filter",
        "rule": "Every aggregation column in a report, Excel sheet, or companion MUST explicitly state its filter in the column name or header comment: per-line, per-FR, per-fund, per-FONDS+FIPEX, per-year, per-company-code, per-ledger. Ambiguous 'total' or 'sum' is forbidden.",
        "why": "Session #053 retro §10: during the INC-BUDGETRATE-EQG investigation, the agent presented a $170K number as if it were per-FR-line consumption when it was actually per-cover-group pool consumption (FONDS+FIPEX). The user asked 'but that doesn't match the Vonthron case which is one line' — this forced a correction and a re-explanation. The ambiguity was in a column named Total_Consumed which could have meant 4 different things. Unambiguous names at report time prevent misinterpretation at review time.",
        "how_to_apply": "Column naming template: <metric>_<filter>_<unit>. Examples: committed_per_FR_USD, available_per_FONDS_FIPEX_USD, actual_per_line_EUR_2026_9H. In Excel headers: freeze row 1 + add a comment explaining the filter. In markdown tables: include filter in the column header, or add a one-line caption below. When in doubt, make the name longer, not shorter. At review: if the user asks 'but is this per X or per Y', the name failed — rename before answering.",
        "severity": "MEDIUM",
        "derives_from_core_principle": "CP-003",
        "created_session": 54,
        "source_file": "knowledge/session_retros/session_053_retro.md",
        "evidence_of_violation": [
            {"session": 53, "artifact": "br_lines_FINAL_table.md v1", "incident": "$170K pool vs per-line consumption ambiguity, required correction"}
        ]
    }
]

with open(RULES_PATH, "r", encoding="utf-8") as f:
    rules = json.load(f)

existing_ids = {r.get("id") for r in rules}
added = 0
for nr in new_rules:
    if nr["id"] in existing_ids:
        print(f"SKIP (exists): {nr['id']}")
    else:
        rules.append(nr)
        added += 1
        print(f"ADDED: {nr['id']} [{nr['severity']}] derives_from={nr['derives_from_core_principle']}")

with open(RULES_PATH, "w", encoding="utf-8") as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)

print(f"\nTotal rules now: {len(rules)} (added {added})")

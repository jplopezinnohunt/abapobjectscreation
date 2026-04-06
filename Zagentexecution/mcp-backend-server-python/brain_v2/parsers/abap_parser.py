"""
abap_parser.py — Regex-based ABAP static analysis for dependency extraction.

Extracts 6 dependency patterns from ABAP source code:
1. SELECT → READS_TABLE + READS_FIELD
2. CALL FUNCTION → CALLS_FM
3. INSERT/MODIFY/UPDATE/DELETE → WRITES_TABLE
4. INHERITING FROM → INHERITS_FROM
5. INTERFACES → IMPLEMENTS_INTF
6. BAdI implementation detection → IMPLEMENTS_BADI

Design: BRAIN_V2_ARCHITECTURE.md Section B.1
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ABAP keywords that look like table names but aren't
ABAP_KEYWORDS = {
    "INTO", "FROM", "WHERE", "AND", "OR", "NOT", "TABLE", "APPENDING",
    "CORRESPONDING", "FIELDS", "OF", "UP", "TO", "ROWS", "ORDER", "BY",
    "GROUP", "HAVING", "FOR", "ALL", "ENTRIES", "IN", "INNER", "LEFT",
    "RIGHT", "OUTER", "JOIN", "ON", "AS", "SINGLE", "DISTINCT", "DATA",
    "TYPE", "TYPES", "LIKE", "REF", "STANDARD", "SORTED", "HASHED",
    "RANGE", "BEGIN", "END", "INCLUDE", "STRUCTURE", "CLASS", "METHOD",
    "METHODS", "ENDMETHOD", "ENDCLASS", "PUBLIC", "PRIVATE", "PROTECTED",
    "SECTION", "DEFINITION", "IMPLEMENTATION", "INHERITING", "ABSTRACT",
    "FINAL", "CREATE", "RETURNING", "EXPORTING", "IMPORTING", "CHANGING",
    "RAISING", "VALUE", "OPTIONAL", "DEFAULT", "REDEFINITION", "LOOP",
    "ENDLOOP", "IF", "ENDIF", "ELSE", "ELSEIF", "CASE", "ENDCASE",
    "WHEN", "OTHERS", "DO", "ENDDO", "WHILE", "ENDWHILE", "CHECK",
    "EXIT", "CONTINUE", "RETURN", "CLEAR", "FREE", "REFRESH", "MOVE",
    "WRITE", "SKIP", "NEW", "LINE", "ULINE", "REPORT", "FORM", "ENDFORM",
    "PERFORM", "USING", "TABLES", "COMMIT", "WORK", "ROLLBACK", "WAIT",
    "SY", "SPACE", "ABAP_TRUE", "ABAP_FALSE", "IS", "INITIAL", "BOUND",
    "ASSIGNED", "SUPPLIED", "NOT", "EQ", "NE", "LT", "GT", "LE", "GE",
    "CO", "CN", "CA", "NA", "CS", "NS", "CP", "NP",
}

# SAP standard tables we recognize (subset — extend as needed)
KNOWN_SAP_TABLES = {
    "BKPF", "BSEG", "BSIS", "BSAS", "BSIK", "BSAK", "BSID", "BSAD",
    "EKKO", "EKPO", "EKBE", "ESSR", "ESLL", "EBAN", "RBKP", "RSEG",
    "FMIFIIT", "FMFCT", "FMFCTR", "FMIOI", "FMBH", "FMBL",
    "PROJ", "PRPS", "COOI", "COEP", "RPSCO",
    "CDHDR", "CDPOS", "TBTCO", "TBTCP",
    "RFCDES", "EDIDC", "ICFSERVLOC",
    "T001", "T001B", "T003", "T012", "T012K",
    "T042A", "T042B", "T042D", "T042E", "T042I", "T042Z",
    "SKA1", "SKAT", "SKB1", "CSKA", "CSKU", "CSKB",
    "REGUH", "REGUP", "PAYR", "FPAYH", "FPAYP",
    "BNK_BATCH_HEADER", "BNK_BATCH_ITEM",
    "FEBKO", "FEBEP", "FEBRE",
    "NRIV", "TADIR", "TRDIR", "REPOSRC",
    "DMEE_TREE", "DMEE_TREE_NODE",
    "DD03L", "DD02L",
    "USR02", "AGR_USERS",
}


class ABAPDependencyParser:
    """Extract dependencies from ABAP source code files."""

    RE_SELECT = re.compile(
        r'SELECT\s+(?:SINGLE\s+)?'
        r'(?P<fields>[\w\s,*~]+?)\s+'
        r'FROM\s+(?P<table>\w+)',
        re.IGNORECASE | re.DOTALL
    )

    RE_CALL_FM = re.compile(
        r"CALL\s+FUNCTION\s+'(?P<fm_name>[A-Za-z0-9_/]+)'",
        re.IGNORECASE
    )

    RE_WRITE = re.compile(
        r'(?:INSERT|MODIFY|UPDATE|DELETE)\s+(?:FROM\s+)?(?P<table>[A-Z]\w{2,30})\b',
        re.IGNORECASE
    )

    RE_INHERITS = re.compile(
        r'CLASS\s+\w+\s+DEFINITION.*?INHERITING\s+FROM\s+(?P<super>\w+)',
        re.IGNORECASE | re.DOTALL
    )

    RE_INTERFACE = re.compile(
        r'INTERFACES\s+(?P<intf>[A-Za-z]\w+)',
        re.IGNORECASE
    )

    RE_BADI_CLASS = re.compile(
        r'CLASS\s+(?P<cls>[YZ]CL_\w*IM\w+)\s+DEFINITION',
        re.IGNORECASE
    )

    RE_BADI_INTERFACE = re.compile(
        r'INTERFACES\s+(?P<intf>IF_EX_\w+)',
        re.IGNORECASE
    )

    def _is_valid_table(self, name: str) -> bool:
        """Check if a name looks like a real SAP table."""
        upper = name.upper().strip()
        if upper in ABAP_KEYWORDS:
            return False
        if len(upper) < 3 or len(upper) > 30:
            return False
        # Must start with a letter
        if not upper[0].isalpha():
            return False
        # Known tables always valid
        if upper in KNOWN_SAP_TABLES:
            return True
        # Z/Y custom tables
        if upper.startswith(("Z", "Y")) and len(upper) >= 4:
            return True
        # Standard SAP tables (heuristic: all-caps, no underscores except known patterns)
        if upper.isalpha() and upper.isupper() and len(upper) <= 12:
            return True
        # Tables with underscores (like BNK_BATCH_HEADER)
        if "_" in upper and all(p.isalpha() or p.isdigit() for p in upper.split("_")):
            return True
        return False

    def parse_file(self, filepath: Path) -> dict[str, Any]:
        """Parse a single ABAP file and return all dependencies."""
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {"tables_read": [], "fields_read": [], "fms_called": [],
                    "tables_written": [], "inherits": [], "interfaces": [],
                    "is_badi_impl": False, "badi_interface": None}

        # Strip comments
        lines = []
        for line in source.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("*") or stripped.startswith('"'):
                continue
            # Inline comments after "
            idx = line.find('"')
            if idx > 0:
                line = line[:idx]
            lines.append(line)
        clean_source = "\n".join(lines)

        tables_read = set()
        fields_read: list[tuple[str, list[str]]] = []
        fms_called = set()
        tables_written = set()
        inherits = set()
        interfaces = set()
        badi_interface = None

        # SELECT → tables + fields
        for m in self.RE_SELECT.finditer(clean_source):
            table = m.group("table").strip().upper()
            if self._is_valid_table(table):
                tables_read.add(table)
                # Parse field list
                raw_fields = m.group("fields").strip()
                if raw_fields != "*":
                    flds = [f.strip().upper() for f in re.split(r'[\s,]+', raw_fields)
                            if f.strip() and f.strip().upper() not in ABAP_KEYWORDS
                            and f.strip() != "*"]
                    # Handle table~field syntax
                    clean_flds = []
                    for f in flds:
                        if "~" in f:
                            parts = f.split("~")
                            if len(parts) == 2:
                                clean_flds.append(parts[1])
                        else:
                            clean_flds.append(f)
                    if clean_flds:
                        fields_read.append((table, clean_flds))

        # CALL FUNCTION
        for m in self.RE_CALL_FM.finditer(clean_source):
            fm = m.group("fm_name").strip().upper()
            if len(fm) >= 3:
                fms_called.add(fm)

        # INSERT/MODIFY/UPDATE/DELETE
        for m in self.RE_WRITE.finditer(clean_source):
            table = m.group("table").strip().upper()
            if self._is_valid_table(table):
                tables_written.add(table)

        # INHERITING FROM
        for m in self.RE_INHERITS.finditer(clean_source):
            inherits.add(m.group("super").strip().upper())

        # INTERFACES
        for m in self.RE_INTERFACE.finditer(clean_source):
            intf = m.group("intf").strip().upper()
            interfaces.add(intf)
            if intf.startswith("IF_EX_"):
                badi_interface = intf

        is_badi = bool(self.RE_BADI_CLASS.search(clean_source)) or badi_interface is not None

        return {
            "tables_read": sorted(tables_read),
            "fields_read": [(t, sorted(set(fs))) for t, fs in fields_read],
            "fms_called": sorted(fms_called),
            "tables_written": sorted(tables_written),
            "inherits": sorted(inherits),
            "interfaces": sorted(interfaces),
            "is_badi_impl": is_badi,
            "badi_interface": badi_interface,
        }

    def parse_directory(self, dir_path: Path) -> dict[str, dict]:
        """Parse all .abap files in a directory tree. Returns {filepath: deps}."""
        results = {}
        abap_files = sorted(dir_path.rglob("*.abap"))
        for f in abap_files:
            deps = self.parse_file(f)
            # Only include files with actual dependencies found
            if any(deps[k] for k in ["tables_read", "fms_called", "tables_written",
                                      "inherits", "interfaces"]) or deps["is_badi_impl"]:
                results[str(f.relative_to(dir_path))] = deps
        return results

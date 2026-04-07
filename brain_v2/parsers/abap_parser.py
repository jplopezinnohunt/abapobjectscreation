"""
Brain v2 ABAP Dependency Parser — Static analysis of ABAP source files.
Extracts the 6 patterns that account for 90%+ of dependencies.
Source: BRAIN_V2_ARCHITECTURE.md Section B.1
"""

import re
from pathlib import Path


# ABAP keywords that look like table names in WRITE patterns but aren't
ABAP_KEYWORDS = {
    'INTO', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'TABLE', 'APPENDING',
    'CORRESPONDING', 'FIELDS', 'OF', 'UP', 'TO', 'ROWS', 'ORDER', 'BY',
    'GROUP', 'HAVING', 'FOR', 'ALL', 'ENTRIES', 'IN', 'INNER', 'LEFT',
    'RIGHT', 'OUTER', 'JOIN', 'ON', 'AS', 'SINGLE', 'DISTINCT',
    'DATA', 'TYPE', 'REF', 'VALUE', 'LIKE', 'BEGIN', 'END',
    'IF', 'ELSE', 'ENDIF', 'CASE', 'WHEN', 'ENDCASE',
    'LOOP', 'AT', 'ENDLOOP', 'DO', 'ENDDO', 'WHILE', 'ENDWHILE',
    'METHOD', 'ENDMETHOD', 'CLASS', 'ENDCLASS', 'FORM', 'ENDFORM',
    'FUNCTION', 'ENDFUNCTION', 'MODULE', 'ENDMODULE',
    'CLEAR', 'FREE', 'REFRESH', 'MOVE', 'WRITE', 'APPEND', 'READ',
    'SORT', 'DELETE', 'COLLECT', 'DESCRIBE', 'SPLIT', 'CONCATENATE',
    'CONDENSE', 'TRANSLATE', 'REPLACE', 'SHIFT', 'OVERLAY',
    'PERFORM', 'CALL', 'RAISE', 'MESSAGE', 'RETURN', 'EXIT',
    'CHECK', 'CONTINUE', 'STOP', 'REJECT',
    'TRY', 'CATCH', 'ENDTRY', 'CLEANUP',
    'ASSIGN', 'UNASSIGN', 'EXPORT', 'IMPORT', 'SUBMIT',
    'COMMIT', 'ROLLBACK', 'WORK', 'TASK',
    'EXPORTING', 'IMPORTING', 'CHANGING', 'EXCEPTIONS', 'TABLES',
    'NEW', 'CAST', 'CONV', 'COND', 'SWITCH', 'REDUCE',
    'SY', 'SPACE', 'ABAP_TRUE', 'ABAP_FALSE', 'ABAP_UNDEFINED',
    'IS', 'INITIAL', 'BOUND', 'ASSIGNED', 'SUPPLIED', 'REQUESTED',
    'LINE', 'LINES', 'INDEX', 'SCREEN', 'AUTHORITY',
}

# Minimum length for a table name to be valid
MIN_TABLE_NAME_LEN = 3


class ABAPDependencyParser:
    """Extract dependencies from ABAP source code files."""

    # Pattern 1: SELECT statements -> READS_TABLE + READS_FIELD
    # Handles: SELECT SINGLE f1 f2 FROM table, SELECT f1~f2 FROM table AS a JOIN table2 AS b
    RE_SELECT = re.compile(
        r'SELECT\s+(?:SINGLE\s+)?'
        r'(?P<fields>[\w\s,*~@]+?)\s+'
        r'FROM\s+(?P<from_clause>[^\n.;]+)',
        re.IGNORECASE
    )

    # Sub-pattern: extract table aliases from FROM clause
    # Matches: table_name AS alias, table_name alias (without AS)
    RE_FROM_ALIAS = re.compile(
        r'(?P<table>[A-Za-z/]\w{2,30})\s+AS\s+(?P<alias>\w+)',
        re.IGNORECASE
    )

    # Pattern 2: CALL FUNCTION -> CALLS_FM
    RE_CALL_FM = re.compile(
        r"CALL\s+FUNCTION\s+'(?P<fm_name>[A-Z0-9_/]+)'",
        re.IGNORECASE
    )

    # Pattern 3: INSERT/MODIFY/UPDATE/DELETE -> WRITES_TABLE
    RE_WRITE = re.compile(
        r'(?:INSERT|MODIFY|UPDATE|DELETE)\s+(?:FROM\s+)?(?P<table>[A-Z]\w{2,30})\b',
        re.IGNORECASE
    )

    # Pattern 4: CLASS ... INHERITING FROM -> INHERITS_FROM
    RE_INHERITS = re.compile(
        r'CLASS\s+\w+\s+DEFINITION.*?INHERITING\s+FROM\s+(?P<super>\w+)',
        re.IGNORECASE | re.DOTALL
    )

    # Pattern 5: INTERFACES -> IMPLEMENTS_INTF
    RE_INTERFACE = re.compile(
        r'INTERFACES\s+(?P<intf>[A-Za-z]\w+)',
        re.IGNORECASE
    )

    # Pattern 6: BAdI implementation (naming convention YCL_IM_* or ZCL_IM_*)
    RE_BADI_IMPL = re.compile(
        r'CLASS\s+(?P<cls>[YZ]CL_IM_\w+)\s+DEFINITION',
        re.IGNORECASE
    )

    # Additional: TYPE REF TO -> class references (object creation)
    RE_TYPE_REF = re.compile(
        r'TYPE\s+REF\s+TO\s+(?P<cls>[A-Za-z]\w{2,40})',
        re.IGNORECASE
    )

    # Additional: CREATE OBJECT / NEW -> instantiation
    RE_CREATE = re.compile(
        r'(?:CREATE\s+OBJECT\s+\w+\s+TYPE\s+(?P<cls1>\w+)|'
        r'NEW\s+(?P<cls2>[a-z]\w{2,40})\s*\()',
        re.IGNORECASE
    )

    def _strip_comments(self, source: str) -> str:
        """Remove ABAP comment lines (starting with * or after \")."""
        lines = []
        for line in source.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('*'):
                continue
            # Remove inline comments after "
            quote_pos = line.find('"')
            if quote_pos >= 0:
                # But not inside strings (simplistic: check if odd number of single quotes before)
                before = line[:quote_pos]
                if before.count("'") % 2 == 0:
                    line = before
            lines.append(line)
        return '\n'.join(lines)

    def _is_valid_table(self, name: str) -> bool:
        """Check if a name could be a valid SAP table."""
        upper = name.upper()
        if upper in ABAP_KEYWORDS:
            return False
        if len(upper) < MIN_TABLE_NAME_LEN:
            return False
        if not re.match(r'^[A-Z/]', upper):
            return False
        # Filter out obvious non-tables
        if upper.startswith(('SY-', 'LV_', 'LS_', 'LT_', 'GV_', 'GS_', 'GT_',
                            'IV_', 'IS_', 'IT_', 'EV_', 'ES_', 'ET_', 'CV_',
                            'CS_', 'CT_', 'MV_', 'MS_', 'MT_', 'WA_', 'LO_',
                            'GO_', 'IO_', 'RV_', 'RS_', 'RT_')):
            return False
        return True

    def _parse_from_clause(self, from_clause: str) -> tuple:
        """Parse FROM clause to extract primary table and alias→table map.

        Returns (primary_table, alias_map) where alias_map maps alias→real_table.
        Handles: FROM table, FROM table AS a, FROM table AS a JOIN table2 AS b ON ...
        """
        alias_map = {}
        # Extract all aliased tables
        for m in self.RE_FROM_ALIAS.finditer(from_clause):
            alias_map[m.group('alias').upper()] = m.group('table').upper()

        # Extract the primary table (first word after FROM, before AS/JOIN/INTO/WHERE)
        primary_match = re.match(r'\s*(?P<table>[A-Za-z/]\w{2,30})', from_clause)
        primary_table = primary_match.group('table').upper() if primary_match else ""

        return primary_table, alias_map

    def _extract_fields_from_select(self, fields_str: str, table: str,
                                     alias_map: dict = None) -> list:
        """Parse field list from SELECT statement, resolving aliases."""
        fields = []
        alias_map = alias_map or {}
        if '*' in fields_str and '~' not in fields_str:
            return []  # SELECT * — we know the table but not specific fields

        # Handle tilde notation: alias~field or table~field
        for token in re.split(r'[\s,]+', fields_str):
            token = token.strip().lstrip('@')
            if not token:
                continue
            if '~' in token:
                parts = token.split('~')
                if len(parts) == 2 and parts[1]:
                    tbl_or_alias = parts[0].upper()
                    # Resolve alias to real table name
                    real_table = alias_map.get(tbl_or_alias, tbl_or_alias)
                    fields.append((real_table, parts[1].upper()))
            elif self._is_valid_table(token):
                # Plain field name — associate with the FROM table
                fields.append((table.upper(), token.upper()))
        return fields

    def parse_source(self, source: str) -> dict:
        """Parse ABAP source text and return all dependencies."""
        clean = self._strip_comments(source)

        # Tables read via SELECT
        tables_read = set()
        fields_read = set()
        for m in self.RE_SELECT.finditer(clean):
            from_clause = m.group('from_clause')
            primary_table, alias_map = self._parse_from_clause(from_clause)
            if not self._is_valid_table(primary_table):
                continue
            # Add primary table and all joined tables
            tables_read.add(primary_table)
            for real_table in alias_map.values():
                if self._is_valid_table(real_table):
                    tables_read.add(real_table)
            # Extract fields with alias resolution
            for tbl, fld in self._extract_fields_from_select(
                    m.group('fields'), primary_table, alias_map):
                if (self._is_valid_table(fld) or len(fld) >= 3) and self._is_valid_table(tbl):
                    fields_read.add((tbl, fld))

        # FMs called
        fms_called = set()
        for m in self.RE_CALL_FM.finditer(clean):
            fms_called.add(m.group('fm_name').upper())

        # Tables written
        tables_written = set()
        for m in self.RE_WRITE.finditer(clean):
            table = m.group('table')
            if self._is_valid_table(table):
                tables_written.add(table.upper())

        # Inheritance
        inherits = set()
        for m in self.RE_INHERITS.finditer(clean):
            inherits.add(m.group('super').upper())

        # Interfaces
        interfaces = set()
        for m in self.RE_INTERFACE.finditer(clean):
            intf = m.group('intf')
            if not intf.upper().startswith(('LV_', 'LS_', 'LT_')):
                interfaces.add(intf.upper())

        # BAdI implementation
        is_badi_impl = bool(self.RE_BADI_IMPL.search(clean))

        # Class references (TYPE REF TO)
        class_refs = set()
        for m in self.RE_TYPE_REF.finditer(clean):
            cls = m.group('cls').upper()
            if cls not in ABAP_KEYWORDS and len(cls) > 3:
                class_refs.add(cls)

        # Object creation
        for m in self.RE_CREATE.finditer(clean):
            cls = (m.group('cls1') or m.group('cls2') or '').upper()
            if cls and cls not in ABAP_KEYWORDS and len(cls) > 3:
                class_refs.add(cls)

        return {
            'tables_read': sorted(tables_read),
            'fields_read': sorted(fields_read),
            'fms_called': sorted(fms_called),
            'tables_written': sorted(tables_written),
            'inherits': sorted(inherits),
            'interfaces': sorted(interfaces),
            'is_badi_impl': is_badi_impl,
            'class_refs': sorted(class_refs),
        }

    def parse_file(self, filepath: Path) -> dict:
        """Parse a single ABAP file."""
        try:
            source = filepath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return self._empty_result()
        if len(source.strip()) < 10:
            return self._empty_result()
        return self.parse_source(source)

    def parse_class_directory(self, class_dir: Path) -> dict:
        """Parse all methods/includes of an ABAP class directory."""
        merged = {
            'tables_read': set(), 'fields_read': set(), 'fms_called': set(),
            'tables_written': set(), 'inherits': set(), 'interfaces': set(),
            'is_badi_impl': False, 'class_refs': set(),
            'methods': {}, 'file_count': 0, 'total_lines': 0,
        }

        for abap_file in sorted(class_dir.glob('*.abap')):
            deps = self.parse_file(abap_file)
            method_name = abap_file.stem
            merged['methods'][method_name] = deps
            merged['file_count'] += 1
            try:
                merged['total_lines'] += sum(1 for _ in open(abap_file, encoding='utf-8', errors='replace'))
            except Exception:
                pass

            for key in ['tables_read', 'fms_called', 'tables_written',
                        'inherits', 'interfaces', 'class_refs']:
                merged[key].update(deps[key])
            merged['fields_read'].update(tuple(f) for f in deps['fields_read'])
            if deps['is_badi_impl']:
                merged['is_badi_impl'] = True

        # Convert sets to sorted lists
        for key in ['tables_read', 'fms_called', 'tables_written',
                    'inherits', 'interfaces', 'class_refs']:
            merged[key] = sorted(merged[key])
        merged['fields_read'] = sorted(merged['fields_read'])

        return merged

    @staticmethod
    def _empty_result():
        return {
            'tables_read': [], 'fields_read': [], 'fms_called': [],
            'tables_written': [], 'inherits': [], 'interfaces': [],
            'is_badi_impl': False, 'class_refs': [],
        }

"""
Backfill `domain_axes` (3-axis taxonomy {functional, module, process}) on:
  - feedback_rules.json (93 rules, 19 already tagged as `domain`)
  - claims.json (54 claims, all with legacy `domain` string)
  - incidents.json (5 records, all with legacy `domain` string + secondary_domains)

Inference order (first match wins):
  1. Keyword match on rule/claim/incident text (most specific)
  2. Related object lookup via brain_state.json objects[X].domain
  3. Legacy `domain` string mapped to functional axis + module inferred

Does NOT drop the legacy `domain` field — CP-002. Adds `domain_axes` next to it.
Rules that already have `domain` as 3-axis object are migrated to `domain_axes`
and the old `domain` field is removed ONLY on rules to resolve the schema
inconsistency (these were added this same session; no traceability loss).

Usage: python brain_v2/scripts/backfill_domain_axes.py
"""
import json
import re
from pathlib import Path
from collections import Counter

PROJECT = Path(__file__).parent.parent.parent
BRAIN_V2 = PROJECT / "brain_v2"


# ----- Keyword -> 3-axis domain mapping (inspired by session_activation_hints) ---

KEYWORD_DOMAIN_MAP = [
    # (regex pattern, {functional, module, process})
    (r'\bBCM\b|dual.control|signatory|CRUSR|CHUSR|BNK_BATCH|90000003|90000004|90000005',
     {'functional': ['BCM', 'Treasury'], 'module': ['FI', 'PD'], 'process': ['T2R']}),
    (r'\bYRGGBS00\b|UXR1|UXR2|XREF|GB90[135]|GB92[12]|substitution',
     {'functional': ['Treasury', 'FI'], 'module': ['FI'], 'process': ['T2R', 'B2R']}),
    (r'\bYTR[0-3]\b|YTBAE|YTBAM|YTBAI|YFI_BANK|Maputo|MZN\b|MODE.E.BDC|bank.recon|field.office',
     {'functional': ['Treasury'], 'module': ['FI'], 'process': ['T2R']}),
    (r'FEBEP|FEBRE|FEBKO|FEBAN|MT940|EBS|Electronic.Bank|FF_5|bank.statement',
     {'functional': ['Treasury'], 'module': ['FI'], 'process': ['T2R']}),
    (r'T012\b|T012K|house.bank|FBZP|HBKID|BKVID|IBAN|TIBAN',
     {'functional': ['Treasury'], 'module': ['FI'], 'process': ['T2R']}),
    (r'F110|REGUH|REGUP|PAYR|DMEE|payment.run|payment.method',
     {'functional': ['Payment', 'Treasury'], 'module': ['FI'], 'process': ['T2R', 'P2P']}),
    (r'PRRW|PR02|PTRV|LHRTS|travel|busa.*derivation|trip',
     {'functional': ['Travel'], 'module': ['TV', 'FI', 'HCM'], 'process': ['H2R']}),
    (r'\bHCM\b|payroll|infotype|PA00\d{2}|HRP1000|HRP1001|PERNR|employee',
     {'functional': ['HCM'], 'module': ['HCM', 'PD'], 'process': ['H2R']}),
    (r'BSEG\b|BSIS\b|BSAS\b|BSIK|BSAK|BSID|BSAD|BKPF|SKA1|SKAT|SKB1\b|GL.account',
     {'functional': ['FI'], 'module': ['FI'], 'process': ['B2R', 'P2P', 'T2R']}),
    (r'\bFM\b|FMIFIIT|budget|fund|PSM|WRTTP|commitment',
     {'functional': ['PSM'], 'module': ['FM'], 'process': ['B2R']}),
    (r'PRPS|POSID|PSPNR|WBS|project.master|PROJ\b',
     {'functional': ['PS', 'PSM'], 'module': ['PS'], 'process': ['B2R']}),
    (r'vendor|LFA1|LFB1|customer|KNA1|KNB1|business.partner|\bBP\b|KTOKK',
     {'functional': ['BusinessPartner', 'FI'], 'module': ['FI'], 'process': ['P2D']}),
    (r'EKKO|EKPO|ESSR|MIRO|MIGO|purchase.order|procurement|GR.IR',
     {'functional': ['Procurement'], 'module': ['MM'], 'process': ['P2P']}),
    (r'\bCTS\b|transport|E070\b|E071\b|E07T|TMSCSYS|SE09|SE10',
     {'functional': ['Transport_Intelligence'], 'module': ['CTS', 'BASIS'], 'process': []}),
    (r'\bRFC\b|IDoc|EDIDC|ICFSERVICE|interface|DBCON|MuleSoft|BizTalk|\.NET.Connector',
     {'functional': ['Integration'], 'module': ['BASIS'], 'process': []}),
    (r'ST22|SU53|SM21|dump|\bauth.*failure|SHORTDUMP|RABAX|TIME_OUT',
     {'functional': ['Support'], 'module': ['BASIS'], 'process': []}),
    (r'ADT\b|RPY_PROGRAM|ABAP.Development.Tools|SNC|SSO.*Kerberos',
     {'functional': ['Support'], 'module': ['BASIS', 'CTS'], 'process': []}),
    (r'RFC_READ_TABLE|RFC_ABAP_INSTALL|BAPI|extraction|Gold.DB|BSEG.*celonis|checkpoint',
     {'functional': ['*'], 'module': ['*'], 'process': ['*']}),
    (r'session|retro|PMO|blind.spot|brain|core.principle|feedback|knowledge',
     {'functional': ['*'], 'module': ['*'], 'process': ['*']}),
]

# Legacy domain string -> 3-axis mapping
LEGACY_DOMAIN_MAP = {
    'Travel': {'functional': ['Travel'], 'module': ['TV', 'FI', 'HCM'], 'process': ['H2R']},
    'FI': {'functional': ['FI'], 'module': ['FI'], 'process': ['B2R', 'P2P', 'T2R']},
    'HCM': {'functional': ['HCM'], 'module': ['HCM', 'PD'], 'process': ['H2R']},
    'Treasury': {'functional': ['Treasury'], 'module': ['FI'], 'process': ['T2R']},
    'PSM': {'functional': ['PSM'], 'module': ['FM'], 'process': ['B2R']},
    'BCM': {'functional': ['BCM', 'Treasury'], 'module': ['FI', 'PD'], 'process': ['T2R']},
    'Payment': {'functional': ['Payment', 'Treasury'], 'module': ['FI'], 'process': ['T2R', 'P2P']},
    'BusinessPartner': {'functional': ['BusinessPartner', 'FI'], 'module': ['FI'], 'process': ['P2D']},
    'Procurement': {'functional': ['Procurement'], 'module': ['MM'], 'process': ['P2P']},
    'Transport_Intelligence': {'functional': ['Transport_Intelligence'], 'module': ['CTS', 'BASIS'], 'process': []},
    'Integration': {'functional': ['Integration'], 'module': ['BASIS'], 'process': []},
    'Support': {'functional': ['Support'], 'module': ['BASIS'], 'process': []},
    'BI': {'functional': ['Integration'], 'module': ['BI'], 'process': []},
    'CTS': {'functional': ['Transport_Intelligence'], 'module': ['CTS'], 'process': []},
    'CUSTOM': {'functional': ['*'], 'module': ['CUSTOM'], 'process': []},
    'SAP_STANDARD': {'functional': ['*'], 'module': ['SAP_STANDARD'], 'process': []},
    'DATA_MODEL': {'functional': ['*'], 'module': ['DATA_MODEL'], 'process': []},
    'BASIS': {'functional': ['Support', 'Integration'], 'module': ['BASIS'], 'process': []},
    'TV': {'functional': ['Travel'], 'module': ['TV'], 'process': ['H2R']},
    'MM': {'functional': ['Procurement'], 'module': ['MM'], 'process': ['P2P']},
    'PS': {'functional': ['PS'], 'module': ['PS'], 'process': ['B2R']},
    'Runtime Performance': {'functional': ['Support'], 'module': ['BASIS'], 'process': []},
    'Bank Reconciliation': {'functional': ['Treasury'], 'module': ['FI'], 'process': ['T2R']},
    'ABAP Custom': {'functional': ['*'], 'module': ['CUSTOM'], 'process': []},
}


def infer_axes_from_text(text: str) -> dict:
    """Return the first matching domain axes set, or None."""
    if not text:
        return None
    for pattern, axes in KEYWORD_DOMAIN_MAP:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return axes
    return None


def infer_axes_from_legacy_domain(legacy: str, secondary: list = None) -> dict:
    """Merge primary + secondary legacy domain strings into 3-axis."""
    primary = LEGACY_DOMAIN_MAP.get(legacy, None)
    if not primary:
        # Split on '/' (e.g., "Treasury / Bank Reconciliation / ABAP Custom / Runtime Performance")
        parts = [p.strip() for p in re.split(r'[\/,]', legacy)]
        for p in parts:
            if p in LEGACY_DOMAIN_MAP:
                primary = LEGACY_DOMAIN_MAP[p]
                break
    if not primary:
        return {'functional': [], 'module': [], 'process': []}
    result = {k: list(v) for k, v in primary.items()}
    if secondary:
        for s in secondary:
            if s in LEGACY_DOMAIN_MAP:
                sec = LEGACY_DOMAIN_MAP[s]
                for axis in ('functional', 'module', 'process'):
                    for val in sec[axis]:
                        if val not in result[axis] and val != '*':
                            result[axis].append(val)
    return result


def merge_axes(a: dict, b: dict) -> dict:
    """Merge two 3-axis dicts, deduping values."""
    if not a:
        return b
    if not b:
        return a
    out = {}
    for axis in ('functional', 'module', 'process'):
        merged = list(a.get(axis, []))
        for val in b.get(axis, []):
            if val not in merged:
                merged.append(val)
        out[axis] = merged
    return out


# ----- Main backfill ------------------------------------------------------

def backfill_rules():
    path = BRAIN_V2 / "agent_rules" / "feedback_rules.json"
    with open(path, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    tagged_before = sum(1 for r in rules if 'domain_axes' in r)
    migrated = 0
    inferred = 0
    global_tagged = 0

    for r in rules:
        if 'domain_axes' in r:
            continue
        # Migrate old `domain` (3-axis object) -> domain_axes
        if isinstance(r.get('domain'), dict):
            r['domain_axes'] = r['domain']
            del r['domain']
            migrated += 1
            continue
        # Infer from rule text
        text = ' '.join(filter(None, [r.get('id', ''), r.get('rule', ''), r.get('why', ''), r.get('how_to_apply', '')]))
        axes = infer_axes_from_text(text)
        if axes:
            r['domain_axes'] = axes
            inferred += 1
            if axes.get('functional') == ['*']:
                global_tagged += 1

    tagged_after = sum(1 for r in rules if 'domain_axes' in r)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    return {'before': tagged_before, 'after': tagged_after, 'migrated': migrated,
            'inferred': inferred, 'global_tagged': global_tagged, 'total': len(rules)}


def backfill_claims():
    path = BRAIN_V2 / "claims" / "claims.json"
    with open(path, 'r', encoding='utf-8') as f:
        claims = json.load(f)

    tagged_before = sum(1 for c in claims if 'domain_axes' in c)
    added = 0

    for c in claims:
        if 'domain_axes' in c:
            continue
        legacy = c.get('domain', '')
        # Try keyword match on claim text first (more specific than legacy)
        axes = infer_axes_from_text(c.get('claim', ''))
        if not axes:
            axes = infer_axes_from_legacy_domain(legacy)
        # Merge with related_objects hints (lightweight heuristic)
        related = c.get('related_objects', [])
        for obj in related:
            obj_axes = infer_axes_from_text(obj)
            if obj_axes:
                axes = merge_axes(axes, obj_axes)
        c['domain_axes'] = axes
        added += 1

    tagged_after = sum(1 for c in claims if 'domain_axes' in c)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)
    return {'before': tagged_before, 'after': tagged_after, 'added': added, 'total': len(claims)}


def backfill_incidents():
    path = BRAIN_V2 / "incidents" / "incidents.json"
    with open(path, 'r', encoding='utf-8') as f:
        incidents = json.load(f)

    tagged_before = sum(1 for i in incidents if 'domain_axes' in i)
    added = 0

    for inc in incidents:
        if 'domain_axes' in inc:
            continue
        legacy = inc.get('domain', '')
        secondary = inc.get('secondary_domains', []) or []
        axes = infer_axes_from_legacy_domain(legacy, secondary)
        # Also enrich from title + root_cause_summary
        text = ' '.join(filter(None, [inc.get('title', ''), inc.get('root_cause_summary', ''), inc.get('scenario', '')]))
        text_axes = infer_axes_from_text(text)
        if text_axes:
            axes = merge_axes(axes, text_axes)
        inc['domain_axes'] = axes
        added += 1

    tagged_after = sum(1 for i in incidents if 'domain_axes' in i)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(incidents, f, indent=2, ensure_ascii=False)
    return {'before': tagged_before, 'after': tagged_after, 'added': added, 'total': len(incidents)}


def main():
    print("=" * 60)
    print("DOMAIN AXES BACKFILL — Rules + Claims + Incidents")
    print("=" * 60)

    r = backfill_rules()
    print(f"\n[RULES]   {r['before']:>3} -> {r['after']:>3} / {r['total']:>3}   "
          f"(migrated={r['migrated']}, inferred={r['inferred']}, global={r['global_tagged']})")
    pct_rules = round(100 * r['after'] / r['total'], 1)
    print(f"          Coverage: {pct_rules}%")

    c = backfill_claims()
    print(f"\n[CLAIMS]  {c['before']:>3} -> {c['after']:>3} / {c['total']:>3}   (added={c['added']})")
    pct_claims = round(100 * c['after'] / c['total'], 1)
    print(f"          Coverage: {pct_claims}%")

    i = backfill_incidents()
    print(f"\n[INCIDENTS] {i['before']:>3} -> {i['after']:>3} / {i['total']:>3}   (added={i['added']})")
    pct_inc = round(100 * i['after'] / i['total'], 1)
    print(f"            Coverage: {pct_inc}%")

    print("\n" + "=" * 60)
    overall = r['after'] + c['after'] + i['after']
    total = r['total'] + c['total'] + i['total']
    print(f"OVERALL: {overall}/{total} ({round(100*overall/total,1)}%) nodes have domain_axes")
    print("=" * 60)


if __name__ == '__main__':
    main()

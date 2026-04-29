"""
Apply the 'creation model' to ALL 9 UNESCO institutes:
1. Find transports with institute name in text (E07T)
2. Enrich with E070 (date, user, function, status)
3. Identify creation cluster (first concentrated burst of institute-labeled transports)
4. Identify lead owner + all team members
5. Extract E071 for each creation transport

Model based on MGIE (2013): D01K9A00FB + 15 related transports by M_SPRONK + team.
"""
import sys
import json
import time
from pathlib import Path
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

INSTITUTES = ['UNES', 'IBE', 'IIEP', 'UBO', 'UIL', 'UIS', 'ICTP', 'ICBA', 'MGIE', 'STEM']


def find_institute_transports(guard, institute):
    """Query E07T for %institute% text, enrich with E070."""
    # Some institutes use variants in text: ICBA also "ICBAE", MGIE also "MGIEP"
    variants = {
        'UNES': ['UNES', 'UNESCO'],  # UNES root — every transport may mention it
        'IBE': ['IBE'],
        'IIEP': ['IIEP'],
        'UBO': ['UBO'],
        'UIL': ['UIL'],
        'UIS': ['UIS'],
        'ICTP': ['ICTP'],
        'ICBA': ['ICBA'],
        'MGIE': ['MGIE', 'MGIEP'],
        'STEM': ['STEM'],
    }
    vars = variants.get(institute, [institute])
    all_trs = {}
    for v in vars:
        res = guard.call('RFC_READ_TABLE', QUERY_TABLE='E07T',
                         FIELDS=[{'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'AS4TEXT'}],
                         OPTIONS=[{'TEXT': f"AS4TEXT LIKE '%{v}%'"}],
                         DELIMITER='|', ROWCOUNT=2000)
        for d in res.get('DATA', []):
            wa = d['WA'].split('|', 1)
            all_trs[wa[0].strip()] = wa[1].strip() if len(wa) > 1 else ''
    return all_trs


def enrich_metadata(guard, trkorrs):
    """Batch query E070 for date, user, function."""
    result = {}
    for tr in trkorrs:
        r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E070',
                       FIELDS=[{'FIELDNAME': 'AS4DATE'}, {'FIELDNAME': 'AS4USER'},
                               {'FIELDNAME': 'TRFUNCTION'}, {'FIELDNAME': 'TRSTATUS'},
                               {'FIELDNAME': 'STRKORR'}],
                       OPTIONS=[{'TEXT': f"TRKORR = '{tr}'"}],
                       DELIMITER='|', ROWCOUNT=1)
        if r.get('DATA'):
            wa = [x.strip() for x in r['DATA'][0]['WA'].split('|')]
            result[tr] = {'date': wa[0], 'user': wa[1], 'fn': wa[2],
                          'st': wa[3], 'parent': wa[4]}
    return result


def identify_creation_cluster(transports):
    """Find the earliest concentrated burst (first 6 months from earliest)."""
    if not transports:
        return []
    sorted_trs = sorted(transports.items(), key=lambda x: x[1].get('date', '99999999'))
    earliest = sorted_trs[0][1].get('date', '')
    if not earliest or len(earliest) != 8:
        return list(transports.keys())
    # Window: earliest → earliest + 6 months
    y = int(earliest[:4]); m = int(earliest[4:6])
    end_y, end_m = (y + 1, m - 6) if m > 6 else (y, m + 6)
    end = f'{end_y:04d}{end_m:02d}31'
    window = [tr for tr, md in transports.items()
              if md.get('date', '') and earliest <= md['date'] <= end]
    return window


def analyze_institute(guard, institute, max_trs=120):
    print(f'\n=== {institute} ===')
    texts = find_institute_transports(guard, institute)
    print(f'  transports with {institute} in text: {len(texts)}')
    if not texts:
        return None

    # Cap to avoid blowing up for UNES/UNESCO (thousands)
    # Pick the earliest ones
    if len(texts) > max_trs:
        # Get dates for all, sort, pick earliest max_trs
        dates = enrich_metadata(guard, list(texts)[:min(1000, len(texts))])
        sorted_trs = sorted(dates.keys(), key=lambda t: dates[t].get('date', '99999999'))[:max_trs]
        texts = {t: texts[t] for t in sorted_trs}
        md = {t: dates[t] for t in sorted_trs if t in dates}
    else:
        md = enrich_metadata(guard, list(texts))

    # Combine
    transports = {}
    for tr in texts:
        info = md.get(tr, {})
        info['text'] = texts[tr]
        transports[tr] = info

    # Identify creation cluster
    creation = identify_creation_cluster(transports)
    if not creation:
        return None

    # Lead owner + team
    users = Counter(transports[tr].get('user', '') for tr in creation if transports[tr].get('user'))
    lead = users.most_common(1)[0] if users else ('unknown', 0)

    dates = [transports[tr].get('date', '') for tr in creation if transports[tr].get('date')]
    dates.sort()

    print(f'  creation cluster size: {len(creation)}')
    print(f'  date range: {dates[0] if dates else "?"} → {dates[-1] if dates else "?"}')
    print(f'  lead owner: {lead[0]} ({lead[1]} transports)')
    print(f'  team: {dict(users.most_common())}')

    return {
        'institute': institute,
        'total_text_transports': len(texts),
        'creation_cluster_trs': creation,
        'date_start': dates[0] if dates else None,
        'date_end': dates[-1] if dates else None,
        'lead_owner': lead[0],
        'lead_owner_transports': lead[1],
        'team': dict(users.most_common()),
        'transport_details': {tr: transports[tr] for tr in creation},
    }


def main():
    print('Connecting D01...')
    guard = get_connection('D01')

    results = {}
    for inst in INSTITUTES:
        try:
            r = analyze_institute(guard, inst)
            if r:
                results[inst] = r
        except Exception as e:
            print(f'  ERR: {e}')

    guard.close()

    with open(HERE / 'all_institutes_creation.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: all_institutes_creation.json')

    # Summary table
    print('\n=== Summary ===')
    print(f'{"Institute":10s} {"Cluster":>7s} {"Start":>10s} {"End":>10s} {"Lead":>14s} {"Team":>5s}')
    for inst in INSTITUTES:
        if inst in results:
            r = results[inst]
            print(f'{inst:10s} {len(r["creation_cluster_trs"]):7d} {r["date_start"] or "-":>10s} {r["date_end"] or "-":>10s} {r["lead_owner"]:>14s} {len(r["team"]):5d}')


if __name__ == '__main__':
    main()

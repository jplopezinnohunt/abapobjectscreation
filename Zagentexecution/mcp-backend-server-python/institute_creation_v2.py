"""
v2: find creation of each BUKRS via multiple approaches.
Separate IN+LIKE query issue; add fallbacks for IBE/UBO/UIL/UIS.
"""
import sys
import json
import datetime
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

INSTITUTES = ['UNES', 'IBE', 'IIEP', 'UBO', 'UIL', 'UIS', 'ICTP', 'ICBA', 'MGIE', 'STEM']


def find_t001(guard, bukrs):
    r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                   FIELDS=[{'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'TABKEY'}],
                   OPTIONS=[{'TEXT': f"OBJNAME = 'T001' AND TABKEY LIKE '%{bukrs}%'"}],
                   DELIMITER='|', ROWCOUNT=100)
    trs = set()
    for d in r.get('DATA', []):
        wa = d['WA'].split('|')
        tr = wa[0].strip()
        tk = wa[1].strip() if len(wa) > 1 else ''
        if len(tk) >= 7 and tk[3:7] == bukrs:
            trs.add(tr)
    return trs


def find_via_table(guard, bukrs, objname, position=3, length=4):
    """Fallback: search any BUKRS-keyed table."""
    r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                   FIELDS=[{'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'TABKEY'}],
                   OPTIONS=[{'TEXT': f"OBJNAME = '{objname}' AND TABKEY LIKE '%{bukrs}%'"}],
                   DELIMITER='|', ROWCOUNT=100)
    trs = set()
    for d in r.get('DATA', []):
        wa = d['WA'].split('|')
        tr = wa[0].strip()
        tk = wa[1].strip() if len(wa) > 1 else ''
        if len(tk) >= position + length and tk[position:position+length] == bukrs:
            trs.add(tr)
    return trs


def get_e070(guard, trs):
    md = {}
    for tr in trs:
        r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E070',
                       FIELDS=[{'FIELDNAME': 'AS4DATE'}, {'FIELDNAME': 'AS4USER'},
                               {'FIELDNAME': 'TRFUNCTION'}, {'FIELDNAME': 'TRSTATUS'},
                               {'FIELDNAME': 'STRKORR'}],
                       OPTIONS=[{'TEXT': f"TRKORR = '{tr}'"}],
                       DELIMITER='|', ROWCOUNT=1)
        if r.get('DATA'):
            wa = [x.strip() for x in r['DATA'][0]['WA'].split('|')]
            md[tr] = {'date': wa[0], 'user': wa[1], 'fn': wa[2], 'st': wa[3], 'parent': wa[4]}
    return md


def get_text(guard, tr):
    r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E07T',
                   FIELDS=[{'FIELDNAME': 'AS4TEXT'}],
                   OPTIONS=[{'TEXT': f"TRKORR = '{tr}' AND LANGU = 'E'"}],
                   DELIMITER='|', ROWCOUNT=1)
    if r.get('DATA'):
        return r['DATA'][0]['WA'].strip()
    return ''


def find_cluster(guard, bukrs, creation_date, window_days=180):
    """All transports with BUKRS in TABKEY in date window."""
    if not creation_date or len(creation_date) != 8:
        return {}
    y = int(creation_date[:4]); m = int(creation_date[4:6]); d = int(creation_date[6:8])
    dt0 = datetime.date(y, m, d)
    start = (dt0 - datetime.timedelta(days=window_days)).strftime('%Y%m%d')
    end = (dt0 + datetime.timedelta(days=window_days)).strftime('%Y%m%d')

    # Single-query LIKE filter (no IN combined)
    r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                   FIELDS=[{'FIELDNAME': 'TRKORR'}],
                   OPTIONS=[{'TEXT': f"TABKEY LIKE '%{bukrs}%'"}],
                   DELIMITER='|', ROWCOUNT=30000)
    trs = {d['WA'].strip() for d in r.get('DATA', [])}
    md = get_e070(guard, trs)
    return {t: md[t] for t in md if md[t].get('date') and start <= md[t]['date'] <= end}


def analyze(guard, bukrs):
    print(f'\n=== {bukrs} ===')
    trs = find_t001(guard, bukrs)
    if not trs:
        # Fallbacks: try T001Q, then TKA02 (CO area assignment)
        for fallback in ['T001Q', 'T001A', 'TKA02', 'TKA01', 'T012', 'SKB1']:
            trs = find_via_table(guard, bukrs, fallback)
            if trs:
                print(f'  T001 not found; using {fallback} as creation anchor')
                break
    if not trs:
        print(f'  No creation anchor found for {bukrs}')
        return None
    md = get_e070(guard, trs)
    if not md:
        return None
    sorted_trs = sorted(md.items(), key=lambda x: x[1].get('date', '99999999'))
    creation_tr, creation_md = sorted_trs[0]
    creation_text = get_text(guard, creation_tr)
    print(f'  Earliest anchor: {creation_tr} on {creation_md.get("date")} by {creation_md.get("user")}')
    print(f'  Text: {creation_text[:80]}')

    # Cluster
    cluster = find_cluster(guard, bukrs, creation_md.get('date'))
    print(f'  Cluster ±180 days: {len(cluster)}')

    users = Counter(cluster[t].get('user', '') for t in cluster if cluster[t].get('user'))
    lead = users.most_common(1)[0] if users else ('unknown', 0)
    print(f'  Lead: {lead[0]} ({lead[1]} transports)')
    print(f'  Team: {dict(users.most_common(6))}')

    return {
        'BUKRS': bukrs,
        'creation_transport': creation_tr,
        'creation_date': creation_md.get('date'),
        'creation_user': creation_md.get('user'),
        'creation_text': creation_text,
        'cluster_size': len(cluster),
        'lead_owner': lead[0],
        'lead_transport_count': lead[1],
        'team': dict(users.most_common()),
    }


def main():
    guard = get_connection('D01')
    results = {}
    for inst in INSTITUTES:
        try:
            r = analyze(guard, inst)
            if r:
                results[inst] = r
        except Exception as e:
            print(f'  ERR: {str(e)[:150]}')
    guard.close()

    Path(HERE / 'institute_creation_v2.json').write_text(
        json.dumps(results, indent=2), encoding='utf-8')

    print('\n=== UNESCO Company Code Creation Summary ===')
    print(f'{"BUKRS":6s} {"Created":>10s} {"Creation TR":>16s} {"Lead Owner":>14s} {"Cluster":>8s} {"Team":>5s}')
    for inst in INSTITUTES:
        if inst in results:
            r = results[inst]
            print(f'{inst:6s} {r["creation_date"] or "-":>10s} {r["creation_transport"]:>16s} {r["lead_owner"]:>14s} {r["cluster_size"]:>8d} {len(r["team"]):>5d}')


if __name__ == '__main__':
    main()

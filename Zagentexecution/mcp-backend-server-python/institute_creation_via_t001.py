"""
Find the REAL creation transport for each BUKRS by looking at E071K
for OBJNAME='T001' where TABKEY contains BUKRS. Earliest such transport = creation.

Then pull the whole cluster (±90 days from T001 creation) of transports where
the institute name is in E07T text OR whose E071K has BUKRS-keyed entries.
"""
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

INSTITUTES = ['UNES', 'IBE', 'IIEP', 'UBO', 'UIL', 'UIS', 'ICTP', 'ICBA', 'MGIE', 'STEM']


def find_t001_creation(guard, bukrs):
    """E071K rows with OBJNAME='T001' and BUKRS in TABKEY."""
    # T001 TABKEY format: MANDT(3) + BUKRS(4) = 7 chars
    res = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                     FIELDS=[{'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'TABKEY'}],
                     OPTIONS=[{'TEXT': f"OBJNAME = 'T001' AND TABKEY LIKE '%{bukrs}%'"}],
                     DELIMITER='|', ROWCOUNT=100)
    trs = set()
    for d in res.get('DATA', []):
        wa = d['WA'].split('|')
        tr = wa[0].strip()
        tk = wa[1].strip() if len(wa) > 1 else ''
        # Validate: TABKEY must contain BUKRS as BUKRS field (position 3-7)
        if len(tk) >= 7 and tk[3:7] == bukrs:
            trs.add(tr)
    return trs


def get_e070(guard, trkorrs):
    out = {}
    for tr in trkorrs:
        r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E070',
                       FIELDS=[{'FIELDNAME': 'AS4DATE'}, {'FIELDNAME': 'AS4USER'},
                               {'FIELDNAME': 'TRFUNCTION'}, {'FIELDNAME': 'TRSTATUS'},
                               {'FIELDNAME': 'STRKORR'}],
                       OPTIONS=[{'TEXT': f"TRKORR = '{tr}'"}],
                       DELIMITER='|', ROWCOUNT=1)
        if r.get('DATA'):
            wa = [x.strip() for x in r['DATA'][0]['WA'].split('|')]
            out[tr] = {'date': wa[0], 'user': wa[1], 'fn': wa[2], 'st': wa[3], 'parent': wa[4]}
    return out


def get_text(guard, trkorr):
    r = guard.call('RFC_READ_TABLE', QUERY_TABLE='E07T',
                   FIELDS=[{'FIELDNAME': 'AS4TEXT'}],
                   OPTIONS=[{'TEXT': f"TRKORR = '{trkorr}' AND LANGU = 'E'"}],
                   DELIMITER='|', ROWCOUNT=1)
    if r.get('DATA'):
        return r['DATA'][0]['WA'].strip()
    return ''


def find_cluster(guard, bukrs, creation_date, window_days=180):
    """Find all transports in a ±window around creation that touch BUKRS-keyed entries."""
    if not creation_date or len(creation_date) != 8:
        return set()
    y = int(creation_date[:4]); m = int(creation_date[4:6]); d = int(creation_date[6:8])
    import datetime
    dt0 = datetime.date(y, m, d)
    start = (dt0 - datetime.timedelta(days=window_days)).strftime('%Y%m%d')
    end = (dt0 + datetime.timedelta(days=window_days)).strftime('%Y%m%d')

    # Query E071K for all BUKRS-keyed entries
    trs = set()
    # Pattern 1: TABKEY starts with 'MANDT' + BUKRS (various tables)
    res = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                     FIELDS=[{'FIELDNAME': 'TRKORR'}],
                     OPTIONS=[{'TEXT': f"TABKEY LIKE '%{bukrs}%'"}],
                     DELIMITER='|', ROWCOUNT=20000)
    trs.update(d['WA'].strip() for d in res.get('DATA', []))
    # Pattern 2: substitution by SUBSTID
    res = guard.call('RFC_READ_TABLE', QUERY_TABLE='E071K',
                     FIELDS=[{'FIELDNAME': 'TRKORR'}],
                     OPTIONS=[{'TEXT': f"OBJNAME IN ('GB90','GB901','GB92','GB921','GB922') AND TABKEY LIKE '%{bukrs}%'"}],
                     DELIMITER='|', ROWCOUNT=5000)
    trs.update(d['WA'].strip() for d in res.get('DATA', []))

    # Enrich and filter by date
    md = get_e070(guard, trs)
    in_window = {t: md[t] for t in md if md[t].get('date', '') and start <= md[t]['date'] <= end}
    return in_window


def analyze(guard, bukrs):
    print(f'\n=== {bukrs} ===')
    # Step 1: find T001 registration transport(s)
    t001_trs = find_t001_creation(guard, bukrs)
    if not t001_trs:
        print(f'  No T001 registration found for {bukrs}')
        return None
    md = get_e070(guard, t001_trs)
    # Earliest date = creation
    sorted_trs = sorted(md.items(), key=lambda x: x[1].get('date', '99999999'))
    creation_tr, creation_md = sorted_trs[0]
    creation_text = get_text(guard, creation_tr)
    print(f'  T001 creation: {creation_tr} on {creation_md.get("date")} by {creation_md.get("user")}')
    print(f'  Text: {creation_text[:70]}')

    # Step 2: find cluster around creation
    cluster = find_cluster(guard, bukrs, creation_md.get('date'))
    print(f'  Cluster size (±180 days, touching BUKRS-keyed entries): {len(cluster)}')

    # Team
    users = Counter(cluster[t].get('user', '') for t in cluster if cluster[t].get('user'))
    lead = users.most_common(1)[0] if users else ('unknown', 0)
    print(f'  Lead owner: {lead[0]} ({lead[1]} transports)')
    print(f'  Team: {dict(users.most_common(10))}')

    return {
        'BUKRS': bukrs,
        'creation_transport': creation_tr,
        'creation_date': creation_md.get('date'),
        'creation_user': creation_md.get('user'),
        'creation_text': creation_text,
        'cluster_transports': list(cluster.keys()),
        'cluster_size': len(cluster),
        'lead_owner': lead[0],
        'lead_transport_count': lead[1],
        'team': dict(users.most_common()),
        'cluster_details': cluster,
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
            print(f'  ERR: {str(e)[:100]}')
    guard.close()

    Path(HERE / 'institute_creation_discovery.json').write_text(
        json.dumps(results, indent=2), encoding='utf-8')
    print(f'\nSaved: institute_creation_discovery.json')

    # Clean summary
    print('\n=== UNESCO Institute Creation Summary ===')
    print(f'{"BUKRS":6s} {"Created":>10s} {"Creation TR":>16s} {"Lead Owner":>14s} {"Cluster":>8s} {"Team size":>10s}')
    for inst in INSTITUTES:
        if inst in results:
            r = results[inst]
            print(f'{inst:6s} {r["creation_date"] or "-":>10s} {r["creation_transport"]:>16s} {r["lead_owner"]:>14s} {r["cluster_size"]:>8d} {len(r["team"]):>10d}')


if __name__ == '__main__':
    main()

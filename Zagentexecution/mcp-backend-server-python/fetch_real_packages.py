"""
fetch_real_packages.py
Queries SAP TADIR via RFC_READ_TABLE (using existing query_table.py infrastructure)
to get the real DEVCLASS for every config object.
Falls back to inferred package if SAP not reachable.
"""
import json, os, sys

# Get list of objects to look up
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

all_names = list(cfg.keys())
print(f'Total config objects to look up: {len(all_names)}')

# ── Try RFC_READ_TABLE via pyrfc ───────────────────────────────────────────────
try:
    import pyrfc
    conn_params = {
        'ashost': os.environ.get('SAP_HOST', 'HQ-SAP-D01.HQ.INT.UNESCO.ORG'),
        'sysnr':  os.environ.get('SAP_SYSNR', '00'),
        'client': os.environ.get('SAP_CLIENT', '350'),
        'user':   os.environ.get('SAP_USER', 'jp_lopez'),
        'passwd': os.environ.get('SAP_PASSWORD', ''),
    }
    conn = pyrfc.Connection(**conn_params)
    print('SAP RFC connection established')

    devclass_map = {}
    BATCH = 50
    for i in range(0, len(all_names), BATCH):
        batch = all_names[i:i+BATCH]
        # Build WHERE clause
        type_pairs = list(set((cfg[n]['obj_type'], n) for n in batch))
        # Use RFC_READ_TABLE on TADIR
        # WHERE: PGMID = 'R3TR' AND (OBJ_NAME = 'XXX' OR OBJ_NAME = 'YYY')
        names_clause = ' OR '.join(f"OBJ_NAME = '{n}'" for n in batch)
        where = [f"PGMID = 'R3TR'", f'AND ({names_clause})']
        try:
            result = conn.call('RFC_READ_TABLE',
                QUERY_TABLE='TADIR',
                DELIMITER='|',
                FIELDS=[{'FIELDNAME':'OBJ_NAME'}, {'FIELDNAME':'DEVCLASS'}, {'FIELDNAME':'OBJECT'}],
                OPTIONS=[{'TEXT': w} for w in where],
            )
            for row in result.get('DATA', []):
                parts = row['WA'].split('|')
                if len(parts) >= 3:
                    obj_name = parts[0].strip()
                    devclass  = parts[1].strip()
                    if devclass:
                        devclass_map[obj_name] = devclass
        except Exception as e:
            print(f'Batch {i}: RFC error - {e}')
            break

    conn.close()
    print(f'RFC lookup: found packages for {len(devclass_map)} objects')

    # Write real DEVCLASS back
    for name, v in cfg.items():
        if name in devclass_map:
            v['package'] = devclass_map[name]

    with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)

    from collections import Counter
    pkgs = Counter(v['package'] for v in cfg.values())
    print('\nTop real SAP packages:')
    for pkg, cnt in pkgs.most_common(20):
        print(f'  {pkg:<40} {cnt:>5}')

except ImportError:
    print('pyrfc not available — keeping inferred packages')
except Exception as e:
    print(f'RFC connection failed: {e} — keeping inferred packages')

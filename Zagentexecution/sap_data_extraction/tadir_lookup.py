import sqlite3
import json
import collections
import sys

db_path = 'sqlite/p01_gold_master_data.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in c.fetchall()]
print("Tables in SQLite DB:", tables)

if 'TADIR' not in tables:
    print("ERROR: TADIR table not found!")
    sys.exit(1)

# load current cfgdetail
cfg_path = '../mcp-backend-server-python/cts_config_detail.json'
with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

# The new logic needs to map the obj_type and obj_name via the new TADIR data
# For TABU, we match OBJECT = 'TABL'
# For VDAT, we match OBJECT = 'VIEW'
TADIR_OBJ_MAP = {
    'TABU': 'TABL',
    'VDAT': 'VIEW',
    'CLAS': 'CLAS',
    'PROG': 'PROG',
    'FUGR': 'FUGR',
    'TABL': 'TABL',
    'VIEW': 'VIEW',
    'DTEL': 'DTEL',
    'DOMA': 'DOMA',
    'TRAN': 'TRAN',
    'DEVC': 'DEVC'
}

general_img = {k: v for k, v in cfg.items() if v.get('module') == 'General IMG'}
print(f"Items in General IMG: {len(general_img)}")

found = 0
for obj_name, item in list(general_img.items()):
    otype = item.get('obj_type')
    tadir_type = TADIR_OBJ_MAP.get(otype, otype)
    
    # query TADIR
    c.execute("SELECT DEVCLASS FROM TADIR WHERE OBJECT = ? AND OBJ_NAME = ?", (tadir_type, obj_name))
    row = c.fetchone()
    if row and row[0]:
        devclass = row[0]
        item['package'] = devclass
        found += 1

print(f"Found new DevClass for {found} items out of {len(general_img)}")

# We can re-run the classification algorithm here! Wait, let's just write the data back first to verify.
with open(cfg_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

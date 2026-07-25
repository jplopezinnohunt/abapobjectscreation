import sqlite3

db_path = 'sqlite/p01_gold_master_data.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("PRAGMA table_info('tadir_enrichment');")
print('tadir_enrichment columns:')
for r in c.fetchall():
    print(f" - {r[1]} ({r[2]})")

c.execute("SELECT * FROM tadir_enrichment LIMIT 5")
print('\nSample Data:')
for r in c.fetchall():
    print(r)

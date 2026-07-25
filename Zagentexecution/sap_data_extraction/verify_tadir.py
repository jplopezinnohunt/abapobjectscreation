import sqlite3
import json

conn = sqlite3.connect('sqlite/p01_gold_master_data.db')
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM tadir_enrichment WHERE devclass != '' AND devclass IS NOT NULL")
print("Filled devclass in tadir_enrichment:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM tadir_enrichment WHERE devclass = '' OR devclass IS NULL")
print("Empty devclass in tadir_enrichment:", c.fetchone()[0])

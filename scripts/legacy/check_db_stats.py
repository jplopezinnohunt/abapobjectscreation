import sqlite3
import os

db_path = r"c:\Users\jp_lopez\projects\abapobjectscreation\knowledge\domains\PSM\p01_master_data_v2.db"
if not os.path.exists(db_path):
    print("DB not found.")
    exit(1)

conn = sqlite3.connect(db_path)
print(f"Funds: {conn.execute('SELECT count(*) from funds').fetchone()[0]}")
print(f"FC: {conn.execute('SELECT count(*) from fc').fetchone()[0]}")
try:
    print(f"Movements: {conn.execute('SELECT count(*) from movements').fetchone()[0]}")
    print("Movements (First 5):")
    for r in conn.execute('SELECT * FROM movements LIMIT 5'):
        print(r)
except:
    print("Movements table not ready.")

print("\nRecent UNES Funds:")
for r in conn.execute("SELECT FIKRS, FINCODE, ERFDAT FROM funds WHERE FIKRS = 'UNES' ORDER BY ERFDAT DESC LIMIT 10"):
    print(r)

print("\nRecent UBO Funds:")
for r in conn.execute("SELECT FIKRS, FINCODE, ERFDAT FROM funds WHERE FIKRS = 'UBO' ORDER BY ERFDAT DESC LIMIT 10"):
    print(r)

conn.close()

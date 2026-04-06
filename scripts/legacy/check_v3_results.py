import sqlite3
import os

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge", "domains", "PSM", "p01_gold_master_data.db")

print(f"Checking DB: {DB_PATH}")
if not os.path.exists(DB_PATH):
    print("Database file missing.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def check_table(name):
    try:
        count = cursor.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        print(f"Table '{name}': {count} rows")
    except Exception as e:
        print(f"Table '{name}': Error or missing - {e}")

check_table("funds")
check_table("fund_centers")
check_table("projects")
check_table("wbs_elements")
check_table("ytfm_fund_cpl")
check_table("ytfm_wrttp_gr")
check_table("movements_summary")

print("\nSample Funds Example (2024+):")
res = cursor.execute("SELECT FIKRS, FINCODE, ERFDAT FROM funds WHERE ERFDAT >= '20240101' LIMIT 10").fetchall()
for r in res:
    print(r)

print("\nSample Custom UNESCO Fund Metadata:")
res = cursor.execute("SELECT * FROM ytfm_fund_cpl LIMIT 5").fetchall()
for r in res:
    print(r)

conn.close()

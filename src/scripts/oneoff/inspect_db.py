import sqlite3
conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# List all tables
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    print(f"\n--- {t} ---")
    # Schema
    cols = c.execute(f"PRAGMA table_info({t})").fetchall()
    print("Columns:", [(col[1], col[2]) for col in cols])
    # Row count
    count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"Rows: {count}")
    # Sample
    if count > 0:
        sample = c.execute(f"SELECT * FROM {t} LIMIT 2").fetchall()
        for row in sample:
            print(f"  {row}")

conn.close()

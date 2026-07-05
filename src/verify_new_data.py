import sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect('D:/japan-car-market/data/japan_car_market.db')
c = conn.cursor()

print("=== New Tables Summary ===")
for t in ['import_car_monthly', 'new_car_export', 'export_by_type', 'import_customs', 'overseas_production_annual']:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = c.fetchone()[0]
    print(f"  {t}: {cnt} rows")

print("\n=== import_car_monthly sample ===")
c.execute("SELECT year, month, brand, rank, units, yoy_pct FROM import_car_monthly WHERE year=2024 AND month=1 ORDER BY rank")
for r in c.fetchall():
    print(f"  {r}")

print("\n=== new_car_export regions ===")
c.execute("SELECT DISTINCT region FROM new_car_export")
print(f"  Regions: {[r[0] for r in c.fetchall()]}")

print("\n=== jama_annual_facts categories ===")
c.execute("SELECT category, COUNT(*) FROM jama_annual_facts GROUP BY category ORDER BY category")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} records")

print("\n=== import_customs sample ===")
c.execute("SELECT year, country, units FROM import_customs WHERE year=2024 ORDER BY units DESC")
for r in c.fetchall():
    print(f"  {r}")

conn.close()
print("\nAll checks passed!")

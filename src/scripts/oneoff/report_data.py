import sqlite3
conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

print("=== 进口车月度 Top10 最新月 ===")
c.execute("SELECT year, month, brand, rank, units, yoy_pct FROM import_car_monthly WHERE year=2026 AND month=5 ORDER BY rank")
for r in c.fetchall():
    print(f"  #{r[3]} {r[2]}: {r[4]}台 (YoY {r[5]}%)")

print("\n=== 进口车月度 总量趋势 ===")
c.execute("SELECT year, month, SUM(units) as total FROM import_car_monthly GROUP BY year, month ORDER BY year, month")
rows = c.fetchall()
for r in rows[-12:]:
    print(f"  {r[0]}-{r[1]:02d}: {r[2]:,}台")

print("\n=== 新车出口 按地区 (最新年2024) ===")
c.execute("SELECT region, units FROM new_car_export WHERE year=2024 AND region!='合计' ORDER BY units DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]:,}台")

print("\n=== 出口按车型 (2024) ===")
c.execute("SELECT vehicle_type, units FROM export_by_type WHERE year=2024 AND vehicle_type!='合计' ORDER BY units DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]:,}台")

print("\n=== 中古车出口 最新月Top10目的国 ===")
c.execute("SELECT country_name, export_count FROM export_statistics WHERE year=2026 AND month=5 AND country_name!='Total' ORDER BY export_count DESC LIMIT 10")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]:,}台")

print("\n=== 海外生产 按地区 (最新年) ===")
c.execute("SELECT year, region, units FROM overseas_production_annual WHERE region!='合计' ORDER BY year DESC, units DESC")
seen = set()
for r in c.fetchall():
    key = r[0]
    if key not in seen:
        seen.add(key)
        print(f"  {r[0]} {r[1]}: {r[2]:,}台")

print("\n=== JAMA facts - import_sales ===")
c.execute("SELECT year, subcategory, label, value FROM jama_annual_facts WHERE category='import_sales' ORDER BY year, subcategory")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]} {r[2]}: {r[3]:,}")

print("\n=== JAMA facts - import_used ===")
c.execute("SELECT year, subcategory, label, value FROM jama_annual_facts WHERE category='import_used' ORDER BY year, subcategory")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]} {r[2]}: {r[3]:,}")

print("\n=== JAMA facts - ev_sales ===")
c.execute("SELECT year, subcategory, label, value FROM jama_annual_facts WHERE category='ev_sales' ORDER BY year, subcategory")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]} {r[2]}: {r[3]:,}")

print("\n=== 通関実績 import_customs ===")
c.execute("SELECT year, country, units FROM import_customs ORDER BY year, units DESC")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]}: {r[2]:,}台")

conn.close()

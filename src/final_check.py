"""验证完整的 japan_monthly_summary 数据"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# 2022-2026 年（有 JADA 数据的）的月度摘要
c.execute("""
    SELECT year, month, total_sales, registered_car_sales, kei_car_sales, kei_yoy_pct 
    FROM japan_monthly_summary 
    WHERE year >= 2022 
    ORDER BY year, month
""")
print("2022-2026 日本月度销量摘要:")
print(f"{'年/月':>8} {'总销量':>10} {'注册车':>10} {'K-car':>10} {'K-car同比':>10}")
for r in c.fetchall():
    reg = f"{r[3]:,}" if r[3] else "N/A"
    kei = f"{r[4]:,}" if r[4] else "N/A"
    yoy = f"{r[5]}%" if r[5] else "N/A"
    print(f"  {r[0]}/{r[1]:<3} {r[2]:>10,} {reg:>10} {kei:>10} {yoy:>10}")

# 统计各表最终数据量
print("\n" + "=" * 60)
print("数据库最终统计:")
for table in ["used_cars", "used_cars_cleaned", "new_car_sales_brand", 
              "kcar_monthly_sales", "kcar_brand_sales", "japan_monthly_summary"]:
    c.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {c.fetchone()[0]} 行")

conn.close()

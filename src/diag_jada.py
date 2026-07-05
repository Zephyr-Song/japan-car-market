"""诊断 JADA 数据问题"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# 看 2024 年每月的品牌数量和总销量
print("2024年 JADA 月度数据:")
c.execute("""
    SELECT month, COUNT(DISTINCT brand), SUM(sales_count)
    FROM new_car_sales_brand WHERE year=2024
    GROUP BY month ORDER BY month
""")
for r in c.fetchall():
    print(f"  {r[0]}月: {r[1]} 个品牌, 总销量 {r[2]:,}")

# 看 2024/1 的所有品牌和销量
print("\n2024/1 所有品牌:")
c.execute("""
    SELECT brand, vehicle_type, sales_count FROM new_car_sales_brand 
    WHERE year=2024 AND month=1 ORDER BY sales_count DESC
""")
for r in c.fetchall():
    print(f"  {r[0]} ({r[1]}): {r[2]:,}")

# 看 2026/1 的所有品牌和销量
print("\n2026/1 所有品牌:")
c.execute("""
    SELECT brand, vehicle_type, sales_count FROM new_car_sales_brand 
    WHERE year=2026 AND month=1 ORDER BY sales_count DESC
""")
for r in c.fetchall():
    print(f"  {r[0]} ({r[1]}): {r[2]:,}")

conn.close()

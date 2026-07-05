"""检查 2025 年 JADA 数据"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'D:\japan-car-market\data\japan_car_market.db')
c = conn.cursor()

# 2025年每月品牌数
c.execute("SELECT month, COUNT(DISTINCT brand), SUM(sales_count) FROM new_car_sales_brand WHERE year=2025 GROUP BY month ORDER BY month")
rows = c.fetchall()
print("2025年 JADA 月度数据:")
for r in rows:
    print(f"  {r[0]}月: {r[1]} 个品牌, 总销量 {r[2]:,}")

# 看看2025年1月的品牌
c.execute("SELECT brand, vehicle_type, sales_count FROM new_car_sales_brand WHERE year=2025 AND month=1 ORDER BY sales_count DESC LIMIT 20")
print("\n2025/1 品牌 TOP20:")
for r in c.fetchall():
    print(f"  {r[0]} ({r[1]}): {r[2]:,}")

conn.close()

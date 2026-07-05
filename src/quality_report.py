"""最终数据质量验证和统计"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'D:\japan-car-market\data\japan_car_market.db')
c = conn.cursor()

print("=" * 70)
print("日本汽车市场数据库 - 最终质量报告")
print("=" * 70)

# 1. 各表统计
tables = {
    "used_cars": "二手车原始数据(carsensor.net)",
    "used_cars_cleaned": "二手车清洗后数据",
    "new_car_sales_brand": "新车品牌别销量(JADA)",
    "kcar_monthly_sales": "K-car月度销量(zenkeijikyo)",
    "kcar_brand_sales": "K-car品牌别销量(zenkeijikyo)",
    "japan_monthly_summary": "日本月度总销量摘要",
}
print("\n📊 各表数据量:")
for table, desc in tables.items():
    c.execute(f"SELECT COUNT(*) FROM {table}")
    count = c.fetchone()[0]
    print(f"  {table}: {count:,} 行 — {desc}")

# 2. JADA 品牌别覆盖
c.execute("SELECT COUNT(DISTINCT brand) FROM new_car_sales_brand")
print(f"\n🏷️ JADA 品牌数: {c.fetchone()[0]}")
c.execute("SELECT DISTINCT brand FROM new_car_sales_brand ORDER BY brand")
brands = [r[0] for r in c.fetchall()]
print(f"   品牌列表: {', '.join(brands[:15])}...")

# 3. 年度总销量
print("\n📈 年度总销量:")
for year in [2022, 2023, 2024, 2025, 2026]:
    c.execute("""
        SELECT SUM(total_sales), SUM(registered_car_sales), SUM(kei_car_sales)
        FROM japan_monthly_summary WHERE year=?
    """, (year,))
    r = c.fetchone()
    if r[0]:
        reg = f"{r[1]:,}" if r[1] else "N/A"
        kei = f"{r[2]:,}" if r[2] else "N/A"
        # 看有多少个月的数据
        c.execute("SELECT COUNT(*) FROM japan_monthly_summary WHERE year=? AND total_sales > 0", (year,))
        months = c.fetchone()[0]
        print(f"  {year}: 总 {r[0]:>10,} (注册车 {reg}, K-car {kei}) — {months}个月")

# 4. 2026年5月品牌别份额
print("\n🏆 2026年5月 品牌别新车销量:")
c.execute("""
    SELECT brand, 
           SUM(CASE WHEN vehicle_type LIKE '%乗用車(登録車)%' THEN sales_count ELSE 0 END) as reg_pax,
           SUM(CASE WHEN vehicle_type LIKE '%貨物車(登録車)%' THEN sales_count ELSE 0 END) as reg_cargo,
           SUM(CASE WHEN vehicle_type LIKE '%軽%' THEN sales_count ELSE 0 END) as kei
    FROM new_car_sales_brand 
    WHERE year=2026 AND month=5
    GROUP BY brand
    ORDER BY (reg_pax + reg_cargo + kei) DESC
""")
for r in c.fetchall():
    total = (r[1] or 0) + (r[2] or 0) + (r[3] or 0)
    print(f"  {r[0]:>15}: 注册{r[1] or 0:>6,}+{r[2] or 0:>5,} K-car{r[3] or 0:>6,} = {total:>7,}")

# 5. K-car 品牌别 2026/5
print("\n🚗 2026年5月 K-car品牌别(zenkeijikyo速报):")
c.execute("SELECT brand, total_count, market_share_pct, yoy_pct FROM kcar_brand_sales WHERE year=2026 AND month=5 ORDER BY total_count DESC")
for r in c.fetchall():
    print(f"  {r[0]:>10}: {r[1]:>6,} 份额{r[2]}% 同比{r[3]}%")

# 6. 数据质量检查
print("\n✅ 数据质量检查:")
c.execute("SELECT COUNT(*) FROM new_car_sales_brand WHERE brand LIKE '%前年%' OR brand LIKE '%合計%'")
bad = c.fetchone()[0]
print(f"  JADA 异常品牌名: {bad} (应为0)")

c.execute("SELECT COUNT(*) FROM kcar_monthly_sales WHERE yoy_pct IS NOT NULL")
not_null = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM kcar_monthly_sales")
total = c.fetchone()[0]
print(f"  K-car月度 yoy_pct 非空: {not_null}/{total}")

c.execute("SELECT COUNT(*) FROM kcar_brand_sales WHERE market_share_pct IS NOT NULL")
not_null = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM kcar_brand_sales")
total = c.fetchone()[0]
print(f"  K-car品牌 market_share 非空: {not_null}/{total}")

conn.close()

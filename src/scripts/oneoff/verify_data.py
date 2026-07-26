"""验证修复后的数据质量"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

print("=" * 60)
print("数据质量验证")
print("=" * 60)

# 1. kcar_monthly_sales yoy_pct
c.execute('SELECT COUNT(*) FROM kcar_monthly_sales WHERE yoy_pct IS NOT NULL')
not_null = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM kcar_monthly_sales')
total = c.fetchone()[0]
print(f"\n1. kcar_monthly_sales yoy_pct: {not_null}/{total} 非空")

# 抽查 2026年5月
c.execute('SELECT year, month, total, yoy_pct FROM kcar_monthly_sales WHERE year=2026 AND month=5')
r = c.fetchone()
print(f"   2026/5: total={r[2]}, yoy={r[3]}% (应为 -2.1)")

c.execute('SELECT year, month, total, yoy_pct FROM kcar_monthly_sales WHERE year=2026 AND month=1')
r = c.fetchone()
print(f"   2026/1: total={r[2]}, yoy={r[3]}% (应为 1.1)")

# 2. kcar_brand_sales market_share
c.execute('SELECT brand, total_count, market_share_pct, yoy_pct FROM kcar_brand_sales')
print("\n2. kcar_brand_sales 数据:")
for r in c.fetchall():
    print(f"   {r[0]}: total={r[1]}, share={r[2]}%, yoy={r[3]}%")
# 期望: スズキ share=35.7, yoy=97.0; ダイハツ share=30.4, yoy=99.3

# 3. japan_monthly_summary 负号
c.execute('SELECT year, month, registered_yoy_pct, kei_yoy_pct, ytd_yoy_pct FROM japan_monthly_summary WHERE year=2024 AND month=12')
r = c.fetchone()
print(f"\n3. 2024/12 yoy: reg={r[2]}%, kei={r[3]}%, ytd={r[4]}% (应为 -9.3, -8.8, -7.5)")

c.execute('SELECT year, month, kei_yoy_pct FROM japan_monthly_summary WHERE year=2026 AND month=5')
r = c.fetchone()
print(f"   2026/5 kei_yoy={r[2]}% (应为 -2.1)")

# 4. JADA 异常品牌检查
c.execute("SELECT DISTINCT brand FROM new_car_sales_brand WHERE brand LIKE '%前年%' OR brand LIKE '%合計%' OR brand LIKE '%計%'")
bad = c.fetchall()
print(f"\n4. JADA 异常品牌名: {bad if bad else '无 (正确)'}")

c.execute("SELECT DISTINCT brand FROM new_car_sales_brand ORDER BY brand")
brands = c.fetchall()
print(f"   品牌总数: {len(brands)}")
print(f"   前10: {[b[0] for b in brands[:10]]}")

conn.close()

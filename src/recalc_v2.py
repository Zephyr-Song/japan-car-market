"""重新计算 japan_monthly_summary（用修复后的 JADA 数据，正确区分注册车和K-car）"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'D:\japan-car-market\data\japan_car_market.db')
c = conn.cursor()

# 清除所有旧 summary 数据
c.execute("DELETE FROM japan_monthly_summary")
print(f"清除旧数据: {c.rowcount} 行")
conn.commit()

crawl_date = '2026-06-24'

# 策略: 对每个月，用 kcar 数据 + JADA 注册车数据
c.execute("SELECT DISTINCT year, month FROM kcar_monthly_sales ORDER BY year, month")
kcar_months = c.fetchall()

inserted = 0
for year, month in kcar_months:
    # K-car 总销量
    c.execute("SELECT total, yoy_pct FROM kcar_monthly_sales WHERE year=? AND month=?", (year, month))
    kcar_row = c.fetchone()
    if not kcar_row or not kcar_row[0]:
        continue
    kei_sales = kcar_row[0]
    kei_yoy = kcar_row[1]
    
    # JADA 注册车（不含軽）总销量
    c.execute("""
        SELECT SUM(sales_count) FROM new_car_sales_brand 
        WHERE year=? AND month=? AND vehicle_type IN ('乗用車(登録車)', '貨物車(登録車)')
    """, (year, month))
    reg_sales = c.fetchone()[0]
    
    if reg_sales is not None:
        total_sales = reg_sales + kei_sales
        data_source = "calculated"
    else:
        total_sales = kei_sales
        data_source = "kcar_only"
    
    row = {
        "year": year, "month": month,
        "total_sales": total_sales,
        "registered_car_sales": reg_sales,
        "kei_car_sales": kei_sales,
        "registered_yoy_pct": None,
        "kei_yoy_pct": kei_yoy,
        "ytd_total": None,
        "ytd_yoy_pct": None,
        "data_source": data_source,
        "crawl_date": crawl_date,
    }
    try:
        c.execute("""
            INSERT OR IGNORE INTO japan_monthly_summary
            (year, month, total_sales, registered_car_sales, kei_car_sales,
             registered_yoy_pct, kei_yoy_pct, ytd_total, ytd_yoy_pct,
             data_source, crawl_date)
            VALUES (:year, :month, :total_sales, :registered_car_sales, :kei_car_sales,
                    :registered_yoy_pct, :kei_yoy_pct, :ytd_total, :ytd_yoy_pct,
                    :data_source, :crawl_date)
        """, row)
        if c.rowcount > 0:
            inserted += 1
    except sqlite3.IntegrityError:
        pass

conn.commit()
print(f"新增 {inserted} 条")

# 验证关键月份数据
print("\n2024-2026 日本月度总销量:")
c.execute("""
    SELECT year, month, total_sales, registered_car_sales, kei_car_sales, kei_yoy_pct, data_source
    FROM japan_monthly_summary WHERE year >= 2024 ORDER BY year, month
""")
print(f"{'年/月':>8} {'总销量':>10} {'注册车':>10} {'K-car':>10} {'K同比%':>8} {'来源':>10}")
for r in c.fetchall():
    reg = f"{r[3]:,}" if r[3] else "N/A"
    yoy = f"{r[5]}" if r[5] else "N/A"
    print(f"  {r[0]}/{r[1]:<3} {r[2]:>10,} {reg:>10} {r[4]:>10,} {yoy:>8} {r[6]:>10}")

# 总计
c.execute("SELECT COUNT(*) FROM japan_monthly_summary")
print(f"\njapan_monthly_summary 总行数: {c.fetchone()[0]}")

conn.close()

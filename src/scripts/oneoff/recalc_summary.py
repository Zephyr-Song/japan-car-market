"""重新计算 japan_monthly_summary（清除旧的 calculated 数据，用修复后的 JADA 数据重新算）"""
import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'japan_car_market.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 删除所有 calculated 来源的数据
c.execute("DELETE FROM japan_monthly_summary WHERE data_source='calculated'")
print(f"清除 calculated 数据: {c.rowcount} 行")
conn.commit()

crawl_date = '2026-06-24'
inserted = 0

# 对每个月，如果有 kcar 数据，就插入
c.execute("SELECT DISTINCT year, month FROM kcar_monthly_sales ORDER BY year, month")
kcar_months = c.fetchall()

for year, month in kcar_months:
    c.execute("SELECT COUNT(*) FROM japan_monthly_summary WHERE year=? AND month=?", (year, month))
    if c.fetchone()[0] > 0:
        continue
    
    # K-car 总销量
    c.execute("SELECT total, yoy_pct FROM kcar_monthly_sales WHERE year=? AND month=?", (year, month))
    kcar_row = c.fetchone()
    if not kcar_row or not kcar_row[0]:
        continue
    kei_sales = kcar_row[0]
    kei_yoy = kcar_row[1]
    
    # JADA 注册车总销量
    c.execute("""
        SELECT SUM(sales_count) FROM new_car_sales_brand 
        WHERE year=? AND month=? AND vehicle_type IN ('乗用車', '貨物車')
    """, (year, month))
    reg_sales = c.fetchone()[0]
    
    if reg_sales is None:
        total_sales = kei_sales
    else:
        total_sales = reg_sales + kei_sales
    
    row = {
        "year": year, "month": month,
        "total_sales": total_sales,
        "registered_car_sales": reg_sales,
        "kei_car_sales": kei_sales,
        "registered_yoy_pct": None,
        "kei_yoy_pct": kei_yoy,
        "ytd_total": None,
        "ytd_yoy_pct": None,
        "data_source": "calculated",
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
print(f"从 kcar+JADA 计算补充: 新增 {inserted} 条")

# 验证 2024-2026
print("\n2024-2026 验证:")
c.execute("""
    SELECT year, month, total_sales, registered_car_sales, kei_car_sales 
    FROM japan_monthly_summary 
    WHERE year >= 2024 
    ORDER BY year, month
""")
for r in c.fetchall():
    reg = f"{r[3]:,}" if r[3] else "N/A"
    print(f"  {r[0]}/{r[1]:<3} total={r[2]:>10,} reg={reg:>10} kei={r[4]:>10,}")

# 最终统计
print("\n各表统计:")
for table in ["used_cars", "used_cars_cleaned", "new_car_sales_brand", 
              "kcar_monthly_sales", "kcar_brand_sales", "japan_monthly_summary"]:
    c.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table}: {c.fetchone()[0]} 行")

conn.close()

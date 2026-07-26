"""从已有 kcar_monthly_sales + JADA new_car_sales_brand 数据补充 japan_monthly_summary"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# 从 kcar 获取 K-car 月度总销量
# 从 JADA 获取注册车月度总销量 (所有品牌同月求和)
# 合并为 japan_monthly_summary

crawl_date = '2026-06-24'
inserted = 0

# 先看 JADA 有哪些年月的数据
c.execute("SELECT DISTINCT year, month FROM new_car_sales_brand ORDER BY year, month")
jada_months = c.fetchall()
print(f"JADA 数据覆盖: {jada_months[0]} ~ {jada_months[-1]} ({len(jada_months)} 个月)")

# 看 kcar 有哪些年月
c.execute("SELECT DISTINCT year, month FROM kcar_monthly_sales ORDER BY year, month")
kcar_months = c.fetchall()
print(f"K-car 数据覆盖: {kcar_months[0]} ~ {kcar_months[-1]} ({len(kcar_months)} 个月)")

# 对每个月，如果有 JADA 注册车数据 + kcar 数据，计算总销量
for year, month in kcar_months:
    # 检查是否已存在
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

    # JADA 注册车总销量 (乗用車 + 貨物車)
    c.execute("""
        SELECT SUM(sales_count) FROM new_car_sales_brand 
        WHERE year=? AND month=? AND vehicle_type IN ('乗用車', '貨物車')
    """, (year, month))
    reg_sales = c.fetchone()[0]

    if reg_sales is None:
        # 没有 JADA 数据的月份，只记录 k-car 数据
        total_sales = kei_sales
    else:
        total_sales = reg_sales + kei_sales

    row = {
        "year": year, "month": month,
        "total_sales": total_sales,
        "registered_car_sales": reg_sales,
        "kei_car_sales": kei_sales,
        "registered_yoy_pct": None,  # 需要计算
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
print(f"\n从 kcar+JADA 计算补充 japan_monthly_summary: 新增 {inserted} 条")

# 最终统计
c.execute("SELECT COUNT(*) FROM japan_monthly_summary")
total_rows = c.fetchone()[0]
c.execute("SELECT MIN(year), MAX(year) FROM japan_monthly_summary")
yr = c.fetchone()
print(f"japan_monthly_summary 总行数: {total_rows}, 覆盖 {yr[0]}-{yr[1]}")

# 抽查
c.execute("SELECT year, month, total_sales, registered_car_sales, kei_car_sales, kei_yoy_pct FROM japan_monthly_summary ORDER BY year, month LIMIT 10")
print("\n前10行:")
for r in c.fetchall():
    print(f"  {r[0]}/{r[1]}: total={r[2]}, reg={r[3]}, kei={r[4]}, kei_yoy={r[5]}")

conn.close()

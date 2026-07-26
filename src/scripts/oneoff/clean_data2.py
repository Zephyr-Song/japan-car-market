import sqlite3
conn = sqlite3.connect(r'D:\japan-car-market\data\japan_car_market.db')
c = conn.cursor()

# 1. 删除 JADA 中的伪品牌行
bad_brands = ['前年比', '構成比', '計', '合計', 'その他計', '総計', '前年', '累計']
for b in bad_brands:
    c.execute("DELETE FROM new_car_sales_brand WHERE brand LIKE ?", (f'%{b}%',))
    if c.rowcount > 0:
        print(f"删除品牌 '{b}': {c.rowcount} 行")

# 2. 修正 japan_monthly_summary 中 registered_yoy_pct 符号
# 2024年12月: 注册车下降9.3%, 应为 -9.3
c.execute("SELECT id, year, month, registered_yoy_pct, kei_yoy_pct FROM japan_monthly_summary WHERE year=2024 AND month=12")
row = c.fetchone()
if row:
    print(f"2024/12: reg_yoy={row[3]}, kei_yoy={row[4]}")
    # MarkLines 文字说 "注册车下降9.3%" = -9.3, "微型车下降8.8%" = -8.8
    c.execute("UPDATE japan_monthly_summary SET registered_yoy_pct=-9.3, kei_yoy_pct=-8.8 WHERE year=2024 AND month=12")
    print(f"修正 2024/12 registered_yoy 为 -9.3")

# 3. 清空 kcar_monthly_sales 和 kcar_brand_sales 重新解析
c.execute("DELETE FROM kcar_monthly_sales")
print(f"清空 kcar_monthly_sales: {c.rowcount} 行")
c.execute("DELETE FROM kcar_brand_sales")
print(f"清空 kcar_brand_sales: {c.rowcount} 行")

conn.commit()
conn.close()
print("数据清理完成")

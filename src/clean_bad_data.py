import sqlite3
conn = sqlite3.connect(r'D:\japan-car-market\data\japan_car_market.db')
c = conn.cursor()

# 删除有问题的数据重新爬取
# 1. JADA 旧格式数据 (vehicle_type='登録車' 是错误的)
c.execute("DELETE FROM new_car_sales_brand WHERE vehicle_type='登録車'")
print(f"删除 JADA 注册车(旧格式): {c.rowcount} 行")

# 2. kcar_monthly_sales yoy_pct 是错误的 (存储了total值)
c.execute("UPDATE kcar_monthly_sales SET yoy_pct=NULL WHERE yoy_pct IS NOT NULL AND ABS(yoy_pct) > 200")
print(f"修正 kcar_monthly_sales yoy_pct: {c.rowcount} 行")

# 3. kcar_brand_sales market_share 和 yoy 错误
c.execute("DELETE FROM kcar_brand_sales")
print(f"删除 kcar_brand_sales: {c.rowcount} 行")

conn.commit()
conn.close()
print("数据清理完成")

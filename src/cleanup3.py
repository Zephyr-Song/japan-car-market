import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# 删除未来月份的空行 (2026/6-12)
c.execute("DELETE FROM kcar_monthly_sales WHERE year=2026 AND month>5")
print(f"删除 2026/6-12 空行: {c.rowcount}")

# 1996/4 yoy_pct 为 None 是正常的（没有1995年数据作对比）
# 保留

c.execute("SELECT COUNT(*) FROM kcar_monthly_sales")
print(f"kcar_monthly_sales 总行数: {c.fetchone()[0]}")

conn.commit()
conn.close()

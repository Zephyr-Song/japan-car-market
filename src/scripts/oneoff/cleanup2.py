"""清理残留数据问题"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/japan_car_market.db')
c = conn.cursor()

# 清理残留的 "前年比" 品牌
c.execute("DELETE FROM new_car_sales_brand WHERE brand LIKE '%前年%'")
print(f"删除残留 前年比 行: {c.rowcount}")

# 查看 yoy_pct 为 None 的 kcar_monthly_sales 行
c.execute('SELECT year, month, total FROM kcar_monthly_sales WHERE yoy_pct IS NULL')
nulls = c.fetchall()
print(f"\nyoy_pct 为 None 的行 ({len(nulls)}):")
for r in nulls:
    print(f"  {r[0]}/{r[1]}: total={r[2]}")

conn.commit()
conn.close()

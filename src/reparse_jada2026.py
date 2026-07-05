"""重解析 2026 年 JADA Excel 数据"""
import sqlite3, sys, os, tempfile, re
import requests
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'japan_car_market.db')

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en;q=0.9"}
TIMEOUT = 60

JADA_2026_URL = "https://www.jada.or.jp/files/libs/7209/20260603154913819.xls"

def parse_int(text):
    if text is None: return None
    s = str(text).replace(",", "").strip()
    if not s or s in ("-", "‐", "—"): return None
    try: return int(float(s))
    except: return None

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 清除 2026 年旧数据
c.execute("DELETE FROM new_car_sales_brand WHERE year=2026")
print(f"清除 2026 旧数据: {c.rowcount} 行")
conn.commit()

# 下载
print("下载 2026 年 JADA Excel...")
resp = requests.get(JADA_2026_URL, headers=HEADERS, timeout=TIMEOUT)
resp.raise_for_status()
fd, path = tempfile.mkstemp(suffix=".xls")
with os.fdopen(fd, "wb") as f:
    f.write(resp.content)

try:
    xl = pd.ExcelFile(path, engine="xlrd")
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet_name in xl.sheet_names:
        m = re.search(r"(\d{4})年(\d{1,2})月", sheet_name)
        if not m:
            continue
        y, mo = int(m.group(1)), int(m.group(2))
        
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
        inserted = 0
        
        for i in range(5, len(df)):
            # 品牌名在 col[0], col[1]=合計 表示品牌小计行
            col0 = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
            col1 = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ""
            
            # 只处理 "品牌名 + 合計" 行
            if col1 != "合計":
                continue
            
            brand_name = col0.replace("　", "").strip()
            if not brand_name or brand_name == "nan":
                continue
            
            # 跳过总合计
            if brand_name in ("合計", "計", "総計", "その他"):
                continue
            
            # 乗用車計 = col[6], 貨物車計 = col[10]
            passenger = parse_int(df.iloc[i, 6]) if df.shape[1] > 6 else None
            cargo = parse_int(df.iloc[i, 10]) if df.shape[1] > 10 else None
            
            if passenger is not None and passenger > 0:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO new_car_sales_brand
                        (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                        VALUES (?, ?, ?, '乗用車', ?, 'JADA', '2026-06-24')
                    """, (y, mo, brand_name, passenger))
                    if c.rowcount > 0:
                        inserted += 1
                except: pass
            
            if cargo is not None and cargo > 0:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO new_car_sales_brand
                        (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                        VALUES (?, ?, ?, '貨物車', ?, 'JADA', '2026-06-24')
                    """, (y, mo, brand_name, cargo))
                    if c.rowcount > 0:
                        inserted += 1
                except: pass
        
        print(f"  {y}/{mo}: 新增 {inserted} 条")
    
    conn.commit()
finally:
    try: os.unlink(path)
    except: pass

# 验证
c.execute("SELECT month, COUNT(DISTINCT brand), SUM(sales_count) FROM new_car_sales_brand WHERE year=2026 GROUP BY month ORDER BY month")
for r in c.fetchall():
    print(f"  2026/{r[0]}: {r[1]} 个品牌, 总销量 {r[2]:,}")

conn.close()

"""重解析 JADA Excel，使用不含 K-car 的注册车数据"""
import sqlite3, sys, os, tempfile, re
import requests
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'D:\japan-car-market\data\japan_car_market.db'
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en;q=0.9"}
TIMEOUT = 60

JADA_URLS = {
    2026: "https://www.jada.or.jp/files/libs/7209/20260603154913819.xls",
    2025: "https://www.jada.or.jp/files/libs/6663/2026020315092526.xls",
    2024: "https://www.jada.or.jp/relays/download/337/1568/1918/6663/?file=/files/libs/5205/202502041551388761.xls&file_name=xxx",
    2023: "https://www.jada.or.jp/relays/download/337/1568/1058/5205/?file=/files/libs/3423/202403281149129338.xls&file_name=xxx",
    2022: "https://www.jada.or.jp/relays/download/337/1568/1059/3423/?file=/files/libs/3424/202403281150366193.xls&file_name=xxx",
}

def parse_int(text):
    if text is None: return None
    s = str(text).replace(",", "").strip()
    if not s or s in ("-", "‐", "—"): return None
    try: return int(float(s))
    except: return None

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 清除所有旧数据
c.execute("DELETE FROM new_car_sales_brand")
print(f"清除所有旧数据: {c.rowcount} 行")
conn.commit()

for year in [2022, 2023, 2024, 2025, 2026]:
    url = JADA_URLS.get(year)
    if not url:
        continue
    
    print(f"\n下载 {year} 年 JADA Excel...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".xls")
        with os.fdopen(fd, "wb") as f:
            f.write(resp.content)
    except Exception as e:
        print(f"  下载失败: {e}")
        continue
    
    try:
        xl = pd.ExcelFile(path, engine="xlrd")
        year_inserted = 0
        
        for sheet_name in xl.sheet_names:
            m = re.search(r"(\d{4})年(\d{1,2})月", sheet_name)
            if not m:
                continue
            y, mo = int(m.group(1)), int(m.group(2))
            
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
            
            for i in range(5, len(df)):
                col0 = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
                col1 = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ""
                
                if col1 != "合計":
                    continue
                
                brand_name = col0.replace("　", "").strip()
                if not brand_name or brand_name == "nan":
                    continue
                if brand_name in ("合計", "計", "総計", "その他"):
                    continue
                
                # Excel 列结构:
                # [3]=乗用普通 [4]=乗用小型 [5]=乗用軽 [6]=乗用計
                # [7]=貨物普通 [8]=貨物小型 [9]=貨物軽 [10]=貨物計
                # [11]=バス計
                
                # 注册车(不含K-car) 乗用車 = 普通+小型
                reg_passenger_normal = parse_int(df.iloc[i, 3]) or 0
                reg_passenger_small = parse_int(df.iloc[i, 4]) or 0
                reg_passenger = reg_passenger_normal + reg_passenger_small
                
                # 注册车(不含K-car) 貨物車 = 普通+小型
                reg_cargo_normal = parse_int(df.iloc[i, 7]) or 0
                reg_cargo_small = parse_int(df.iloc[i, 8]) or 0
                reg_cargo = reg_cargo_normal + reg_cargo_small
                
                # K-car 部分
                kei_passenger = parse_int(df.iloc[i, 5]) or 0
                kei_cargo = parse_int(df.iloc[i, 9]) or 0
                
                # 注册車（不含軽）乗用
                if reg_passenger > 0:
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '乗用車(登録車)', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_name, reg_passenger))
                        year_inserted += c.rowcount
                    except: pass
                
                # 注册車（不含軽）貨物
                if reg_cargo > 0:
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '貨物車(登録車)', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_name, reg_cargo))
                        year_inserted += c.rowcount
                    except: pass
                
                # 軽自動車 乗用
                if kei_passenger > 0:
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '乗用車(軽)', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_name, kei_passenger))
                        year_inserted += c.rowcount
                    except: pass
                
                # 軽自動車 貨物
                if kei_cargo > 0:
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '貨物車(軽)', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_name, kei_cargo))
                        year_inserted += c.rowcount
                    except: pass
        
        print(f"  {year}: 新增 {year_inserted} 条")
        conn.commit()
    except Exception as e:
        print(f"  解析失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try: os.unlink(path)
        except: pass

# 验证
print("\n验证:")
c.execute("SELECT COUNT(*) FROM new_car_sales_brand")
print(f"总行数: {c.fetchone()[0]}")

# 抽查 2025/1
c.execute("SELECT brand, vehicle_type, sales_count FROM new_car_sales_brand WHERE year=2025 AND month=1 AND brand='トヨタ'")
print("\n2025/1 トヨタ:")
for r in c.fetchall():
    print(f"  {r[1]}: {r[2]:,}")

c.execute("SELECT brand, vehicle_type, sales_count FROM new_car_sales_brand WHERE year=2025 AND month=1 AND brand='スズキ'")
print("\n2025/1 スズキ:")
for r in c.fetchall():
    print(f"  {r[1]}: {r[2]:,}")

# 注册车合计
c.execute("""
    SELECT month, SUM(sales_count) FROM new_car_sales_brand 
    WHERE year=2025 AND vehicle_type IN ('乗用車(登録車)', '貨物車(登録車)')
    GROUP BY month ORDER BY month
""")
print("\n2025年 注册车(不含K-car) 月度合计:")
for r in c.fetchall():
    print(f"  {r[0]}月: {r[1]:,}")

conn.close()

"""重新下载和解析 JADA 2024-2025 年 Excel 数据"""
import sqlite3, sys, os, tempfile, re
import requests
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'japan_car_market.db')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ja,en;q=0.9",
}
TIMEOUT = 60

JADA_EXCEL_URLS = {
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

# 先删除 2024-2025 的旧数据（只剩 内輸入）
c.execute("DELETE FROM new_car_sales_brand WHERE year IN (2022, 2023, 2024, 2025)")
print(f"清除 2022-2025 旧数据: {c.rowcount} 行")
conn.commit()

# 下载并解析
for year in [2022, 2023, 2024, 2025]:
    url = JADA_EXCEL_URLS.get(year)
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
        print(f"  Sheets: {xl.sheet_names}")
        
        for sheet_name in xl.sheet_names:
            m = re.search(r"(\d{4})年(\d{1,2})月", sheet_name)
            if not m:
                continue
            y = int(m.group(1))
            mo = int(m.group(2))
            
            df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
            print(f"  Sheet '{sheet_name}': {df.shape[0]} rows x {df.shape[1]} cols")
            
            # 查看前10行，了解格式
            if mo == 1:
                for i in range(min(15, len(df))):
                    row_vals = []
                    for j in range(min(12, df.shape[1])):
                        v = df.iloc[i, j]
                        if pd.notna(v):
                            row_vals.append(f"[{j}]={v}")
                    if row_vals:
                        print(f"    Row {i}: {' '.join(row_vals)}")
            
            # 解析品牌数据
            # 策略: 寻找含有 "合計" 后缀的品牌行（这些是品牌小计行）
            # 或者寻找不含合計的品牌行但数据量足够
            inserted = 0
            for i in range(5, len(df)):  # 跳过前5行标题
                brand_parts = []
                for j in range(min(3, df.shape[1])):
                    v = str(df.iloc[i, j]).strip() if pd.notna(df.iloc[i, j]) else ""
                    if v and v != "nan":
                        brand_parts.append(v)
                brand_name = "".join(brand_parts).replace("　", "").strip()
                
                if not brand_name or brand_name == "nan":
                    continue
                
                # 跳过表头关键字
                if any(kw in brand_name for kw in ["ブランド", "新車", "販売", "乗用", "貨物", "普通", "小型", "前年"]):
                    continue
                
                # 跳过总合计行
                if brand_name in ("合計", "計", "総計"):
                    continue
                
                # 跳过"その他"行（不是具体品牌）
                if brand_name == "その他":
                    continue
                
                # 只保留带 "合計" 后缀的品牌行（品牌小计行）
                # 或者 2026年格式的不带合計的行
                is_total_row = brand_name.endswith("合計")
                
                if is_total_row:
                    # 去掉 "合計" 后缀，得到品牌名
                    brand_clean = brand_name[:-2].strip()
                else:
                    # 2026年格式：品牌行不带合計后缀
                    # 检查是否是子车型行（如 クラウン, カローラ 等）
                    # 策略：如果数据量够大（>100），认为是品牌行
                    passenger = parse_int(df.iloc[i, 6]) if df.shape[1] > 6 else None
                    if passenger is not None and passenger > 100:
                        brand_clean = brand_name
                    else:
                        continue  # 跳过子车型行
                
                # 读取乗用車計 (col6) 和 貨物車計 (col10)
                passenger = parse_int(df.iloc[i, 6]) if df.shape[1] > 6 else None
                cargo = parse_int(df.iloc[i, 10]) if df.shape[1] > 10 else None
                
                if (passenger is not None and passenger > 0):
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '乗用車', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_clean, passenger))
                        if c.rowcount > 0:
                            inserted += 1
                    except: pass
                
                if (cargo is not None and cargo > 0):
                    try:
                        c.execute("""
                            INSERT OR IGNORE INTO new_car_sales_brand
                            (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                            VALUES (?, ?, ?, '貨物車', ?, 'JADA', '2026-06-24')
                        """, (y, mo, brand_clean, cargo))
                        if c.rowcount > 0:
                            inserted += 1
                    except: pass
            
            print(f"    {y}/{mo}: 新增 {inserted} 条")
        
        conn.commit()
    except Exception as e:
        print(f"  解析失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try: os.unlink(path)
        except: pass

# 验证
print("\n" + "=" * 60)
for yr in [2022, 2023, 2024, 2025, 2026]:
    c.execute("""
        SELECT month, COUNT(DISTINCT brand), SUM(sales_count)
        FROM new_car_sales_brand WHERE year=?
        GROUP BY month ORDER BY month LIMIT 2
    """, (yr,))
    rows = c.fetchall()
    if rows:
        print(f"{yr}: {rows}")

c.execute("SELECT COUNT(*) FROM new_car_sales_brand")
print(f"总行数: {c.fetchone()[0]}")

conn.close()

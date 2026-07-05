"""
日本财务省贸易统计 - 汽车出口数据爬虫
通过财务省贸易统计API获取汽车出口数据
数据源: https://www.customs.go.jp/toukei/info/
API: https://api.e-stat.go.jp/ (总务省e-Stat API)
"""

import requests
import sqlite3
import time
import json
import re
from datetime import datetime

# 财务省贸易统计URL
# 可以通过HS品目代码查询
# HS 8703: 乗用車 ( automobiles )
# HS 8702: バス ( buses )
# HS 8704: 貨物自動車 ( trucks )
# HS 8711: オートバイ ( motorcycles )

# e-Stat API (政府统计综合窗口)
ESTAT_API = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"

# 财务省贸易统计直接CSV下载
CUSTOMS_CSV_BASE = "https://www.customs.go.jp/toukei/shinbun/trade-st/tsp/indexCA01.html"

# HS codes for vehicles
HS_CODES = {
    "8703": "乗用車",
    "870322": "HV乗用車",  # 1500cc-3000cc hybrid
    "870323": "EV乗用車",
    "870324": "PHV乗用車",
    "8702": "バス",
    "8704": "貨物自動車",
    "8711": "オートバイ",
}


def get_customs_trade_data(year, month):
    """从财务省贸易统计获取汽车出口数据"""
    # 财务省贸易统计的数据格式: 年月, 国名, HS品目, 重量, 価額, 数量
    # 直接访问财务省的CSV下载页面

    results = []
    base_url = f"https://www.customs.go.jp/toukei/shinbun/trade-st/tsp/CA01-{year}{month:02d}.html"

    print(f"  Fetching: {base_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = requests.get(base_url, headers=headers, timeout=30)
        resp.encoding = resp.apparent_encoding or "shift_jis"
        if resp.status_code == 200:
            # 解析HTML中的表格
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 5:
                        hs_code = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                        country = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        if hs_code.startswith("8703") or hs_code.startswith("8702") or hs_code.startswith("8704"):
                            results.append({
                                "hs_code": hs_code,
                                "country": country,
                                "raw": [c.get_text(strip=True) for c in cells],
                            })
        else:
            print(f"    HTTP {resp.status_code}")
    except Exception as e:
        print(f"    Error: {e}")

    return results


def fetch_estat_data(app_id, statsDataId, limit=10000):
    """通过e-Stat API获取统计数据"""
    params = {
        "appId": app_id,
        "statsDataId": statsDataId,
        "limit": limit,
        "format": "json",
    }
    try:
        resp = requests.get(ESTAT_API, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  e-Stat API error: {e}")
        return None


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS customs_trade_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            hs_code TEXT,
            hs_name TEXT,
            country_code TEXT,
            country_name TEXT,
            export_value_yen REAL,
            export_quantity INTEGER,
            export_weight_kg REAL,
            data_source TEXT DEFAULT 'customs.go.jp',
            crawl_date TEXT,
            UNIQUE(year, month, hs_code, country_code)
        )
    """)

    conn.commit()
    return conn


def scrape_customs_monthly(year, month):
    """爬取财务省月度贸易统计中的汽车相关数据"""
    print(f"\n  Processing {year}年{month}月...")

    # 财务省贸易统计URL格式变化，尝试多种格式
    urls_to_try = [
        f"https://www.customs.go.jp/toukei/shinbun/trade-st/tsp/CA01-{year}{month:02d}.html",
        f"https://www.customs.go.jp/toukei/shinbun/trade-st/tsp/CA01-{year}-{month:02d}.html",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "ja,en-US;q=0.9",
    }

    html = None
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                resp.encoding = resp.apparent_encoding or "shift_jis"
                html = resp.text
                print(f"    [OK] {url}")
                break
        except:
            pass

    if not html:
        print(f"    [WARN] No data found for {year}-{month}")
        return []

    # 解析数据
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    results = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            row_data = [c.get_text(strip=True) for c in cells]

            # 检查是否包含汽车HS代码
            first_cell = row_data[0]
            if first_cell.startswith("87") and len(first_cell) >= 4:
                hs_code = first_cell[:4]

                # 尝试解析数值
                value_yen = None
                quantity = None
                weight = None

                for cell in row_data[2:]:
                    # 金额（千日元）
                    val_match = re.search(r"([\d,]+)", cell)
                    if val_match and not value_yen:
                        num = int(re.sub(r"[^\d]", "", val_match.group(1)))
                        if num > 1000:
                            value_yen = num
                            continue
                    if val_match and value_yen and not quantity:
                        num = int(re.sub(r"[^\d]", "", val_match.group(1)))
                        if num > 0:
                            quantity = num
                            continue
                    if val_match and value_yen and quantity and not weight:
                        num = float(re.sub(r"[^\d.]", "", val_match.group(1)))
                        weight = num

                results.append({
                    "year": year,
                    "month": month,
                    "hs_code": hs_code,
                    "country_name": row_data[1] if len(row_data) > 1 else "",
                    "export_value_yen": value_yen,
                    "export_quantity": quantity,
                    "export_weight_kg": weight,
                })

    return results


def main():
    db_path = "data/japan_car_market.db"
    conn = init_db(db_path)

    print("=" * 60)
    print("Scraping customs trade statistics...")
    print("=" * 60)

    # 爬取最近12个月的数据
    now = datetime.now()
    total_data = []

    for i in range(12):
        d = datetime(now.year, now.month, 1)
        # 减去i个月
        if d.month - i <= 0:
            year = d.year - 1
            month = 12 + d.month - i
        else:
            year = d.year
            month = d.month - i

        data = scrape_customs_monthly(year, month)
        if data:
            total_data.extend(data)
            print(f"    Found {len(data)} vehicle-related records")
        time.sleep(1)

    # 保存到数据库
    c = conn.cursor()
    now_str = datetime.now().isoformat()

    inserted = 0
    for item in total_data:
        try:
            c.execute("""
                INSERT OR REPLACE INTO customs_trade_stats
                (year, month, hs_code, hs_name, country_code, country_name,
                 export_value_yen, export_quantity, export_weight_kg,
                 data_source, crawl_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["year"], item["month"], item["hs_code"],
                HS_CODES.get(item["hs_code"], ""),
                "",  # country_code
                item.get("country_name", ""),
                item.get("export_value_yen"),
                item.get("export_quantity"),
                item.get("export_weight_kg"),
                "customs.go.jp",
                now_str,
            ))
            inserted += 1
        except Exception as e:
            print(f"  [WARN] DB error: {e}")

    conn.commit()
    print(f"\n[OK] Saved {inserted} records to customs_trade_stats")

    # 统计
    total = c.execute("SELECT COUNT(*) FROM customs_trade_stats").fetchone()[0]
    print(f"[DONE] customs_trade_stats table: {total} records")

    conn.close()


if __name__ == "__main__":
    main()

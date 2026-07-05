"""
車選びドットコム 中古車市場統計レポート 爬虫 v2
准确解析每个月度报告中的年度表格数据
数据源: https://www.kurumaerabi.co.jp/useful_category/market/
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import json
from datetime import datetime

BASE_URL = "https://www.kurumaerabi.co.jp"
MARKET_URL = f"{BASE_URL}/useful_category/market/"


def get_page(url, retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    for i in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as e:
            print(f"  Retry {i+1}/{retries}: {e}")
            time.sleep(2)
    return None


def find_report_links():
    """找到所有月次报告链接"""
    print("Searching for monthly report links...")
    html = get_page(MARKET_URL)
    if not html:
        print("[ERROR] Cannot access market page")
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if "中古車市場統計レポート" in text or "月次市場レポート" in text:
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            date_match = re.search(r"(\d{4})年(\d{1,2})月", text)
            if date_match:
                links.append({
                    "url": full_url,
                    "title": text,
                    "year": int(date_match.group(1)),
                    "month": int(date_match.group(2)),
                })

    seen = set()
    unique = []
    for l in links:
        if l["url"] not in seen:
            seen.add(l["url"])
            unique.append(l)

    print(f"Found {len(unique)} report links")
    for l in unique:
        print(f"  {l['year']}年{l['month']}月: {l['url']}")
    return unique


def parse_report_tables(html):
    """解析报告页面中的所有表格数据"""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    all_tables = []
    for table in tables:
        rows = table.find_all("tr")
        table_data = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            row_data = [c.get_text(strip=True) for c in cells]
            if any(row_data):
                table_data.append(row_data)
        if table_data:
            all_tables.append(table_data)

    return all_tables


def extract_monthly_data(tables):
    """从表格中提取月度注册台数数据
    表格格式:
    行1: [空, 4月, 5月, 6月, 7月, 8月, 9月, 10月, 11月, 12月, 1月, 2月, 3月, 平均]
    行2: [新車登録台数, 342878, 324069, ...]
    行3: [前年比, 110.5%, 103.7%, ...]
    行4: [中古車登録台数, 544174, 506139, ...]
    行5: [前年比, 100.7%, 96.3%, ...]
    """
    results = []

    for table in tables:
        if len(table) < 3:
            continue

        # 找到包含月份表头的行
        header_row = None
        header_idx = -1
        for i, row in enumerate(table):
            row_text = " ".join(row)
            # 检查是否包含月份序列
            month_count = sum(1 for cell in row if re.match(r"^\d{1,2}月$", cell.strip()))
            if month_count >= 6:
                header_row = row
                header_idx = i
                break

        if not header_row:
            continue

        # 解析月份映射
        month_map = {}  # col_index -> month_number
        fiscal_year_start = None

        for j, cell in enumerate(header_row):
            cell = cell.strip()
            m = re.match(r"^(\d{1,2})月$", cell)
            if m:
                m_num = int(m.group(1))
                month_map[j] = m_num
                if m_num >= 4 and fiscal_year_start is None:
                    fiscal_year_start = m_num

        if not month_map:
            continue

        # 确定财政年度
        # 如果包含4月开始的序列，则财政年度 = 4月所在年份
        # 报告标题中的年份是报告发布月份的年份
        # 财政年度: 2026年度 = 2026年4月 ~ 2027年3月

        # 找数据行
        for row in table[header_idx + 1:]:
            if len(row) < 2:
                continue

            label = row[0].strip()

            # 新車登録台数
            if "新車" in label and "登録" in label and "台数" in label:
                for col_idx, month_num in month_map.items():
                    if col_idx < len(row):
                        val = parse_number(row[col_idx])
                        if val:
                            # 确定年份: 4-12月 = 财政年度那年, 1-3月 = 财政年度+1
                            if fiscal_year_start and fiscal_year_start >= 4:
                                if month_num >= 4:
                                    year = fiscal_year_start  # 需要从标题获取
                                else:
                                    year = fiscal_year_start + 1
                            else:
                                year = 2000  # placeholder
                            results.append({
                                "metric": "new_car_registered",
                                "month": month_num,
                                "year_from_header": year,
                                "value": val,
                            })

            # 中古車登録台数
            elif "中古車" in label and "登録" in label and "台数" in label:
                for col_idx, month_num in month_map.items():
                    if col_idx < len(row):
                        val = parse_number(row[col_idx])
                        if val:
                            results.append({
                                "metric": "used_car_registered",
                                "month": month_num,
                                "year_from_header": year,
                                "value": val,
                            })

            # 新車 前年比
            elif "前年比" in label and len(results) > 0:
                # 找到对应的新車/中古車行
                is_new = any(r["metric"] == "new_car_registered" for r in results[-20:])
                for col_idx, month_num in month_map.items():
                    if col_idx < len(row):
                        val = parse_percent(row[col_idx])
                        if val:
                            metric = "new_car_yoy" if is_new else "used_car_yoy"
                            results.append({
                                "metric": metric,
                                "month": month_num,
                                "value": val,
                            })

    return results


def parse_number(text):
    """从文本中提取数字"""
    text = text.strip().replace(",", "")
    m = re.search(r"(\d+)", text)
    if m:
        return int(m.group(1))
    return None


def parse_percent(text):
    """从文本中提取百分比"""
    text = text.strip()
    m = re.search(r"([\d.]+)%?", text)
    if m:
        return float(m.group(1))
    return None


def extract_rankings(tables):
    """提取销售排名表格"""
    rankings = []

    for table in tables:
        if len(table) < 2:
            continue

        # 检查是否是排名表
        first_cells = " ".join(table[0]) if table[0] else ""
        if "順位" in first_cells or "位" in first_cells:
            for row in table[1:]:
                if len(row) >= 2:
                    rank_match = re.search(r"(\d+)位", row[0])
                    if rank_match:
                        rank = int(rank_match.group(1))
                        name = row[1] if len(row) > 1 else ""
                        extra = row[2:] if len(row) > 2 else []
                        rankings.append({
                            "rank": rank,
                            "name": name,
                            "extra": extra,
                        })

    return rankings


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 月度注册台数
    c.execute("""
        CREATE TABLE IF NOT EXISTS market_report_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            new_car_registered INTEGER,
            used_car_registered INTEGER,
            new_car_yoy_pct REAL,
            used_car_yoy_pct REAL,
            data_source TEXT DEFAULT 'kurumaerabi',
            crawl_date TEXT,
            UNIQUE(year, month)
        )
    """)

    # 销售排名
    c.execute("""
        CREATE TABLE IF NOT EXISTS market_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_year INTEGER,
            report_month INTEGER,
            category TEXT,
            rank INTEGER,
            name TEXT,
            extra TEXT,
            data_source TEXT DEFAULT 'kurumaerabi',
            crawl_date TEXT,
            UNIQUE(report_year, report_month, category, rank, name)
        )
    """)

    conn.commit()
    return conn


def save_monthly_data(conn, all_monthly_data, report_year, report_month):
    """保存月度数据"""
    c = conn.cursor()
    now = datetime.now().isoformat()

    # 按月份分组
    month_data = {}
    for item in all_monthly_data:
        m = item.get("month")
        if m:
            if m not in month_data:
                month_data[m] = {}
            month_data[m][item["metric"]] = item["value"]

    # 推断年份
    # 报告是2026年3月发布的，包含2026年度数据（2026年4月~2027年3月）
    # 但报告中可能包含的是上一年的实际数据
    # 从表格中看到的月份序列: 4月~3月
    # 报告标题年份 = 数据中4月~12月的年份
    # 1月~3月 = 标题年份 + 1

    inserted = 0
    for month, data in month_data.items():
        if month >= 4:
            year = report_year
        else:
            year = report_year + 1

        # 但是报告可能引用的是去年的数据
        # 例如2026年3月报告中的数据可能是2025年度(2025年4月~2026年3月)的
        # 需要看表格标题 "2026年度" 或 "2025年度"

        new_car = data.get("new_car_registered")
        used_car = data.get("used_car_registered")
        new_yoy = data.get("new_car_yoy")
        used_yoy = data.get("used_car_yoy")

        if new_car or used_car:
            try:
                c.execute("""
                    INSERT OR REPLACE INTO market_report_monthly
                    (year, month, new_car_registered, used_car_registered,
                     new_car_yoy_pct, used_car_yoy_pct, data_source, crawl_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (year, month, new_car, used_car, new_yoy, used_yoy,
                      "kurumaerabi", now))
                inserted += 1
            except Exception as e:
                print(f"  [WARN] DB error: {e}")

    conn.commit()
    print(f"  [OK] Saved {inserted} monthly records")
    return inserted


def save_rankings(conn, rankings, report_year, report_month, category):
    """保存排名数据"""
    c = conn.cursor()
    now = datetime.now().isoformat()

    inserted = 0
    for r in rankings:
        try:
            c.execute("""
                INSERT OR REPLACE INTO market_rankings
                (report_year, report_month, category, rank, name, extra, data_source, crawl_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_year, report_month, category,
                  r["rank"], r["name"], json.dumps(r["extra"], ensure_ascii=False),
                  "kurumaerabi", now))
            inserted += 1
        except Exception as e:
            print(f"  [WARN] DB error: {e}")

    conn.commit()
    return inserted


def main():
    db_path = "data/japan_car_market.db"
    conn = init_db(db_path)

    # 1. 找到所有报告链接
    report_links = find_report_links()

    # 2. 爬取每个报告
    total_monthly = 0
    total_rankings = 0

    for link in report_links:
        print(f"\n  Crawling: {link['year']}年{link['month']}月...")
        html = get_page(link["url"])
        if not html:
            print(f"  [ERROR] Cannot fetch {link['url']}")
            continue

        tables = parse_report_tables(html)
        print(f"    Found {len(tables)} tables")

        # 提取月度注册数据
        monthly_data = extract_monthly_data(tables)
        if monthly_data:
            count = save_monthly_data(conn, monthly_data, link["year"], link["month"])
            total_monthly += count

        # 提取排名数据
        # 需要确定排名类别（国産ボディタイプ/国産車種/輸入ボディタイプ/輸入車種）
        soup = BeautifulSoup(html, "html.parser")

        # 找到所有标题，确定排名类别
        headings = soup.find_all(["h3", "h4", "h5"])
        current_category = None
        for heading in headings:
            h_text = heading.get_text(strip=True)

            if "ボディタイプ" in h_text and "国産" in h_text:
                current_category = "domestic_body_type"
            elif "車種別" in h_text and "国産" in h_text:
                current_category = "domestic_model"
            elif "ボディタイプ" in h_text and "輸入" in h_text:
                current_category = "imported_body_type"
            elif "車種別" in h_text and "輸入" in h_text:
                current_category = "imported_model"
            else:
                continue

            # 找后面的table
            table = heading.find_next("table")
            if table:
                table_data = []
                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    row_data = [c.get_text(strip=True) for c in cells]
                    if any(row_data):
                        table_data.append(row_data)

                if table_data:
                    rankings = []
                    for row in table_data[1:]:  # skip header
                        if len(row) >= 2:
                            rank_match = re.search(r"(\d+)位", row[0])
                            if rank_match:
                                rankings.append({
                                    "rank": int(rank_match.group(1)),
                                    "name": row[1],
                                    "extra": row[2:] if len(row) > 2 else [],
                                })

                    if rankings:
                        count = save_rankings(conn, rankings, link["year"], link["month"], current_category)
                        total_rankings += count
                        print(f"    {current_category}: {count} rankings")

        time.sleep(1)

    # 统计
    c = conn.cursor()
    monthly_total = c.execute("SELECT COUNT(*) FROM market_report_monthly").fetchone()[0]
    rankings_total = c.execute("SELECT COUNT(*) FROM market_rankings").fetchone()[0]

    print(f"\n{'='*60}")
    print(f"[DONE] market_report_monthly: {monthly_total} records")
    print(f"[DONE] market_rankings: {rankings_total} records")

    print(f"\nMonthly data (latest 12):")
    for row in c.execute("""
        SELECT year, month, new_car_registered, used_car_registered, new_car_yoy_pct, used_car_yoy_pct
        FROM market_report_monthly
        ORDER BY year DESC, month DESC
        LIMIT 12
    """):
        y, m, nc, uc, ny, uy = row
        ny_str = f"{ny}%" if ny else "N/A"
        uy_str = f"{uy}%" if uy else "N/A"
        nc_str = f"{nc:,}" if nc else "N/A"
        uc_str = f"{uc:,}" if uc else "N/A"
        print(f"  {y}年{m:02d}月: 新車={nc_str} ({ny_str}), 中古車={uc_str} ({uy_str})")

    print(f"\nRankings by category:")
    for row in c.execute("""
        SELECT category, COUNT(*), MIN(report_year), MAX(report_year)
        FROM market_rankings
        GROUP BY category
    """):
        print(f"  {row[0]}: {row[1]} records ({row[2]}~{row[3]})")

    conn.close()


if __name__ == "__main__":
    main()

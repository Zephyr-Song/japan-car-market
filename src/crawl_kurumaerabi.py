"""
車選びドットコム 中古車市場統計レポート 爬虫
爬取月次市场报告中的注册台数、销售排名等数据
数据源: https://www.kurumaerabi.co.jp/useful_category/market/
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
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
        # 匹配包含"中古車市場統計レポート"的链接
        if "中古車市場統計レポート" in text or "market" in href.lower():
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            # 提取报告日期
            date_match = re.search(r"(\d{4})年(\d{1,2})月", text)
            if date_match:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                links.append({
                    "url": full_url,
                    "title": text,
                    "year": year,
                    "month": month,
                })

    # 去重
    seen = set()
    unique_links = []
    for link in links:
        if link["url"] not in seen:
            seen.add(link["url"])
            unique_links.append(link)

    print(f"Found {len(unique_links)} report links")
    for l in unique_links[:5]:
        print(f"  {l['year']}年{l['month']}月: {l['url']}")
    return unique_links


def parse_report(html, url):
    """解析报告页面，提取注册台数和市场数据"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    data = {"url": url, "tables": [], "text_sections": []}

    # 1. 提取所有表格数据
    tables = soup.find_all("table")
    for table in tables:
        table_data = []
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            row_data = [c.get_text(strip=True) for c in cells]
            if any(row_data):
                table_data.append(row_data)
        if table_data:
            data["tables"].append(table_data)

    # 2. 提取注册台数数据
    # 模式: "新車登録台数" "中古車登録台数" "前月比" "前年比"
    reg_patterns = {
        "new_car_registered": r"新車登録台数[：:\s]*([\d,]+)",
        "used_car_registered": r"中古車登録台数[：:\s]*([\d,]+)",
        "new_car_yoy": r"新車.*?前年比[：:\s]*([\d.]+)%?",
        "used_car_yoy": r"中古車.*?前年比[：:\s]*([\d.]+)%?",
        "new_car_mom": r"新車.*?前月比[：:\s]*([\d.]+)%?",
        "used_car_mom": r"中古車.*?前月比[：:\s]*([\d.]+)%?",
    }

    for key, pattern in reg_patterns.items():
        match = re.search(pattern, text)
        if match:
            val_str = re.sub(r"[^\d.]", "", match.group(1))
            try:
                data[key] = float(val_str) if "." in val_str else int(val_str)
            except ValueError:
                pass

    # 3. 提取表格中的月度数据 (格式: 月份, 新車台数, 前年比, 中古車台数, 前年比)
    for table_data in data["tables"]:
        for row in table_data:
            if len(row) >= 3:
                # 检查是否是月度数据行
                month_match = re.match(r"(\d{1,2})月", row[0])
                if month_match:
                    month = int(month_match.group(1))
                    row_info = {"month": month, "raw": row}

                    # 尝试解析数值
                    for i, cell in enumerate(row[1:], 1):
                        num_match = re.findall(r"[\d,]+\.?\d*", cell.replace(",", ""))
                        if num_match:
                            try:
                                val = float(num_match[0]) if "." in num_match[0] else int(num_match[0])
                                row_info[f"col_{i}"] = val
                                row_info[f"col_{i}_text"] = cell
                            except (ValueError, IndexError):
                                pass

                    data["text_sections"].append(row_info)

    # 4. 提取销售排名
    ranking_section = None
    for heading in soup.find_all(["h3", "h4", "h5"]):
        h_text = heading.get_text(strip=True)
        if "ランキング" in h_text or "販売" in h_text:
            ranking_section = heading
            break

    if ranking_section:
        # 找后面的列表或表格
        sibling = ranking_section.find_next_sibling()
        while sibling:
            if sibling.name == "table":
                table_data = []
                for row in sibling.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    row_data = [c.get_text(strip=True) for c in cells]
                    if any(row_data):
                        table_data.append(row_data)
                if table_data:
                    data["rankings"] = table_data
                break
            elif sibling.name in ["ol", "ul"]:
                items = sibling.find_all("li")
                data["rankings_list"] = [li.get_text(strip=True) for li in items]
                break
            sibling = sibling.find_next_sibling()

    return data


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS market_report_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            new_car_registered INTEGER,
            used_car_registered INTEGER,
            new_car_yoy_pct REAL,
            used_car_yoy_pct REAL,
            new_car_mom_pct REAL,
            used_car_mom_pct REAL,
            raw_tables TEXT,
            data_source TEXT DEFAULT 'kurumaerabi',
            crawl_date TEXT,
            UNIQUE(year, month)
        )
    """)

    conn.commit()
    return conn


def save_to_db(conn, report_data, year, month):
    import json
    c = conn.cursor()
    now = datetime.now().isoformat()

    raw_json = json.dumps(report_data.get("tables", []), ensure_ascii=False)

    c.execute("""
        INSERT OR REPLACE INTO market_report_monthly
        (year, month, new_car_registered, used_car_registered,
         new_car_yoy_pct, used_car_yoy_pct, new_car_mom_pct, used_car_mom_pct,
         raw_tables, data_source, crawl_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        year, month,
        report_data.get("new_car_registered"),
        report_data.get("used_car_registered"),
        report_data.get("new_car_yoy"),
        report_data.get("used_car_yoy"),
        report_data.get("new_car_mom"),
        report_data.get("used_car_mom"),
        raw_json,
        "kurumaerabi",
        now,
    ))
    conn.commit()
    print(f"  [OK] Saved {year}年{month}月 report")


def main():
    db_path = "data/japan_car_market.db"
    conn = init_db(db_path)

    # 1. 找到所有报告链接
    report_links = find_report_links()

    if not report_links:
        print("[ERROR] No report links found, trying direct URL pattern...")
        # 尝试直接URL模式
        # https://www.kurumaerabi.co.jp/useful-details/7644/ (2025年1月)
        # 尝试最近的几个月
        for detail_id in range(7644, 7900):
            url = f"https://www.kurumaerabi.co.jp/useful-details/{detail_id}/"
            html = get_page(url)
            if html and "中古車市場統計レポート" in html:
                soup = BeautifulSoup(html, "html.parser")
                title = soup.find("h1")
                if title:
                    title_text = title.get_text(strip=True)
                    date_match = re.search(r"(\d{4})年(\d{1,2})月", title_text)
                    if date_match:
                        year = int(date_match.group(1))
                        month = int(date_match.group(2))
                        print(f"  Found: {year}年{month}月 at {url}")
                        report_data = parse_report(html, url)
                        save_to_db(conn, report_data, year, month)
                        time.sleep(1)

    # 2. 爬取每个报告
    for link in report_links:
        print(f"\n  Crawling: {link['year']}年{link['month']}月...")
        html = get_page(link["url"])
        if not html:
            print(f"  [ERROR] Cannot fetch {link['url']}")
            continue

        report_data = parse_report(html, link["url"])
        save_to_db(conn, report_data, link["year"], link["month"])

        # 打印摘要
        if report_data.get("new_car_registered"):
            print(f"    新車: {report_data['new_car_registered']:,}台")
        if report_data.get("used_car_registered"):
            print(f"    中古車: {report_data['used_car_registered']:,}台")
        if report_data.get("tables"):
            print(f"    テーブル数: {len(report_data['tables'])}")

        time.sleep(1)  # 礼貌延迟

    # 统计
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM market_report_monthly").fetchone()[0]
    print(f"\n{'='*60}")
    print(f"[DONE] market_report_monthly table: {total} records")

    for row in c.execute("SELECT year, month, new_car_registered, used_car_registered FROM market_report_monthly ORDER BY year DESC, month DESC LIMIT 10"):
        print(f"  {row[0]}年{row[1]}月: 新車={row[2]}, 中古車={row[3]}")

    conn.close()


if __name__ == "__main__":
    main()

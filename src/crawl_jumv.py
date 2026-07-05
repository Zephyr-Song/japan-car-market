"""
jumv.net 中古車輸出統計爬虫
爬取日本二手车出口统计数据：按车型（普通车/HV/EV/K-car/卡车/巴士）× 国别 × 月度
数据源: https://jumv.net/
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://jumv.net"
STATS_BASE = "/basic_knowledge_usedcar_export/export_statistics/statistics"

# 车型映射: shape code -> 名称
VEHICLE_TYPES = {
    1: "普通車",
    2: "トラック",
    4: "バス",
    8: "ハイブリッド",
    16: "軽自動車",
    32: "電気自動車",
}

# 国别代码 -> 国名（从页面抓取时动态填充，这里做缓存）
COUNTRY_CACHE = {}


def get_page(url, retries=3):
    """获取页面内容"""
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


def parse_monthly_ranking(html):
    """解析月度排行榜首页，获取各车型Top5国别数据"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # 首页有多个表格，每个车型一个
    # 结构: <h5><a>普通車</a></h5> 后面跟 <table>
    sections = soup.find_all(["h5", "h4"])

    for section in sections:
        text = section.get_text(strip=True)
        shape_name = None
        shape_code = None

        for code, name in VEHICLE_TYPES.items():
            if name in text:
                shape_name = name
                shape_code = code
                break

        if not shape_code:
            continue

        # 找后面的table
        table = section.find_next("table")
        if not table:
            continue

        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            rank_text = cells[0].get_text(strip=True)
            country_cell = cells[1]
            count_text = cells[2].get_text(strip=True)

            # 提取国名和链接
            country_link = country_cell.find("a")
            if country_link:
                country_name = country_link.get_text(strip=True)
                country_url = country_link.get("href", "")
                # 提取country code from URL
                code_match = re.search(r"country=(\w+)", country_url)
                country_code = code_match.group(1) if code_match else None
            else:
                country_name = country_cell.get_text(strip=True)
                country_code = None

            # 解析台数
            count = None
            count_clean = re.sub(r"[^\d]", "", count_text)
            if count_clean:
                count = int(count_clean)

            if count and country_name:
                results.append({
                    "shape_code": shape_code,
                    "shape_name": shape_name,
                    "rank": int(re.sub(r"[^\d]", "", rank_text)) if re.sub(r"[^\d]", "", rank_text) else 0,
                    "country_code": country_code,
                    "country_name": country_name,
                    "export_count": count,
                })

    return results


def parse_year_page(html, shape_code, year):
    """解析年度页面，获取该年度各月各国的出口台数"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # 年度页面通常有月度表格
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            # 尝试解析 "月 | 国名 | 台数" 或其他格式
            row_text = " | ".join(c.get_text(strip=True) for c in cells)
            # 查找月份数字
            month_match = re.match(r"(\d{1,2})月", cells[0].get_text(strip=True))
            if month_match:
                month = int(month_match.group(1))
                # 剩余cells是数据
                for cell in cells[1:]:
                    link = cell.find("a")
                    if link:
                        country_name = link.get_text(strip=True)
                        count_text = cell.get_text(strip=True)
                        count_clean = re.sub(r"[^\d]", "", count_text)
                        if count_clean:
                            results.append({
                                "year": year,
                                "month": month,
                                "shape_code": shape_code,
                                "country_name": country_name,
                                "export_count": int(count_clean),
                            })

    return results


def scrape_statistics_page(url):
    """爬取单个统计页面（按国家+车型+年份+月份）"""
    html = get_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # 提取总台数和平均FOB价格
    data = {}
    text = soup.get_text()

    # 总台数
    total_match = re.search(r"総台数[：:\s]*([\d,]+)", text)
    if total_match:
        data["total_count"] = int(re.sub(r"[^\d]", "", total_match.group(1)))

    # 平均FOB
    fob_match = re.search(r"平均FOB[：:\s]*([\d,]+)", text)
    if fob_match:
        data["avg_fob"] = int(re.sub(r"[^\d]", "", fob_match.group(1)))

    return data


def scrape_jumv_monthly():
    """爬取jumv.net首页最新月度排名"""
    print("=" * 60)
    print("爬取 jumv.net 月度出口排名...")
    print("=" * 60)

    html = get_page(BASE_URL)
    if not html:
        print("[ERROR] 无法获取jumv.net首页")
        return []

    rankings = parse_monthly_ranking(html)
    print(f"[OK] 获取 {len(rankings)} 条排名数据")

    # 提取最新月份
    soup = BeautifulSoup(html, "html.parser")
    date_text = soup.get_text()
    month_match = re.search(r"(\d{4})年(\d{2})月分", date_text)
    if month_match:
        year = int(month_match.group(1))
        month = int(month_match.group(2))
        print(f"[DATE] 数据月份: {year}年{month}月")
    else:
        # 使用当前月份
        now = datetime.now()
        year = now.year
        month = now.month - 1
        if month == 0:
            year -= 1
            month = 12
        print(f"[WARN] 未找到月份标注，使用: {year}年{month}月")

    # 为每条记录添加年月
    for r in rankings:
        r["year"] = year
        r["month"] = month

    return rankings


def scrape_jumv_history(years_back=3):
    """爬取历史年度数据"""
    print("\n" + "=" * 60)
    print(f"爬取 jumv.net 历史数据 (近{years_back}年)...")
    print("=" * 60)

    all_data = []
    current_year = datetime.now().year

    for shape_code, shape_name in VEHICLE_TYPES.items():
        for year in range(current_year, current_year - years_back - 1, -1):
            url = f"{BASE_URL}/basic_knowledge_usedcar_export/export_statistics/statistics-by-year?year_from={year}&shape={shape_code}"
            print(f"  爬取 {year}年 {shape_name}...")
            html = get_page(url)
            if not html:
                continue

            data = parse_year_page(html, shape_code, year)
            if data:
                all_data.extend(data)
                print(f"    [OK] {len(data)} 条")
            else:
                # 尝试从首页格式解析
                soup = BeautifulSoup(html, "html.parser")
                tables = soup.find_all("table")
                for table in tables:
                    rows = table.find_all("tr")
                    for row in rows[1:]:
                        cells = row.find_all("td")
                        if len(cells) >= 3:
                            country_link = cells[1].find("a") if len(cells) > 1 else None
                            country_name = country_link.get_text(strip=True) if country_link else cells[1].get_text(strip=True)
                            count_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            count_clean = re.sub(r"[^\d]", "", count_text)
                            if count_clean and country_name:
                                all_data.append({
                                    "year": year,
                                    "month": 0,  # 年度汇总
                                    "shape_code": shape_code,
                                    "shape_name": shape_name,
                                    "country_name": country_name,
                                    "export_count": int(count_clean),
                                })

            time.sleep(0.5)  # 礼貌延迟

    print(f"\n[OK] 历史数据总计 {len(all_data)} 条")
    return all_data


def init_db(db_path):
    """创建出口统计表"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS export_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            shape_code INTEGER,
            shape_name TEXT,
            rank INTEGER,
            country_code TEXT,
            country_name TEXT,
            export_count INTEGER,
            data_source TEXT DEFAULT 'jumv.net',
            crawl_date TEXT,
            UNIQUE(year, month, shape_code, country_name)
        )
    """)

    conn.commit()
    return conn


def save_to_db(conn, data_list):
    """保存数据到数据库"""
    c = conn.cursor()
    now = datetime.now().isoformat()

    inserted = 0
    updated = 0

    for item in data_list:
        try:
            c.execute("""
                INSERT OR REPLACE INTO export_statistics
                (year, month, shape_code, shape_name, rank, country_code, country_name, export_count, data_source, crawl_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("year"),
                item.get("month"),
                item.get("shape_code"),
                item.get("shape_name"),
                item.get("rank", 0),
                item.get("country_code"),
                item.get("country_name"),
                item.get("export_count"),
                item.get("data_source", "jumv.net"),
                now,
            ))
            if c.rowcount == 1:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            print(f"  [WARN] 保存失败: {e}, data={item}")

    conn.commit()
    print(f"\n[DB] 数据库写入完成: {inserted} 新增, {updated} 更新")


def main():
    db_path = "data/japan_car_market.db"
    conn = init_db(db_path)

    # 1. 爬取最新月度排名
    monthly_data = scrape_jumv_monthly()
    if monthly_data:
        save_to_db(conn, monthly_data)

    # 2. 爬取历史数据（近3年）
    history_data = scrape_jumv_history(years_back=3)
    if history_data:
        save_to_db(conn, history_data)

    # 打印统计
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM export_statistics").fetchone()[0]
    print(f"\n{'=' * 60}")
    print(f"[DONE] 爬取完成！export_statistics 表共 {total} 条记录")

    # 按车型统计
    print("\n按车型统计:")
    for row in c.execute("SELECT shape_name, COUNT(*), SUM(export_count) FROM export_statistics GROUP BY shape_name ORDER BY SUM(export_count) DESC"):
        print(f"  {row[0]}: {row[1]} 条, 总出口 {row[2]:,} 辆")

    # 最新月份Top5
    print("\n最新月度数据:")
    latest = c.execute("SELECT MAX(year), MAX(month) FROM export_statistics WHERE month > 0").fetchone()
    if latest[0]:
        print(f"  {latest[0]}年{latest[1]}月:")
        for row in c.execute("""
            SELECT shape_name, country_name, export_count, rank
            FROM export_statistics
            WHERE year=? AND month=? AND rank > 0
            ORDER BY shape_code, rank
        """, (latest[0], latest[1])):
            print(f"    {row[0]} - #{row[3]} {row[1]}: {row[2]:,}辆")

    conn.close()


if __name__ == "__main__":
    main()

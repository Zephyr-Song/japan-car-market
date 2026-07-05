"""
crawl_jama.py - JAMA (日本自動車工業会) 数据爬虫
抓取以下数据:
1. 四轮车年度统计 (生产/销售/进口/出口/保有) - 从 facts 页面
2. 海外生产统计 (四半期/年度) - 从 foreign_prdct 页面
3. 世界生产/销售/保有/输出统计 - 从 world facts 页面

数据源: https://www.jama.or.jp/statistics/
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = Path(__file__).parent.parent / "data" / "japan_car_market.db"
BASE_URL = "https://www.jama.or.jp"

def get_soup(url):
    """Fetch URL and return BeautifulSoup object"""
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None

def parse_number(text):
    """Extract number from Japanese text (handle commas, units like 万/千)"""
    if not text:
        return None
    text = text.strip()
    # Remove commas
    text = text.replace(",", "")
    # Handle patterns like "823万5千" or "442万1千"
    m = re.match(r"(\d+)万(\d+)千?", text)
    if m:
        return int(m.group(1)) * 10000 + int(m.group(2)) * 1000
    # Handle "823万"
    m = re.match(r"(\d+)万", text)
    if m:
        return int(m.group(1)) * 10000
    # Handle plain numbers
    m = re.match(r"(\d+)", text)
    if m:
        return int(m.group(1))
    return None

def extract_annual_data(html_text):
    """Extract annual statistics from JAMA four_wheeled page"""
    soup = BeautifulSoup(html_text, "html.parser")
    data = []
    
    # Find all h3/h4 headings and their following paragraphs
    for section in soup.find_all(["h3"]):
        heading = section.get_text(strip=True)
        
        # Get the next paragraph with data
        p = section.find_next("p")
        if not p:
            continue
        text = p.get_text(strip=True)
        
        # Parse different sections
        if "生産台数" in heading and "四輪車生産台数" in heading:
            # "四輪車生産台数は823万台"
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "total", "四輪車", 2024, total))
            
            # Parse breakdown
            # 乗用車: 713万9千台 (普通475万2千/小型113万3千/軽125万5千)
            m = re.search(r"乗用車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "passenger", "乗用車", 2024, val))
            
            m = re.search(r"普通車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "standard", "普通車", 2024, val))
            
            m = re.search(r"小型四輪車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "small", "小型四輪車", 2024, val))
            
            m = re.search(r"軽四輪車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "kei", "軽四輪車", 2024, val))
            
            m = re.search(r"トラックは.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "truck", "トラック", 2024, val))
            
            m = re.search(r"バスは.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("production", "bus", "バス", 2024, val))
        
        elif "販売台数" in heading and "四輪車販売台数" in heading and "新車" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("domestic_sales", "total_new", "新車販売合計", 2024, total))
            
            m = re.search(r"乗用車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("domestic_sales", "passenger_new", "乗用車(新車)", 2024, val))
        
        elif "輸入車販売" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("import_sales", "total", "輸入車販売合計", 2024, total))
            
            m = re.search(r"乗用車は.*?(\d+)万(\d+)千台", text)
            if m:
                val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("import_sales", "passenger", "輸入乗用車", 2024, val))
            
            m = re.search(r"商用車.*?(\d+)万台", text)
            if m:
                val = int(m.group(1)) * 10000
                data.append(("import_sales", "commercial", "輸入商用車", 2024, val))
        
        elif "輸入中古車" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("import_used", "total", "輸入中古車合計", 2024, total))
        
        elif "中古車販売" in heading and "四輪中古車" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("used_sales", "total", "中古車販売合計", 2024, total))
        
        elif "保有台数" in heading and "四輪車保有" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("ownership", "total", "保有台数合計", 2024, total))
        
        elif "輸出台数" in heading and "四輪車輸出" in heading:
            m = re.search(r"(\d+)万(\d+)千台", text)
            if m:
                total = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                data.append(("export", "total_new", "新車輸出合計", 2024, total))
            
            m = re.search(r"乗用車は.*?(\d+)万台", text)
            if m:
                val = int(m.group(1)) * 10000
                data.append(("export", "passenger_new", "乗用車輸出", 2024, val))
    
    # Parse 仕向地別輸出 (export by destination)
    for h4 in soup.find_all("h4"):
        h4_text = h4.get_text(strip=True)
        p = h4.find_next("p")
        if not p:
            continue
        text = p.get_text(strip=True)
        
        if "仕向地別" in h4_text or "アジア" in text:
            # Parse destinations
            destinations = {
                "北米": r"北米向け.*?(\d+)万(\d+)千台",
                "欧州": r"欧州向け.*?(\d+)万(\d+)千台",
                "アジア": r"アジア向け.*?(\d+)万(\d+)千台",
                "中近東": r"中近東向け.*?(\d+)万(\d+)千台",
                "大洋州": r"大洋州向け.*?(\d+)万(\d+)千台",
                "中南米": r"中南米向け.*?(\d+)万(\d+)千台",
                "アフリカ": r"アフリカ向け.*?(\d+)万(\d+)千台",
            }
            for dest, pattern in destinations.items():
                m = re.search(pattern, text)
                if m:
                    val = int(m.group(1)) * 10000 + int(m.group(2)) * 1000
                    data.append(("export_by_region", dest, dest, 2024, val))
    
    return data

def crawl_overseas_production():
    """Crawl JAMA overseas production statistics"""
    print("[1] Crawling JAMA overseas production statistics...")
    url = f"{BASE_URL}/statistics/foreign_prdct/index.html"
    soup = get_soup(url)
    if not soup:
        return []
    
    data = []
    # Find all report links - only crawl recent years (2020+)
    links = soup.find_all("a", href=re.compile(r"^20(2[0-9]|3[0-9])\d{4}\.html$"))
    print(f"  Found {len(links)} report links (filtering 2020+")
    
    for link in links:
        href = link.get("href")
        report_url = f"{BASE_URL}/statistics/foreign_prdct/{href}"
        title = link.get_text(strip=True)
        
        # Extract date from filename
        date_str = href.replace(".html", "")
        if len(date_str) == 8:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
        else:
            continue
        
        print(f"  Fetching: {title} ({date_str})")
        
        report_soup = get_soup(report_url)
        if not report_soup:
            continue
        
        # Parse tables
        tables = report_soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            current_period = None
            
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_texts = [c.get_text(strip=True) for c in cells]
                
                # Detect period headers
                joined = " ".join(cell_texts)
                if "四半期" in joined or "年度" in joined or "累計" in joined:
                    if "1四半期" in joined or "第1四半期" in joined:
                        current_period = "Q1"
                    elif "2四半期" in joined or "第2四半期" in joined:
                        current_period = "Q2"
                    elif "3四半期" in joined or "第3四半期" in joined:
                        current_period = "Q3"
                    elif "4四半期" in joined or "第4四半期" in joined:
                        current_period = "Q4"
                    elif "累計" in joined or "年度" in joined:
                        current_period = "annual"
                    continue
                
                # Parse data rows (region, value1, value2, yoy)
                if len(cell_texts) >= 4 and current_period:
                    region = cell_texts[0]
                    if region in ["アジア", "中近東", "欧州", "北米", "中南米", "アフリカ", "大洋州", "合計"]:
                        try:
                            val_current = int(cell_texts[1].replace(",", "")) if cell_texts[1] not in ["-", "－", ""] else 0
                            val_prev = int(cell_texts[2].replace(",", "")) if cell_texts[2] not in ["-", "－", ""] else 0
                            yoy_str = cell_texts[3].replace("%", "").replace("％", "")
                            yoy = float(yoy_str) if yoy_str not in ["-", "－", ""] else None
                            
                            data.append({
                                "report_date": f"{year}-{month:02d}-{day:02d}",
                                "period": current_period,
                                "region": region,
                                "current_value": val_current,
                                "previous_value": val_prev,
                                "yoy_percent": yoy,
                                "title": title
                            })
                        except (ValueError, IndexError):
                            pass
        
        time.sleep(0.3)  # Be polite
    
    print(f"  Total overseas production records: {len(data)}")
    return data

def crawl_jama_facts():
    """Crawl JAMA facts pages for annual summary data"""
    print("[2] Crawling JAMA facts pages...")
    
    pages = {
        "four_wheeled": f"{BASE_URL}/statistics/facts/four_wheeled/index.html",
        "world": f"{BASE_URL}/statistics/facts/world/index.html",
    }
    
    all_data = []
    
    for page_name, url in pages.items():
        print(f"  Fetching: {page_name}")
        soup = get_soup(url)
        if not soup:
            continue
        
        text = soup.get_text()
        data = extract_annual_data(str(soup))
        all_data.extend(data)
        print(f"    Extracted {len(data)} records from {page_name}")
    
    return all_data

def save_to_db(overseas_data, facts_data):
    """Save crawled data to database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create overseas production table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jama_overseas_production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT,
            period TEXT,
            region TEXT,
            current_value INTEGER,
            previous_value INTEGER,
            yoy_percent REAL,
            title TEXT
        )
    """)
    
    # Create JAMA annual facts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jama_annual_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            subcategory TEXT,
            label TEXT,
            year INTEGER,
            value INTEGER
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM jama_overseas_production")
    cursor.execute("DELETE FROM jama_annual_facts")
    
    # Insert overseas production data
    for record in overseas_data:
        cursor.execute("""
            INSERT INTO jama_overseas_production 
            (report_date, period, region, current_value, previous_value, yoy_percent, title)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record["report_date"], record["period"], record["region"],
            record["current_value"], record["previous_value"],
            record["yoy_percent"], record["title"]
        ))
    
    # Insert annual facts data
    for category, subcategory, label, year, value in facts_data:
        cursor.execute("""
            INSERT INTO jama_annual_facts
            (category, subcategory, label, year, value)
            VALUES (?, ?, ?, ?, ?)
        """, (category, subcategory, label, year, value))
    
    conn.commit()
    
    # Summary
    cursor.execute("SELECT COUNT(*) FROM jama_overseas_production")
    overseas_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jama_annual_facts")
    facts_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n[DB] Saved {overseas_count} overseas production records")
    print(f"[DB] Saved {facts_count} annual facts records")
    return overseas_count, facts_count

def main():
    print("=" * 60)
    print("JAMA Data Crawler")
    print("=" * 60)
    
    # 1. Crawl overseas production
    overseas_data = crawl_overseas_production()
    
    # 2. Crawl annual facts
    facts_data = crawl_jama_facts()
    
    # 3. Save to database
    if overseas_data or facts_data:
        save_to_db(overseas_data, facts_data)
    else:
        print("\n[WARN] No data collected!")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()

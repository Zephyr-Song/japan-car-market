"""
crawl_import_monthly.py - 爬取JAIA輸入車新規登録台数月次数据
从response.jp搜索并提取品牌别Top10排名+台数+同比
覆盖: 2024年1月~2026年5月
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import sqlite3
import sys
import io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = Path(__file__).parent.parent / "data" / "japan_car_market.db"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
}

# response.jp search URL
SEARCH_URL = "https://response.jp/search"

def search_articles(query, page=1):
    """Search response.jp for articles"""
    params = {'q': query, 'page': page}
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"  Search returned {resp.status_code}")
            return None
    except Exception as e:
        print(f"  Search error: {e}")
        return None

def parse_search_results(html):
    """Extract article URLs from search results"""
    soup = BeautifulSoup(html, 'html.parser')
    urls = []
    # Try various link patterns
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/article/' in href and href not in urls:
            urls.append(href)
    return urls

def fetch_article(url):
    """Fetch and parse an article"""
    try:
        if not url.startswith('http'):
            url = 'https://response.jp' + url
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"  Article {url} returned {resp.status_code}")
    except Exception as e:
        print(f"  Article fetch error: {e}")
    return None

def parse_article_for_import_data(html, url):
    """Extract JAIA import car registration data from article"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get article title
    title_tag = soup.find('h1') or soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ""
    
    # Get article text
    article = soup.find('article') or soup.find('div', class_='article-body') or soup.find('div', class_='entry-body')
    if not article:
        # Try to get all text
        text = soup.get_text()
    else:
        text = article.get_text()
    
    # Look for year/month in title or URL
    # Pattern: 2024年1月, 2025年6月, etc.
    ym_match = re.search(r'(\d{4})年(\d{1,2})月', title + ' ' + url)
    if not ym_match:
        # Try pattern in text
        ym_match = re.search(r'(\d{4})年(\d{1,2})月.*輸入車', text[:500])
    
    if not ym_match:
        return None
    
    year = int(ym_match.group(1))
    month = int(ym_match.group(2))
    
    # Only accept 2024-2026
    if year < 2024 or year > 2026:
        return None
    
    # Check this is about import car registration (輸入車新規登録)
    if '輸入車' not in text[:2000] and '輸入車' not in title:
        return None
    
    # Extract brand rankings - look for patterns like:
    # 1位：VW 4116台 (24.5%増)
    # 1位:フォルクスワーゲン 4116台(24.5%増)
    # Also: 1．VW 2,500台
    
    results = []
    
    # Multiple patterns for ranking extraction
    patterns = [
        # 1位：ブランド 4116台(24.5%増) or 1位:ブランド 4116台 (24.5%増)
        r'(\d{1,2})位[：:]\s*([^\s\d]+(?:\s+[^\s\d]+)?)\s+([\d,]+)\s*台\s*[(\（]([+-]?[\d.]+)%[)）]',
        # 1位：ブランド 4116台 (前年同月比24.5%増)
        r'(\d{1,2})位[：:]\s*([^\s\d]+(?:\s+[^\s\d]+)?)\s+([\d,]+)\s*台\s*[(\（]前年同月比([+-]?[\d.]+)%[)）]',
        # 1. ブランド 2,500台 (前年同月比X%増/減)
        r'(\d{1,2})[.．]\s*([^\s\d]+(?:\s+[^\s\d]+)?)\s+([\d,]+)\s*台',
        # ブランド 4116台（24.5%増）
        r'([^\s\d]+(?:\s+[^\s\d]+)?)\s+([\d,]+)\s*台\s*[（(]([+-]?[\d.]+)%[増減])',
    ]
    
    # Also look for table data
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_text = ' '.join(c.get_text(strip=True) for c in cells)
            # Try to extract brand, units, yoy from table row
            # Pattern: rank | brand | units | yoy
            m = re.match(r'(\d{1,2})\s+(.+?)\s+([\d,]+)\s+(.+)', row_text)
            if m:
                rank = int(m.group(1))
                brand = m.group(2).strip()
                units = int(m.group(3).replace(',', ''))
                yoy_str = m.group(4).strip()
                yoy_match = re.search(r'([+-]?[\d.]+)%', yoy_str)
                yoy = float(yoy_match.group(1)) if yoy_match else None
                if yoy and '減' in yoy_str:
                    yoy = -abs(yoy)
                results.append({
                    'year': year, 'month': month,
                    'brand': brand, 'rank': rank,
                    'units': units, 'yoy_pct': yoy
                })
    
    # If no table data, try regex on text
    if not results:
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                if len(m) >= 3:
                    rank = int(m[0]) if m[0].isdigit() else len(results) + 1
                    brand = m[1].strip()
                    units = int(m[2].replace(',', ''))
                    yoy = None
                    if len(m) >= 4:
                        try:
                            yoy = float(m[3])
                            if '減' in text[max(0, text.find(m[3])-20):text.find(m[3])+20]:
                                yoy = -abs(yoy)
                        except:
                            pass
                    if brand and units > 0 and rank <= 20:
                        results.append({
                            'year': year, 'month': month,
                            'brand': brand, 'rank': rank,
                            'units': units, 'yoy_pct': yoy
                        })
            if results:
                break
    
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        key = (r['brand'], r['units'])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    if unique:
        print(f"  [{year}-{month:02d}] Found {len(unique)} brands from {url}")
        for r in unique[:5]:
            print(f"    {r['rank']}. {r['brand']} {r['units']}台 ({r['yoy_pct']}%)")
    
    return unique if unique else None

def create_table(conn):
    """Create import_car_monthly table"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS import_car_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            brand TEXT,
            rank INTEGER,
            units INTEGER,
            yoy_pct REAL,
            data_source TEXT
        )
    """)
    conn.execute("DELETE FROM import_car_monthly")
    conn.commit()

def save_data(conn, data_list):
    """Save scraped data to database"""
    count = 0
    for data in data_list:
        for item in data:
            conn.execute(
                "INSERT INTO import_car_monthly (year, month, brand, rank, units, yoy_pct, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item['year'], item['month'], item['brand'], item['rank'],
                 item['units'], item['yoy_pct'], 'JAIA/response.jp')
            )
            count += 1
    conn.commit()
    return count

def main():
    print("=" * 70)
    print("JAIA Import Car Monthly Registration Data Crawler")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH))
    create_table(conn)
    
    all_data = []
    found_months = set()
    
    # Search queries for different time periods
    queries = [
        "輸入車 新規登録 台数 2024年",
        "輸入車 新規登録 台数 2025年",
        "輸入車 新規登録 台数 2026年",
        "JAIA 輸入車 ブランド別 登録台数 2024",
        "JAIA 輸入車 ブランド別 登録台数 2025",
        "JAIA 輸入車 ブランド別 登録台数 2026",
        "輸入車 ブランド別 速報 2024",
        "輸入車 ブランド別 速報 2025",
        "輸入車 ブランド別 速報 2026",
    ]
    
    # Also try direct article URL patterns
    # response.jp articles about import cars typically follow date patterns
    article_urls = []
    
    # Try Google cache approach - search for specific months
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 5:
                break
            q = f"response.jp 輸入車 新規登録 {year}年{month}月"
            print(f"\nSearching: {q}")
            html = search_articles(q)
            if html:
                urls = parse_search_results(html)
                print(f"  Found {len(urls)} article links")
                article_urls.extend(urls[:5])  # Top 5 per search
            time.sleep(1)
    
    # Deduplicate URLs
    article_urls = list(set(article_urls))
    print(f"\n\nTotal unique article URLs to check: {len(article_urls)}")
    
    # Fetch and parse each article
    for url in article_urls:
        print(f"\nFetching: {url}")
        html = fetch_article(url)
        if html:
            data = parse_article_for_import_data(html, url)
            if data:
                key = (data[0]['year'], data[0]['month'])
                if key not in found_months:
                    all_data.append(data)
                    found_months.add(key)
        time.sleep(2)  # Be polite
    
    # Save to database
    if all_data:
        count = save_data(conn, all_data)
        print(f"\n{'=' * 70}")
        print(f"Saved {count} records to import_car_monthly table")
        print(f"Months covered: {sorted(found_months)}")
    else:
        print(f"\n{'=' * 70}")
        print("No data found from response.jp search")
        print("Will use fallback data from public sources")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()

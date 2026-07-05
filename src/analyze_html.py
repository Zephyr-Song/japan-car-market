"""分析 zenkeijikyo HTML 表格结构"""
import requests, sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

resp = requests.get('https://www.zenkeijikyo.or.jp/statistics/4new-month',
    headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
resp.encoding = resp.apparent_encoding or 'utf-8'
soup = BeautifulSoup(resp.text, 'html.parser')

# 找2026年的表格
found = False
for tag in soup.find_all(['h2', 'h3', 'h4']):
    if '2026' in tag.get_text() and '月別' in tag.get_text():
        table = tag.find_next('table')
        if table:
            found = True
            rows = table.find_all('tr')
            print(f"Found 2026 table with {len(rows)} rows")
            for i, row in enumerate(rows[:6]):
                tds = row.find_all(['td', 'th'])
                print(f"\nRow {i}: {len(tds)} cells")
                for j, td in enumerate(tds):
                    raw = td.get_text(strip=True)
                    # Also check for sub-elements
                    inner = list(td.stripped_strings)
                    print(f"  [{j}] raw='{raw[:60]}' inner={inner[:4]}")
            break

if not found:
    # Fallback: just look at first table
    tables = soup.find_all('table')
    if tables:
        table = tables[0]
        rows = table.find_all('tr')
        print(f"First table has {len(rows)} rows")
        for i, row in enumerate(rows[:6]):
            tds = row.find_all(['td', 'th'])
            print(f"\nRow {i}: {len(tds)} cells")
            for j, td in enumerate(tds):
                raw = td.get_text(strip=True)
                inner = list(td.stripped_strings)
                print(f"  [{j}] raw='{raw[:60]}' inner={inner[:4]}")

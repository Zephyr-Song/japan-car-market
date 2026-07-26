"""分析 zenkeijikyo 4soku 品牌别速报 HTML 结构"""
import requests, sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

resp = requests.get('https://www.zenkeijikyo.or.jp/statistics/4soku',
    headers={'User-Agent': 'Mozilla/5.0'}, timeout=60, verify=False)
resp.encoding = resp.apparent_encoding or 'utf-8'
soup = BeautifulSoup(resp.text, 'html.parser')

# 找各 section
for h in soup.find_all(['h2','h3','h4']):
    htxt = h.get_text(strip=True)
    if any(kw in htxt for kw in ['総台数', '乗用車台数', '貨物車台数']):
        table = h.find_next('table')
        if not table:
            print(f"\nSection: {htxt} - NO TABLE")
            continue
        rows = table.find_all('tr')
        print(f"\n{'='*60}")
        print(f"Section: {htxt} ({len(rows)} rows)")
        print(f"{'='*60}")
        # 只打印前3行（表头+2个数据行）
        for i, row in enumerate(rows[:4]):
            tds = row.find_all(['td', 'th'])
            print(f"\nRow {i}: {len(tds)} cells")
            for j, td in enumerate(tds[:15]):
                raw = td.get_text(strip=True)
                print(f"  [{j}] '{raw[:40]}'")

from playwright.sync_api import sync_playwright
import time, re

with open("D:/japan-car-market/cjk_result2.txt", "w", encoding="utf-8") as f:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 2400})
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(6)
        
        tabs = page.locator('[data-baseweb="tab"]')
        tabs.nth(11).click()
        time.sleep(4)
        
        text = page.inner_text("body")
        chinese = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text)
        
        f.write(f"CJK groups found: {len(chinese)}\n")
        for c in chinese:
            f.write(f"  {c}\n")
        
        for region in ['North America', 'Middle East', 'Central/South America']:
            f.write(f"  '{region}' in text: {region in text}\n")
        for cjk in ['北美', '中近东', '中南美', '最新爬取']:
            f.write(f"  '{cjk}' in text: {cjk in text}\n")
        
        browser.close()

print("Done")

from playwright.sync_api import sync_playwright
import time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 2400})
    page.goto("http://localhost:8501", wait_until="networkidle")
    time.sleep(6)
    
    # Click tab 11 "Import & Export"
    tabs = page.locator('[data-baseweb="tab"]')
    tabs.nth(11).click()
    time.sleep(4)
    
    # Take full page screenshot
    page.screenshot(path="D:/japan-car-market/dashboard_full.png", full_page=True)
    
    # Get all text
    text = page.inner_text("body")
    
    # Write text to file for analysis
    with open("D:/japan-car-market/page_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    chinese = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text)
    
    # Write summary
    with open("D:/japan-car-market/cjk_result.txt", "w", encoding="utf-8") as f:
        f.write(f"CJK groups found: {len(chinese)}\n")
        for c in chinese:
            f.write(f"  {c}\n")
        f.write(f"\n'New Car Export' in text: {'New Car Export' in text}\n")
        for region in ['North America', 'Europe', 'Asia', 'Middle East', 'Oceania', 'Central/South America', 'Africa']:
            f.write(f"  '{region}' in text: {region in text}\n")
        for cjk in ['北美', '中近东', '中南美', '欧州', '非洲', '亚洲', '合计', '最新爬取']:
            f.write(f"  '{cjk}' in text: {cjk in text}\n")
    
    browser.close()

print("Done")

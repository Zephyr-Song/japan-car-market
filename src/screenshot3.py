"""Verify dashboard tab count and check for CJK characters."""
from playwright.sync_api import sync_playwright
import time, re, sys

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("http://localhost:8501", wait_until="networkidle")
    time.sleep(6)
    
    tabs = page.locator('[data-baseweb="tab"]')
    tab_count = tabs.count()
    
    # Write results to file to avoid encoding issues
    with open("D:/japan-car-market/verify_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Tab count: {tab_count}\n")
        for i in range(tab_count):
            f.write(f"  Tab {i}: {tabs.nth(i).inner_text()}\n")
        
        # Click last tab
        if tab_count > 0:
            tabs.nth(tab_count - 1).click()
            time.sleep(3)
        
        text = page.inner_text("body")
        chinese = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text)
        f.write(f"\nCJK chars found: {chinese[:30]}\n")
        
        # Check specific region names
        for region in ['North America', 'Europe', 'Asia', 'Middle East', 'Oceania', 'Central']:
            f.write(f"  '{region}' in page: {region in text}\n")
        for cjk in ['北美', '中近东', '中南美', '欧州', '非洲', '亚洲', '合计']:
            f.write(f"  '{cjk}' in page: {cjk in text}\n")
        
        # Scroll down and check for the export chart
        page.evaluate("window.scrollBy(0, 600)")
        time.sleep(2)
        text2 = page.inner_text("body")
        f.write(f"\nAfter scroll, 'New Car Export by Destination Region' in page: {'New Car Export' in text2}\n")
        chinese2 = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text2)
        f.write(f"CJK after scroll: {chinese2[:30]}\n")
    
    browser.close()

print("Results written to verify_result.txt")

"""Take screenshot of Streamlit dashboard to verify translations."""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("http://localhost:8501", wait_until="networkidle")
    time.sleep(5)  # Wait for Streamlit to fully render
    
    # Get all text content
    text = page.inner_text("body")
    
    # Check for Chinese characters
    import re
    chinese_chars = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text)
    print(f"Chinese/Japanese characters found on page: {chinese_chars[:30]}")
    
    # Click on the last tab "Import & Export"
    tabs = page.locator('[data-baseweb="tab"]')
    tab_count = tabs.count()
    print(f"Tab count: {tab_count}")
    
    if tab_count >= 12:
        tabs.nth(11).click()  # 0-indexed, tab 12 = "Import & Export"
        time.sleep(3)
        
        # Get text after clicking
        text2 = page.inner_text("body")
        chinese2 = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text2)
        print(f"Chinese/Japanese chars on Import&Export tab: {chinese2[:30]}")
        
        # Screenshot
        page.screenshot(path="dashboard_import_export.png", full_page=False)
        print("Screenshot saved: dashboard_import_export.png")
    
    browser.close()

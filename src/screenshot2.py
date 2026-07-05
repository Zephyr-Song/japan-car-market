"""Take screenshot of the 'New Car Export by Destination Region' chart."""
from playwright.sync_api import sync_playwright
import time, re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 1800})
    page.goto("http://localhost:8501", wait_until="networkidle")
    time.sleep(5)
    
    # Click on the last tab "Import & Export"
    tabs = page.locator('[data-baseweb="tab"]')
    tab_count = tabs.count()
    print(f"Tab count: {tab_count}")
    
    # Print all tab names
    for i in range(tab_count):
        print(f"  Tab {i}: {tabs.nth(i).inner_text()}")
    
    # Click last tab
    tabs.nth(tab_count - 1).click()
    time.sleep(3)
    
    # Scroll to find "New Car Export by Destination Region"
    page_text = page.inner_text("body")
    
    # Find the heading and scroll to it
    try:
        heading = page.locator("text=New Car Export by Destination Region")
        if heading.count() > 0:
            heading.scroll_into_view_if_needed()
            time.sleep(2)
            print("Found and scrolled to 'New Car Export by Destination Region'")
        else:
            print("Heading not found, trying alternative...")
            # Just scroll down
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(2)
    except:
        page.evaluate("window.scrollBy(0, 800)")
        time.sleep(2)
    
    # Get all text
    text = page.inner_text("body")
    chinese = re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+', text)
    print(f"Chinese/Japanese chars: {chinese[:30]}")
    
    # Screenshot
    page.screenshot(path="D:/japan-car-market/dashboard_export_region.png", full_page=False)
    print("Screenshot saved")
    
    browser.close()

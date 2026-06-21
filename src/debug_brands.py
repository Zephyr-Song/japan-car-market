"""调试：查看品牌筛选URL结构"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 检查トヨタ品牌页面的URL
    page.goto('https://www.carsensor.net/usedcar/', timeout=30000)
    page.wait_for_timeout(3000)
    
    # 找到品牌筛选链接
    brand_links = page.evaluate("""
        () => {
            const links = document.querySelectorAll('a[href*="/usedcar/"]');
            const brandUrls = [];
            for (const a of links) {
                const href = a.getAttribute('href') || '';
                const text = a.textContent.trim();
                // 找品牌链接（路径比 /usedcar/ 更长但不包含 /detail/）
                if (href.includes('/usedcar/') && !href.includes('/detail/') && text.length < 20 && text.length > 0) {
                    brandUrls.push({ href, text });
                }
            }
            return brandUrls;
        }
    """)
    
    print("=== 品牌筛选链接 ===")
    for item in brand_links[:30]:
        print(f"  {item['text']} -> {item['href']}")
    
    browser.close()

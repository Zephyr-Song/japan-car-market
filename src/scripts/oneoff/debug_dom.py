"""调试脚本：查看carsensor.net页面DOM结构"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.carsensor.net/usedcar/', timeout=30000)
    page.wait_for_timeout(3000)

    # 找detail链接的结构
    result = page.evaluate("""
        () => {
            const anchors = document.querySelectorAll('a');
            const detailAnchors = [];
            for (const a of anchors) {
                const href = a.getAttribute('href') || '';
                if (href.includes('/usedcar/detail/')) {
                    detailAnchors.push({
                        href: href,
                        textContent: a.textContent.substring(0, 100),
                        childCount: a.children.length,
                        hasScript: a.querySelector('script') !== null,
                        html: a.innerHTML.substring(0, 500)
                    });
                }
            }
            return detailAnchors.slice(0, 3);
        }
    """)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 也看看页面的整体结构
    structure = page.evaluate("""
        () => {
            // 找包含价格信息的块
            const allElements = document.querySelectorAll('div, li, section');
            const carBlocks = [];
            for (const el of allElements) {
                const text = el.innerText || '';
                if (text.includes('万円') && text.includes('年式') && text.length > 100 && text.length < 1000) {
                    carBlocks.push({
                        tag: el.tagName,
                        className: el.className.substring(0, 100),
                        text: text.substring(0, 300)
                    });
                    if (carBlocks.length >= 3) break;
                }
            }
            return carBlocks;
        }
    """)
    print("\n\n=== 车辆信息块 ===")
    print(json.dumps(structure, ensure_ascii=False, indent=2))

    browser.close()

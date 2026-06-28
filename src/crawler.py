"""
日本汽车市场数据采集 - Playwright 爬虫 v8 (P0 改进版)
改进:
  1. 增加爬取深度 PAGES_PER_CATEGORY = 50 (原10)
  2. 改进品牌识别 - 多方法提取 + 扩展品牌列表
  3. 增加异常价格过滤
"""

import sqlite3
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_PATH = "data/japan_car_market.db"

# P0 改进: 增加爬取深度
PAGES_PER_CATEGORY = 50

CATEGORIES = {
    '国产车': '/usedcar/spD/',
    '进口车': '/usedcar/spY/',
    '轻自动车': '/usedcar/spK/',
    'SUV': '/usedcar/bodytype/btX/',
    'MPV': '/usedcar/bodytype/btM/',
    '轿车': '/usedcar/bodytype/btS/',
    '掀背车': '/usedcar/bodytype/btD/',
    '旅行车': '/usedcar/bodytype/btW/',
    '跑车': '/usedcar/bodytype/btC/',
    '混合动力': '/usedcar/spH/',
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS used_cars")
    c.execute("""
        CREATE TABLE used_cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            price_total REAL,
            price_vehicle REAL,
            year TEXT,
            mileage TEXT,
            displacement TEXT,
            transmission TEXT,
            prefecture TEXT,
            category TEXT,
            link TEXT UNIQUE,
            crawl_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def parse_price(text):
    if not text:
        return None
    text = text.strip().replace(",", "").replace("万円", "").replace("万", "")
    try:
        return float(text)
    except ValueError:
        return None


EXTRACT_CARS_JS = """
(category) => {
    const results = [];
    const cassettes = document.querySelectorAll('.cassetteWrap.js-mainCassette');
    if (!cassettes.length) return results;

    // P0 改进: 扩展品牌列表 + 日文别名映射
    const BRANDS = [
        // 日本品牌
        'トヨタ','ホンダ','日産','スズキ','ダイハツ','マツダ','スバル','三菱',
        'レクサス','光岡','いすゞ','UDトラックス','日野',
        // 德国品牌
        'BMW','メルセデス・ベンツ','ベンツ','アウディ','フォルクスワーゲン',
        'ポルシェ','ミニ','オペル','Smart','スマート',
        // 欧洲其他
        'ボルボ','ジープ','ランドローバー','プジョー','シトロエン',
        'フィアット','アルファロメオ','ジャガー','ランボルギーニ',
        'フェラーリ','ベントレー','ロールスロイス','マセラティ',
        // 美国
        'テスラ','シボレー','フォード','キャデラック','GMC','ハマー',
        // 韩国/中国
        'ヒュンダイ','キア','サンヨン','BYD','Geely','ジーリー',
        // 其他
        'ルノー','レナウル','サアブ'
    ];

    // 品牌别名映射 (处理不同写法)
    const BRAND_ALIAS = {
        'ベンツ': 'メルセデス・ベンツ',
        'Smart': 'スマート',
        'レナウル': 'ルノー',
        'ハマー': 'GMC',
    };

    function normalizeBrand(b) {
        return BRAND_ALIAS[b] || b;
    }

    function findBrandInText(text) {
        if (!text) return '';
        const t = text.trim();
        // 精确匹配优先
        for (const b of BRANDS) {
            if (t === b) return normalizeBrand(b);
        }
        // 开头匹配
        for (const b of BRANDS) {
            if (t.startsWith(b)) return normalizeBrand(b);
        }
        // 包含匹配 (更宽松)
        for (const b of BRANDS) {
            if (t.includes(b)) return normalizeBrand(b);
        }
        return '';
    }

    for (const cassette of cassettes) {
        let brand = '';

        // 方法1: 检查所有带 class 的元素 (carsensor 通常用 class 标记品牌)
        const brandEl = cassette.querySelector('.makerName, .brandName, .maker, [class*="maker"], [class*="brand"]');
        if (brandEl) {
            brand = findBrandInText(brandEl.textContent);
        }

        // 方法2: 检查所有 p/span/a 元素的文本内容
        if (!brand) {
            const textEls = cassette.querySelectorAll('p, span, a');
            for (const el of textEls) {
                // 只检查短文本 (品牌名通常 < 15 字符)
                const t = el.textContent.trim();
                if (t.length > 0 && t.length < 20) {
                    brand = findBrandInText(t);
                    if (brand) break;
                }
            }
        }

        // 方法3: 检查图片 alt 文本 (品牌 logo)
        if (!brand) {
            const imgs = cassette.querySelectorAll('img[alt]');
            for (const img of imgs) {
                brand = findBrandInText(img.getAttribute('alt'));
                if (brand) break;
            }
        }

        // 方法4: 从 detail link 推断 (部分 carsensor 页面 URL 含品牌代码)
        if (!brand) {
            const linkEl = cassette.querySelector('a[href*="/usedcar/detail/"]');
            if (linkEl) {
                const href = linkEl.getAttribute('href') || '';
                // 部分 URL 模式: /usedcar/spD/brand_XXX/...
                const brandMatch = href.match(/spD\/brand_([^\/]+)/);
                if (brandMatch) {
                    // 尝试从 brand code 映射
                    const codeMap = {
                        'toyota': 'トヨタ', 'honda': 'ホンダ', 'nissan': '日産',
                        'suzuki': 'スズキ', 'daihatsu': 'ダイハツ', 'mazda': 'マツダ',
                        'subaru': 'スバル', 'mitsubishi': '三菱', 'lexus': 'レクサス'
                    };
                    const code = brandMatch[1].toLowerCase();
                    if (codeMap[code]) brand = codeMap[code];
                }
            }
        }

        // 提取 model: 从图片 alt 文本
        let model = '';
        const mainImg = cassette.querySelector('img[alt]');
        if (mainImg) {
            const alt = (mainImg.getAttribute('alt') || '').replace(/\\u00a0/g, ' ').trim();
            if (brand && alt.startsWith(brand)) {
                model = alt.substring(brand.length).trim();
            } else {
                model = alt;
            }
        }

        const detailLink = cassette.querySelector('a[href*="/usedcar/detail/"]');
        const link = detailLink ? new URL(detailLink.getAttribute('href'), 'https://www.carsensor.net').pathname : '';

        const text = cassette.innerText || '';
        const priceMatch = text.match(/車両本体価格[\\s\\S]*?([\\d,.]+)\\s*万円/);
        const totalPriceMatch = text.match(/支払総額[\\s\\S]*?([\\d,.]+)\\s*万円/);
        const yearMatch = text.match(/年式[\\s\\S]*?(\\d{4}\\s*\\([RHSH]\\s*\\d{2}\\)|\\d{4})/);
        const mileageMatch = text.match(/走行距離[\\s\\S]*?([\\d,.]+\\s*万?km)/);
        const dispMatch = text.match(/排気量[\\s\\S]*?(\\d+\\s*CC|\\d+\\s*cc|\\d+\\.\\d+\\s*[Ll])/);
        const transMatch = text.match(/ミッション[\\s\\S]*?([A-Z0-9]+)/);
        const prefMatch = text.match(/(東京都|北海道|[\\u4e00-\\u9fff]{2,3}県|京都府|大阪府)/);

        results.push({
            brand: brand || '',
            model: model.substring(0, 200),
            link,
            category,
            price_total: totalPriceMatch ? totalPriceMatch[1] : '',
            price_vehicle: priceMatch ? priceMatch[1] : '',
            year: yearMatch ? yearMatch[1] : '',
            mileage: mileageMatch ? mileageMatch[1] : '',
            displacement: dispMatch ? dispMatch[1] : '',
            transmission: transMatch ? transMatch[1] : '',
            prefecture: prefMatch ? prefMatch[1] : ''
        });
    }
    return results;
}
"""


def extract_cars_from_page(page, category=""):
    """从当前页面提取车辆数据 (改进版: 多方法品牌识别)"""
    return page.evaluate(EXTRACT_CARS_JS, category)


def insert_cars(conn, cars, crawl_date):
    c = conn.cursor()
    new_count = 0
    for car in cars:
        if not car.get('model') or not car.get('link'):
            continue
        # P0 改进: 过滤异常价格 (如 3,748 万円的 G63 可能是数据错误)
        price = parse_price(car.get('price_vehicle', ''))
        if price and (price < 1 or price > 5000):
            continue  # 过滤 <1万 或 >5000万円 的异常价格
        try:
            c.execute("""
                INSERT OR IGNORE INTO used_cars
                (brand, model, price_total, price_vehicle, year, mileage,
                 displacement, transmission, prefecture, category, link, crawl_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                car.get("brand", ""),
                car.get("model", ""),
                parse_price(car.get("price_total", "")),
                price,
                car.get("year", ""),
                car.get("mileage", ""),
                car.get("displacement", ""),
                car.get("transmission", ""),
                car.get("prefecture", ""),
                car.get("category", ""),
                car.get("link", ""),
                crawl_date
            ))
            if c.rowcount > 0:
                new_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return new_count


def crawl():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    crawl_date = datetime.now().strftime("%Y-%m-%d")
    total_cars = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for cat_name, cat_path in CATEGORIES.items():
            print(f"\\n=== [{cat_name}] ===")
            empty_pages = 0

            for page_num in range(1, PAGES_PER_CATEGORY + 1):
                if page_num == 1:
                    url = f"https://www.carsensor.net{cat_path}index.html"
                else:
                    url = f"https://www.carsensor.net{cat_path}index{page_num}.html"

                print(f"  Page {page_num}/{PAGES_PER_CATEGORY}: {url}")
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"    加载失败: {e}")
                    empty_pages += 1
                    if empty_pages >= 3:
                        print(f"    连续失败, 跳过 {cat_name} 后续页")
                        break
                    continue

                cars = extract_cars_from_page(page, cat_name)
                if not cars:
                    empty_pages += 1
                    print(f"    无数据 (连续空页: {empty_pages})")
                    if empty_pages >= 3:
                        break
                    continue
                empty_pages = 0  # 重置
                new = insert_cars(conn, cars, crawl_date)
                total_cars += new
                print(f"    提取 {len(cars)} 条, 新增 {new} 条 (累计: {total_cars})")
                time.sleep(1.5)  # P0 改进: 减少延迟, 但保持礼貌

            print(f"  [{cat_name}] 完成, 累计: {total_cars} 台")

        # 通用列表页
        print(f"\\n=== [通用列表] ===")
        for page_num in range(1, 31):
            if page_num == 1:
                url = "https://www.carsensor.net/usedcar/index.html"
            else:
                url = f"https://www.carsensor.net/usedcar/index{page_num}.html"
            print(f"  Page {page_num}: {url}")
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            except Exception as e:
                continue
            cars = extract_cars_from_page(page, "通用")
            if not cars:
                break
            new = insert_cars(conn, cars, crawl_date)
            total_cars += new
            print(f"    提取 {len(cars)} 条, 新增 {new} 条 (累计: {total_cars})")
            time.sleep(1.5)

        browser.close()

    conn.close()
    print(f"\\n✅ 采集完成! 共 {total_cars} 台车")
    print(f"数据库: {DB_PATH}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    crawl()

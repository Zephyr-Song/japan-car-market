"""
日本汽车市场数据采集 - Playwright 爬虫 v7 (最终版)
数据源: carsensor.net
URL结构发现:
  - 分页: /usedcar/index2.html, index3.html, ...
  - 国产车: /usedcar/spD/index.html, index2.html, ...
  - 进口车: /usedcar/spY/index.html, ...
  - K-car: /usedcar/spK/index.html, ...
  - 车型: /usedcar/bodytype/btX/index.html (SUV), btM (MPV), btS (sedan), ...
"""

import sqlite3
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_PATH = "data/japan_car_market.db"

# 采集分类和页数
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
PAGES_PER_CATEGORY = 10


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


def extract_cars_from_page(page, category=""):
    """从当前页面提取车辆数据"""
    return page.evaluate("""
        (category) => {
            const results = [];
            const cassettes = document.querySelectorAll('.cassetteWrap.js-mainCassette');
            
            for (const cassette of cassettes) {
                let brand = '';
                const pElements = cassette.querySelectorAll('p');
                for (const p of pElements) {
                    const t = p.textContent.trim();
                    const brands = ['トヨタ','ホンダ','日産','スズキ','ダイハツ','マツダ','スバル','三菱','レクサス','光岡','BMW','メルセデス・ベンツ','ベンツ','アウディ','フォルクスワーゲン','ポルシェ','ミニ','ボルボ','ジープ','ランドローバー','プジョー','シトロエン','フィアット','アルファロメオ','ジャガー','ランボルギーニ','フェラーリ','ベントレー','ロールスロイス','テスラ','BYD','シボレー','フォード','キャデラック','スマート','オペル','マセラティ'];
                    for (const b of brands) {
                        if (t === b || t.startsWith(b)) { brand = b; break; }
                    }
                    if (brand) break;
                }
                
                let model = '';
                const mainImg = cassette.querySelector('img[alt]');
                if (mainImg) {
                    const alt = (mainImg.getAttribute('alt') || '').replace(/\\u00a0/g, ' ').trim();
                    const parts = alt.split(/\\s+/);
                    if (parts.length > 1 && parts[0] === brand) {
                        model = parts.slice(1).join(' ').trim();
                    } else {
                        model = alt;
                    }
                }
                
                const detailLink = cassette.querySelector('a[href*="/usedcar/detail/"]');
                const link = detailLink ? detailLink.getAttribute('href') : '';
                
                const text = cassette.innerText || '';
                const priceMatch = text.match(/車両本体価格[\\s\\S]*?([\\d,.]+)\\s*万円/);
                const totalPriceMatch = text.match(/支払総額[\\s\\S]*?([\\d,.]+)\\s*万円/);
                const yearMatch = text.match(/年式[\\s\\S]*?(\\d{4}\\s*\\([RHSH]\\s*\\d{2}\\)|\\d{4})/);
                const mileageMatch = text.match(/走行距離[\\s\\S]*?([\\d,.]+\\s*万?km)/);
                const dispMatch = text.match(/排気量[\\s\\S]*?(\\d+\\s*CC|\\d+\\s*cc|\\d+\\.\\d+\\s*[Ll])/);
                const transMatch = text.match(/ミッション[\\s\\S]*?([A-Z0-9]+)/);
                const prefMatch = text.match(/(東京都|北海道|[\\u4e00-\\u9fff]{2,3}県|京都府|大阪府)/);
                
                results.push({
                    brand, model: model.substring(0, 200), link, category,
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
    """, category)


def insert_cars(conn, cars, crawl_date):
    c = conn.cursor()
    new_count = 0
    for car in cars:
        if not car.get('model') or not car.get('link'):
            continue
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
                parse_price(car.get("price_vehicle", "")),
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
            print(f"\n=== [{cat_name}] ===")
            
            for page_num in range(1, PAGES_PER_CATEGORY + 1):
                if page_num == 1:
                    url = f"https://www.carsensor.net{cat_path}index.html"
                else:
                    url = f"https://www.carsensor.net{cat_path}index{page_num}.html"

                print(f"  Page {page_num}: {url}")
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"    加载失败: {e}")
                    continue

                cars = extract_cars_from_page(page, cat_name)
                if not cars:
                    print(f"    无数据，跳过后续页")
                    break
                new = insert_cars(conn, cars, crawl_date)
                total_cars += new
                print(f"    提取 {len(cars)} 条，新增 {new} 条 (累计: {total_cars})")
                time.sleep(2)

        # 也采集通用列表页
        print(f"\n=== [通用列表] ===")
        for page_num in range(1, 11):
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
            print(f"    提取 {len(cars)} 条，新增 {new} 条 (累计: {total_cars})")
            time.sleep(2)

        browser.close()

    conn.close()
    print(f"\n✅ 采集完成! 共 {total_cars} 台车")
    print(f"数据库: {DB_PATH}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    crawl()

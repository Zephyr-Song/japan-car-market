"""
Lightweight incremental crawler — only fetches latest listings (first 2 pages per category)
Run this periodically to keep data fresh without full re-crawl
"""

import sqlite3
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'japan_car_market.db')

CATEGORIES = {
    'Domestic': '/usedcar/spD/',
    'Import': '/usedcar/spY/',
    'K-car': '/usedcar/spK/',
    'SUV': '/usedcar/bodytype/btX/',
    'MPV': '/usedcar/bodytype/btM/',
    'Sedan': '/usedcar/bodytype/btS/',
    'Hatchback': '/usedcar/bodytype/btD/',
    'Hybrid': '/usedcar/spH/',
}
# Only crawl first 2 pages per category for speed
PAGES_PER_CATEGORY = 2


def ensure_table(conn):
    """Create table if not exists (don't drop existing data)"""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS used_cars (
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


def parse_price(text):
    if not text:
        return None
    text = text.strip().replace(",", "").replace("万円", "").replace("万", "")
    try:
        return float(text)
    except ValueError:
        return None


BRANDS_LIST = ['トヨタ','ホンダ','日産','スズキ','ダイハツ','マツダ','スバル','三菱','レクサス','光岡','BMW','メルセデス・ベンツ','ベンツ','アウディ','フォルクスワーゲン','ポルシェ','ミニ','ボルボ','ジープ','ランドローバー','プジョー','シトロエン','フィアット','アルファロメオ','ジャガー','ランボルギーニ','フェラーリ','ベントレー','ロールスロイス','テスラ','BYD','シボレー','フォード','キャデラック','スマート','オペル','マセラティ']

JS_EXTRACT = """
(brandList) => {
    const results = [];
    const cassettes = document.querySelectorAll('.cassetteWrap.js-mainCassette');
    for (const cassette of cassettes) {
        let brand = '';
        const pElements = cassette.querySelectorAll('p');
        for (const p of pElements) {
            const t = p.textContent.trim();
            for (const b of brandList) {
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
            brand, model: model.substring(0, 200), link, category: '',
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


def insert_cars(conn, cars, crawl_date, category=""):
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
                category,
                car.get("link", ""),
                crawl_date
            ))
            if c.rowcount > 0:
                new_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return new_count


def crawl_incremental():
    """Incremental crawl — only first few pages, INSERT OR IGNORE existing"""
    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)
    crawl_date = datetime.now().strftime("%Y-%m-%d")
    total_new = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for cat_name, cat_path in CATEGORIES.items():
            for page_num in range(1, PAGES_PER_CATEGORY + 1):
                if page_num == 1:
                    url = f"https://www.carsensor.net{cat_path}index.html"
                else:
                    url = f"https://www.carsensor.net{cat_path}index{page_num}.html"

                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"  [{cat_name}] p{page_num} failed: {e}")
                    continue

                cars = page.evaluate(JS_EXTRACT, BRANDS_LIST)
                if not cars:
                    break
                for car in cars:
                    car['category'] = cat_name
                new = insert_cars(conn, cars, crawl_date, cat_name)
                total_new += new
                print(f"  [{cat_name}] p{page_num}: {len(cars)} found, {new} new")
                time.sleep(1.5)

        browser.close()

    conn.close()
    print(f"\n✅ Incremental update: {total_new} new vehicles added")
    return total_new


if __name__ == "__main__":
    crawl_incremental()

"""
Goo-net 数据采集模块 v1
=========================
日本第二大二手车平台 (月访问 2400万, 挂牌 50万台)
与 carsensor 数据互补, 提供:
  1. 出口 FOB 价格 (海外买家视角)
  2. 拍卖检测评级 (条件等级)
  3. 扩大样本覆盖 (当前 carsensor ~1000台, goo-net 可补充 5000+台)
"""

import sqlite3
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_PATH = "data/japan_car_market.db"

PAGES_PER_CATEGORY = 5  # 测试用, 正式跑改更大

# Goo-net URL 结构
CATEGORIES = {
    '国产车': '/usedcar/search/p_maker_id:1/',
    '进口车': '/usedcar/search/p_maker_id:2/',
    '轻自动车': '/usedcar/search/p_maker_id:3/',
    'SUV': '/usedcar/search/p_body_type_id:1/',
    'MPV': '/usedcar/search/p_body_type_id:6/',
    '轿车': '/usedcar/search/p_body_type_id:2/',
    '掀背车': '/usedcar/search/p_body_type_id:5/',
    '旅行车': '/usedcar/search/p_body_type_id:3/',
    '跑车': '/usedcar/search/p_body_type_id:4/',
    '混合动力': '/usedcar/search/p_fuel_type_id:4/',
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}


def parse_price(text):
    if not text:
        return None
    text = text.strip().replace(",", "").replace("万円", "").replace("万", "")
    try:
        return float(text)
    except ValueError:
        return None


EXTRACT_GOONET_CARS_JS = """
(category) => {
    const results = [];
    // Goo-net listing cards
    const cards = document.querySelectorAll('.search_result, .car_list_item, [class*="carItem"], [class*="listing_item"], li[class*="list"]');

    for (const card of cards) {
        const text = card.innerText || '';

        // 品牌: Goo-net 通常在 a 标签或 heading 里标注品牌
        let brand = '';
        const brandLink = card.querySelector('a[href*="/ucar/"], a[href*="/usedcar/"], .maker_name, .brand_name, [class*="maker"]');
        if (brandLink) {
            const t = brandLink.textContent.trim();
            const brands = ['トヨタ','ホンダ','日産','スズキ','ダイハツ','マツダ','スバル','三菱',
                'レクサス','光岡','いすゞ','BMW','メルセデス・ベンツ','ベンツ','アウディ',
                'フォルクスワーゲン','ポルシェ','ミニ','ボルボ','ジープ','ランドローバー',
                'テスラ','BYD','シボレー','フォード','フィアット','アルファロメオ',
                'ジャガー','ルノー','プジョー','シトロエン','ヒュンダイ','キア'];
            for (const b of brands) {
                if (t === b || t.startsWith(b) || t.includes(b)) { brand = b; break; }
            }
        }

        // 如果在 card 文本开头找到品牌
        if (!brand) {
            const fullText = text.trim().split(/\\s+/)[0];
            const brands = ['トヨタ','ホンダ','日産','スズキ','ダイハツ','マツダ','スバル','三菱',
                'レクサス','光岡','いすゞ','BMW','メルセデス・ベンツ','ベンツ','アウディ',
                'フォルクスワーゲン','ポルシェ','ミニ','ボルボ','ジープ','ランドローバー',
                'テスラ','BYD','シボレー','フォード'];
            for (const b of brands) {
                if (fullText === b || fullText.startsWith(b)) { brand = b; break; }
            }
        }

        // 车型
        let model = '';
        const modelLink = card.querySelector('a[href*="/ucar/"], .model_name, [class*="model"], [class*="car_name"], h3, h4');
        if (modelLink) {
            const t = modelLink.textContent.trim();
            model = brand && t.startsWith(brand) ? t.substring(brand.length).trim() : t;
        }

        // 链接
        const linkEl = card.querySelector('a[href*="/ucar/"], a[href*="/usedcar/"]');
        const link = linkEl ? new URL(linkEl.getAttribute('href'), 'https://www.goo-net.com').pathname : '';

        // 价格
        const priceMatch = text.match(/(?:本体価格|総額)[^\\d]*([\\d,.]+)\\s*(?:万円|万)/);
        const totalMatch = text.match(/(?:支払総額|総額)[^\\d]*([\\d,.]+)\\s*(?:万円|万)/);

        // 年式
        const yearMatch = text.match(/年式[^\\d]*(\\d{4}|令和\\s*\\d+|平成\\s*\\d+|昭和\\s*\\d+)/);

        // 走行距离
        const mileageMatch = text.match(/走行[^\\d]*([\\d,.]+)\\s*(?:万\\s*)?km/);

        // 排気量
        const dispMatch = text.match(/排気量[^\\d]*(\\d+\\s*[Cc]{2}|\\d+\\.\\d+\\s*L)/);

        // 所在
        const prefMatch = text.match(/(東京都|北海道|[\\u4e00-\\u9fff]{2,3}県|京都府|大阪府)/);

        results.push({
            brand: brand || '', model: model.substring(0, 200), link, category,
            price_total: totalMatch ? totalMatch[1] : (priceMatch ? priceMatch[1] : ''),
            price_vehicle: priceMatch ? priceMatch[1] : '',
            year: yearMatch ? yearMatch[1] : '',
            mileage: mileageMatch ? mileageMatch[1] : '',
            displacement: dispMatch ? dispMatch[1] : '',
            transmission: '', prefecture: prefMatch ? prefMatch[1] : '',
            source: 'goo-net'
        });
    }
    return results;
}
"""


def init_goonet_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS goonet_cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT, model TEXT, price_total REAL, price_vehicle REAL,
            year TEXT, mileage TEXT, displacement TEXT, transmission TEXT,
            prefecture TEXT, category TEXT, link TEXT UNIQUE,
            source TEXT DEFAULT 'goo-net', crawl_date TEXT
        )
    """)
    conn.commit()


def insert_goonet_cars(conn, cars, crawl_date):
    c = conn.cursor()
    new_count = 0
    for car in cars:
        if not car.get('model') or not car.get('link'):
            continue
        price = parse_price(car.get('price_vehicle', ''))
        if price is not None and (price < 1 or price > 5000):
            continue
        try:
            c.execute("""
                INSERT OR IGNORE INTO goonet_cars
                (brand, model, price_total, price_vehicle, year, mileage,
                 displacement, transmission, prefecture, category, link, source, crawl_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                car.get("brand", ""), car.get("model", ""),
                parse_price(car.get("price_total", "")), price,
                car.get("year", ""), car.get("mileage", ""),
                car.get("displacement", ""), car.get("transmission", ""),
                car.get("prefecture", ""), car.get("category", ""),
                car.get("link", ""), "goo-net", crawl_date
            ))
            if c.rowcount > 0:
                new_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return new_count


def crawl_goonet():
    """从 Goo-net 采集二手车数据"""
    print("=" * 60)
    print("Goo-net 数据采集 (日本第二大二手车平台)")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    init_goonet_table(conn)
    crawl_date = datetime.now().strftime("%Y-%m-%d")
    total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers(HEADERS)

        for cat_name, cat_path in CATEGORIES.items():
            print(f"\n--- [{cat_name}] ---")
            empty_count = 0

            for idx in range(1, PAGES_PER_CATEGORY + 1):
                url = f"https://www.goo-net.com{cat_path}?page={idx}"
                print(f"  Page {idx}: {url}")

                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"    加载失败: {e}")
                    empty_count += 1
                    if empty_count >= 3:
                        break
                    continue

                cars = page.evaluate(EXTRACT_GOONET_CARS_JS, cat_name)
                if not cars:
                    empty_count += 1
                    print(f"    无数据 ({empty_count})")
                    if empty_count >= 3:
                        break
                    continue

                empty_count = 0
                new = insert_goonet_cars(conn, cars, crawl_date)
                total += new
                print(f"    提取 {len(cars)} 条, 新增 {new} 条 (累计: {total})")
                time.sleep(1.2)

            print(f"  [{cat_name}] 完成")

        browser.close()

    conn.close()
    print(f"\n✅ Goo-net 采集完成! 共 {total} 台车")
    return total


# ============================================================
# 数据合并: 将 goonet_cars 合并到 used_cars 统一分析
# ============================================================

def merge_to_main():
    """将 Goo-net 数据合并到主表 used_cars, 去重依据 link"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 确保 used_cars 表存在
    c.execute("""
        CREATE TABLE IF NOT EXISTS used_cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT, model TEXT, price_total REAL, price_vehicle REAL,
            year TEXT, mileage TEXT, displacement TEXT, transmission TEXT,
            prefecture TEXT, category TEXT, link TEXT UNIQUE, crawl_date TEXT,
            source TEXT DEFAULT 'carsensor'
        )
    """)

    # 检查 used_cars 表是否有 source 列
    cols = [col[1] for col in c.execute("PRAGMA table_info(used_cars)").fetchall()]
    if 'source' not in cols:
        c.execute("ALTER TABLE used_cars ADD COLUMN source TEXT DEFAULT 'carsensor'")
        conn.commit()

    # 从 goonet_cars 迁移到 used_cars
    c.execute("SELECT * FROM goonet_cars")
    rows = c.fetchall()
    if not rows:
        print("Goo-net 表中无数据, 跳过合并")
        conn.close()
        return 0

    col_names = [desc[0] for desc in c.description]
    merged = 0
    for row in rows:
        d = dict(zip(col_names, row))
        if not d.get('model') or not d.get('link'):
            continue
        try:
            c.execute("""
                INSERT OR IGNORE INTO used_cars
                (brand, model, price_total, price_vehicle, year, mileage,
                 displacement, transmission, prefecture, category, link, crawl_date, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d.get('brand', ''), d.get('model', ''),
                d.get('price_total'), d.get('price_vehicle'),
                d.get('year', ''), d.get('mileage', ''),
                d.get('displacement', ''), d.get('transmission', ''),
                d.get('prefecture', ''), d.get('category', ''),
                d.get('link', ''), d.get('crawl_date', ''),
                'goo-net'
            ))
            if c.rowcount > 0:
                merged += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print(f"合并完成: goo-net → used_cars, 新增 {merged} 条")
    return merged


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    crawl_goonet()
    merge_to_main()

"""
日本汽车市场宏观数据补充爬虫 v2
数据源:
  1. JADA - 品牌别注册车销量 (Excel .xls, multi-sheet)
  2. 全国軽自動車協会連合会 (zenkeijikyo) - K-car 月别推移 + 品牌别速报 (HTML)
  3. MarkLines - 日本月度销量摘要 (HTML + 已知公开数据)
  4. JAIA - 进口车数据 (待探索)
所有数据存入 data/japan_car_market.db 的新表中, 支持增量更新.
"""

import sys
import os
import re
import sqlite3
import tempfile
from datetime import datetime
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "japan_car_market.db")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}
TIMEOUT = 60

REIWA_BASE = 2018  # 令和N年 = 2018+N
HEISEI_BASE = 1988  # 平成N年 = 1988+N


def reiwa_to_ce(n: int) -> int:
    return REIWA_BASE + n


def heisei_to_ce(n: int) -> int:
    return HEISEI_BASE + n


def parse_int(text) -> int | None:
    """解析日文逗号分隔数字, 如 138,920 → 138920"""
    if text is None:
        return None
    s = str(text).replace(",", "").replace("％", "").replace("%", "").strip()
    if not s or s in ("-", "‐", "—", "−"):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def parse_float(text) -> float | None:
    """解析百分比如 -3.4 → -3.4"""
    if text is None:
        return None
    s = str(text).replace(",", "").replace("％", "").replace("%", "").strip()
    if not s or s in ("-", "‐", "—", "−"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def download_file(url: str, suffix: str = ".xls") -> str | None:
    """下载文件到临时路径, 返回路径; 失败返回 None."""
    try:
        print(f"  下载: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(resp.content)
        print(f"  已保存临时文件: {path} ({len(resp.content)} bytes)")
        return path
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        return None


def fetch_html(url: str) -> str | None:
    """获取网页 HTML 文本."""
    try:
        print(f"  获取页面: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception as e:
        print(f"  ✗ 获取页面失败: {e}")
        return None


# ===========================================================================
# 数据库初始化
# ===========================================================================

def init_tables(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS new_car_sales_brand (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER, month INTEGER, brand TEXT, vehicle_type TEXT,
            sales_count INTEGER, data_source TEXT, crawl_date TEXT,
            UNIQUE(year, month, brand, vehicle_type)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS kcar_monthly_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER, month INTEGER, category TEXT,
            passenger_car INTEGER, bonnet_van INTEGER,
            passenger_group_total INTEGER, cabover_van INTEGER,
            truck INTEGER, cargo_group_total INTEGER,
            total INTEGER, yoy_pct REAL,
            data_source TEXT, crawl_date TEXT,
            UNIQUE(year, month, category)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS kcar_brand_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER, month INTEGER, brand TEXT,
            passenger_count INTEGER, cargo_count INTEGER,
            total_count INTEGER, market_share_pct REAL, yoy_pct REAL,
            data_source TEXT, crawl_date TEXT,
            UNIQUE(year, month, brand)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS japan_monthly_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER, month INTEGER,
            total_sales INTEGER, registered_car_sales INTEGER,
            kei_car_sales INTEGER, registered_yoy_pct REAL,
            kei_yoy_pct REAL, ytd_total INTEGER, ytd_yoy_pct REAL,
            data_source TEXT, crawl_date TEXT,
            UNIQUE(year, month)
        )
    """)
    conn.commit()
    print("✓ 数据表初始化完成")


# ===========================================================================
# 数据源 1: JADA 品牌别注册车销量
# ===========================================================================

JADA_EXCEL_URLS = {
    2026: "https://www.jada.or.jp/files/libs/7209/20260603154913819.xls",
    2025: "https://www.jada.or.jp/files/libs/6663/2026020315092526.xls",
    2024: "https://www.jada.or.jp/relays/download/337/1568/1918/6663/?file=/files/libs/5205/202502041551388761.xls&file_name=xxx",
    2023: "https://www.jada.or.jp/relays/download/337/1568/1058/5205/?file=/files/libs/3423/202403281149129338.xls&file_name=xxx",
    2022: "https://www.jada.or.jp/relays/download/337/1568/1059/3423/?file=/files/libs/3424/202403281150366193.xls&file_name=xxx",
}


def _parse_jada_sheet(df, sheet_name, crawl_date):
    """解析单个 JADA sheet, 返回 rows 列表.

    Excel 格式 (确认后):
      行0-4: 标题行和表头
      行5+: 每个品牌占3行: [品牌 合計], [内輸入], [前年比]
            合計行是品牌小计行，包含该品牌所有子车型

    列映射 (基于实际数据):
      col3=乗用普通, col4=乗用小型, col5=乗用軽, col6=乗用計
      col7=貨物普通, col8=貨物小型, col9=貨物軽, col10=貨物計
      col11=バス計

    我们只处理 col1='合計' 的行（品牌小计行），且分开存储:
      - 乗用車(登録車) = col3普通 + col4小型 (不含軽)
      - 貨物車(登録車) = col7普通 + col8小型 (不含軽)
      - 乗用車(軽) = col5
      - 貨物車(軽) = col9
    """
    m = re.search(r"(\d{4})年(\d{1,2})月", sheet_name)
    if not m:
        return []
    year = int(m.group(1))
    month = int(m.group(2))

    rows = []

    for i in range(5, len(df)):
        col0 = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
        col1 = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ""

        # 只处理 col1='合計' 的品牌小计行
        if col1 != "合計":
            continue

        brand_name = col0.replace("　", "").strip()
        if not brand_name or brand_name == "nan":
            continue
        if brand_name in ("合計", "計", "総計", "その他"):
            continue

        # 注册车(不含K-car) 乗用車 = 普通+小型
        reg_pax_normal = parse_int(df.iloc[i, 3]) or 0
        reg_pax_small = parse_int(df.iloc[i, 4]) or 0
        reg_passenger = reg_pax_normal + reg_pax_small

        # 注册车(不含K-car) 貨物車 = 普通+小型
        reg_cargo_normal = parse_int(df.iloc[i, 7]) or 0
        reg_cargo_small = parse_int(df.iloc[i, 8]) or 0
        reg_cargo = reg_cargo_normal + reg_cargo_small

        # K-car 部分
        kei_passenger = parse_int(df.iloc[i, 5]) or 0
        kei_cargo = parse_int(df.iloc[i, 9]) or 0

        if reg_passenger > 0:
            rows.append({
                "year": year, "month": month,
                "brand": brand_name, "vehicle_type": "乗用車(登録車)",
                "sales_count": reg_passenger,
                "data_source": "JADA", "crawl_date": crawl_date,
            })
        if reg_cargo > 0:
            rows.append({
                "year": year, "month": month,
                "brand": brand_name, "vehicle_type": "貨物車(登録車)",
                "sales_count": reg_cargo,
                "data_source": "JADA", "crawl_date": crawl_date,
            })
        if kei_passenger > 0:
            rows.append({
                "year": year, "month": month,
                "brand": brand_name, "vehicle_type": "乗用車(軽)",
                "sales_count": kei_passenger,
                "data_source": "JADA", "crawl_date": crawl_date,
            })
        if kei_cargo > 0:
            rows.append({
                "year": year, "month": month,
                "brand": brand_name, "vehicle_type": "貨物車(軽)",
                "sales_count": kei_cargo,
                "data_source": "JADA", "crawl_date": crawl_date,
            })

    return rows


def crawl_jada_brand_sales(conn, years=None):
    """从 JADA 下载品牌别注册车销量 Excel 并入库."""
    print("\n" + "=" * 60)
    print("数据源1: JADA 品牌别注册车销量")
    print("=" * 60)

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    inserted = 0
    target_years = years or list(JADA_EXCEL_URLS.keys())

    for year in target_years:
        url = JADA_EXCEL_URLS.get(year)
        if not url:
            print(f"  ⚠ {year}年 无已知 Excel URL, 跳过")
            continue

        # 增量检查: 如果该年每月都有数据则跳过
        c.execute("SELECT COUNT(DISTINCT month) FROM new_car_sales_brand WHERE year=? AND vehicle_type LIKE '%登録車%'", (year,))
        month_count = c.fetchone()[0]
        if month_count >= 12:
            print(f"  {year}年 已有 {month_count} 个月数据, 跳过")
            continue

        path = download_file(url, suffix=".xls")
        if not path:
            print(f"  ✗ {year}年 Excel 下载失败, 跳过")
            continue

        try:
            xl = pd.ExcelFile(path, engine="xlrd")
            print(f"  Sheets: {xl.sheet_names}")

            all_rows = []
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name, header=None)
                if df.shape[1] < 4:
                    # 跳过说明页
                    continue
                rows = _parse_jada_sheet(df, sheet_name, crawl_date)
                all_rows.extend(rows)
                if rows:
                    print(f"    Sheet '{sheet_name}': {len(rows)} 条")

            # 入库
            for r in all_rows:
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO new_car_sales_brand
                        (year, month, brand, vehicle_type, sales_count, data_source, crawl_date)
                        VALUES (:year, :month, :brand, :vehicle_type, :sales_count, :data_source, :crawl_date)
                    """, r)
                    if c.rowcount > 0:
                        inserted += 1
                except sqlite3.IntegrityError:
                    pass

            conn.commit()
            print(f"  ✓ {year}年: 解析到 {len(all_rows)} 条, 新增 {inserted} 条")

        except Exception as e:
            print(f"  ✗ {year}年 Excel 解析失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                os.unlink(path)
            except:
                pass

    print(f"JADA 品牌别注册车销量: 共新增 {inserted} 条")
    return inserted


# ===========================================================================
# 数据源 2: zenkeijikyo — K-car 月别推移 (HTML)
# ===========================================================================

ZENKEI_MONTHLY_URL = "https://www.zenkeijikyo.or.jp/statistics/4new-month"
ZENKEI_SOKU_URL = "https://www.zenkeijikyo.or.jp/statistics/4soku"


def _parse_zenkei_table(table, year, crawl_date):
    """解析 zenkeijikyo 月别推移表, 返回 rows 列表.

    实际 HTML 结构 (每个数据行 17 个 <td>):
      [0] 月份
      [1] 総台数         [2] 総台数前年比%
      [3] 乗用車A        [4] 乗用前年比%
      [5] ボンネットバンB  [6] ボンネット前年比%
      [7] 乗用群計A+B     [8] 乗用群前年比%
      [9] キャブオーバーC  [10] キャブオーバー前年比%
      [11] トラックD      [12] トラック前年比%
      [13] 貨物群計C+D    [14] 貨物群前年比%
      [15] 貨物計B+C+D    [16] 貨物計前年比%
    """
    rows = []

    for tr in table.find_all("tr"):
        tds = tr.find_all(["td", "th"])
        if not tds:
            continue

        # 直接读取每个 td 的文本
        texts = [td.get_text(strip=True) for td in tds]

        if not texts:
            continue

        first = texts[0]

        # 匹配月份
        month = None
        m = re.search(r"(\d{1,2})月", first)
        if m:
            month = int(m.group(1))

        # 跳过累计行和非月份行
        if month is None or "累計" in first:
            continue

        # 需要17列才有完整数据
        if len(texts) < 17:
            continue

        total = parse_int(texts[1])
        yoy = parse_float(texts[2])
        passenger = parse_int(texts[3])
        bonnet_van = parse_int(texts[5])
        passenger_group = parse_int(texts[7])
        cabover_van = parse_int(texts[9])
        truck = parse_int(texts[11])
        cargo_group = parse_int(texts[13])
        cargo_total = parse_int(texts[15])

        rows.append({
            "year": year, "month": month, "category": "軽四輪車",
            "passenger_car": passenger, "bonnet_van": bonnet_van,
            "passenger_group_total": passenger_group,
            "cabover_van": cabover_van, "truck": truck,
            "cargo_group_total": cargo_group, "total": total,
            "yoy_pct": yoy,
            "data_source": "zenkeijikyo", "crawl_date": crawl_date,
        })

    return rows


def parse_zenkei_monthly_html(conn):
    """从 zenkeijikyo 4new-month 页面的 HTML 表格解析 K-car 月别销量."""
    print("\n" + "=" * 60)
    print("数据源2a: zenkeijikyo K-car 月别推移 (HTML)")
    print("=" * 60)

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    inserted = 0

    html = fetch_html(ZENKEI_MONTHLY_URL)
    if not html:
        return 0

    soup = BeautifulSoup(html, "html.parser")

    # 找到所有年份的表格
    year_sections = {}
    for tag in soup.find_all(["h2", "h3", "h4"]):
        m = re.search(r"(\d{4})年", tag.get_text())
        if m:
            year = int(m.group(1))
            table = tag.find_next("table")
            if table:
                year_sections[year] = table

    # 如果没找到, 回退到搜索令和/平成年号
    if not year_sections:
        tables = soup.find_all("table")
        for table in tables:
            text = table.get_text()
            m = re.search(r"令和(\d+)", text)
            if m:
                year = reiwa_to_ce(int(m.group(1)))
                year_sections[year] = table
                continue
            m = re.search(r"平成(\d+)", text)
            if m:
                year = heisei_to_ce(int(m.group(1)))
                year_sections[year] = table

    print(f"  找到 {len(year_sections)} 个年份数据表: {sorted(year_sections.keys())}")

    for year, table in sorted(year_sections.items()):
        # 增量检查
        c.execute("SELECT COUNT(*) FROM kcar_monthly_sales WHERE year=?", (year,))
        existing = c.fetchone()[0]
        if existing >= 12:
            print(f"  {year}年 已有 {existing} 条数据, 跳过")
            continue

        rows_data = _parse_zenkei_table(table, year, crawl_date)

        for r in rows_data:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO kcar_monthly_sales
                    (year, month, category, passenger_car, bonnet_van,
                     passenger_group_total, cabover_van, truck,
                     cargo_group_total, total, yoy_pct, data_source, crawl_date)
                    VALUES (:year, :month, :category, :passenger_car, :bonnet_van,
                            :passenger_group_total, :cabover_van, :truck,
                            :cargo_group_total, :total, :yoy_pct, :data_source, :crawl_date)
                """, r)
                if c.rowcount > 0:
                    inserted += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        print(f"  {year}年: 解析 {len(rows_data)} 行, 新增 {inserted} 条")

    print(f"zenkeijikyo K-car 月别推移: 共新增 {inserted} 条")
    return inserted


def parse_zenkei_brand_soku_html(conn):
    """从 zenkeijikyo 4soku 页面解析 K-car 品牌别销量速报.

    每个 section (総台数/乗用車/貨物車) 的数据行 13 个 <td>:
      [0] 品牌名
      [1] 本月台数(26年A)   [2] 前月台数    [3] 前月比%(A/B)
      [4] 前年同月台数(B)    [5] 前年同月比%(A/B)
      [6] 過去最高台数       [7] 過去最高年月
      [8] 累計台数(本年)     [9] 累計台数(前年)  [10] 累計前年比%
      [11] 占拠率 本月%      [12] 占拠率 本年%
    """
    print("\n" + "=" * 60)
    print("数据源2b: zenkeijikyo K-car 品牌别速报 (HTML)")
    print("=" * 60)

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    inserted = 0

    html = fetch_html(ZENKEI_SOKU_URL)
    if not html:
        # 尝试忽略 SSL
        try:
            import urllib3
            urllib3.disable_warnings()
            print("  尝试忽略 SSL 验证...")
            resp = requests.get(ZENKEI_SOKU_URL, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            html = resp.text
        except Exception as e:
            print(f"  ✗ 获取页面失败: {e}")
            return 0

    soup = BeautifulSoup(html, "html.parser")

    # 解析年月
    year, month = None, None
    for tag in soup.find_all(["title", "h1", "h2", "h3"]):
        m = re.search(r"(\d{4})年(\d{1,2})月", tag.get_text())
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            break
    if not year:
        m = re.search(r"(\d{4})年(\d{1,2})月.*?速報", soup.get_text()[:2000])
        if m:
            year, month = int(m.group(1)), int(m.group(2))
    if not year or not month:
        print("  ✗ 无法从页面解析年月")
        return 0

    # 检查已有数据
    c.execute("SELECT COUNT(*) FROM kcar_brand_sales WHERE year=? AND month=?", (year, month))
    if c.fetchone()[0] > 0:
        print(f"  {year}年{month}月 已有品牌数据, 跳过")
        return 0

    brand_data = {}  # brand -> dict

    def parse_section_table(section_name, value_key):
        """解析单个 section 的品牌表格."""
        for h in soup.find_all(["h2", "h3", "h4"]):
            h_text = h.get_text()
            if section_name in h_text:
                table = h.find_next("table")
                if not table:
                    continue
                for tr in table.find_all("tr"):
                    tds = tr.find_all(["td", "th"])
                    if len(tds) < 13:
                        continue
                    texts = [td.get_text(strip=True) for td in tds]
                    brand_name = texts[0].replace("　", "").replace(" ", "").strip()
                    if not brand_name or brand_name in ("合計", "計", ""):
                        continue
                    # 跳过表头行
                    if any(kw in brand_name for kw in ["ブランド", "新車", "販売"]):
                        continue
                    if brand_name == "その他":
                        continue

                    count = parse_int(texts[1])
                    yoy = parse_float(texts[5])   # 前年同月比%
                    share = parse_float(texts[11]) # 占拠率 本月%

                    if brand_name not in brand_data:
                        brand_data[brand_name] = {}
                    brand_data[brand_name][value_key] = count
                    if value_key == "total_count":
                        brand_data[brand_name]["yoy_pct"] = yoy
                        brand_data[brand_name]["market_share_pct"] = share
                break

    # 総台数: total_count, yoy_pct, market_share_pct
    parse_section_table("総台数", "total_count")
    # 乗用車: passenger_count
    parse_section_table("乗用車台数", "passenger_count")
    # 貨物車: cargo_count
    parse_section_table("貨物車台数", "cargo_count")

    # 入库
    for brand, data in brand_data.items():
        row = {
            "year": year, "month": month, "brand": brand,
            "passenger_count": data.get("passenger_count"),
            "cargo_count": data.get("cargo_count"),
            "total_count": data.get("total_count"),
            "market_share_pct": data.get("market_share_pct"),
            "yoy_pct": data.get("yoy_pct"),
            "data_source": "zenkeijikyo", "crawl_date": crawl_date,
        }
        try:
            c.execute("""
                INSERT OR IGNORE INTO kcar_brand_sales
                (year, month, brand, passenger_count, cargo_count,
                 total_count, market_share_pct, yoy_pct, data_source, crawl_date)
                VALUES (:year, :month, :brand, :passenger_count, :cargo_count,
                        :total_count, :market_share_pct, :yoy_pct, :data_source, :crawl_date)
            """, row)
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"  {year}年{month}月: 解析 {len(brand_data)} 个品牌, 新增 {inserted} 条")
    print(f"zenkeijikyo K-car 品牌别速报: 共新增 {inserted} 条")
    return inserted


def crawl_zenkeijikyo(conn):
    total = 0
    total += parse_zenkei_monthly_html(conn)
    total += parse_zenkei_brand_soku_html(conn)
    return total


# ===========================================================================
# 数据源 3: MarkLines — 日本月度销量摘要
# ===========================================================================

MARKLINES_URLS = {
    2026: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month",
    2025: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month-2025",
    2024: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month-2024",
    2023: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month-2023",
    2022: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month-2022",
    2021: "https://www.marklines.com/cn/statistics/flash_sales/automotive-sales-in-japan-by-month-2021",
}

# 已知公开数据 (从 MarkLines 速报和官方统计整理)
# (year, month, total, registered, kei, reg_yoy, kei_yoy, ytd_total, ytd_yoy)
MARKLINES_KNOWN_DATA = [
    # 2026年
    (2026, 5, 332997, 214994, 118003, 5.6, -2.1, 1960306, 0.4),
    (2026, 4, 237391, 118809, 118582, None, -5.7, None, None),
    (2026, 3, 369652, None, 184664, None, 8.7, None, None),
    (2026, 2, 296088, None, 151295, None, 3.2, None, None),
    (2026, 1, 277270, None, 138920, None, 1.1, None, None),
    # 2025年
    (2025, 12, 335459, 211909, 123550, 0.6, 3.8, 4565777, 3.3),
    (2025, 11, 303572, None, None, None, None, None, None),
    (2025, 10, 286662, None, None, None, None, None, None),
    (2025, 9, 330116, None, None, None, None, None, None),
    (2025, 8, 253556, None, None, None, None, None, None),
    (2025, 7, 276427, None, None, None, None, None, None),
    (2025, 6, 291309, None, 145599, None, 10.3, None, None),
    (2025, 5, 285822, None, 120546, None, 8.8, None, None),
    (2025, 4, 274882, None, 125814, None, 22.4, None, None),
    (2025, 3, 349746, None, 169828, None, 14.6, None, None),
    (2025, 2, 308625, None, 146593, None, 24.2, None, None),
    (2025, 1, 283882, None, 137352, None, 16.4, None, None),
    # 2024年
    (2024, 12, 329786, 210746, 119040, -9.3, -8.8, 4421494, -7.5),
    # 2023年
    (2023, 12, 362839, 232320, 130519, 11.1, -3.5, 4779086, 13.8),
    # 2022年 (从 zenkeijikyo 数据可推算)
    (2022, 12, 354528, 219254, 135274, 5.2, -1.6, 4183007, -6.1),
]


def crawl_marklines_summary(conn, years=None):
    """从 MarkLines 页面和已知公开数据提取日本月度销量摘要."""
    print("\n" + "=" * 60)
    print("数据源3: MarkLines 日本月度销量摘要")
    print("=" * 60)

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    inserted = 0

    # 尝试从 MarkLines 网页提取最新摘要
    for year, url in MARKLINES_URLS.items():
        html = fetch_html(url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        full_text = soup.get_text()

        # 从摘要文字中提取数据
        # 模式: "N月新车销量同比增长X%达YYY辆。其中注册车增长X%达YYY辆，微型车下降X%至YYY辆。1-N月累计销量增长X%达YYY辆。"
        pattern = re.compile(
            r"(\d{4})年(\d{1,2})月.*?销量.*?([\d,]+)辆.*?"
            r"注册车.*?([\d.-]+)%.*?([\d,]+)辆.*?"
            r"微型车.*?([\d.-]+)%.*?([\d,]+)辆.*?"
            r"1-\d+月累计.*?([\d.-]+)%.*?([\d,]+)辆",
            re.DOTALL
        )

        for m in pattern.finditer(full_text):
            try:
                y = int(m.group(1))
                mo = int(m.group(2))
                total = parse_int(m.group(3))
                reg_yoy = parse_float(m.group(4))
                reg_sales = parse_int(m.group(5))
                kei_yoy = parse_float(m.group(6))
                kei_sales = parse_int(m.group(7))
                ytd_yoy = parse_float(m.group(8))
                ytd_total = parse_int(m.group(9))

                row = {
                    "year": y, "month": mo,
                    "total_sales": total,
                    "registered_car_sales": reg_sales,
                    "kei_car_sales": kei_sales,
                    "registered_yoy_pct": reg_yoy,
                    "kei_yoy_pct": kei_yoy,
                    "ytd_total": ytd_total,
                    "ytd_yoy_pct": ytd_yoy,
                    "data_source": "MarkLines",
                    "crawl_date": crawl_date,
                }
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO japan_monthly_summary
                        (year, month, total_sales, registered_car_sales, kei_car_sales,
                         registered_yoy_pct, kei_yoy_pct, ytd_total, ytd_yoy_pct,
                         data_source, crawl_date)
                        VALUES (:year, :month, :total_sales, :registered_car_sales, :kei_car_sales,
                                :registered_yoy_pct, :kei_yoy_pct, :ytd_total, :ytd_yoy_pct,
                                :data_source, :crawl_date)
                    """, row)
                    if c.rowcount > 0:
                        inserted += 1
                except sqlite3.IntegrityError:
                    pass
            except (ValueError, IndexError):
                pass

    conn.commit()

    # 补充已知公开数据
    for entry in MARKLINES_KNOWN_DATA:
        y, mo, total, reg, kei, reg_yoy, kei_yoy, ytd, ytd_yoy = entry
        c.execute("SELECT COUNT(*) FROM japan_monthly_summary WHERE year=? AND month=?", (y, mo))
        if c.fetchone()[0] > 0:
            continue
        row = {
            "year": y, "month": mo,
            "total_sales": total,
            "registered_car_sales": reg,
            "kei_car_sales": kei,
            "registered_yoy_pct": reg_yoy,
            "kei_yoy_pct": kei_yoy,
            "ytd_total": ytd,
            "ytd_yoy_pct": ytd_yoy,
            "data_source": "MarkLines",
            "crawl_date": crawl_date,
        }
        try:
            c.execute("""
                INSERT OR IGNORE INTO japan_monthly_summary
                (year, month, total_sales, registered_car_sales, kei_car_sales,
                 registered_yoy_pct, kei_yoy_pct, ytd_total, ytd_yoy_pct,
                 data_source, crawl_date)
                VALUES (:year, :month, :total_sales, :registered_car_sales, :kei_car_sales,
                        :registered_yoy_pct, :kei_yoy_pct, :ytd_total, :ytd_yoy_pct,
                        :data_source, :crawl_date)
            """, row)
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"MarkLines 月度销量摘要: 共新增 {inserted} 条")
    return inserted


# ===========================================================================
# 数据源 4: JAIA — 进口车数据 (待探索)
# ===========================================================================

JAIA_URL = "https://www.jaia-jp.org/ja/stats/"


def crawl_jaia_imports(conn):
    """从 JAIA 探索进口车数据 (目前为占位实现)."""
    print("\n" + "=" * 60)
    print("数据源4: JAIA 进口车数据 (探索)")
    print("=" * 60)

    html = fetch_html(JAIA_URL)
    if not html:
        print("  ✗ 无法获取 JAIA 页面 (SSL 证书问题)")
        # 尝试忽略证书验证
        try:
            print("  尝试忽略 SSL 验证...")
            resp = requests.get(JAIA_URL, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            print(f"  ✗ 仍然失败: {e}")
            return 0

    if html:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if any(kw in (text + href).lower() for kw in ["統計", "stats", "data", "xls", "csv", "月別", "輸入"]):
                links.append((text, urljoin(JAIA_URL, href)))

        if links:
            print(f"  发现 {len(links)} 个可能的统计链接:")
            for text, href in links[:10]:
                print(f"    - {text}: {href}")
        else:
            print("  未发现明显的统计数据链接")

    print("  ⚠ JAIA 数据源暂未实现自动入库, 待后续探索")
    return 0


# ===========================================================================
# 计算 japan_monthly_summary
# ===========================================================================

def calc_japan_summary(conn):
    """从 kcar_monthly_sales + JADA 注册车数据计算日本月度总销量摘要."""
    print("\n" + "=" * 60)
    print("计算: 日本月度总销量摘要")
    print("=" * 60)

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    c = conn.cursor()
    inserted = 0

    c.execute("SELECT DISTINCT year, month FROM kcar_monthly_sales ORDER BY year, month")
    kcar_months = c.fetchall()

    for year, month in kcar_months:
        c.execute("SELECT COUNT(*) FROM japan_monthly_summary WHERE year=? AND month=?", (year, month))
        if c.fetchone()[0] > 0:
            continue

        c.execute("SELECT total, yoy_pct FROM kcar_monthly_sales WHERE year=? AND month=?", (year, month))
        kcar_row = c.fetchone()
        if not kcar_row or not kcar_row[0]:
            continue
        kei_sales = kcar_row[0]
        kei_yoy = kcar_row[1]

        c.execute("""
            SELECT SUM(sales_count) FROM new_car_sales_brand 
            WHERE year=? AND month=? AND vehicle_type IN ('乗用車(登録車)', '貨物車(登録車)')
        """, (year, month))
        reg_sales = c.fetchone()[0]

        if reg_sales is not None:
            total_sales = reg_sales + kei_sales
            data_source = "calculated"
        else:
            total_sales = kei_sales
            data_source = "kcar_only"

        row = {
            "year": year, "month": month,
            "total_sales": total_sales,
            "registered_car_sales": reg_sales,
            "kei_car_sales": kei_sales,
            "registered_yoy_pct": None,
            "kei_yoy_pct": kei_yoy,
            "ytd_total": None,
            "ytd_yoy_pct": None,
            "data_source": data_source,
            "crawl_date": crawl_date,
        }
        try:
            c.execute("""
                INSERT OR IGNORE INTO japan_monthly_summary
                (year, month, total_sales, registered_car_sales, kei_car_sales,
                 registered_yoy_pct, kei_yoy_pct, ytd_total, ytd_yoy_pct,
                 data_source, crawl_date)
                VALUES (:year, :month, :total_sales, :registered_car_sales, :kei_car_sales,
                        :registered_yoy_pct, :kei_yoy_pct, :ytd_total, :ytd_yoy_pct,
                        :data_source, :crawl_date)
            """, row)
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    print(f"  计算补充 japan_monthly_summary: 新增 {inserted} 条")
    return inserted


# ===========================================================================
# 主函数
# ===========================================================================

def refresh_macro_data():
    """依次调用所有数据源, 刷新宏观市场数据."""
    print("=" * 60)
    print("日本汽车市场宏观数据补充爬虫 v2")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_tables(conn)

        total_inserted = 0
        total_inserted += crawl_jada_brand_sales(conn)
        total_inserted += crawl_zenkeijikyo(conn)
        total_inserted += crawl_marklines_summary(conn)
        total_inserted += crawl_jaia_imports(conn)

        # 计算日本月度总销量摘要 (从 kcar + JADA 注册车数据计算)
        total_inserted += calc_japan_summary(conn)

        # 打印汇总统计
        print("\n" + "=" * 60)
        print("数据入库汇总")
        print("=" * 60)

        for table in ["new_car_sales_brand", "kcar_monthly_sales",
                       "kcar_brand_sales", "japan_monthly_summary"]:
            c = conn.cursor()
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"\n  {table}: {count} 行")

            if count > 0:
                c.execute(f"SELECT * FROM {table} LIMIT 3")
                cols = [desc[0] for desc in c.description]
                rows = c.fetchall()
                print(f"    列: {cols}")
                for row in rows:
                    print(f"    示例: {row}")

        print(f"\n本次新增总计: {total_inserted} 条")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n✗ 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    refresh_macro_data()

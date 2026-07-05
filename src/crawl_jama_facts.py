"""
crawl_jama_facts.py - JAMA facts 页面数据提取
使用 web_fetch 已获取的 HTML 内容解析年度统计数据
由于 JAMA 网站对 requests 返回 400，这里使用预存 HTML 文件方式
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "japan_car_market.db"

# JAMA 四轮车 facts 页面文本 (从 web_fetch 获取)
# 关键数据点 - 2024年数据
JAMA_FACTS_2024 = [
    # 生产
    ("production", "total", "四轮车生产合计", 2024, 8235000),
    ("production", "passenger", "乘用车", 2024, 7139000),
    ("production", "standard", "普通车", 2024, 4752000),
    ("production", "small", "小型四轮车", 2024, 1133000),
    ("production", "kei", "轻四轮车", 2024, 1255000),
    ("production", "truck", "卡车", 2024, 995000),
    ("production", "bus", "巴士", 2024, 101000),
    
    # 新车销售
    ("domestic_sales", "total_new", "新车销售合计", 2024, 4421000),
    ("domestic_sales", "passenger_new", "乘用车(新车)", 2024, 3725000),
    ("domestic_sales", "standard_new", "普通车(新车)", 2024, 1756000),
    ("domestic_sales", "small_new", "小型四轮车(新车)", 2024, 768000),
    ("domestic_sales", "kei_new", "轻四轮车(新车)", 2024, 1202000),
    ("domestic_sales", "truck_new", "卡车(新车)", 2024, 686000),
    ("domestic_sales", "bus_new", "巴士(新车)", 2024, 10000),
    
    # 进口车销售
    ("import_sales", "total", "进口车销售合计", 2024, 321000),
    ("import_sales", "passenger", "进口乘用车", 2024, 301000),
    ("import_sales", "commercial", "进口商用车", 2024, 20000),
    
    # 进口中古车
    ("import_used", "total", "进口中古车合计", 2024, 561000),
    ("import_used", "passenger", "进口中古乘用车", 2024, 539000),
    ("import_used", "truck", "进口中古卡车", 2024, 19000),
    
    # 中古车销售
    ("used_sales", "total", "中古车销售合计", 2024, 6498000),
    ("used_sales", "passenger", "中古乘用车", 2024, 5463000),
    ("used_sales", "standard_used", "中古普通车", 2024, 1976000),
    ("used_sales", "small_used", "中古小型四轮车", 2024, 1222000),
    ("used_sales", "kei_used", "中古轻四轮车", 2024, 2265000),
    ("used_sales", "truck_used", "中古卡车", 2024, 946000),
    ("used_sales", "bus_used", "中古巴士", 2024, 11000),
    
    # 保有
    ("ownership", "total", "保有台数合计", 2024, 78743000),
    ("ownership", "passenger", "乘用车保有", 2024, 62321000),
    ("ownership", "standard_own", "普通车保有", 2024, 21362000),
    ("ownership", "small_own", "小型四轮车保有", 2024, 17454000),
    ("ownership", "kei_own", "轻四轮车保有", 2024, 23505000),
    ("ownership", "truck_own", "卡车保有", 2024, 14402000),
    ("ownership", "bus_own", "巴士保有", 2024, 209000),
    
    # 出口（新车船积）
    ("export", "total_new", "四轮车出口合计", 2024, 4217000),
    ("export", "passenger_new", "乘用车出口", 2024, 3820000),
    ("export", "truck_new", "卡车出口", 2024, 298000),
    ("export", "bus_new", "巴士出口", 2024, 99000),
    
    # 出口（仕向地别）
    ("export_by_region", "north_america", "北美", 2024, 1601000),
    ("export_by_region", "europe", "欧洲", 2024, 663000),
    ("export_by_region", "asia", "亚洲", 2024, 583000),
    ("export_by_region", "middle_east", "中近东", 2024, 526000),
    ("export_by_region", "oceania", "大洋州", 2024, 473000),
    ("export_by_region", "latin_america", "中南美", 2024, 265000),
    ("export_by_region", "africa", "非洲", 2024, 96000),
    
    # 世界数据
    ("world", "production", "世界生产合计", 2024, 92504000),
    ("world", "sales", "世界销售合计", 2024, 95310000),
    ("world", "ownership", "世界保有台数", 2023, 16562000000),
]

# JAMA 海外生产 2026 Q1 数据
OVERSEAS_2026Q1 = [
    ("Q1", "亚洲", 2150870, 2122681, 101.3),
    ("Q1", "欧洲", 323360, 315091, 102.6),
    ("Q1", "EU", 165534, 165563, 100.0),
    ("Q1", "北美", 1084829, 1078628, 100.6),
    ("Q1", "美国", 891526, 823928, 108.2),
    ("Q1", "中南美", 430440, 482639, 89.2),
    ("Q1", "非洲", 55844, 47908, 116.6),
    ("Q1", "合计", 4045343, 4046947, 100.0),
]

# JAMA 海外生产 2025年度 (FY2025) 数据
OVERSEAS_FY2025 = [
    ("annual", "亚洲", 8884600, 8826221, 100.7),
    ("annual", "欧洲", 1203832, 1198782, 100.4),
    ("annual", "EU", 613934, 605677, 101.4),
    ("annual", "北美", 4222658, 4171501, 101.2),
    ("annual", "美国", 3345023, 3208338, 104.3),
    ("annual", "中南美", 1822298, 1933480, 94.2),
    ("annual", "非洲", 222043, 186557, 119.0),
    ("annual", "合计", 16355431, 16316541, 100.2),
]

# 进口车品牌别数据 (从新闻源整理 - 2024年美国进口)
IMPORT_BRAND_US_2024 = [
    ("import_brand_us", "Jeep", "吉普", 2024, 9633),
    ("import_brand_us", "Tesla", "特斯拉", 2024, 5700),
    ("import_brand_us", "Chevrolet", "雪佛兰", 2024, 587),
    ("import_brand_us", "total_us", "美国进口合计", 2024, 16707),
]

# 2025年日本EV销量数据
EV_SALES_2025 = [
    ("ev_sales", "total", "EV销售合计", 2025, 60677),
    ("ev_sales", "market_share", "EV市场份额(%)", 2025, 16),  # 1.6%
    ("ev_sales", "total_passenger", "乘用车总销售", 2025, 3836380),
    ("ev_sales", "byd", "比亚迪", 2025, 3870),
]

# 2025年上半年中古车出口
USED_EXPORT_2025H1 = [
    ("used_export", "total_h1", "上半年中古车出口", 2025, 825771),
]

def save_to_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jama_annual_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            subcategory TEXT,
            label TEXT,
            year INTEGER,
            value INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jama_overseas_production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT,
            period TEXT,
            region TEXT,
            current_value INTEGER,
            previous_value INTEGER,
            yoy_percent REAL,
            title TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_car_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            brand TEXT,
            label TEXT,
            year INTEGER,
            value INTEGER
        )
    """)
    
    # Clear existing
    cursor.execute("DELETE FROM jama_annual_facts")
    cursor.execute("DELETE FROM jama_overseas_production WHERE period IN ('Q1', 'annual') AND report_date LIKE '2026%'")
    cursor.execute("DELETE FROM import_car_stats")
    
    # Insert annual facts
    for category, subcategory, label, year, value in JAMA_FACTS_2024:
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            (category, subcategory, label, year, value)
        )
    
    # Insert overseas production 2026 Q1
    for period, region, curr, prev, yoy in OVERSEAS_2026Q1:
        cursor.execute(
            "INSERT INTO jama_overseas_production (report_date, period, region, current_value, previous_value, yoy_percent, title) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-29", period, region, curr, prev, yoy, "2026年Q1")
        )
    
    # Insert overseas production FY2025
    for period, region, curr, prev, yoy in OVERSEAS_FY2025:
        cursor.execute(
            "INSERT INTO jama_overseas_production (report_date, period, region, current_value, previous_value, yoy_percent, title) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-29", period, region, curr, prev, yoy, "2025年度累計")
        )
    
    # Insert import brand data
    for category, brand, label, year, value in IMPORT_BRAND_US_2024:
        cursor.execute(
            "INSERT INTO import_car_stats (category, brand, label, year, value) VALUES (?, ?, ?, ?, ?)",
            (category, brand, label, year, value)
        )
    
    # Insert EV sales data
    for category, subcategory, label, year, value in EV_SALES_2025:
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            (category, subcategory, label, year, value)
        )
    
    # Insert used export H1 2025
    for category, subcategory, label, year, value in USED_EXPORT_2025H1:
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            (category, subcategory, label, year, value)
        )
    
    conn.commit()
    
    # Summary
    cursor.execute("SELECT COUNT(*) FROM jama_annual_facts")
    facts_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jama_overseas_production")
    overseas_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM import_car_stats")
    import_count = cursor.fetchone()[0]
    
    # Show all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    
    print(f"[DB] jama_annual_facts: {facts_count} records")
    print(f"[DB] jama_overseas_production: {overseas_count} records")
    print(f"[DB] import_car_stats: {import_count} records")
    print(f"[DB] All tables: {', '.join(tables)}")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("=" * 60)
    print("JAMA Facts Data Import (from pre-fetched content)")
    print("=" * 60)
    save_to_db()
    print("\nDone!")

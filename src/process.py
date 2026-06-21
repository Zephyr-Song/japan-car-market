"""
数据清洗与处理模块
参考德国汽车市场分析系统的方法论
"""

import pandas as pd
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "data/japan_car_market.db"


def load_data():
    """从 SQLite 加载原始数据"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()
    print(f"加载原始数据: {len(df)} 条记录")
    return df


def parse_japanese_year(year_str):
    """解析日本年号为西元年份
    R=令和, H=平成, S=昭和
    例: 2022(R04) -> 2022, H17 -> 2005
    """
    if not year_str or pd.isna(year_str):
        return None

    # 先尝试直接解析4位数字
    match = re.match(r'^(\d{4})', str(year_str))
    if match:
        return int(match.group(1))

    # 解析日本年号
    match = re.match(r'(R|H|S)(\d{1,2})', str(year_str))
    if match:
        era, year = match.group(1), int(match.group(2))
        if era == 'R':
            return 2018 + year  # 令和元年=2019
        elif era == 'H':
            return 1988 + year  # 平成元年=1989
        elif era == 'S':
            return 1925 + year  # 昭和元年=1926
    return None


def parse_mileage(mileage_str):
    """解析里程文本为公里数（万km）"""
    if not mileage_str or pd.isna(mileage_str):
        return None
    mileage_str = str(mileage_str).strip()
    match = re.match(r'([\d.]+)\s*万km', mileage_str)
    if match:
        return float(match.group(1))
    match = re.match(r'([\d.]+)\s*km', mileage_str)
    if match:
        return float(match.group(1)) / 10000
    return None


def parse_displacement(disp_str):
    """解析排量文本为cc数"""
    if not disp_str or pd.isna(disp_str):
        return None
    disp_str = str(disp_str).strip()
    match = re.match(r'([\d]+)\s*[Cc][Cc]', disp_str)
    if match:
        return int(match.group(1))
    match = re.match(r'([\d.]+)\s*[Ll]', disp_str)
    if match:
        return int(float(match.group(1)) * 1000)
    return None


def classify_fuel(displacement):
    """根据排量分类（日本特色：轻自动车 K-car ≤660cc）"""
    if displacement is None:
        return "不明"
    if displacement <= 660:
        return "軽自動車(K-car)"
    elif displacement <= 1500:
        return "小型車(≤1500cc)"
    elif displacement <= 2000:
        return "普通車(1501-2000cc)"
    elif displacement <= 3000:
        return "中級車(2001-3000cc)"
    else:
        return "高級車(3001cc+)"


def classify_brand(brand):
    """品牌分类：国产(日本) vs 外国"""
    japanese_brands = [
        'トヨタ', 'ホンダ', '日産', 'マツダ', 'スバル',
        'スズキ', 'ダイハツ', 'レクサス', '三菱', '光岡',
        'トヨタ', 'ホンダ', 'ニッサン'
    ]
    if not brand or pd.isna(brand):
        return "不明"
    for jb in japanese_brands:
        if jb in str(brand):
            return "国産"
    return "輸入車(进口)"


def process_data():
    """主处理流程"""
    df = load_data()

    print("\n=== 数据清洗开始 ===")

    # 1. 删除完全空记录
    before = len(df)
    df = df.dropna(subset=['model'])
    print(f"删除空车型记录: {before - len(df)} 条")

    # 2. 解析年式
    df['year_ce'] = df['year'].apply(parse_japanese_year)
    print(f"成功解析年式: {df['year_ce'].notna().sum()} / {len(df)}")

    # 3. 解析里程
    df['mileage_wan_km'] = df['mileage'].apply(parse_mileage)
    print(f"成功解析里程: {df['mileage_wan_km'].notna().sum()} / {len(df)}")

    # 4. 解析排量
    df['displacement_cc'] = df['displacement'].apply(parse_displacement)
    print(f"成功解析排量: {df['displacement_cc'].notna().sum()} / {len(df)}")

    # 5. 燃料/排量分类
    df['vehicle_class'] = df['displacement_cc'].apply(classify_fuel)

    # 6. 品牌分类
    df['brand_type'] = df['brand'].apply(classify_brand)

    # 7. 清理品牌名（提取核心品牌）
    def clean_brand(brand):
        if not brand or pd.isna(brand):
            return "不明"
        brand = str(brand).strip()
        # 常见品牌映射
        brand_map = {
            'トヨタ': 'Toyota', 'ホンダ': 'Honda', '日産': 'Nissan',
            'スズキ': 'Suzuki', 'ダイハツ': 'Daihatsu', 'マツダ': 'Mazda',
            'スバル': 'Subaru', '三菱': 'Mitsubishi', 'レクサス': 'Lexus',
            '光岡': 'Mitsuoka', 'BMW': 'BMW', 'メルセデス': 'Mercedes-Benz',
            'ベンツ': 'Mercedes-Benz', 'アウディ': 'Audi', 'フォルクスワーゲン': 'VW',
            'ポルシェ': 'Porsche', 'ミニ': 'MINI', 'ボルボ': 'Volvo',
            'ジープ': 'Jeep', 'ランドローバー': 'Land Rover',
            'プジョー': 'Peugeot', 'シトロエン': 'Citroen',
        }
        for jp, en in brand_map.items():
            if jp in brand:
                return en
        return brand

    df['brand_clean'] = df['brand'].apply(clean_brand)

    # 8. 保存清洗后数据
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('used_cars_cleaned', conn, if_exists='replace', index=False)
    conn.close()

    print(f"\n=== 数据清洗完成 ===")
    print(f"清洗后记录数: {len(df)}")
    print(f"\n品牌分布 (Top 15):")
    print(df['brand_clean'].value_counts().head(15).to_string())
    print(f"\n车辆级别分布:")
    print(df['vehicle_class'].value_counts().to_string())
    print(f"\n价格统计 (万円):")
    print(df['price_vehicle'].describe().to_string())
    print(f"\n年式范围: {df['year_ce'].min()} - {df['year_ce'].max()}")

    return df


if __name__ == "__main__":
    process_data()

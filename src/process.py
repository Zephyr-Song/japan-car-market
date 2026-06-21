"""
Data Cleaning & Processing Module
Converts raw crawled data into analysis-ready format with English labels
"""

import pandas as pd
import sqlite3
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'japan_car_market.db')


# ====== Mapping tables ======

JAPANESE_TO_ENGLISH_BRAND = {
    'トヨタ': 'Toyota', 'ホンダ': 'Honda', '日産': 'Nissan',
    'スズキ': 'Suzuki', 'ダイハツ': 'Daihatsu', 'マツダ': 'Mazda',
    'スバル': 'Subaru', '三菱': 'Mitsubishi', 'レクサス': 'Lexus',
    '光岡': 'Mitsuoka', 'BMW': 'BMW', 'メルセデス・ベンツ': 'Mercedes-Benz',
    'メルセデス': 'Mercedes-Benz', 'ベンツ': 'Mercedes-Benz',
    'アウディ': 'Audi', 'フォルクスワーゲン': 'VW',
    'ポルシェ': 'Porsche', 'ミニ': 'MINI', 'ボルボ': 'Volvo',
    'ジープ': 'Jeep', 'ランドローバー': 'Land Rover',
    'プジョー': 'Peugeot', 'シトロエン': 'Citroen',
    'フィアット': 'Fiat', 'スマート': 'Smart',
    'アルファロメオ': 'Alfa Romeo', 'ジャガー': 'Jaguar',
    'ケンワース': 'Kenworth', 'フォード': 'Ford',
    'シボレー': 'Chevrolet', 'キャデラック': 'Cadillac',
    'ベントレー': 'Bentley', 'ロールスロイス': 'Rolls-Royce',
    'フェラーリ': 'Ferrari', 'マセラティ': 'Maserati',
    'ランボルギーニ': 'Lamborghini', 'アストンマーティン': 'Aston Martin',
    'テスラ': 'Tesla', 'リンカーン': 'Lincoln',
    'オペル': 'Opel', 'ルノー': 'Renault', 'サーブ': 'Saab',
}

JAPANESE_TO_ENGLISH_PREFECTURE = {
    '北海道': 'Hokkaido', '青森県': 'Aomori', '岩手県': 'Iwate',
    '宮城県': 'Miyagi', '秋田県': 'Akita', '山形県': 'Yamagata',
    '福島県': 'Fukushima', '茨城県': 'Ibaraki', '栃木県': 'Tochigi',
    '群馬県': 'Gunma', '埼玉県': 'Saitama', '千葉県': 'Chiba',
    '東京都': 'Tokyo', '神奈川県': 'Kanagawa', '新潟県': 'Niigata',
    '富山県': 'Toyama', '石川県': 'Ishikawa', '福井県': 'Fukui',
    '山梨県': 'Yamanashi', '長野県': 'Nagano', '岐阜県': 'Gifu',
    '静岡県': 'Shizuoka', '愛知県': 'Aichi', '三重県': 'Mie',
    '滋賀県': 'Shiga', '京都府': 'Kyoto', '大阪府': 'Osaka',
    '兵庫県': 'Hyogo', '奈良県': 'Nara', '和歌山県': 'Wakayama',
    '鳥取県': 'Tottori', '島根県': 'Shimane', '岡山県': 'Okayama',
    '広島県': 'Hiroshima', '山口県': 'Yamaguchi', '徳島県': 'Tokushima',
    '香川県': 'Kagawa', '愛媛県': 'Ehime', '高知県': 'Kochi',
    '福岡県': 'Fukuoka', '佐賀県': 'Saga', '長崎県': 'Nagasaki',
    '熊本県': 'Kumamoto', '大分県': 'Oita', '宮崎県': 'Miyazaki',
    '鹿児島県': 'Kagoshima', '沖縄県': 'Okinawa',
}


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()
    print(f"Loaded raw data: {len(df)} records")
    return df


def parse_japanese_year(year_str):
    if not year_str or pd.isna(year_str):
        return None
    match = re.match(r'^(\d{4})', str(year_str))
    if match:
        return int(match.group(1))
    match = re.match(r'(R|H|S)(\d{1,2})', str(year_str))
    if match:
        era, year = match.group(1), int(match.group(2))
        if era == 'R': return 2018 + year
        elif era == 'H': return 1988 + year
        elif era == 'S': return 1925 + year
    return None


def parse_mileage(mileage_str):
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


def classify_vehicle(displacement):
    if displacement is None:
        return "Unknown"
    if displacement <= 660:
        return "K-car (<=660cc)"
    elif displacement <= 1500:
        return "Compact (<=1500cc)"
    elif displacement <= 2000:
        return "Mid-size (1501-2000cc)"
    elif displacement <= 3000:
        return "Large (2001-3000cc)"
    else:
        return "Luxury (3001cc+)"


def classify_brand_origin(brand):
    japanese_brands = [
        'Toyota', 'Honda', 'Nissan', 'Suzuki', 'Daihatsu',
        'Mazda', 'Subaru', 'Mitsubishi', 'Lexus', 'Mitsuoka',
    ]
    if not brand or pd.isna(brand):
        return "Unknown"
    if brand in japanese_brands:
        return "Domestic"
    return "Import"


def clean_brand(brand):
    if not brand or pd.isna(brand):
        return "Unknown"
    brand = str(brand).strip()
    for jp, en in JAPANESE_TO_ENGLISH_BRAND.items():
        if jp in brand:
            return en
    return brand


def clean_prefecture(pref):
    if not pref or pd.isna(pref):
        return "Unknown"
    pref = str(pref).strip()
    return JAPANESE_TO_ENGLISH_PREFECTURE.get(pref, pref)


def process_data():
    df = load_data()

    print("\n=== Data Cleaning Started ===")

    before = len(df)
    df = df.dropna(subset=['model'])
    print(f"Removed empty model records: {before - len(df)}")

    df['year_ce'] = df['year'].apply(parse_japanese_year)
    print(f"Year parsed: {df['year_ce'].notna().sum()} / {len(df)}")

    df['mileage_wan_km'] = df['mileage'].apply(parse_mileage)
    print(f"Mileage parsed: {df['mileage_wan_km'].notna().sum()} / {len(df)}")

    df['displacement_cc'] = df['displacement'].apply(parse_displacement)
    print(f"Displacement parsed: {df['displacement_cc'].notna().sum()} / {len(df)}")

    df['vehicle_class'] = df['displacement_cc'].apply(classify_vehicle)
    df['brand_clean'] = df['brand'].apply(clean_brand)
    df['brand_origin'] = df['brand_clean'].apply(classify_brand_origin)
    df['prefecture'] = df['prefecture'].apply(clean_prefecture)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql('used_cars_cleaned', conn, if_exists='replace', index=False)
    conn.close()

    print(f"\n=== Data Cleaning Complete ===")
    print(f"Records: {len(df)}")
    print(f"\nBrand distribution (Top 15):")
    print(df['brand_clean'].value_counts().head(15).to_string())
    print(f"\nVehicle class distribution:")
    print(df['vehicle_class'].value_counts().to_string())
    print(f"\nPrefecture distribution (Top 10):")
    print(df['prefecture'].value_counts().head(10).to_string())
    print(f"\nPrice stats (man-yen):")
    print(df['price_vehicle'].describe().to_string())
    print(f"\nYear range: {df['year_ce'].min()} - {df['year_ce'].max()}")

    return df


if __name__ == "__main__":
    process_data()

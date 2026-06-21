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
    """English vehicle class labels to avoid encoding issues in SQLite"""
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


JAPANESE_TO_ENGLISH_BRAND = {
    'トヨタ': 'Toyota', 'ホンダ': 'Honda', '日産': 'Nissan',
    'スズキ': 'Suzuki', 'ダイハツ': 'Daihatsu', 'マツダ': 'Mazda',
    'スバル': 'Subaru', '三菱': 'Mitsubishi', 'レクサス': 'Lexus',
    '光岡': 'Mitsuoka', 'BMW': 'BMW', 'メルセデス': 'Mercedes-Benz',
    'ベンツ': 'Mercedes-Benz', 'アウディ': 'Audi', 'フォルクスワーゲン': 'VW',
    'ポルシェ': 'Porsche', 'ミニ': 'MINI', 'ボルボ': 'Volvo',
    'ジープ': 'Jeep', 'ランドローバー': 'Land Rover',
    'プジョー': 'Peugeot', 'シトロエン': 'Citroen',
}


def clean_brand(brand):
    if not brand or pd.isna(brand):
        return "Unknown"
    brand = str(brand).strip()
    for jp, en in JAPANESE_TO_ENGLISH_BRAND.items():
        if jp in brand:
            return en
    return brand


def process_data():
    df = load_data()

    print("\n=== Data Cleaning Started ===")

    # Remove empty records
    before = len(df)
    df = df.dropna(subset=['model'])
    print(f"Removed empty model records: {before - len(df)}")

    # Parse year
    df['year_ce'] = df['year'].apply(parse_japanese_year)
    print(f"Year parsed: {df['year_ce'].notna().sum()} / {len(df)}")

    # Parse mileage
    df['mileage_wan_km'] = df['mileage'].apply(parse_mileage)
    print(f"Mileage parsed: {df['mileage_wan_km'].notna().sum()} / {len(df)}")

    # Parse displacement
    df['displacement_cc'] = df['displacement'].apply(parse_displacement)
    print(f"Displacement parsed: {df['displacement_cc'].notna().sum()} / {len(df)}")

    # Vehicle class (English labels)
    df['vehicle_class'] = df['displacement_cc'].apply(classify_vehicle)

    # Brand origin
    df['brand_origin'] = df['brand_clean'] if 'brand_clean' in df.columns else df['brand'].apply(clean_brand)
    # Re-apply clean_brand on raw brand
    df['brand_clean'] = df['brand'].apply(clean_brand)
    df['brand_origin'] = df['brand_clean'].apply(classify_brand_origin)

    # Save
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('used_cars_cleaned', conn, if_exists='replace', index=False)
    conn.close()

    print(f"\n=== Data Cleaning Complete ===")
    print(f"Records: {len(df)}")
    print(f"\nBrand distribution (Top 15):")
    print(df['brand_clean'].value_counts().head(15).to_string())
    print(f"\nVehicle class distribution:")
    print(df['vehicle_class'].value_counts().to_string())
    print(f"\nPrice stats (man-yen):")
    print(df['price_vehicle'].describe().to_string())
    print(f"\nYear range: {df['year_ce'].min()} - {df['year_ce'].max()}")

    return df


if __name__ == "__main__":
    process_data()

import sqlite3, pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/japan_car_market.db')
df = pd.read_sql_query('SELECT * FROM used_cars_cleaned', conn)
conn.close()

kcar = (df['vehicle_class'] == 'K-car (<=660cc)').mean() * 100
print(f'K-car Share: {kcar:.1f}%')
print(f'brand_origin distribution:')
for k, v in df['brand_origin'].value_counts().items():
    print(f'  {k}: {v}')

# Check if the column name is exactly right
print(f'\nColumns: {list(df.columns)}')
print(f'vehicle_class dtype: {df["vehicle_class"].dtype}')
print(f'vehicle_class sample: {df["vehicle_class"].head().tolist()}')

# Check NaN
print(f'vehicle_class NaN count: {df["vehicle_class"].isna().sum()}')

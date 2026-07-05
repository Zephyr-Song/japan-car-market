import sqlite3, pandas as pd
conn = sqlite3.connect('D:/japan-car-market/data/japan_car_market.db')

# Test all tables used by chart_import_export
tables = {
    'jama_annual_facts': 'SELECT COUNT(*) FROM jama_annual_facts',
    'jama_overseas_production': 'SELECT COUNT(*) FROM jama_overseas_production',
    'import_car_stats': 'SELECT COUNT(*) FROM import_car_stats',
    'export_statistics': 'SELECT COUNT(*) FROM export_statistics',
    'import_car_monthly': 'SELECT COUNT(*) FROM import_car_monthly',
    'new_car_export': 'SELECT COUNT(*) FROM new_car_export',
    'export_by_type': 'SELECT COUNT(*) FROM export_by_type',
    'import_customs': 'SELECT COUNT(*) FROM import_customs',
    'overseas_production_annual': 'SELECT COUNT(*) FROM overseas_production_annual',
}

for name, sql in tables.items():
    try:
        c = pd.read_sql_query(sql, conn)
        print(f"  {name}: {c.iloc[0,0]} rows")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

# Check region values in overseas_production_annual
print("\nRegions in overseas_production_annual:")
df = pd.read_sql_query("SELECT DISTINCT region FROM overseas_production_annual", conn)
print(df['region'].tolist())

# Check vehicle_type values in export_by_type
print("\nVehicle types in export_by_type:")
df = pd.read_sql_query("SELECT DISTINCT vehicle_type FROM export_by_type", conn)
print(df['vehicle_type'].tolist())

# Check region values in new_car_export
print("\nRegions in new_car_export:")
df = pd.read_sql_query("SELECT DISTINCT region FROM new_car_export", conn)
print(df['region'].tolist())

conn.close()

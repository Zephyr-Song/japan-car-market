path = 'D:/japan-car-market/src/dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The filter '!= Total' won't match Chinese '合计' in the DB.
# Fix: change 'Total' back to '合计' for DB-level filters, and add display translation.

# Fix export_type_df filter
content = content.replace(
    "et_pivot = export_type_df[export_type_df['vehicle_type'] != 'Total'].pivot_table(",
    "et_pivot = export_type_df[export_type_df['vehicle_type'] != '\\u5408\\u8BA1'].pivot_table("
)

# Fix new_car_export_df filter  
content = content.replace(
    "nce_pivot = new_car_export_df[new_car_export_df['region'] != 'Total'].pivot_table(",
    "nce_pivot = new_car_export_df[new_car_export_df['region'] != '\\u5408\\u8BA1'].pivot_table("
)

# Fix overseas_annual_df filter
content = content.replace(
    "op_pivot = overseas_annual_df[overseas_annual_df['region'] != 'Total'].pivot_table(",
    "op_pivot = overseas_annual_df[overseas_annual_df['region'] != '\\u5408\\u8BA1'].pivot_table("
)

# Fix import_customs_df filter
content = content.replace(
    "ic_pivot = import_customs_df[import_customs_df['country'] != 'Total'].pivot_table(",
    "ic_pivot = import_customs_df[import_customs_df['country'] != '\\u5408\\u8BA1'].pivot_table("
)

# Now add region/vehicle_type translation maps right after the conn.close() in chart_import_export
old_close = """    conn.close()

    if facts_df.empty:
        st.warning("No JAMA data available. Run crawl_jama_facts.py first.")
        return"""

new_close = """    conn.close()

    # Translation maps: Chinese DB values -> English display
    region_cn_map = {'\\u5317\\u7C73': 'North America', '\\u6B27\\u5DDE': 'Europe', '\\u4E9A\\u6D32': 'Asia',
                     '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania',
                     '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u975E\\u6D32': 'Africa',
                     '\\u5408\\u8BA1': 'Total'}
    vtype_cn_map = {'\\u4E58\\u7528\\u8F66': 'Passenger Car', '\\u5361\\u8F66': 'Truck', '\\u5DF4\\u58EB': 'Bus',
                    '\\u5408\\u8BA1': 'Total'}
    country_cn_map = {'\\u5FB7\\u56FD': 'Germany', '\\u97E9\\u56FD': 'South Korea', '\\u7F8E\\u56FD': 'USA',
                      '\\u82F1\\u56FD': 'UK', '\\u610F\\u5927\\u5229': 'Italy', '\\u6CD5\\u56FD': 'France',
                      '\\u4E2D\\u56FD': 'China', '\\u5176\\u4ED6': 'Others', '\\u5408\\u8BA1': 'Total'}

    # Apply translations to DataFrames
    if not new_car_export_df.empty:
        new_car_export_df['region'] = new_car_export_df['region'].map(lambda x: region_cn_map.get(x, x))
    if not export_by_type_df.empty:
        export_by_type_df['vehicle_type'] = export_by_type_df['vehicle_type'].map(lambda x: vtype_cn_map.get(x, x))
    if not overseas_annual_df.empty:
        overseas_annual_df['region'] = overseas_annual_df['region'].map(lambda x: region_cn_map.get(x, x))
    if not import_customs_df.empty:
        import_customs_df['country'] = import_customs_df['country'].map(lambda x: country_cn_map.get(x, x))

    # JAMA facts label translation
    facts_label_map = {
        '\\u4E58\\u7528\\u8F66\\u65B0\\u8F66': 'Passenger (New)', '\\u666E\\u901A\\u8F66\\u65B0\\u8F66': 'Standard (New)',
        '\\u5C0F\\u578B\\u8F66\\u65B0\\u8F66': 'Small (New)', '\\u8F7B\\u81EA\\u52D5\\u8F66\\u65B0\\u8F66': 'Kei (New)',
        '\\u30C8\\u30E9\\u30C3\\u30AF\\u65B0\\u8F66': 'Truck (New)', '\\u30D0\\u30B9\\u65B0\\u8F66': 'Bus (New)',
        '\\u65B0\\u8F66\\u5408\\u8A08': 'Total (New)',
        '\\u8F38\\u5165\\u4E57\\u7528\\u8F66': 'Import Passenger', '\\u8F38\\u5165\\u5546\\u7528\\u8F66': 'Import Commercial',
        '\\u8F38\\u5165\\u8ECA\\u8CA9\\u58F2\\u5408\\u8A08': 'Import Total',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u4E57\\u7528\\u8F66': 'Import Used Passenger',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u30AB\\u30FC\\u30C8': 'Import Used Truck',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u8ECA\\u5408\\u8A08': 'Import Used Total',
        '\\u4E2D\\u53E4\\u8F66\\u5408\\u8A08': 'Used Car Total',
        '\\u751F\\u7523\\u5408\\u8A08': 'Production Total', '\\u4E57\\u7528\\u8F66': 'Passenger',
        '\\u666E\\u901A\\u8F66': 'Standard', '\\u5C0F\\u578B\\u8F66': 'Small', '\\u8F7B\\u81EA\\u52D5\\u8F66': 'Kei',
        '\\u30C8\\u30E9\\u30C3\\u30AF': 'Truck', '\\u30D0\\u30B9': 'Bus',
        '\\u4FDD\\u6709\\u53F0\\u6570\\u5408\\u8A08': 'Ownership Total',
        '\\u51FA\\u53E3\\u65B0\\u8F66\\u5408\\u8A08': 'Export Total (New)',
    }
    if not facts_df.empty and 'label' in facts_df.columns:
        facts_df['label'] = facts_df['label'].map(lambda x: facts_label_map.get(x, x))

    if facts_df.empty:
        st.warning("No JAMA data available. Run crawl_jama_facts.py first.")
        return"""

content = content.replace(old_close, new_close)

# Also fix the quarterly overseas production region names (Japanese -> English)
# The region_map already added for q1_display and annual_display, but let's also fix the filter
# '合計' vs '合计' - check which one is in jama_overseas_production
# The quarterly table uses Japanese '合計' (U+5408 U+8A08), annual uses Chinese '合计' (U+5408 U+8BA1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix applied successfully!")

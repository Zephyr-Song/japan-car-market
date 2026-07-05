path = 'D:/japan-car-market/src/dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the translation maps section with comprehensive version
old_maps = """    # Translation maps: Chinese DB values -> English display
    region_cn_map = {'\\u5317\\u7C73': 'North America', '\\u6B27\\u5DDE': 'Europe', '\\u4E9A\\u6D32': 'Asia',
                     '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania',
                     '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u975E\\u6D32': 'Africa',
                     '\\u5408\\u8BA1': 'Total'}
    vtype_cn_map = {'\\u4E58\\u7528\\u8F66': 'Passenger Car', '\\u5361\\u8F66': 'Truck', '\\u5DF4\\u58EB': 'Bus',
                    '\\u5408\\u8BA1': 'Total'}
    country_cn_map = {'\\u5FB7\\u56FD': 'Germany', '\\u97E9\\u56FD': 'South Korea', '\\u7F8E\\u56FD': 'USA',
                      '\\u82F1\\u56FD': 'UK', '\\u610F\\u5927\\u5229': 'Italy', '\\u6CD5\\u56FD': 'France',
                      '\\u4E2D\\u56FD': 'China', '\\u5176\\u4ED6': 'Others', '\\u5408\\u8BA1': 'Total'}"""

new_maps = """    # Translation maps: DB values (mixed CN/JP) -> English display
    region_map = {
        # Chinese
        '\\u5317\\u7C73': 'North America', '\\u6B27\\u5DDE': 'Europe', '\\u4E9A\\u6D32': 'Asia',
        '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania',
        '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u975E\\u6D32': 'Africa',
        '\\u5408\\u8BA1': 'Total',
        # Japanese (quarterly table)
        '\\u30A2\\u30B8\\u30A2': 'Asia', '\\u6B27\\u5DDE': 'Europe', '\\u5317\\u7C73': 'North America',
        '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u30A2\\u30D5\\u30EA\\u30AB': 'Africa',
        '\\u5408\\u8A08': 'Total', '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania',
        '\\u4E2D\\u5357\\u7C73': 'Central/South America',
        # Other variants
        'EU': 'Europe', '\\u7C73\\u56FD': 'USA',
    }
    vtype_map = {
        '\\u4E58\\u7528\\u8F66': 'Passenger Car', '\\u5361\\u8F66': 'Truck', '\\u5DF4\\u58EB': 'Bus',
        '\\u5408\\u8BA1': 'Total',
        '\\u30C8\\u30E9\\u30C3\\u30AF': 'Truck', '\\u30D0\\u30B9': 'Bus',
    }
    country_map = {
        # Japanese
        '\\u30C9\\u30A4\\u30C4': 'Germany', '\\u30A2\\u30E1\\u30EA\\u30AB': 'USA',
        '\\u30A4\\u30AE\\u30EA\\u30B9': 'UK', '\\u30A4\\u30BF\\u30EA\\u30A2': 'Italy',
        '\\u30D5\\u30E9\\u30F3\\u30B9': 'France', '\\u97D3\\u56FD': 'South Korea',
        '\\u4E2D\\u56FD': 'China', '\\u305D\\u306E\\u4ED6': 'Others', '\\u5408\\u8BA1': 'Total',
        # Chinese
        '\\u5FB7\\u56FD': 'Germany', '\\u97E9\\u56FD': 'South Korea', '\\u7F8E\\u56FD': 'USA',
        '\\u82F1\\u56FD': 'UK', '\\u610F\\u5927\\u5229': 'Italy', '\\u6CD5\\u56FD': 'France',
        '\\u5176\\u4ED6': 'Others',
    }"""

content = content.replace(old_maps, new_maps)

# Update the apply references
content = content.replace("new_car_export_df['region'].map(lambda x: region_cn_map.get(x, x))",
                          "new_car_export_df['region'].map(lambda x: region_map.get(x, x))")
content = content.replace("export_by_type_df['vehicle_type'].map(lambda x: vtype_cn_map.get(x, x))",
                          "export_by_type_df['vehicle_type'].map(lambda x: vtype_map.get(x, x))")
content = content.replace("overseas_annual_df['region'].map(lambda x: region_cn_map.get(x, x))",
                          "overseas_annual_df['region'].map(lambda x: region_map.get(x, x))")
content = content.replace("import_customs_df['country'].map(lambda x: country_cn_map.get(x, x))",
                          "import_customs_df['country'].map(lambda x: country_map.get(x, x))")

# Update quarterly region_map reference to use the unified map
content = content.replace(
    "region_map = {'\\u30A2\\u30B8\\u30A2': 'Asia', '\\u6B27\\u5DDE': 'Europe', '\\u5317\\u7C73': 'North America', '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u30A2\\u30D5\\u30EA\\u30AB': 'Africa', '\\u5408\\u8A08': 'Total', '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania'}\n                    q1_display = q1_data[q1_data['region'] != '\\u5408\\u8A08'].copy()\n                    q1_display['region'] = q1_display['region'].map(lambda x: region_map.get(x, x))",
    "# Use unified region_map defined above\n                    q1_display = q1_data[q1_data['region'] != '\\u5408\\u8A08'].copy()\n                    q1_display['region'] = q1_display['region'].map(lambda x: region_map.get(x, x))"
)

# Also update facts_label_map to cover all labels found in DB
old_facts_label = """    facts_label_map = {
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
        '\\u751F\\u7523\\u5408\\u8A08': 'Production Total', '\\u4E58\\u7528\\u8F66': 'Passenger',
        '\\u666E\\u901A\\u8F66': 'Standard', '\\u5C0F\\u578B\\u8F66': 'Small', '\\u8F7B\\u81EA\\u52D5\\u8F66': 'Kei',
        '\\u30C8\\u30E9\\u30C3\\u30AF': 'Truck', '\\u30D0\\u30B9': 'Bus',
        '\\u4FDD\\u6709\\u53F0\\u6570\\u5408\\u8A08': 'Ownership Total',
        '\\u51FA\\u53E3\\u65B0\\u8F66\\u5408\\u8A08': 'Export Total (New)',
    }"""

# Build comprehensive label map from actual DB values
new_facts_label = """    facts_label_map = {
        # Production
        '\\u56DB\\u8F2A\\u8E66\\u751F\\u7523\\u5408\\u8A08': 'Production Total',
        '\\u4E58\\u7528\\u8F66': 'Passenger', '\\u666E\\u901A\\u8F66': 'Standard',
        '\\u5C0F\\u578B\\u56DB\\u8F2A\\u8F66': 'Small', '\\u8F7B\\u56DB\\u8F2A\\u8F66': 'Kei',
        '\\u5361\\u8F66': 'Truck', '\\u5DF4\\u58EB': 'Bus',
        # Domestic sales (new)
        '\\u65B0\\u8F66\\u9500\\u552E\\u5408\\u8BA1': 'New Car Sales Total',
        '\\u4E58\\u7528\\u8F66(\\u65B0\\u8F66)': 'Passenger (New)', '\\u666E\\u901A\\u8F66(\\u65B0\\u8F66)': 'Standard (New)',
        '\\u5C0F\\u578B\\u56DB\\u8F2A\\u8F66(\\u65B0\\u8F66)': 'Small (New)', '\\u8F7B\\u56DB\\u8F2A\\u8F66(\\u65B0\\u8F66)': 'Kei (New)',
        '\\u5361\\u8F66(\\u65B0\\u8F66)': 'Truck (New)', '\\u5DF4\\u58EB(\\u65B0\\u8F66)': 'Bus (New)',
        # Used car sales
        '\\u4E2D\\u53E4\\u8F66\\u9500\\u552E\\u5408\\u8BA1': 'Used Car Sales Total',
        '\\u4E2D\\u53E4\\u4E58\\u7528\\u8F66': 'Used Passenger', '\\u4E2D\\u53E4\\u666E\\u901A\\u8F66': 'Used Standard',
        '\\u4E2D\\u53E4\\u5C0F\\u578B\\u56DB\\u8F2A\\u8F66': 'Used Small', '\\u4E2D\\u53E4\\u8F7B\\u56DB\\u8F2A\\u8F66': 'Used Kei',
        '\\u4E2D\\u53E4\\u5361\\u8F66': 'Used Truck', '\\u4E2D\\u53E4\\u5DF4\\u58EB': 'Used Bus',
        # Ownership
        '\\u4FDD\\u6709\\u53F0\\u6570\\u5408\\u8BA1': 'Ownership Total',
        '\\u4E58\\u7528\\u8F66\\u4FDD\\u6709': 'Passenger Ownership', '\\u666E\\u901A\\u8F66\\u4FDD\\u6709': 'Standard Ownership',
        '\\u5C0F\\u578B\\u56DB\\u8F2A\\u8F66\\u4FDD\\u6709': 'Small Ownership', '\\u8F7B\\u56DB\\u8F2A\\u8F66\\u4FDD\\u6709': 'Kei Ownership',
        '\\u5361\\u8F66\\u4FDD\\u6709': 'Truck Ownership', '\\u5DF4\\u58EB\\u4FDD\\u6709': 'Bus Ownership',
        # Export
        '\\u56DB\\u8F2A\\u8F66\\u51FA\\u53E3\\u5408\\u8BA1': 'Export Total',
        '\\u4E58\\u7528\\u8F66\\u51FA\\u53E3': 'Passenger Export', '\\u5361\\u8F66\\u51FA\\u53E3': 'Truck Export',
        '\\u5DF4\\u58EB\\u51FA\\u53E3': 'Bus Export',
        # World stats
        '\\u4E16\\u754C\\u751F\\u7523\\u5408\\u8BA1': 'World Production Total',
        '\\u4E16\\u754C\\u9500\\u552E\\u5408\\u8BA1': 'World Sales Total',
        '\\u4E16\\u754C\\u4FDD\\u6709\\u53F0\\u6570': 'World Ownership',
        # EV
        'EV\\u9500\\u552E\\u5408\\u8BA1': 'EV Sales Total', 'EV\\u5E02\\u573A\\u4EFD\\u989D(%)': 'EV Market Share (%)',
        '\\u4E58\\u7528\\u8F66\\u603B\\u9500\\u552E': 'Passenger Total Sales', '\\u6BD4\\u4E9A\\u8FEA': 'BYD',
        # Used car export
        '\\u4E0A\\u534A\\u5E74\\u4E2D\\u53E4\\u8F66\\u51FA\\u53E3': 'H1 Used Car Export',
        # Import sales (Japanese labels)
        '\\u8F38\\u5165\\u8ECA\\u8CA9\\u58F2\\u5408\\u8A08': 'Import Sales Total',
        '\\u8F38\\u5165\\u4E57\\u7528\\u8F66': 'Import Passenger', '\\u8F38\\u5165\\u5546\\u7528\\u8F66': 'Import Commercial',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u8ECA\\u5408\\u8A08': 'Import Used Total',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u4E57\\u7528\\u8F66': 'Import Used Passenger',
        '\\u8F38\\u5165\\u4E2D\\u53E4\\u30AB\\u30FC\\u30C8': 'Import Used Truck',
        # Regions (in facts table)
        '\\u5317\\u7C73': 'North America', '\\u6B27\\u5DDE': 'Europe', '\\u4E9A\\u6D32': 'Asia',
        '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania',
        '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u975E\\u6D32': 'Africa',
        '\\u5408\\u8BA1': 'Total', '\\u4E2D\\u5357\\u7C73': 'Central/South America',
    }"""

content = content.replace(old_facts_label, new_facts_label)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Comprehensive translation maps applied!")

import sys
sys.stdout.reconfigure(encoding='utf-8')

SHAPE_MAP = {'普通車': 'Standard Car', 'ハイブリッド': 'Hybrid', '電気自動車': 'EV', '軽自動車': 'Kei Car', 'トラック': 'Truck', 'バス': 'Bus'}
COUNTRY_MAP = {'ロシア': 'Russia', 'モンゴル': 'Mongolia', 'ニュージーランド': 'New Zealand', 'マレーシア': 'Malaysia', 'アメリカ': 'USA', 'イギリス': 'UK', '中国': 'China', '韓国': 'South Korea', '香港': 'Hong Kong', '台湾': 'Taiwan'}

print("Shape:", {k: SHAPE_MAP[k] for k in list(SHAPE_MAP)[:3]})
print("Country:", {k: COUNTRY_MAP[k] for k in list(COUNTRY_MAP)[:5]})

# Check if dashboard.py loads without error
import py_compile
py_compile.compile(r'D:\japan-car-market\src\dashboard.py', doraise=True)
print("Syntax: OK")

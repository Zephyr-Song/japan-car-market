import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

# Test the translation functions
import importlib.util
spec = importlib.util.spec_from_file_location("dash", r"D:\japan-car-market\src\dashboard.py")
# Can't import streamlit module directly, so just test the maps
exec(open(r"D:\japan-car-market\src\dashboard.py", encoding="utf-8").read().split("st.set_page_config")[0])

# Test shape translation
print("=== Shape names ===")
for s in ['普通車', 'ハイブリッド', '電気自動車', '軽自動車', 'トラック', 'バス']:
    print(f"  {s} -> {translate_shape(s)}")

# Test country translation
print("\n=== Country names (first 15) ===")
for c in ['ロシア', 'モンゴル', 'ニュージーランド', 'マレーシア', 'アメリカ', 'イギリス', '中国', '韓国', '香港', '台湾', 'タイ', 'タンザニア', 'ウガンダ', 'ガーナ', 'チリ']:
    print(f"  {c} -> {translate_country(c)}")

# Test model name translation
print("\n=== Model names (first 10) ===")
for m in ['プリウス（トヨタ）', 'セレナ（日産）', 'N-BOXカスタム（ホンダ）', 'ステップワゴン（ホンダ）', 'タント（ダイハツ）', 'アクア（トヨタ）', 'ワゴンR（スズキ）', 'ハイゼットカーゴ（ダイハツ）', 'ミニ（BMW MINI）', 'モデル3（テスラ）']:
    print(f"  {m} -> {translate_model_name(m)}")

# Test body type translation
print("\n=== Body types ===")
for b in ['軽自動車', 'ミニバン/ワンボックス', 'コンパクト/ハッチバック', 'セダン/ハードトップ', 'SUV/クロカン', 'クーペ']:
    print(f"  {b} -> {translate_body_type(b)}")

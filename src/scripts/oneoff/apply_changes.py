import re

path = 'D:/japan-car-market/src/dashboard.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# === 1. Merge Tab 11 (Export Stats) into Tab 13 (Import & Export), remove Tab 11 ===

# Replace tab list: remove Export Stats, keep 12 tabs
old_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
        "💰 Price", "🏭 Brands", "📊 Scatter",
        "🚙 Vehicle Class", "📈 Year Trend", "🔮 Forecast",
        "🗺️ Region", "🇯🇵 JADA Sales",
        "⚡ Powertrain", "🆚 Domestic vs Import",
        "🚢 Export Stats", "📋 Market Report",
        "🌐 Import & Export"
    ])'''
new_tabs = '''    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
        "💰 Price", "🏭 Brands", "📊 Scatter",
        "🚙 Vehicle Class", "📈 Year Trend", "🔮 Forecast",
        "🗺️ Region", "🇯🇵 JADA Sales",
        "⚡ Powertrain", "🆚 Domestic vs Import",
        "📋 Market Report", "🌐 Import & Export"
    ])'''
content = content.replace(old_tabs, new_tabs)

# Remove the tab11 Export Stats block and renumber tab12->tab11, tab13->tab12
old_tab11_block = '''    with tab11:
        st.markdown('<div class="section-title">Japan Used Car Export Statistics</div>', unsafe_allow_html=True)
        chart_export_statistics()

    with tab12:
        st.markdown('<div class="section-title">Monthly Market Report — Registration & Rankings</div>', unsafe_allow_html=True)
        chart_market_report()

    with tab13:
        st.markdown('<div class="section-title">Japan Auto Market — Import & Export Overview</div>', unsafe_allow_html=True)
        chart_import_export()'''
new_tab11_block = '''    with tab11:
        st.markdown('<div class="section-title">Monthly Market Report — Registration & Rankings</div>', unsafe_allow_html=True)
        chart_market_report()

    with tab12:
        st.markdown('<div class="section-title">Japan Auto Market — Import & Export Overview</div>', unsafe_allow_html=True)
        chart_import_export()'''
content = content.replace(old_tab11_block, new_tab11_block)

# Update footer
old_footer = "13 Tabs: Price · Brands · Scatter · Vehicle Class · Year Trend · Forecast · Region · JADA Sales · Powertrain · Domestic vs Import · Export Stats · Market Report · Import & Export"
new_footer = "12 Tabs: Price · Brands · Scatter · Vehicle Class · Year Trend · Forecast · Region · JADA Sales · Powertrain · Domestic vs Import · Market Report · Import & Export"
content = content.replace(old_footer, new_footer)

# === 2. Replace all Japanese UI text in chart_import_export with English ===

# Export Overview sub-tab
content = content.replace('st.markdown("#### \\U0001F4CA Export Overview (New + Used)")', 'st.markdown("#### Export Overview (New + Used)")')
content = content.replace('st.markdown("**\\u65B0\\u8ECA\\u51FA\\u53E3\\u53F0\\u6570\\u63A8\\u79FB (JAMA)**")', 'st.markdown("**New Car Export (JAMA)**")')
content = content.replace('st.markdown("**\\u4E2D\\u53E4\\u8E66\\u51FA\\u53E3 (jumv.net)**")', 'st.markdown("**Used Car Export (jumv.net)**")')

# Filter: vehicle_type != '合計'
content = content.replace("export_type_df['vehicle_type'] != '\\u5408\\uBA1'", "export_type_df['vehicle_type'] != 'Total'")
content = content.replace("new_car_export_df['region'] != '\\u5408\\uBA1'", "new_car_export_df['region'] != 'Total'")
content = content.replace("overseas_annual_df['region'] != '\\u5408\\uBA1'", "overseas_annual_df['region'] != 'Total'")
content = content.replace("import_customs_df['country'] != '\\u5408\\uBA1'", "import_customs_df['country'] != 'Total'")

# shape_name label
content = content.replace("labels={'export_count': 'Units', 'shape_name': ''}", "labels={'export_count': 'Units', 'shape_name': 'Vehicle Type'}")

# Section headers
content = content.replace('st.markdown("#### \\u4ED5\\u5411\\u5730\\u5225\\u51FA\\u53E3\\u63A8\\u79FB (Destination Region)")', 'st.markdown("#### New Car Export by Destination Region")')
content = content.replace('st.markdown("#### EV / HV \\u51FA\\u53E3\\u8D8B\\u52BF (EV Trend)")', 'st.markdown("#### EV / HV Export Trend")')
content = content.replace('st.markdown("**\\u4ED5\\u5411\\u5730\\u5225\\u51FA\\u53E3\\u30C7\\u30FC\\u30BF**")', 'st.markdown("**Export by Region - Data Table**")')

# Import Overview sub-tab
content = content.replace('st.markdown("#### \\u8FDB\\u53E3\\u8F66\\u54C1\\u724C\\u522B\\u6708\\u6B21\\u63A8\\u79FB (Top10 Brands)")', 'st.markdown("#### Import Car Monthly Top 10 Brands")')
content = content.replace('st.markdown("#### \\u8FDB\\u53E3 vs \\u56FD\\u4EA7\\u5BF9\\u6BD4 (Import vs Domestic)")', 'st.markdown("#### Import vs Domestic Comparison")')
content = content.replace('st.markdown("#### \\u8F38\\u5165\\u8ECA\\u8CA9\\u58F2\\u53F0\\u6570\\u63A8\\u79FB (2019-2024)")', 'st.markdown("#### Import Car Sales Trend (2019-2024)")')
content = content.replace('st.markdown("#### \\u81EA\\u52D5\\u8ECA\\u8F38\\u5165\\u53F0\\u6570 (\\u901A\\u95A2\\u5B9F\\u7E3E - by Country)")', 'st.markdown("#### Import by Country (Customs Data)")')

# Overseas Production sub-tab
content = content.replace('st.markdown("#### \\u6D77\\u5916\\u751F\\u4EA7\\u30C7\\u30FC\\u30BF (Overseas Production)")', 'st.markdown("#### Overseas Production Data")')

# Quarterly data - region name mapping
# Add region_map after the overseas_df loading
old_q1_display = "q1_display = q1_data[q1_data['region'] != '\\u5408\\u8A08'].copy()"
new_q1_display = """region_map = {'\\u30A2\\u30B8\\u30A2': 'Asia', '\\u6B27\\u5DDE': 'Europe', '\\u5317\\u7C73': 'North America', '\\u4E2D\\u5357\\u7C73': 'Central/South America', '\\u30A2\\u30D5\\u30EA\\u30AB': 'Africa', '\\u5408\\u8A08': 'Total', '\\u4E2D\\u8FD1\\u6771': 'Middle East', '\\u5927\\u6D0B\\u5DDE': 'Oceania'}
                    q1_display = q1_data[q1_data['region'] != '\\u5408\\u8A08'].copy()
                    q1_display['region'] = q1_display['region'].map(lambda x: region_map.get(x, x))"""
content = content.replace(old_q1_display, new_q1_display, 1)

old_annual_display = "annual_display = annual_data[annual_data['region'] != '\\u5408\\u8A08'].copy()"
new_annual_display = """annual_display = annual_data[annual_data['region'] != '\\u5408\\u8A08'].copy()
                    annual_display['region'] = annual_display['region'].map(lambda x: region_map.get(x, x))"""
content = content.replace(old_annual_display, new_annual_display, 1)

# YoY comparison - map region names
old_yoy = "q1_compare = q1_data[q1_data['region'].isin(['\\u30A2\\u30B8\\u30A2', '\\u6B27\\u5DDE', '\\u5317\\u7C73', '\\u4E2D\\u5357\\u7C73', '\\u30A2\\u30D5\\u30EA\\u30AB', '\\u5408\\u8A08'])].copy()"
new_yoy = """q1_compare = q1_data[q1_data['region'].isin(['\\u30A2\\u30B8\\u30A2', '\\u6B27\\u5DDE', '\\u5317\\u7C73', '\\u4E2D\\u5357\\u7C73', '\\u30A2\\u30D5\\u30EA\\u30AB', '\\u5408\\u8A08'])].copy()
                q1_compare['region'] = q1_compare['region'].map(lambda x: region_map.get(x, x))"""
content = content.replace(old_yoy, new_yoy)

# === 3. Add used car export detail (from chart_export_statistics) into Export Overview ===
# Find the insertion point: after the Used Car Export chart and before Chart 2
old_insertion_point = """        # --- Chart 2: Destination Region Export Trend ---
        st.markdown("---")
        st.markdown("#### New Car Export by Destination Region")"""

new_insertion_block = """        # --- Used Car Export Detail (merged from Export Stats tab) ---
        st.markdown("---")
        st.markdown("#### Used Car Export Destinations (jumv.net)")
        if not export_df.empty:
            df_monthly_exp = export_df[export_df['month'] > 0].copy() if 'month' in export_df.columns else export_df.copy()
            df_annual_exp = export_df[export_df['month'] == 0].copy() if 'month' in export_df.columns else pd.DataFrame()

            if not df_monthly_exp.empty and 'country_name' in df_monthly_exp.columns:
                latest_exp = df_monthly_exp.groupby(['year', 'month'])['export_count'].sum().idxmax()
                latest_exp_data = df_monthly_exp[(df_monthly_exp['year'] == latest_exp[0]) & (df_monthly_exp['month'] == latest_exp[1])]

                st.markdown(f"**Top Destinations ({latest_exp[0]}-{latest_exp[1]:02d})**")
                if 'shape_name' in latest_exp_data.columns:
                    vtypes = latest_exp_data['shape_name'].unique()
                    if len(vtypes) > 1:
                        vtabs = st.tabs([str(v) for v in sorted(vtypes)[:6]])
                        for i, vt in enumerate(sorted(vtypes)[:6]):
                            with vtabs[i]:
                                sub = latest_exp_data[latest_exp_data['shape_name'] == vt].nlargest(10, 'export_count')
                                if not sub.empty:
                                    fig = px.bar(sub, x='export_count', y='country_name', orientation='h',
                                                 title=f"{vt} - Top 10 Destinations",
                                                 color='export_count', color_continuous_scale='Viridis',
                                                 height=350)
                                    fig.update_layout(yaxis={'categoryorder': 'total ascending'},
                                                      xaxis_title="Units", yaxis_title="Country")
                                    st.plotly_chart(fig, use_container_width=True)
                    else:
                        sub = latest_exp_data.nlargest(15, 'export_count')
                        fig = px.bar(sub, x='export_count', y='country_name', orientation='h',
                                     color='export_count', color_continuous_scale='Viridis', height=400)
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'},
                                          xaxis_title="Units", yaxis_title="Country")
                        st.plotly_chart(fig, use_container_width=True)

            if not df_annual_exp.empty and 'country_name' in df_annual_exp.columns:
                st.markdown("**Annual Export Trend - Top 5 Destinations**")
                top_countries = df_annual_exp.groupby('country_name')['export_count'].sum().nlargest(5).index.tolist()
                country_trend = df_annual_exp[df_annual_exp['country_name'].isin(top_countries)].groupby(['year', 'country_name'])['export_count'].sum().reset_index()
                fig = px.line(country_trend, x='year', y='export_count', color='country_name',
                              title="Annual Export Trend - Top 5 Countries", height=400, markers=True)
                fig.update_layout(xaxis_title="Year", yaxis_title="Units", legend_title="Country")
                st.plotly_chart(fig, use_container_width=True)

        # --- Chart 2: Destination Region Export Trend ---
        st.markdown("---")
        st.markdown("#### New Car Export by Destination Region")"""

content = content.replace(old_insertion_point, new_insertion_block)

# === 4. Replace other Chinese UI text ===
content = content.replace('st.warning("⚠️ 二手车数据库为空，部分功能不可用。请运行 `python src/crawler.py` 采集数据，或点击下方按钮刷新。")', 
                          'st.warning("Used car database is empty. Run `python src/crawler.py` to collect data, or click refresh below.")')
content = content.replace('# 仍然展示宏观数据', '# Show macro data anyway')
content = content.replace('st.metric("📦 二手车总量", f"{total_used:,}", f"+{new_listings} 最新批次")', 
                          'st.metric("Used Cars", f"{total_used:,}", f"+{new_listings} latest")')
content = content.replace('st.metric("🇯🇵 行业数据"', 'st.metric("JADA Data"')
content = content.replace('st.metric("🏭 新车品牌数"', 'st.metric("Brands"')
content = content.replace('st.metric("🚗 K-car 品牌数"', 'st.metric("K-car Brands"')
content = content.replace('st.caption(f"📋 最近 {len(crawl_recent)} 次爬取: " + " | ".join([f"{d}: {c}辆" for d, c in crawl_recent]))',
                          'st.caption(f"Last {len(crawl_recent)} crawls: " + " | ".join([f"{d}: {c} cars" for d, c in crawl_recent]))')
content = content.replace('tab_a, tab_b = st.tabs(["⛽ 动力类型", "🔧 变速箱"])', 
                          'tab_a, tab_b = st.tabs(["Fuel Type", "Transmission"])')
content = content.replace('st.metric("🇯🇵 日本品牌"', 'st.metric("JP Brands"')
content = content.replace('st.metric("🌍 进口品牌"', 'st.metric("Import Brands"')
content = content.replace('st.metric("📊 品牌数"', 'st.metric("Total Brands"')
content = content.replace("labels={'mileage_wan_km': 'Mileage (万km)'", "labels={'mileage_wan_km': 'Mileage (10k km)'")
content = content.replace("st.markdown(\"#### 📏 排量分布对比\")", "st.markdown(\"#### Displacement Distribution\")")

# Macro monthly Chinese
content = content.replace('st.metric(f"📍 {int(latest[\'year\'])}/{int(latest[\'month\'])}月 总销量", v)',
                          'st.metric(f"Latest: {int(latest[\'year\'])}/{int(latest[\'month\']):02d} Total", v)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("All replacements done successfully!")

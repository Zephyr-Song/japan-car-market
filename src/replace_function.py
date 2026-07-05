import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

filepath = r'D:\japan-car-market\src\dashboard.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the function boundaries
start_marker = "def chart_import_export():"
end_marker = "def main():"

start_idx = content.index(start_marker)
end_idx = content.index(end_marker)

print(f"Replacing from {start_idx} to {end_idx} (length: {end_idx - start_idx})")

new_func = '''def chart_import_export():
    """Japan auto market import & export overview - JAMA + JAIA data"""
    import sqlite3 as _sqlite3

    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "japan_car_market.db")
    conn = _sqlite3.connect(str(db_path))

    # Load all relevant tables
    facts_df = pd.read_sql_query("SELECT * FROM jama_annual_facts", conn)
    overseas_df = pd.read_sql_query("SELECT * FROM jama_overseas_production", conn)
    import_df = pd.read_sql_query("SELECT * FROM import_car_stats", conn)
    export_df = pd.read_sql_query("SELECT * FROM export_statistics", conn)
    import_monthly_df = pd.read_sql_query("SELECT * FROM import_car_monthly", conn)
    new_car_export_df = pd.read_sql_query("SELECT * FROM new_car_export", conn)
    export_type_df = pd.read_sql_query("SELECT * FROM export_by_type", conn)
    import_customs_df = pd.read_sql_query("SELECT * FROM import_customs", conn)
    overseas_annual_df = pd.read_sql_query("SELECT * FROM overseas_production_annual", conn)

    conn.close()

    if facts_df.empty:
        st.warning("No JAMA data available. Run crawl_jama_facts.py first.")
        return

    # Sub-tabs
    ie_tab1, ie_tab2, ie_tab3, ie_tab4 = st.tabs([
        "\\U0001F6A2 Export Overview",
        "\\U0001F4E5 Import Overview",
        "\\U0001F310 Overseas Production",
        "\\U0001F3ED Production & Sales"
    ])

    # ====== Tab 1: Export Overview ======
    with ie_tab1:
        st.markdown("#### \\U0001F4CA Export Overview (New + Used)")

        # --- Chart 1: New Car Export + Used Car Export by year ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**\\u65B0\\u8ECA\\u51FA\\u53E3\\u53F0\\u6570\\u63A8\\u79FB (JAMA)**")
            if not export_type_df.empty:
                et_pivot = export_type_df[export_type_df['vehicle_type'] != '\\u5408\\u8BA1'].pivot_table(
                    index='year', columns='vehicle_type', values='units', aggfunc='sum'
                ).reset_index()
                fig = go.Figure()
                for col_name in et_pivot.columns[1:]:
                    fig.add_trace(go.Bar(
                        x=et_pivot['year'], y=et_pivot[col_name],
                        name=col_name
                    ))
                fig.update_layout(
                    barmode='stack',
                    title='New Car Export by Vehicle Type (2019-2024)',
                    xaxis_title='Year', yaxis_title='Units',
                    height=400, legend=dict(orientation='h', y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**\\u4E2D\\u53E4\\u8E66\\u51FA\\u53E3 (jumv.net)**")
            if not export_df.empty:
                latest_month = export_df[export_df['month'] > 0]['month'].max()
                latest_year = export_df[export_df['month'] > 0]['year'].max()
                shape_counts = export_df[
                    (export_df['year'] == latest_year) &
                    (export_df['month'] == latest_month) &
                    (export_df['country_name'] != 'Total')
                ].groupby('shape_name')['export_count'].sum().reset_index()
                shape_counts = shape_counts.sort_values('export_count', ascending=False)
                if not shape_counts.empty:
                    fig = px.bar(
                        shape_counts,
                        x='shape_name', y='export_count',
                        color='export_count', color_continuous_scale='Sunset',
                        title=f'Used Car Export by Type ({latest_year}-{latest_month:02d})',
                        labels={'export_count': 'Units', 'shape_name': ''}
                    )
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)

        # --- Chart 2: Destination Region Export Trend ---
        st.markdown("---")
        st.markdown("#### \\u4ED5\\u5411\\u5730\\u5225\\u51FA\\u53E3\\u63A8\\u79FB (Destination Region)")
        if not new_car_export_df.empty:
            nce_pivot = new_car_export_df[new_car_export_df['region'] != '\\u5408\\u8BA1'].pivot_table(
                index='year', columns='region', values='units', aggfunc='sum'
            ).reset_index()

            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                for col_name in nce_pivot.columns[1:]:
                    fig.add_trace(go.Bar(
                        x=nce_pivot['year'], y=nce_pivot[col_name],
                        name=col_name
                    ))
                fig.update_layout(
                    barmode='stack',
                    title='Export by Region (Stacked Bar)',
                    xaxis_title='Year', yaxis_title='Units',
                    height=450, legend=dict(orientation='h', y=-0.15)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = go.Figure()
                for col_name in nce_pivot.columns[1:]:
                    fig.add_trace(go.Scatter(
                        x=nce_pivot['year'], y=nce_pivot[col_name],
                        name=col_name, mode='lines+markers'
                    ))
                fig.update_layout(
                    title='Export by Region (Trend Lines)',
                    xaxis_title='Year', yaxis_title='Units',
                    height=450, legend=dict(orientation='h', y=-0.15)
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- Chart 5: EV Export Trend ---
        st.markdown("---")
        st.markdown("#### EV / HV \\u51FA\\u53E3\\u8D8B\\u52BF (EV Trend)")
        ev_data = facts_df[facts_df['category'] == 'ev_sales'].copy()
        if not ev_data.empty:
            ev_total = ev_data[ev_data['subcategory'] == 'total']['value'].values
            ev_share = ev_data[ev_data['subcategory'] == 'market_share']['value'].values
            ev_passenger = ev_data[ev_data['subcategory'] == 'total_passenger']['value'].values
            byd = ev_data[ev_data['subcategory'] == 'byd']['value'].values

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("EV Sales 2025", f"{ev_total[0]:,}" if len(ev_total) else "N/A")
            with col2:
                st.metric("EV Market Share", f"{ev_share[0]/10:.1f}%" if len(ev_share) else "N/A")
            with col3:
                st.metric("BYD Sales", f"{byd[0]:,}" if len(byd) else "N/A")

            if len(ev_passenger) and len(ev_total):
                fig = px.pie(
                    values=[ev_total[0], max(ev_passenger[0] - ev_total[0], 1)],
                    names=['EV', 'Non-EV'],
                    title='EV vs Non-EV in Passenger Car Sales (2025)',
                    color_discrete_sequence=['#00c853', '#b0bec5']
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

        # Export data table
        st.markdown("---")
        st.markdown("**\\u4ED5\\u5411\\u5730\\u5225\\u51FA\\u53E3\\u30C7\\u30FC\\u30BF**")
        if not new_car_export_df.empty:
            display_df = new_car_export_df.pivot_table(
                index='year', columns='region', values='units', aggfunc='sum'
            ).reset_index()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ====== Tab 2: Import Overview ======
    with ie_tab2:
        st.markdown("#### \\u8FDB\\u53E3\\u8F66\\u54C1\\u724C\\u522B\\u6708\\u6B21\\u63A8\\u79FB (Top10 Brands)")

        # --- Chart 3: Import car monthly Top10 brands trend ---
        if not import_monthly_df.empty:
            im_df = import_monthly_df.copy()
            im_df['ym'] = im_df['year'].astype(str) + '-' + im_df['month'].astype(str).str.zfill(2)

            # Get top brands by total volume
            top_brands = im_df.groupby('brand')['units'].sum().nlargest(10).index.tolist()

            # Pivot for line chart
            im_pivot = im_df[im_df['brand'].isin(top_brands)].pivot_table(
                index='ym', columns='brand', values='units', aggfunc='sum'
            ).reset_index()
            im_pivot = im_pivot.sort_values('ym')

            fig = go.Figure()
            colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
            for i, brand in enumerate(top_brands):
                if brand in im_pivot.columns:
                    fig.add_trace(go.Scatter(
                        x=im_pivot['ym'], y=im_pivot[brand],
                        name=brand, mode='lines+markers',
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=5)
                    ))
            fig.update_layout(
                title='Import Car Monthly Registration - Top 10 Brands',
                xaxis_title='Year-Month', yaxis_title='Units',
                height=500, legend=dict(orientation='h', y=-0.2),
                xaxis=dict(tickangle=-45, nticks=15)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Latest month table
            latest_ym = im_df['ym'].max()
            latest_im = im_df[im_df['ym'] == latest_ym].sort_values('rank')
            st.markdown(f"**Latest month: {latest_ym}**")
            st.dataframe(
                latest_im[['rank', 'brand', 'units', 'yoy_pct']].rename(
                    columns={'rank': 'Rank', 'brand': 'Brand', 'units': 'Units', 'yoy_pct': 'YoY (%)'}
                ),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No monthly import data available.")

        # --- Chart 4: Import vs Domestic ---
        st.markdown("---")
        st.markdown("#### \\u8FDB\\u53E3 vs \\u56FD\\u4EA7\\u5BF9\\u6BD4 (Import vs Domestic)")
        imp_sales = facts_df[facts_df['category'] == 'import_sales'].copy()
        imp_used = facts_df[facts_df['category'] == 'import_used'].copy()

        col1, col2 = st.columns(2)

        with col1:
            if not imp_sales.empty:
                imp_total = imp_sales[imp_sales['subcategory'] == 'total'].copy()
                dom_total = facts_df[(facts_df['category'] == 'domestic_sales') & (facts_df['subcategory'] == 'total_new')].copy()

                if not imp_total.empty and not dom_total.empty:
                    merged = imp_total[['year', 'value']].rename(columns={'value': 'import'}).merge(
                        dom_total[['year', 'value']].rename(columns={'value': 'domestic'}),
                        on='year', how='outer'
                    ).fillna(0)
                    merged = merged.sort_values('year')

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=merged['year'], y=merged['domestic'],
                        name='Domestic', marker_color='#1a73e8'
                    ))
                    fig.add_trace(go.Bar(
                        x=merged['year'], y=merged['import'],
                        name='Import', marker_color='#e8710a'
                    ))
                    fig.update_layout(
                        barmode='group',
                        title='Domestic vs Import Sales (Multi-Year)',
                        xaxis_title='Year', yaxis_title='Units',
                        height=400, legend=dict(orientation='h', y=-0.15)
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with col2:
            if not imp_sales.empty:
                imp_2024 = imp_sales[(imp_sales['subcategory'] == 'total') & (imp_sales['year'] == 2024)]['value'].values
                dom_2024 = facts_df[(facts_df['category'] == 'domestic_sales') & (facts_df['subcategory'] == 'total_new') & (facts_df['year'] == 2024)]['value'].values
                if len(imp_2024) and len(dom_2024):
                    compare_df = pd.DataFrame({
                        'Type': ['Domestic', 'Import'],
                        'Volume': [dom_2024[0], imp_2024[0]]
                    })
                    fig = px.pie(compare_df, values='Volume', names='Type',
                                 title='2024: Domestic vs Import Share',
                                 color_discrete_sequence=['#1a73e8', '#e8710a'])
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                    ratio = imp_2024[0] / (dom_2024[0] + imp_2024[0]) * 100
                    st.metric("Import Market Share (2024)", f"{ratio:.1f}%")

        # Import sales historical
        st.markdown("---")
        st.markdown("#### \\u8F38\\u5165\\u8ECA\\u8CA9\\u58F2\\u53F0\\u6570\\u63A8\\u79FB (2019-2024)")
        col1, col2 = st.columns(2)
        with col1:
            if not imp_sales.empty:
                is_pivot = imp_sales.pivot_table(
                    index='year', columns='label', values='value', aggfunc='sum'
                ).reset_index()
                fig = px.bar(
                    is_pivot, x='year',
                    y=[c for c in is_pivot.columns if c != 'year'],
                    title='Import Car Sales Trend',
                    labels={'value': 'Units', 'year': 'Year'},
                    barmode='group'
                )
                fig.update_layout(height=400, legend=dict(orientation='h', y=-0.2))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if not imp_used.empty:
                iu_pivot = imp_used.pivot_table(
                    index='year', columns='label', values='value', aggfunc='sum'
                ).reset_index()
                fig = px.bar(
                    iu_pivot, x='year',
                    y=[c for c in iu_pivot.columns if c != 'year'],
                    title='Import Used Car Trend',
                    labels={'value': 'Units', 'year': 'Year'},
                    barmode='group'
                )
                fig.update_layout(height=400, legend=dict(orientation='h', y=-0.2))
                st.plotly_chart(fig, use_container_width=True)

        # Customs import by country
        st.markdown("---")
        st.markdown("#### \\u81EA\\u52D5\\u8ECA\\u8F38\\u5165\\u53F0\\u6570 (\\u901A\\u95A2\\u5B9F\\u7E3E - by Country)")
        if not import_customs_df.empty:
            ic_pivot = import_customs_df[import_customs_df['country'] != '\\u5408\\u8BA1'].pivot_table(
                index='year', columns='country', values='units', aggfunc='sum'
            ).reset_index()

            fig = go.Figure()
            for col_name in ic_pivot.columns[1:]:
                fig.add_trace(go.Bar(
                    x=ic_pivot['year'], y=ic_pivot[col_name],
                    name=col_name
                ))
            fig.update_layout(
                barmode='stack',
                title='Import by Country (Customs Data)',
                xaxis_title='Year', yaxis_title='Units',
                height=400, legend=dict(orientation='h', y=-0.2)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ====== Tab 3: Overseas Production ======
    with ie_tab3:
        st.markdown("#### \\u6D77\\u5916\\u751F\\u4EA7\\u30C7\\u30FC\\u30BF (Overseas Production)")

        # --- Chart 6: Overseas production by region (annual) ---
        if not overseas_annual_df.empty:
            op_pivot = overseas_annual_df[overseas_annual_df['region'] != '\\u5408\\u8BA1'].pivot_table(
                index='year', columns='region', values='units', aggfunc='sum'
            ).reset_index()

            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                for col_name in op_pivot.columns[1:]:
                    fig.add_trace(go.Bar(
                        x=op_pivot['year'], y=op_pivot[col_name],
                        name=col_name
                    ))
                fig.update_layout(
                    barmode='stack',
                    title='Overseas Production by Region (Stacked)',
                    xaxis_title='Year', yaxis_title='Units',
                    height=450, legend=dict(orientation='h', y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = go.Figure()
                for col_name in op_pivot.columns[1:]:
                    fig.add_trace(go.Scatter(
                        x=op_pivot['year'], y=op_pivot[col_name],
                        name=col_name, mode='lines+markers'
                    ))
                fig.update_layout(
                    title='Overseas Production Trend (Lines)',
                    xaxis_title='Year', yaxis_title='Units',
                    height=450, legend=dict(orientation='h', y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)

        # Quarterly data
        st.markdown("---")
        st.markdown("#### JAMA Quarterly Overseas Production")
        if not overseas_df.empty:
            latest_date = overseas_df['report_date'].max()
            latest_data = overseas_df[overseas_df['report_date'] == latest_date].copy()
            st.caption(f"Report date: {latest_date}")

            q1_data = latest_data[latest_data['period'] == 'Q1']
            annual_data = latest_data[latest_data['period'] == 'annual']

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Q1 Overseas Production**")
                if not q1_data.empty:
                    q1_display = q1_data[q1_data['region'] != '\\u5408\\u8A08'].copy()
                    fig = px.bar(
                        q1_display,
                        x='region', y='current_value',
                        color='current_value', color_continuous_scale='Deep',
                        labels={'current_value': 'Units', 'region': ''},
                        text='current_value'
                    )
                    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**Annual Overseas Production**")
                if not annual_data.empty:
                    annual_display = annual_data[annual_data['region'] != '\\u5408\\u8A08'].copy()
                    fig = px.bar(
                        annual_display,
                        x='region', y='current_value',
                        color='current_value', color_continuous_scale='Matter',
                        labels={'current_value': 'Units', 'region': ''},
                        text='current_value'
                    )
                    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)

            # YoY comparison
            if not q1_data.empty:
                st.markdown("---")
                st.markdown("**Year-over-Year Comparison**")
                q1_compare = q1_data[q1_data['region'].isin(['\\u30A2\\u30B8\\u30A2', '\\u6B27\\u5DDE', '\\u5317\\u7C73', '\\u4E2D\\u5357\\u7C73', '\\u30A2\\u30D5\\u30EA\\u30AB', '\\u5408\\u8A08'])].copy()
                q1_compare = q1_compare.rename(columns={'current_value': '2026 Q1', 'previous_value': '2025 Q1'})
                if not q1_compare.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='2025 Q1', x=q1_compare['region'], y=q1_compare['2025 Q1'], marker_color='#90caf9'))
                    fig.add_trace(go.Bar(name='2026 Q1', x=q1_compare['region'], y=q1_compare['2026 Q1'], marker_color='#1565c0'))
                    fig.update_layout(barmode='group', title='Q1 YoY Comparison', height=400)
                    st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.markdown("---")
            st.markdown("**Detailed Quarterly Data**")
            display_df = latest_data[['period', 'region', 'current_value', 'previous_value', 'yoy_percent']].copy()
            display_df.columns = ['Period', 'Region', 'Current', 'Previous', 'YoY (%)']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ====== Tab 4: Production & Sales ======
    with ie_tab4:
        st.markdown("#### 2024 Production & Domestic Sales (JAMA)")

        prod = facts_df[facts_df['category'] == 'production'].copy()
        sales = facts_df[facts_df['category'] == 'domestic_sales'].copy()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Production by Vehicle Type**")
            if not prod.empty:
                fig = px.bar(
                    prod[prod['subcategory'].isin(['total', 'passenger', 'standard', 'small', 'kei', 'truck', 'bus'])],
                    x='label', y='value',
                    color='value', color_continuous_scale='Blues',
                    title='2024 Production Volume',
                    labels={'value': 'Units', 'label': ''}
                )
                fig.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Domestic New Car Sales**")
            if not sales.empty:
                fig = px.bar(
                    sales[sales['subcategory'].isin(['total_new', 'passenger_new', 'standard_new', 'small_new', 'kei_new', 'truck_new', 'bus_new'])],
                    x='label', y='value',
                    color='value', color_continuous_scale='Greens',
                    title='2024 Domestic Sales Volume',
                    labels={'value': 'Units', 'label': ''}
                )
                fig.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)

        # Key metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        total_prod = facts_df[(facts_df['category'] == 'production') & (facts_df['subcategory'] == 'total')]['value']
        total_sales = facts_df[(facts_df['category'] == 'domestic_sales') & (facts_df['subcategory'] == 'total_new')]['value']
        total_export = facts_df[(facts_df['category'] == 'export') & (facts_df['subcategory'] == 'total_new')]['value']
        total_own = facts_df[(facts_df['category'] == 'ownership') & (facts_df['subcategory'] == 'total')]['value']
        with col1:
            st.metric("Total Production", f"{total_prod.values[0]:,.0f}" if len(total_prod) else "N/A")
        with col2:
            st.metric("Domestic Sales", f"{total_sales.values[0]:,.0f}" if len(total_sales) else "N/A")
        with col3:
            st.metric("Total Export", f"{total_export.values[0]:,.0f}" if len(total_export) else "N/A")
        with col4:
            st.metric("Total Ownership", f"{total_own.values[0]:,.0f}" if len(total_own) else "N/A")

        # Used car market
        st.markdown("---")
        st.markdown("#### Used Car Market (2024)")
        used = facts_df[facts_df['category'] == 'used_sales'].copy()
        if not used.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    used[used['subcategory'] != 'total'],
                    x='label', y='value',
                    color='value', color_continuous_scale='Oranges',
                    title='Used Car Sales by Type',
                    labels={'value': 'Units', 'label': ''}
                )
                fig.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                used_total = used[used['subcategory'] == 'total']['value'].values
                new_total = total_sales.values
                if len(used_total) and len(new_total):
                    compare_df = pd.DataFrame({
                        'Type': ['New Car Sales', 'Used Car Sales'],
                        'Volume': [new_total[0], used_total[0]]
                    })
                    fig = px.pie(compare_df, values='Volume', names='Type',
                                 title='New vs Used Car Sales Ratio',
                                 color_discrete_sequence=['#4285F4', '#FF6D00'])
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)


'''

new_content = content[:start_idx] + new_func + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Done! File updated. New length: {len(new_content)}")
print(f"Function replaced: {len(new_func)} chars")

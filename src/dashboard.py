"""
Japan Used Car Market Intelligence Dashboard
Real-time monitoring of prices, brand distribution, and market trends
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'japan_car_market.db')

st.set_page_config(
    page_title="Japan Used Car Market Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====== Custom CSS ======
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 20px 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .kpi-card h2 { margin:0; font-size:2em; font-weight:800; }
    .kpi-card p { margin:4px 0 0; opacity:0.9; font-size:0.9em; }
    .kpi-red { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); box-shadow: 0 4px 15px rgba(245,87,108,0.4); }
    .kpi-green { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); box-shadow: 0 4px 15px rgba(79,172,254,0.4); }
    .kpi-gold { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); box-shadow: 0 4px 15px rgba(253,160,133,0.4); }
    .section-title {
        font-size: 1.4em;
        font-weight: 700;
        border-left: 4px solid #1a73e8;
        padding-left: 12px;
        margin: 24px 0 12px;
    }
    .gradient-divider {
        height: 3px;
        background: linear-gradient(90deg, #1a73e8, #ea4335, #fbbc04, #34a853);
        border-radius: 2px;
        margin: 20px 0;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .live-badge {
        display: inline-block;
        background: #ea4335;
        color: white;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.8em;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: slideIn 0.6s ease-out;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    except Exception:
        try:
            df = pd.read_sql_query("SELECT * FROM used_cars", conn)
        except Exception:
            df = pd.DataFrame()
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_macro_data():
    """加载宏观数据: 月度总销量 + 品牌别销量."""
    conn = sqlite3.connect(DB_PATH)
    try:
        summary = pd.read_sql_query(
            "SELECT * FROM japan_monthly_summary ORDER BY year, month", conn)
    except Exception:
        summary = pd.DataFrame()
    try:
        brand = pd.read_sql_query(
            "SELECT * FROM new_car_sales_brand ORDER BY year, month", conn)
    except Exception:
        brand = pd.DataFrame()
    try:
        kcar_brand = pd.read_sql_query(
            "SELECT * FROM kcar_brand_sales ORDER BY year, month", conn)
    except Exception:
        kcar_brand = pd.DataFrame()
    try:
        kcar_monthly = pd.read_sql_query(
            "SELECT * FROM kcar_monthly_sales ORDER BY year, month", conn)
    except Exception:
        kcar_monthly = pd.DataFrame()
    conn.close()
    return summary, brand, kcar_brand, kcar_monthly


def render_kpi_cards(df):
    price_col = 'price_vehicle'
    total = len(df)
    avg_price = df[price_col].mean() if price_col in df.columns and len(df) > 0 else 0
    n_brands = df['brand_clean'].nunique() if 'brand_clean' in df.columns else 0
    kcar_pct = (df['vehicle_class'] == 'K-car (<=660cc)').mean() * 100 if 'vehicle_class' in df.columns and len(df) > 0 else 0

    cols = st.columns(4)
    kpis = [
        ("🚗", f"{total:,}", "Vehicles Listed", ""),
        ("💰", f"{avg_price:.1f}", "Avg Price (man-yen)", "kpi-red"),
        ("🏭", f"{n_brands}", "Brands", "kpi-green"),
        ("🇯🇵", f"{kcar_pct:.1f}%", "K-car Share", "kpi-gold"),
    ]
    for col, (icon, value, label, cls) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls} animate-in">
                <p>{icon}</p>
                <h2>{value}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)


def chart_price_distribution(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & (df[price_col] < 2000)].copy()
    if len(df_p) == 0:
        st.info("No data in selected price range.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.histogram(df_p, x=price_col, nbins=60,
                           title="Price Distribution",
                           color_discrete_sequence=['#1a73e8'], opacity=0.75)
        fig.add_vline(x=df_p[price_col].mean(), line_dash="dash", line_color="#ea4335",
                      annotation_text=f"Mean: {df_p[price_col].mean():.0f}")
        fig.add_vline(x=df_p[price_col].median(), line_dash="dot", line_color="#34a853",
                      annotation_text=f"Median: {df_p[price_col].median():.0f}")
        fig.update_layout(xaxis_title="Price (man-yen)", yaxis_title="Count", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Price Range Breakdown")
        price_bins = [0, 50, 100, 150, 200, 300, 500, 10000]
        labels = ['<50', '50-100', '100-150', '150-200', '200-300', '300-500', '500+']
        df_p2 = df_p.copy()
        df_p2['range'] = pd.cut(df_p2[price_col], bins=price_bins, labels=labels)
        bin_stats = df_p2.groupby('range', observed=True).agg(
            count=(price_col, 'count'), avg_price=(price_col, 'mean'),
        )
        for label, row in bin_stats.iterrows():
            if row['count'] == 0:
                continue
            pct = row['count'] / len(df_p) * 100
            dot = "🟢" if pct > 20 else "🔵" if pct > 10 else "⚪"
            st.markdown(f"**{dot} {label} man-yen**: {int(row['count'])} cars ({pct:.1f}%) · avg {row['avg_price']:.0f}")


def chart_brand_analysis(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['brand_clean'].notna()].copy()
    if len(df_p) == 0:
        st.info("No data available.")
        return

    brand_counts = df_p['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()

    tab1, tab2, tab3 = st.tabs(["📈 Price Range by Brand", "🥧 Market Share", "🎬 Brand Race"])

    with tab1:
        selected = st.multiselect("Select brands (max 8)", top_brands,
                                   default=top_brands[:8], key='brand_box')
        if selected:
            df_sel = df_p[df_p['brand_clean'].isin(selected)]
            fig = go.Figure()
            for brand in selected:
                brand_data = df_sel[df_sel['brand_clean'] == brand][price_col]
                fig.add_trace(go.Box(y=brand_data, name=brand, boxpoints='outliers',
                                     marker_size=3, line_width=2))
            fig.update_layout(title="Brand Price Range (Box Plot)",
                             yaxis_title="Price (man-yen)", showlegend=True, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        df_p2 = df_p.copy()
        df_p2['origin'] = df_p2['brand_clean'].apply(
            lambda b: 'Domestic (JP)' if b in ['Toyota','Honda','Nissan','Suzuki','Daihatsu','Mazda','Subaru','Mitsubishi','Lexus'] else 'Import'
        )
        sunburst_data = df_p2.groupby(['origin', 'brand_clean']).size().reset_index(name='count')
        fig = px.sunburst(sunburst_data, path=['origin', 'brand_clean'], values='count',
                          title="Brand Market Composition (Sunburst)",
                          color='count', color_continuous_scale='RdYlBu_r')
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### 🎬 Animated Brand Price Race")
        st.caption("Use the ▶️ Play button or slider to animate across model year groups")

        df_anim = df_p[df_p['brand_clean'].isin(top_brands[:12]) & df_p['year_ce'].notna()].copy()
        df_anim['year_bin'] = (df_anim['year_ce'] // 3) * 3

        brand_year = df_anim.groupby(['year_bin', 'brand_clean']).agg(
            avg_price=(price_col, 'mean'),
            count=(price_col, 'count'),
        ).reset_index()

        # Build animated bar chart with proper frame structure
        fig = px.bar(brand_year, x='avg_price', y='brand_clean',
                     color='brand_clean', orientation='h',
                     animation_frame='year_bin',
                     range_x=[0, brand_year['avg_price'].max() * 1.2],
                     title="Average Price by Brand Over Years",
                     labels={'avg_price': 'Avg Price (man-yen)', 'brand_clean': 'Brand'},
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     height=550)
        fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})

        # Slower animation speed
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 800
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 600

        st.plotly_chart(fig, use_container_width=True)


def chart_scatter(df):
    price_col = 'price_vehicle'
    df_s = df[(df[price_col] > 0) & df['mileage_wan_km'].notna() & (df['mileage_wan_km'] > 0)
              & df['brand_clean'].notna() & (df['brand_clean'] != 'Unknown')
              & df['displacement_cc'].notna()].copy()
    if len(df_s) == 0:
        st.info("No data available for scatter plot.")
        return

    brand_counts = df_s['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()

    col1, col2 = st.columns([1, 3])
    with col1:
        selected = st.multiselect("Filter brands", top_brands, default=top_brands[:6], key='scatter_brand')
        show_anim = st.checkbox("Animate by Year", value=True)
    with col2:
        df_plot = df_s[df_s['brand_clean'].isin(selected)].copy() if selected else df_s.copy()
        if len(df_plot) == 0:
            st.info("Select at least one brand.")
            return

        if show_anim and 'year_ce' in df_plot.columns:
            df_plot = df_plot[df_plot['year_ce'] >= 2010]
            fig = px.scatter(df_plot, x='mileage_wan_km', y=price_col,
                           color='brand_clean', size='displacement_cc',
                           animation_frame='year_ce',
                           hover_name='model',
                           title="Price vs Mileage (Animated by Year)",
                           labels={'mileage_wan_km': 'Mileage (10k km)', price_col: 'Price (man-yen)'},
                           height=550,
                           range_y=[0, min(df_plot[price_col].quantile(0.98), 1000)])
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 400
        else:
            fig = px.scatter(df_plot, x='mileage_wan_km', y=price_col,
                           color='brand_clean', size='displacement_cc',
                           hover_name='model',
                           title="Price vs Mileage",
                           labels={'mileage_wan_km': 'Mileage (10k km)', price_col: 'Price (man-yen)'},
                           height=550)
        st.plotly_chart(fig, use_container_width=True)


def chart_vehicle_class(df):
    price_col = 'price_vehicle'

    tab1, tab2 = st.tabs(["📊 Class Comparison", "🚗 K-car Deep Dive"])

    with tab1:
        df_p = df[(df[price_col] > 0) & df['vehicle_class'].notna()].copy()
        if len(df_p) == 0:
            st.info("No data.")
            return

        c1, c2 = st.columns(2)
        with c1:
            class_counts = df_p['vehicle_class'].value_counts()
            fig_pie = px.pie(values=class_counts.values, names=class_counts.index,
                            title="Market Share by Class", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            class_avg = df_p.groupby('vehicle_class')[price_col].mean().reindex(class_counts.index)
            fig_bar = px.bar(x=class_avg.index, y=class_avg.values,
                            title="Avg Price by Class",
                            labels={'x': 'Class', 'y': 'Avg Price (man-yen)'},
                            color_discrete_sequence=['#1a73e8'])
            fig_bar.update_xaxes(tickangle=15)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.markdown("### 🇯🇵 K-car (Kei Jidosha) — Japan's Unique Micro-Car Culture")
        st.markdown("""
        K-car is a uniquely Japanese vehicle category: engine ≤660cc, length ≤3.4m, width ≤1.48m.
        Benefits include **reduced taxes**, **lower insurance**, and **no parking certificate required**.
        """)

        df_kcar = df[(df['vehicle_class'] == 'K-car (<=660cc)') & (df[price_col] > 0)].copy()

        if len(df_kcar) > 0:
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("K-car Count", f"{len(df_kcar)}")
            with k2: st.metric("Avg Price", f"{df_kcar[price_col].mean():.1f} man-yen")
            with k3: st.metric("Lowest Price", f"{df_kcar[price_col].min():.1f} man-yen")
            with k4: st.metric("Market Share", f"{len(df_kcar)/max(len(df),1)*100:.1f}%")

            kcar_brands = df_kcar['brand_clean'].value_counts().head(6)
            fig = px.bar(x=kcar_brands.index, y=kcar_brands.values,
                        title="K-car Brand Distribution",
                        color=kcar_brands.values, color_continuous_scale='Greens',
                        labels={'x': 'Brand', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)


def chart_year_trend(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)].copy()
    if len(df_p) == 0:
        st.info("No data for year trend.")
        return

    year_stats = df_p.groupby('year_ce').agg(
        avg_price=(price_col, 'mean'),
        median_price=(price_col, 'median'),
        count=(price_col, 'count'),
        p25=(price_col, lambda x: x.quantile(0.25)),
        p75=(price_col, lambda x: x.quantile(0.75)),
    ).reset_index()

    # Dual-axis: price lines on left, count bars on right
    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    # P25-P75 band
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p75'],
        mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p25'],
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(26,115,232,0.2)', name='P25–P75',
        hovertemplate='P25: %{y:.0f}<extra></extra>'
    ))

    # Average price
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers+text', name='Average',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=10, color='#1a73e8', line=dict(color='white', width=2)),
        text=[f"{v:.0f}" for v in year_stats['avg_price']],
        textposition='top center', textfont=dict(size=9, color='#1a73e8'),
        hovertemplate='Year %{x} · Avg: %{y:.0f} · n=%{customdata}<extra></extra>',
        customdata=year_stats['count'],
    ), secondary_y=False)

    # Median
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['median_price'],
        mode='lines+markers', name='Median',
        line=dict(color='#34a853', width=2, dash='dash'),
        marker=dict(size=7, color='#34a853', line=dict(color='white', width=1.5)),
        hovertemplate='Year %{x} · Median: %{y:.0f}<extra></extra>',
    ), secondary_y=False)

    # Count bars on secondary axis
    fig.add_trace(go.Bar(
        x=year_stats['year_ce'], y=year_stats['count'],
        name='Sample Size', marker_color='rgba(251,188,4,0.5)',
        marker_line_color='#fbbc04', marker_line_width=1,
        hovertemplate='Year %{x}: %{y} cars<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        title="Price Trend by Model Year",
        hovermode="x unified", height=550,
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        bargap=0.3,
    )
    fig.update_yaxes(title_text="Price (man-yen)", secondary_y=False)
    fig.update_yaxes(title_text="Sample Size", secondary_y=True, showgrid=False, rangemode='tozero')
    fig.update_xaxes(title_text="Model Year", dtick=2)

    st.plotly_chart(fig, use_container_width=True)


def chart_prefecture(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['prefecture'].notna()].copy()
    if len(df_p) == 0:
        st.info("No data for region analysis.")
        return

    pref_stats = df_p.groupby('prefecture').agg(
        avg_price=(price_col, 'mean'),
        count=(price_col, 'count'),
    ).reset_index().sort_values('avg_price', ascending=False)

    fig = px.bar(pref_stats, y='prefecture', x='avg_price',
                orientation='h',
                title="Average Price by Prefecture",
                color='count', color_continuous_scale='Viridis',
                labels={'prefecture': '', 'avg_price': 'Avg Price (man-yen)', 'count': 'Listings'},
                height=max(500, len(pref_stats) * 22))
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig.update_yaxes(tickfont=dict(size=11))
    st.plotly_chart(fig, use_container_width=True)


def chart_forecast_demo(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)].copy()
    if len(df_p) == 0:
        st.info("No data for forecast.")
        return

    st.markdown("> 💡 **Prediction Module**: Cross-sectional trend by model year. With multi-day crawl data, Prophet time-series will auto-enable.")

    year_stats = df_p.groupby('year_ce').agg(
        avg_price=(price_col, 'mean'),
        count=(price_col, 'count'),
    ).reset_index()

    if len(year_stats) < 3:
        st.info("Not enough data for trend analysis.")
        return

    # Fit 2nd degree polynomial
    z = np.polyfit(year_stats['year_ce'], year_stats['avg_price'], 2)
    p = np.poly1d(z)

    future_years = np.arange(year_stats['year_ce'].min(), year_stats['year_ce'].max() + 4)
    predicted = p(future_years)

    last_year = year_stats['year_ce'].max()
    future_mask = future_years > last_year

    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers+text', name='Historical Avg',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=10, color='#1a73e8', line=dict(color='white', width=2)),
        text=[f"{v:.0f}" for v in year_stats['avg_price']],
        textposition='top center', textfont=dict(size=9, color='#1a73e8'),
        hovertemplate='Year %{x} · Avg: %{y:.0f} · n=%{customdata}<extra></extra>',
        customdata=year_stats['count'],
    ))

    # Trend line
    fig.add_trace(go.Scatter(
        x=future_years, y=predicted,
        mode='lines', name='Trend Fit',
        line=dict(color='#ea4335', width=2, dash='dash')
    ))

    # Forecast
    if future_mask.any():
        fy = future_years[future_mask]
        fp = predicted[future_mask]

        fig.add_trace(go.Scatter(
            x=fy, y=fp,
            mode='lines+markers+text', name='Forecast',
            line=dict(color='#ea4335', width=3),
            marker=dict(size=12, color='#ea4335', symbol='diamond',
                        line=dict(color='white', width=2)),
            text=[f"{v:.0f}" for v in fp],
            textposition='top center', textfont=dict(size=10, color='#ea4335'),
            hovertemplate='Forecast %{x} · %{y:.0f} man-yen<extra></extra>',
        ))

        # Confidence band
        fig.add_trace(go.Scatter(
            x=fy, y=fp * 1.15, mode='lines', line=dict(width=0), showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=fy, y=fp * 0.85, mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(234,67,53,0.2)', name='80% Confidence',
        ))

    fig.add_vline(x=last_year + 0.5, line_dash="dot", line_color="#9e9e9e", line_width=2,
                  annotation_text="Forecast →", annotation_position="top left",
                  annotation_font=dict(size=13, color='#ea4335'))

    fig.update_layout(
        title="Price Trend & 3-Year Forecast",
        xaxis_title="Model Year", yaxis_title="Avg Price (man-yen)",
        hovermode="x unified", height=550,
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        xaxis=dict(dtick=2),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Brand trends
    st.markdown("#### 🏭 Top 5 Brand Price Trends")
    brand_counts = df_p['brand_clean'].value_counts()
    top5 = brand_counts.head(5).index.tolist()

    df_top = df_p[df_p['brand_clean'].isin(top5)]
    brand_year = df_top.groupby(['year_ce', 'brand_clean']).agg(
        avg_price=(price_col, 'mean'),
    ).reset_index()

    fig2 = px.line(brand_year, x='year_ce', y='avg_price', color='brand_clean',
                   title="Top 5 Brand Price Trends",
                   labels={'year_ce': 'Model Year', 'avg_price': 'Avg Price (man-yen)', 'brand_clean': 'Brand'},
                   markers=True, height=450)
    fig2.update_layout(
        hovermode="x unified",
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        xaxis=dict(dtick=2),
    )
    for trace in fig2.data:
        trace.line.width = 3
        trace.marker.size = 8
        trace.marker.line = dict(color='white', width=1.5)
    st.plotly_chart(fig2, use_container_width=True)


# ===========================================================================
# 宏观市场数据图表
# ===========================================================================

BRAND_NAME_MAP = {
    'トヨタ': 'Toyota', 'ホンダ': 'Honda', '日産': 'Nissan',
    'スズキ': 'Suzuki', 'ダイハツ': 'Daihatsu', 'マツダ': 'Mazda',
    '三菱': 'Mitsubishi', 'ＳＵＢＡＲＵ': 'Subaru', 'スバル': 'Subaru',
    'レクサス': 'Lexus', 'いすゞ': 'Isuzu', '日野': 'Hino',
    '三菱ふそう': 'Fuso', 'UDトラックス': 'UD Trucks',
    'Mercedes-Benz': 'Mercedes', 'BMW': 'BMW', 'VW': 'VW',
    'Audi': 'Audi', 'BMW MINI': 'MINI', 'Volvo': 'Volvo',
    'Porsche': 'Porsche', 'Jeep': 'Jeep', 'Peugeot': 'Peugeot',
    'Land Rover': 'Land Rover', 'BYD': 'BYD', 'Fiat': 'Fiat',
    'Citroen': 'Citroen', 'Renault': 'Renault', 'Alfa Romeo': 'Alfa Romeo',
    'Ferrari': 'Ferrari', 'Hyundai': 'Hyundai', 'Lamborghini': 'Lamborghini',
    'Maserati': 'Maserati', 'Bentley': 'Bentley', 'Cadillac': 'Cadillac',
    'Aston Martin': 'Aston Martin', 'DS': 'DS', 'Ford': 'Ford',
    'ABARTH': 'Abarth', 'Dodge': 'Dodge', 'Lotus': 'Lotus',
    'ＭcＬaren': 'McLaren', 'Rolls Royce': 'Rolls Royce', 'Roｌｌs Royce': 'Rolls Royce',
    'Chevrolet': 'Chevrolet', 'Scania': 'Scania', 'BMW Alpina': 'Alpina',
}

JAPANESE_BRANDS = {'Toyota', 'Honda', 'Nissan', 'Suzuki', 'Daihatsu', 'Mazda',
                   'Mitsubishi', 'Subaru', 'Lexus', 'Isuzu', 'Hino', 'Fuso',
                   'UD Trucks'}


def chart_macro_monthly(summary):
    """日本新车月度销量趋势."""
    if summary.empty:
        st.info("No macro data available. Run `macro_data_crawler.py` first.")
        return

    df = summary.copy()
    df['period'] = df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)

    # KPI cards
    latest = df.sort_values(['year', 'month']).iloc[-1]
    prev_month = df[df['year'] * 100 + df['month'] < latest['year'] * 100 + latest['month']].sort_values(['year', 'month'])
    prev_month = prev_month.iloc[-1] if len(prev_month) > 0 else None

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        v = f"{latest['total_sales']:,.0f}" if pd.notna(latest['total_sales']) else 'N/A'
        st.metric(f"📍 {int(latest['year'])}/{int(latest['month'])}月 总销量", v)
    with k2:
        v = f"{latest['registered_car_sales']:,.0f}" if pd.notna(latest['registered_car_sales']) else 'N/A'
        st.metric("注册车 (非K-car)", v)
    with k3:
        v = f"{latest['kei_car_sales']:,.0f}" if pd.notna(latest['kei_car_sales']) else 'N/A'
        st.metric("軽自動車 (K-car)", v)
    with k4:
        kei_pct = latest['kei_car_sales'] / latest['total_sales'] * 100 if pd.notna(latest['total_sales']) and latest['total_sales'] > 0 and pd.notna(latest['kei_car_sales']) else 0
        st.metric("K-car 占比", f"{kei_pct:.1f}%")

    st.markdown("---")

    # --- 年份筛选 ---
    all_years = sorted(df['year'].unique())
    selected_years = st.multiselect("选择年份", all_years, default=all_years[-3:], key='macro_year')
    df_sel = df[df['year'].isin(selected_years)] if selected_years else df

    if df_sel.empty:
        st.info("No data for selected years.")
        return

    # 标记数据完整性：注册车=0 说明只有K-car数据
    df_sel = df_sel.copy()
    df_sel['has_reg'] = df_sel['registered_car_sales'].fillna(0) > 0
    df_complete = df_sel[df_sel['has_reg']]
    df_kcar_only = df_sel[~df_sel['has_reg']]

    if len(df_kcar_only) > 0 and len(df_complete) > 0:
        st.caption("⚠️ 2020-2021 年仅有 K-car 数据（无注册车），图表从 2022 年起展示完整数据")
        df_plot = df_complete
    else:
        df_plot = df_sel

    # --- 堆叠面积图: 注册车 + K-car ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot['period'], y=df_plot['registered_car_sales'],
        mode='lines+markers', name='Registered Cars',
        line=dict(color='#1a73e8', width=2.5),
        marker=dict(size=6),
        stackgroup='one',
        hovertemplate='%{x}<br>Registered: %{y:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df_plot['period'], y=df_plot['kei_car_sales'],
        mode='lines+markers', name='K-car (軽自動車)',
        line=dict(color='#ea4335', width=2.5),
        marker=dict(size=6),
        stackgroup='one',
        hovertemplate='%{x}<br>K-car: %{y:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df_plot['period'], y=df_plot['total_sales'],
        mode='lines+markers', name='Total',
        line=dict(color='#34a853', width=3, dash='dot'),
        marker=dict(size=7, symbol='diamond'),
        hovertemplate='%{x}<br>Total: %{y:,.0f}<extra></extra>',
    ))
    fig.update_layout(
        title="🇯🇵 Monthly New Car Sales — Registered + K-car",
        xaxis_title="Month", yaxis_title="Units Sold",
        hovermode="x unified", height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    # --- 如果有不完整数据，单独显示K-car趋势 ---
    if len(df_kcar_only) > 0:
        fig_kcar = go.Figure()
        fig_kcar.add_trace(go.Scatter(
            x=df_kcar_only['period'], y=df_kcar_only['kei_car_sales'],
            mode='lines+markers', name='K-car Only',
            line=dict(color='#ea4335', width=2),
            marker=dict(size=5),
            hovertemplate='%{x}<br>K-car: %{y:,.0f}<extra></extra>',
        ))
        fig_kcar.update_layout(
            title="K-car Sales (2020-2021, registered car data unavailable)",
            xaxis_title="Month", yaxis_title="Units Sold",
            hovermode="x unified", height=300,
        )
        fig_kcar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_kcar, use_container_width=True)

    # --- 同比增长率 ---
    df_yoy = df_sel[df_sel['kei_yoy_pct'].notna()].copy()
    if len(df_yoy) > 0:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_yoy['period'], y=df_yoy['kei_yoy_pct'],
            name='K-car YoY %',
            marker_color=df_yoy['kei_yoy_pct'].apply(lambda x: '#34a853' if x >= 0 else '#ea4335'),
            hovertemplate='%{x}<br>YoY: %{y:.1f}%<extra></extra>',
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
        fig2.update_layout(
            title="K-car Year-over-Year Growth (%)",
            xaxis_title="Month", yaxis_title="YoY %",
            hovermode="x unified", height=350,
        )
        fig2.update_xaxes(tickangle=45)
        st.plotly_chart(fig2, use_container_width=True)


def chart_macro_brand(brand_df):
    """品牌别新车销量排名."""
    if brand_df.empty:
        st.info("No brand data available.")
        return

    df = brand_df.copy()
    # 英译品牌名
    df['brand_en'] = df['brand'].map(BRAND_NAME_MAP).fillna(df['brand'])
    df['is_jp'] = df['brand_en'].isin(JAPANESE_BRANDS)

    # 选年月
    all_ym = sorted(df.apply(lambda r: f"{int(r['year'])}/{int(r['month']):02d}", axis=1).unique())
    selected_ym = st.selectbox("选择月份", all_ym, index=len(all_ym) - 1, key='macro_brand_ym')
    ym_parts = selected_ym.split('/')
    sel_y, sel_m = int(ym_parts[0]), int(ym_parts[1])
    df_m = df[(df['year'] == sel_y) & (df['month'] == sel_m)]

    # 品牌总销量 (登録車 + 軽)
    brand_total = df_m.groupby(['brand_en', 'is_jp'])['sales_count'].sum().reset_index()
    brand_total = brand_total.sort_values('sales_count', ascending=False)
    top15 = brand_total.head(15)

    # KPI
    total_all = brand_total['sales_count'].sum()
    jp_total = brand_total[brand_total['is_jp']]['sales_count'].sum()
    import_total = brand_total[~brand_total['is_jp']]['sales_count'].sum()
    k1, k2, k3 = st.columns(3)
    with k1: st.metric("🇯🇵 日本品牌", f"{jp_total:,.0f}", f"{jp_total/total_all*100:.1f}%")
    with k2: st.metric("🌍 进口品牌", f"{import_total:,.0f}", f"{import_total/total_all*100:.1f}%")
    with k3: st.metric("📊 品牌数", f"{len(brand_total)}")

    st.markdown("---")

    # 横向条形图
    fig = px.bar(top15, x='sales_count', y='brand_en', orientation='h',
                 color='is_jp', color_discrete_map={True: '#1a73e8', False: '#ea4335'},
                 title=f"{sel_y}/{sel_m:02d} Top 15 Brands by Sales",
                 labels={'sales_count': 'Units Sold', 'brand_en': 'Brand', 'is_jp': 'Japanese'},
                 height=500)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=True)
    # 添加数值标签
    for trace in fig.data:
        trace.textposition = 'outside'
    st.plotly_chart(fig, use_container_width=True)

    # 注册车 vs K-car 分拆
    df_split = df_m.groupby('brand_en').agg(
        reg=('sales_count', lambda x: x[df_m.loc[x.index, 'vehicle_type'].str.contains('登録車')].sum()),
        kei=('sales_count', lambda x: x[df_m.loc[x.index, 'vehicle_type'].str.contains('軽')].sum()),
    ).reset_index().sort_values('reg', ascending=False).head(10)

    if not df_split.empty and df_split['kei'].sum() > 0:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=df_split['brand_en'], x=df_split['reg'], orientation='h',
            name='Registered', marker_color='#1a73e8',
            hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
        ))
        fig2.add_trace(go.Bar(
            y=df_split['brand_en'], x=df_split['kei'], orientation='h',
            name='K-car', marker_color='#ea4335',
            hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
        ))
        fig2.update_layout(
            barmode='stack',
            title=f"{sel_y}/{sel_m:02d} Top 10 — Registered vs K-car",
            xaxis_title='Units Sold', yaxis_title='',
            height=450,
            yaxis={'categoryorder': 'total ascending'},
            legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='right', x=1),
        )
        st.plotly_chart(fig2, use_container_width=True)


def chart_macro_kcar(kcar_brand_df, kcar_monthly_df):
    """K-car 品牌别份额 + 月度趋势."""
    if kcar_brand_df.empty and kcar_monthly_df.empty:
        st.info("No K-car data available.")
        return

    tab_a, tab_b = st.tabs(["🥧 Brand Share", "📈 Monthly Trend"])

    with tab_a:
        if kcar_brand_df.empty:
            st.info("No K-car brand data.")
        else:
            df = kcar_brand_df.copy()
            # 英译
            df['brand_en'] = df['brand'].map(BRAND_NAME_MAP).fillna(df['brand'])
            all_ym = sorted(df.apply(lambda r: f"{int(r['year'])}/{int(r['month']):02d}", axis=1).unique())
            selected_ym = st.selectbox("选择月份", all_ym, index=len(all_ym) - 1, key='kcar_brand_ym')
            ym_parts = selected_ym.split('/')
            sel_y, sel_m = int(ym_parts[0]), int(ym_parts[1])
            df_m = df[(df['year'] == sel_y) & (df['month'] == sel_m)]

            if df_m.empty:
                st.info("No data for selected month.")
            else:
                fig = px.pie(df_m, values='total_count', names='brand_en',
                             title=f"K-car Brand Share — {sel_y}/{sel_m:02d}",
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

                # 同比表
                df_show = df_m[['brand_en', 'total_count', 'market_share_pct', 'yoy_pct']].copy()
                df_show.columns = ['Brand', 'Sales', 'Share %', 'YoY %']
                df_show = df_show.sort_values('Sales', ascending=False)
                st.dataframe(df_show, use_container_width=True, hide_index=True)

    with tab_b:
        if kcar_monthly_df.empty:
            st.info("No K-car monthly data.")
        else:
            df = kcar_monthly_df.copy()
            df['period'] = df['year'].astype(str) + '/' + df['month'].astype(str).str.zfill(2)

            # 乘客 vs 货物
            fig = go.Figure()
            if 'passenger_group_total' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['period'], y=df['passenger_group_total'],
                    mode='lines+markers', name='Passenger',
                    line=dict(color='#1a73e8', width=2.5),
                    hovertemplate='%{x}<br>Passenger: %{y:,.0f}<extra></extra>',
                ))
            if 'cargo_group_total' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['period'], y=df['cargo_group_total'],
                    mode='lines+markers', name='Cargo',
                    line=dict(color='#ea4335', width=2.5),
                    hovertemplate='%{x}<br>Cargo: %{y:,.0f}<extra></extra>',
                ))
            fig.add_trace(go.Scatter(
                x=df['period'], y=df['total'],
                mode='lines+markers', name='Total',
                line=dict(color='#34a853', width=3, dash='dot'),
                marker=dict(symbol='diamond', size=7),
                hovertemplate='%{x}<br>Total: %{y:,.0f}<extra></extra>',
            ))
            fig.update_layout(
                title="K-car Monthly Sales — Passenger vs Cargo",
                xaxis_title="Month", yaxis_title="Units Sold",
                hovermode="x unified", height=450,
                legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)


def main():
    st.markdown("""
    <div style="text-align:center; padding: 12px 0;">
        <h1 style="font-size:2.2em; margin:0;">🇯🇵 Japan Used Car Market Analytics
        <span class="live-badge">LIVE</span></h1>
        <p style="color:#5f6368; font-size:1.05em; margin:6px 0 0;">
            Dynamic monitoring of car prices · Brand distribution · Market trends · Source: <a href="https://www.carsensor.net/usedcar/">carsensor.net</a>
        </p>
    </div>
    <div class="gradient-divider"></div>
    """, unsafe_allow_html=True)

    # Load raw data ONCE
    df_raw = load_data()
    has_used_car_data = len(df_raw) > 0

    if not has_used_car_data:
        st.warning("⚠️ 二手车数据库为空，部分功能不可用。请运行 `python src/crawler.py` 采集数据，或点击下方按钮刷新。")
        # 仍然展示宏观数据
        summary, brand_df, kcar_brand_df, kcar_monthly_df = load_macro_data()
        if not summary.empty or not brand_df.empty:
            st.markdown('<div class="section-title">🇯🇵 Japan Macro Market — New Car Sales</div>', unsafe_allow_html=True)
            st.caption("Data: JADA (品牌別登録車) + 全軽自協 (K-car) · Updated monthly")
            macro_tab1, macro_tab2, macro_tab3 = st.tabs([
                "📈 Monthly Total", "🏭 Brand Ranking", "🚗 K-car"
            ])
            with macro_tab1:
                chart_macro_monthly(summary)
            with macro_tab2:
                chart_macro_brand(brand_df)
            with macro_tab3:
                chart_macro_kcar(kcar_brand_df, kcar_monthly_df)
        return

    # ====== Sidebar Filters (use df_raw for range, filter into df) ======
    with st.sidebar:
        st.markdown("## 🔍 Filters")
        price_col = 'price_vehicle'

        # Show last refresh time + manual refresh
        ts_file = os.path.join(PROJECT_ROOT, 'data', '.last_refresh')
        if os.path.exists(ts_file):
            with open(ts_file, 'r', encoding='utf-8') as f:
                last_refresh = f.read().strip()
            st.caption(f"🕐 Last data refresh: {last_refresh}")
        else:
            st.caption("🕐 Data not refreshed yet")

        if st.button("🔄 Refresh Data Now", use_container_width=True, type="primary"):
            with st.spinner("Crawling latest listings & reprocessing..."):
                import subprocess
                result = subprocess.run(
                    [sys.executable, os.path.join(PROJECT_ROOT, 'src', 'refresh_data.py')],
                    capture_output=True, text=True, encoding='utf-8',
                    cwd=PROJECT_ROOT
                )
            st.cache_data.clear()
            st.success("Data refreshed! Reloading...")
            st.rerun()

        # Price range — use FULL data range
        if price_col in df_raw.columns:
            p_min = float(df_raw[price_col].min())
            p_max = float(df_raw[price_col].max())
            price_lo, price_hi = st.slider(
                "Price Range (man-yen)", p_min, p_max, (p_min, p_max), step=10.0, key='price_slider')

        # Year range — use FULL data range
        year_lo, year_hi = None, None
        if 'year_ce' in df_raw.columns:
            yr_min = int(df_raw['year_ce'].min())
            yr_max = int(df_raw['year_ce'].max())
            year_lo, year_hi = st.slider(
                "Model Year Range", yr_min, yr_max, (yr_min, yr_max), key='year_slider')

        # Brand origin
        sel_origins = None
        if 'brand_origin' in df_raw.columns:
            all_origins = sorted(df_raw['brand_origin'].dropna().unique().tolist())
            sel_origins = st.multiselect("Brand Origin", all_origins, default=all_origins, key='origin_select')

        # Vehicle class
        sel_classes = None
        if 'vehicle_class' in df_raw.columns:
            all_classes = sorted(df_raw['vehicle_class'].dropna().unique().tolist())
            sel_classes = st.multiselect("Vehicle Class", all_classes, default=all_classes, key='class_select')

        # Apply ALL filters to df_raw → df
        df = df_raw.copy()
        if price_col in df.columns:
            df = df[(df[price_col] >= price_lo) & (df[price_col] <= price_hi)]
        if year_lo is not None and 'year_ce' in df.columns:
            df = df[(df['year_ce'] >= year_lo) & (df['year_ce'] <= year_hi)]
        if sel_origins is not None and 'brand_origin' in df.columns:
            df = df[df['brand_origin'].isin(sel_origins)]
        if sel_classes is not None and 'vehicle_class' in df.columns:
            df = df[df['vehicle_class'].isin(sel_classes)]

        st.markdown("---")
        st.caption(f"Showing {len(df):,} / {len(df_raw):,} vehicles")

        if st.button("🔄 Reset Filters", use_container_width=True):
            st.rerun()

    # ====== KPI ======
    render_kpi_cards(df)
    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # ====== Tabs ======
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💰 Price", "🏭 Brands", "📊 Scatter",
        "🚙 Vehicle Class", "📈 Year Trend", "🔮 Forecast",
        "🗺️ Region", "🇯🇵 Macro Market"
    ])

    with tab1:
        st.markdown('<div class="section-title">Price Distribution & Range Statistics</div>', unsafe_allow_html=True)
        chart_price_distribution(df)

    with tab2:
        st.markdown('<div class="section-title">Brand Price Range & Market Share</div>', unsafe_allow_html=True)
        chart_brand_analysis(df)

    with tab3:
        st.markdown('<div class="section-title">Price vs Mileage Scatter</div>', unsafe_allow_html=True)
        chart_scatter(df)

    with tab4:
        st.markdown('<div class="section-title">Vehicle Class Analysis — K-car Spotlight</div>', unsafe_allow_html=True)
        chart_vehicle_class(df)

    with tab5:
        st.markdown('<div class="section-title">Price Trend by Model Year</div>', unsafe_allow_html=True)
        chart_year_trend(df)

    with tab6:
        st.markdown('<div class="section-title">Price Forecast</div>', unsafe_allow_html=True)
        chart_forecast_demo(df)

    with tab7:
        st.markdown('<div class="section-title">Regional Price Analysis</div>', unsafe_allow_html=True)
        chart_prefecture(df)

    with tab8:
        st.markdown('<div class="section-title">🇯🇵 Japan Macro Market — New Car Sales</div>', unsafe_allow_html=True)
        st.caption("Data: JADA (品牌別登録車) + 全軽自協 (K-car) · Updated monthly")
        summary, brand_df, kcar_brand_df, kcar_monthly_df = load_macro_data()

        macro_tab1, macro_tab2, macro_tab3 = st.tabs([
            "📈 Monthly Total", "🏭 Brand Ranking", "🚗 K-car"
        ])
        with macro_tab1:
            chart_macro_monthly(summary)
        with macro_tab2:
            chart_macro_brand(brand_df)
        with macro_tab3:
            chart_macro_kcar(kcar_brand_df, kcar_monthly_df)

    st.markdown("""
    <div class="gradient-divider"></div>
    <div style="text-align:center; color:#5f6368; font-size:0.85em; padding:12px 0;">
        🇯🇵 Japan Used Car Market Analytics · Source: carsensor.net + JADA + 全軽自協 · Stack: Playwright + Pandas + SQLite + Prophet + Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

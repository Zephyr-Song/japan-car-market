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
    """Load macro data: monthly total sales + brand sales."""
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
# Macro market charts
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

# ====== Japanese to English Translation Maps (for export & ranking data) ======
SHAPE_MAP = {'普通車': 'Standard Car', 'ハイブリッド': 'Hybrid', '電気自動車': 'EV', '軽自動車': 'Kei Car', 'トラック': 'Truck', 'バス': 'Bus'}
COUNTRY_MAP = {'アイルランド': 'Ireland', 'アメリカ': 'USA', 'アラブ首長国連邦': 'UAE', 'アルメニア': 'Armenia', 'アンギラ': 'Anguilla', 'アンティグア・バーブーダ': 'Antigua & Barbuda', 'イギリス': 'UK', 'インドネシア': 'Indonesia', 'ウガンダ': 'Uganda', 'エストニア': 'Estonia', 'オランダ': 'Netherlands', 'オランダ領アンティル': 'Netherlands Antilles', 'オーストラリア': 'Australia', 'カザフスタン': 'Kazakhstan', 'カナダ': 'Canada', 'カメルーン': 'Cameroon', 'カンボジア': 'Cambodia', 'ガイアナ': 'Guyana', 'ガーナ': 'Ghana', 'キプロス': 'Cyprus', 'キリバティ': 'Kiribati', 'キルギス': 'Kyrgyzstan', 'ギニア': 'Guinea', 'クック諸島': 'Cook Islands', 'グアテマラ': 'Guatemala', 'グアム': 'Guam', 'グルジア': 'Georgia', 'グレナダ': 'Grenada', 'ケイマン諸島': 'Cayman Islands', 'ケニア': 'Kenya', 'コンゴ民主共和国': 'DR Congo', 'サモア': 'Samoa', 'ザンビア': 'Zambia', 'シンガポール': 'Singapore', 'ジャマイカ': 'Jamaica', 'ジンバブエ': 'Zimbabwe', 'スリナム': 'Suriname', 'スリランカ': 'Sri Lanka', 'スワジランド': 'Eswatini', 'セントキッツ・ネービス': 'St. Kitts & Nevis', 'セントビンセント・グレナディーン諸島': 'St. Vincent & Grenadines', 'セントルシア': 'St. Lucia', 'ソマリア': 'Somalia', 'ソロモン諸島': 'Solomon Islands', 'タイ': 'Thailand', 'タンザニア': 'Tanzania', 'タークス・カイコス諸島': 'Turks & Caicos', 'チェコ': 'Czechia', 'チリ': 'Chile', 'トリニダード・トバゴ': 'Trinidad & Tobago', 'トルコ': 'Turkey', 'トンガ': 'Tonga', 'ドイツ': 'Germany', 'ドミニカ': 'Dominica', 'ドミニカ共和国': 'Dominican Republic', 'ナイジェリア': 'Nigeria', 'ナミビア': 'Namibia', 'ニュージーランド': 'New Zealand', 'ノーフォーク島': 'Norfolk Island', 'バハマ': 'Bahamas', 'バミューダ諸島': 'Bermuda', 'バルバドス': 'Barbados', 'バングラデシュ': 'Bangladesh', 'バーレーン': 'Bahrain', 'パキスタン': 'Pakistan', 'パプアニューギニア': 'Papua New Guinea', 'パラオ': 'Palau', 'パラグアイ': 'Paraguay', 'フィジー': 'Fiji', 'フィリピン': 'Philippines', 'フィンランド': 'Finland', 'フランス': 'France', 'ブルキナファソ': 'Burkina Faso', 'ブルンジ': 'Burundi', 'プエルトリコ': 'Puerto Rico', 'ボツワナ': 'Botswana', 'ボリビア': 'Bolivia', 'ポーランド': 'Poland', 'マカオ': 'Macau', 'マラウイ': 'Malawi', 'マルタ': 'Malta', 'マレーシア': 'Malaysia', 'ミクロネシア': 'Micronesia', 'ミャンマー': 'Myanmar', 'モザンビーク': 'Mozambique', 'モルディブ共和国': 'Maldives', 'モンゴル': 'Mongolia', 'モントセラト': 'Montserrat', 'モーリシャス': 'Mauritius', 'ラオス': 'Laos', 'ラトビア': 'Latvia', 'レソト': 'Lesotho', 'ロシア': 'Russia', '中国': 'China', '南アフリカ': 'South Africa', '南スーダン': 'South Sudan', '東ティモール': 'East Timor', '英領ヴァージン諸島': 'BVI', '韓国': 'South Korea', '香港': 'Hong Kong', 'イラク': 'Iraq', 'エジプト': 'Egypt', 'ギリシャ': 'Greece', 'セーシェル共和国': 'Seychelles', 'ツバル': 'Tuvalu', 'ハイチ': 'Haiti', 'パナマ': 'Panama', 'ベトナム': 'Vietnam', 'マダガスカル': 'Madagascar', 'レバノン': 'Lebanon', '北マリアナ諸島': 'N. Mariana Islands', '台湾': 'Taiwan', 'インド': 'India', 'ウクライナ': 'Ukraine', 'コンゴ共和国': 'Congo', 'ナウル': 'Nauru', 'ニウエ': 'Niue', 'ベナン': 'Benin', 'ベルギー': 'Belgium', 'ルワンダ': 'Rwanda', '米領ヴァージン諸島': 'USVI', 'アゼルバイジャン': 'Azerbaijan', 'イタリア': 'Italy', 'オマーン': 'Oman', 'オーストリア': 'Austria', 'サウジアラビア': 'Saudi Arabia', 'リトアニア': 'Lithuania', 'アルゼンチン': 'Argentina', 'ブラジル': 'Brazil', 'ブータン': 'Bhutan', 'タジキスタン': 'Tajikistan', 'ノルウェー': 'Norway', 'ペルー': 'Peru', 'セネガル': 'Senegal', 'マリ': 'Mali', 'モーリタニア': 'Mauritania', 'ルクセンブルク': 'Luxembourg', 'カナリア諸島': 'Canary Islands', 'デンマーク': 'Denmark', 'メキシコ': 'Mexico', 'スペイン': 'Spain', 'リベリア': 'Liberia', 'ガボン': 'Gabon', 'シリア': 'Syria', 'ブルネイ': 'Brunei', 'ボスニア・ヘルツェゴビナ': 'Bosnia & Herzegovina', 'ポルトガル': 'Portugal', 'アフガニスタン': 'Afghanistan', 'ウズベキスタン': 'Uzbekistan', 'エチオピア': 'Ethiopia', 'トーゴ': 'Togo', 'キリバス': 'Kiribati'}
BODY_TYPE_MAP = {'軽自動車': 'Kei Car', 'ミニバン/ワンボックス': 'Minivan/Onebox', 'コンパクト/ハッチバック': 'Compact/Hatchback', '軽バン/軽ワゴン': 'Kei Van/Wagon', 'セダン/ハードトップ': 'Sedan/Hardtop', 'SUV/クロカン': 'SUV/Crossover', 'クーペ': 'Coupe', 'ステーションワゴン': 'Station Wagon'}
MODEL_MAP = {'プリウス': 'Prius', 'セレナ': 'Serena', 'N-BOXカスタム': 'N-BOX Custom', 'ステップワゴン': 'Step Wagon', 'N-BOX': 'N-BOX', 'タント': 'Tanto', 'タントカスタム': 'Tanto Custom', 'アクア': 'Aqua', 'ワゴンR': 'WagonR', 'ハイゼットカーゴ': 'HiJet Cargo', 'ミニ': 'Mini', 'ミニクラブマン': 'Mini Clubman', '500': 'Fiat 500', 'ゴルフ': 'Golf', 'Gクラス': 'G-Class', 'X1': 'X1', 'XC60': 'XC60', '5シリーズセダン': '5 Series Sedan', 'TTクーペ': 'TT Coupe', 'ミニクロスオーバー': 'Mini Countryman', 'エブリイ': 'Every', 'ハイエースバン': 'HiAce Van', 'ハスラー': 'Hustler', 'カングー': 'Kangoo', 'アバルト595': 'Abarth 595', 'マカン': 'Macan', '911': '911', 'ラングラー': 'Wrangler', 'ジムニー': 'Jimny', '3シリーズツーリング': '3 Series Touring', 'アルトラパン': 'Alto Lapin', 'ヴォクシー': 'Voxy', '1シリーズ': '1 Series', 'V40': 'V40', 'ザ・ビートル': 'Beetle', 'ハイゼットトラック': 'HiJet Truck', 'カイエン': 'Cayenne', 'ケイマン': 'Cayman', 'デイズルークス': 'Dayz Roox', 'モデル3': 'Model 3', '3シリーズセダン': '3 Series Sedan', 'Eクラス': 'E-Class', 'Cクラスワゴン': 'C-Class Wagon'}
BRAND_MAP_JP = {'トヨタ': 'Toyota', '日産': 'Nissan', 'ホンダ': 'Honda', 'ダイハツ': 'Daihatsu', 'スズキ': 'Suzuki', 'BMW MINI': 'BMW Mini', 'フィアット': 'Fiat', 'フォルクスワーゲン': 'Volkswagen', 'メルセデス・ベンツ': 'Mercedes-Benz', 'BMW': 'BMW', 'ボルボ': 'Volvo', 'アウディ': 'Audi', 'ルノー': 'Renault', 'アバルト': 'Abarth', 'ポルシェ': 'Porsche', 'クライスラージープ': 'Jeep', 'テスラ': 'Tesla'}

def translate_shape(name):
    return SHAPE_MAP.get(name, name)

def translate_country(name):
    return COUNTRY_MAP.get(name, name)

def translate_body_type(name):
    return BODY_TYPE_MAP.get(name, name)

def translate_model_name(name):
    import re as _re
    m = _re.match(r'^(.+?)\uff08(.+?)\uff09$', name)
    if m:
        model_jp, brand_jp = m.group(1), m.group(2)
        model_en = MODEL_MAP.get(model_jp, model_jp)
        brand_en = BRAND_MAP_JP.get(brand_jp, brand_jp)
        return f"{model_en} ({brand_en})"
    if name in MODEL_MAP:
        return MODEL_MAP[name]
    if name in BODY_TYPE_MAP:
        return BODY_TYPE_MAP[name]
    return name


JAPANESE_BRANDS = {'Toyota', 'Honda', 'Nissan', 'Suzuki', 'Daihatsu', 'Mazda',
                   'Mitsubishi', 'Subaru', 'Lexus', 'Isuzu', 'Hino', 'Fuso',
                   'UD Trucks'}


def chart_macro_monthly(summary):
    """Japan new car monthly sales trend."""
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
        st.metric("Registered (non-K-car)", v)
    with k3:
        v = f"{latest['kei_car_sales']:,.0f}" if pd.notna(latest['kei_car_sales']) else 'N/A'
        st.metric("Kei Car (K-car)", v)
    with k4:
        kei_pct = latest['kei_car_sales'] / latest['total_sales'] * 100 if pd.notna(latest['total_sales']) and latest['total_sales'] > 0 and pd.notna(latest['kei_car_sales']) else 0
        st.metric("K-car Share", f"{kei_pct:.1f}%")

    st.markdown("---")

    # --- 年份筛选 ---
    # 先标记数据完整性
    df_tagged = df.copy()
    df_tagged['has_reg'] = df_tagged['registered_car_sales'].fillna(0) > 0
    complete_years = sorted(df_tagged[df_tagged['has_reg']]['year'].unique())
    all_years = sorted(df_tagged['year'].unique())
    available_years = complete_years if complete_years else all_years
    selected_years = st.multiselect("Select Year", available_years, default=available_years[-3:], key='macro_year')
    df_sel = df_tagged[df_tagged['year'].isin(selected_years)] if selected_years else df_tagged

    if df_sel.empty:
        st.info("No data for selected years.")
        return

    # 只展示有完整数据的月份（注册车>0）
    df_complete = df_sel[df_sel['has_reg']]
    df_plot = df_complete if len(df_complete) > 0 else df_sel

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
        mode='lines+markers', name='K-car (Kei Car)',
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
    """New car sales ranking by brand."""
    if brand_df.empty:
        st.info("No brand data available.")
        return

    df = brand_df.copy()
    # Brand name translation
    df['brand_en'] = df['brand'].map(BRAND_NAME_MAP).fillna(df['brand'])
    df['is_jp'] = df['brand_en'].isin(JAPANESE_BRANDS)

    # Select year/month
    all_ym = sorted(df.apply(lambda r: f"{int(r['year'])}/{int(r['month']):02d}", axis=1).unique())
    selected_ym = st.selectbox("Select Month", all_ym, index=len(all_ym) - 1, key='macro_brand_ym')
    ym_parts = selected_ym.split('/')
    sel_y, sel_m = int(ym_parts[0]), int(ym_parts[1])
    df_m = df[(df['year'] == sel_y) & (df['month'] == sel_m)]

    # Brand total (Registered + Kei)
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

    # Horizontal bar chart
    fig = px.bar(top15, x='sales_count', y='brand_en', orientation='h',
                 color='is_jp', color_discrete_map={True: '#1a73e8', False: '#ea4335'},
                 title=f"{sel_y}/{sel_m:02d} Top 15 Brands by Sales",
                 labels={'sales_count': 'Units Sold', 'brand_en': 'Brand', 'is_jp': 'Japanese'},
                 height=500)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=True)
    # Add value labels
    for trace in fig.data:
        trace.textposition = 'outside'
    st.plotly_chart(fig, use_container_width=True)

    # Registered vs K-car breakdown
    df_split = df_m.groupby('brand_en').agg(
        reg=('sales_count', lambda x: x[df_m.loc[x.index, 'vehicle_type'].str.contains('Registered', case=False)].sum()),
        kei=('sales_count', lambda x: x[df_m.loc[x.index, 'vehicle_type'].str.contains('Kei', case=False)].sum()),
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
    """K-car brand share + monthly trend."""
    if kcar_brand_df.empty and kcar_monthly_df.empty:
        st.info("No K-car data available.")
        return

    tab_a, tab_b = st.tabs(["🥧 Brand Share", "📈 Monthly Trend"])

    with tab_a:
        if kcar_brand_df.empty:
            st.info("No K-car brand data.")
        else:
            df = kcar_brand_df.copy()
            # Translate
            df['brand_en'] = df['brand'].map(BRAND_NAME_MAP).fillna(df['brand'])
            all_ym = sorted(df.apply(lambda r: f"{int(r['year'])}/{int(r['month']):02d}", axis=1).unique())
            selected_ym = st.selectbox("Select Month", all_ym, index=len(all_ym) - 1, key='kcar_brand_ym')
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

                # YoY table
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

            # Passenger vs Cargo
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


def render_data_summary(df_raw):
    """Data Freshness & Summary Panel."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Latest crawl date and count
    c.execute("SELECT crawl_date, COUNT(*) FROM used_cars GROUP BY crawl_date ORDER BY crawl_date DESC LIMIT 5")
    crawl_recent = c.fetchall()

    # Macro data latest month
    c.execute("SELECT MAX(year), MAX(month) FROM japan_monthly_summary")
    macro_latest = c.fetchone()

    # Total used cars
    c.execute("SELECT COUNT(*) FROM used_cars")
    total_used = c.fetchone()[0]

    # Macro brand count
    c.execute("SELECT COUNT(DISTINCT brand) FROM new_car_sales_brand")
    total_brands_macro = c.fetchone()[0]

    # K-car brand count
    c.execute("SELECT COUNT(*) FROM kcar_brand_sales")
    kcar_brand_cnt = c.fetchone()[0]

    conn.close()

    latest_crawl = crawl_recent[0] if crawl_recent else (None, 0)
    prev_crawl = crawl_recent[1] if len(crawl_recent) > 1 else (None, 0)
    new_listings = latest_crawl[1] if latest_crawl[0] else 0

    cols = st.columns(5)
    with cols[0]:
        st.metric("📦 二手车总量", f"{total_used:,}", f"+{new_listings} 最新批次")
    with cols[1]:
        st.metric("🕐 最新爬取", latest_crawl[0] or "N/A")
    with cols[2]:
        st.metric("🇯🇵 行业数据", f"{macro_latest[0]}/{macro_latest[1]:02d}" if macro_latest[0] else "N/A")
    with cols[3]:
        st.metric("🏭 新车品牌数", f"{total_brands_macro}")
    with cols[4]:
        st.metric("🚗 K-car 品牌数", f"{kcar_brand_cnt}")

    # Data coverage progress bar
    if crawl_recent:
        st.caption(f"📋 最近 {len(crawl_recent)} 次爬取: " + " | ".join([f"{d}: {c}辆" for d, c in crawl_recent]))


def chart_powertrain(df):
    """Powertrain & Transmission Analysis."""
    price_col = 'price_vehicle'

    tab_a, tab_b = st.tabs(["⛽ 动力类型", "🔧 变速箱"])

    with tab_a:
        # Unify category field
        df_p = df.copy()
        cat_map = {
            'Import': 'Import', 'Domestic': 'Domestic',
            'K-car': 'K-car', 'Hybrid': 'Hybrid',
            'K-car': 'K-car', 'Domestic': 'Domestic',
            'Hybrid': 'Hybrid', 'Import': 'Import',
        }
        df_p['cat_clean'] = df_p['category'].map(cat_map).fillna('Other')

        if df_p['cat_clean'].nunique() == 0:
            st.info("No powertrain data available.")
            return

        c1, c2 = st.columns([1, 2])
        with c1:
            cat_counts = df_p['cat_clean'].value_counts()
            fig_pie = px.pie(
                values=cat_counts.values, names=cat_counts.index,
                title="Powertrain Type Distribution",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            df_pp = df_p[(df_p[price_col] > 0) & (df_p[price_col] < 2000)].copy()
            cat_order = df_pp.groupby('cat_clean')[price_col].median().sort_values(ascending=False).index.tolist()
            fig_box = px.box(
                df_pp, x='cat_clean', y=price_col,
                category_orders={'cat_clean': cat_order},
                title="Price Distribution by Powertrain Type",
                labels={price_col: 'Price (man-yen)', 'cat_clean': 'Type'},
                color='cat_clean',
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_box.update_layout(showlegend=False, height=450)
            st.plotly_chart(fig_box, use_container_width=True)

        # Stats table
        st.markdown("#### 📊 Powertrain Statistics")
        cat_stats = df_pp.groupby('cat_clean').agg(
            count=(price_col, 'count'),
            avg_price=(price_col, 'mean'),
            median_price=(price_col, 'median'),
            min_price=(price_col, 'min'),
            max_price=(price_col, 'max'),
            avg_mileage=('mileage_wan_km', 'mean'),
        ).round(1).sort_values('count', ascending=False)
        cat_stats.columns = ['Count', 'Avg Price', 'Median Price', 'Min Price', 'Max Price', 'Avg Mileage (万km)']
        st.dataframe(cat_stats, use_container_width=True, hide_index=True)

    with tab_b:
        df_t = df[df['transmission'].notna()].copy()
        if len(df_t) == 0:
            st.info("No transmission data available.")
            return

        # Classify transmission
        def simplify_trans(t):
            t = str(t).upper()
            if 'CVT' in t: return 'CVT'
            if 'MT' in t: return 'MT'
            if 'AT' in t: return 'AT'
            return 'Other'
        df_t['trans_simple'] = df_t['transmission'].apply(simplify_trans)

        c1, c2 = st.columns(2)
        with c1:
            trans_counts = df_t['trans_simple'].value_counts()
            fig1 = px.bar(
                x=trans_counts.index, y=trans_counts.values,
                title="Transmission Type Distribution",
                labels={'x': 'Transmission', 'y': 'Count'},
                color=trans_counts.values,
                color_continuous_scale='Blues',
                text=trans_counts.values,
            )
            fig1.update_traces(textposition='outside')
            fig1.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            df_tp = df_t[(df_t[price_col] > 0) & (df_t[price_col] < 2000)].copy()
            fig2 = px.box(
                df_tp, x='trans_simple', y=price_col,
                title="Price by Transmission Type",
                labels={price_col: 'Price (man-yen)', 'trans_simple': 'Transmission'},
                color='trans_simple',
                color_discrete_sequence=['#1a73e8', '#ea4335', '#34a853', '#fbbc04'],
            )
            fig2.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig2, use_container_width=True)

        # Transmission × Year Trend
        df_ty = df_t[(df_t['year_ce'].notna()) & (df_t['year_ce'] >= 2010) & (df_t[price_col] > 0)].copy()
        if len(df_ty) > 5:
            trans_year = df_ty.groupby(['year_ce', 'trans_simple']).size().reset_index(name='count')
            fig3 = px.area(
                trans_year, x='year_ce', y='count', color='trans_simple',
                title="Transmission Trend by Model Year",
                labels={'year_ce': 'Model Year', 'count': 'Listings', 'trans_simple': 'Transmission'},
                height=350,
            )
            fig3.update_layout(hovermode="x unified")
            st.plotly_chart(fig3, use_container_width=True)


def chart_domestic_vs_import(df):
    """Import vs Domestic Deep Comparison."""
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & (df[price_col] < 2000) & df['brand_origin'].notna()].copy()
    if len(df_p) == 0:
        st.info("No data for domestic vs import comparison.")
        return

    # KPI comparison
    domestic = df_p[df_p['brand_origin'] == 'Domestic']
    imported = df_p[df_p['brand_origin'] == 'Import']

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("🇯🇵 Domestic Count", f"{len(domestic):,}", f"{len(domestic)/max(len(df_p),1)*100:.1f}%")
    with k2:
        st.metric("🌍 Import Count", f"{len(imported):,}", f"{len(imported)/max(len(df_p),1)*100:.1f}%")
    with k3:
        d_avg = domestic[price_col].mean() if len(domestic) > 0 else 0
        i_avg = imported[price_col].mean() if len(imported) > 0 else 0
        st.metric("💰 Domestic Avg Price", f"{d_avg:.1f}", f"vs Import {i_avg:.1f}")
    with k4:
        d_med = domestic[price_col].median() if len(domestic) > 0 else 0
        i_med = imported[price_col].median() if len(imported) > 0 else 0
        st.metric("💰 Import Avg Price", f"{i_avg:.1f}", f"vs Domestic {d_med:.1f}")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        # Price distribution comparison
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=domestic[price_col], name='Domestic',
            opacity=0.7, marker_color='#1a73e8',
            nbinsx=50,
            hovertemplate='Price: %{x} · Count: %{y}<extra></extra>',
        ))
        fig.add_trace(go.Histogram(
            x=imported[price_col], name='Import',
            opacity=0.7, marker_color='#ea4335',
            nbinsx=50,
            hovertemplate='Price: %{x} · Count: %{y}<extra></extra>',
        ))
        fig.update_layout(
            title="Price Distribution: Domestic vs Import",
            xaxis_title="Price (man-yen)", yaxis_title="Count",
            barmode='overlay', height=450,
            legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Mileage vs Price scatter
        df_s = df_p[df_p['mileage_wan_km'].notna() & (df_p['mileage_wan_km'] > 0)].copy()
        fig2 = px.scatter(
            df_s, x='mileage_wan_km', y=price_col,
            color='brand_origin',
            hover_name='brand_clean',
            title="Price vs Mileage: Domestic vs Import",
            labels={'mileage_wan_km': 'Mileage (万km)', price_col: 'Price (man-yen)'},
            color_discrete_map={'Domestic': '#1a73e8', 'Import': '#ea4335'},
            opacity=0.6, height=450,
        )
        fig2.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1))
        st.plotly_chart(fig2, use_container_width=True)

    # Displacement distribution comparison
    df_d = df_p[df_p['displacement_cc'].notna() & (df_p['displacement_cc'] > 0)].copy()
    if len(df_d) > 0:
        st.markdown("#### 📏 排量分布对比")
        fig3 = go.Figure()
        fig3.add_trace(go.Violin(
            x=df_d[df_d['brand_origin']=='Domestic']['displacement_cc'],
            name='Domestic', side='negative',
            line_color='#1a73e8', fillcolor='rgba(26,115,232,0.3)',
        ))
        fig3.add_trace(go.Violin(
            x=df_d[df_d['brand_origin']=='Import']['displacement_cc'],
            name='Import', side='positive',
            line_color='#ea4335', fillcolor='rgba(234,67,53,0.3)',
        ))
        fig3.update_layout(
            title="Displacement Distribution: Domestic vs Import",
            xaxis_title="Displacement (cc)",
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='right', x=1),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Brand ranking comparison
    st.markdown("#### 🏆 Top 10 Brands by Origin")
    c1, c2 = st.columns(2)
    with c1:
        dom_top = domestic.groupby('brand_clean').agg(
            count=(price_col, 'count'), avg_price=(price_col, 'mean')
        ).sort_values('count', ascending=False).head(10).round(1)
        dom_top.columns = ['Listings', 'Avg Price']
        st.markdown("**🇯🇵 Domestic Top 10**")
        st.dataframe(dom_top, use_container_width=True, hide_index=True)
    with c2:
        imp_top = imported.groupby('brand_clean').agg(
            count=(price_col, 'count'), avg_price=(price_col, 'mean')
        ).sort_values('count', ascending=False).head(10).round(1)
        imp_top.columns = ['Listings', 'Avg Price']
        st.markdown("**🌍 Import Top 10**")
        st.dataframe(imp_top, use_container_width=True, hide_index=True)


@st.cache_data(ttl=120)
def load_export_data():
    """加载jumv.net出口统计数据"""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM export_statistics ORDER BY year, month", conn)
        df['shape_name'] = df['shape_name'].apply(translate_shape)
        df['country_name'] = df['country_name'].apply(translate_country)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_market_report_data():
    """加载 Kurumaerabi 市场报告数据"""
    conn = sqlite3.connect(DB_PATH)
    try:
        monthly = pd.read_sql_query("SELECT * FROM market_report_monthly ORDER BY year, month", conn)
    except Exception:
        monthly = pd.DataFrame()
    try:
        rankings = pd.read_sql_query("SELECT * FROM market_rankings ORDER BY report_year, report_month, category, rank", conn)
        rankings['name'] = rankings['name'].apply(translate_model_name)
    except Exception:
        rankings = pd.DataFrame()
    conn.close()
    return monthly, rankings


def chart_export_statistics():
    """日本中古车出口统计 (jumv.net)"""
    df = load_export_data()
    if df.empty:
        st.info("No export data. Run crawl_jumv.py first.")
        return

    st.caption("Data: jumv.net (based on MOF Trade Statistics) · Updated monthly")

    # Data overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        if 'year' in df.columns:
            latest = df[df['year'] == df['year'].max()]
            st.metric("Latest Year", f"{int(df['year'].max())}")
    with col3:
        if 'shape_name' in df.columns:
            st.metric("Vehicle Types", f"{df['shape_name'].nunique()}")
    with col4:
        if 'country_name' in df.columns:
            st.metric("Export Destinations", f"{df['country_name'].nunique()}")

    # Separate monthly and annual data
    df_monthly = df[df['month'] > 0].copy() if 'month' in df.columns else df.copy()
    df_annual = df[df['month'] == 0].copy() if 'month' in df.columns else pd.DataFrame()

    st.markdown("---")

    # Export trend by vehicle type (annual)
    if not df_annual.empty and 'shape_name' in df_annual.columns:
        st.markdown("#### 📊 Annual Export Volume by Vehicle Type")
        annual = df_annual.groupby(['year', 'shape_name'])['export_count'].sum().reset_index()
        fig = px.bar(annual, x='year', y='export_count', color='shape_name',
                     title="Annual Export Units by Vehicle Type",
                     barmode='group', height=400)
        fig.update_layout(xaxis_title="Year", yaxis_title="Units Exported",
                          legend_title="Vehicle Type")
        st.plotly_chart(fig, use_container_width=True)

    # Latest month top destinations
    if not df_monthly.empty and 'country_name' in df_monthly.columns:
        latest_month = df_monthly.groupby(['year', 'month'])['export_count'].sum().idxmax()
        latest_data = df_monthly[(df_monthly['year'] == latest_month[0]) & (df_monthly['month'] == latest_month[1])]

        st.markdown(f"#### 🌍 Top Export Destinations ({latest_month[0]}-{latest_month[1]:02d})")

        # Tabs by vehicle type
        if 'shape_name' in latest_data.columns:
            vtypes = latest_data['shape_name'].unique()
            if len(vtypes) > 1:
                vtabs = st.tabs([str(v) for v in vtypes[:6]])
                for i, vt in enumerate(sorted(vtypes)[:6]):
                    with vtabs[i]:
                        sub = latest_data[latest_data['shape_name'] == vt].nlargest(10, 'export_count')
                        if not sub.empty:
                            fig = px.bar(sub, x='export_count', y='country_name', orientation='h',
                                         title=f"{vt} - Top 10 Destinations",
                                         color='export_count', color_continuous_scale='Viridis',
                                         height=350)
                            fig.update_layout(yaxis={'categoryorder': 'total ascending'},
                                              xaxis_title="Units", yaxis_title="Country")
                            st.plotly_chart(fig, use_container_width=True)
            else:
                sub = latest_data.nlargest(15, 'export_count')
                fig = px.bar(sub, x='export_count', y='country_name', orientation='h',
                             color='export_count', color_continuous_scale='Viridis', height=400)
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

    # Country trend (annual)
    if not df_annual.empty and 'country_name' in df_annual.columns:
        st.markdown("#### 📈 Export Trends for Top 5 Destinations")
        top_countries = df_annual.groupby('country_name')['export_count'].sum().nlargest(5).index.tolist()
        country_trend = df_annual[df_annual['country_name'].isin(top_countries)].groupby(['year', 'country_name'])['export_count'].sum().reset_index()
        fig = px.line(country_trend, x='year', y='export_count', color='country_name',
                      title="Annual Export Trend - Top 5 Countries", height=400,
                      markers=True)
        fig.update_layout(xaxis_title="Year", yaxis_title="Units", legend_title="Country")
        st.plotly_chart(fig, use_container_width=True)


def chart_market_report():
    """Kurumaerabi 月次市场报告"""
    monthly, rankings = load_market_report_data()
    if monthly.empty and rankings.empty:
        st.info("No market report data. Run crawl_kurumaerabi_v2.py first.")
        return

    st.caption("Data: Kurumaerabi / symphony market report · Monthly registration & rankings")

    # KPI
    if not monthly.empty:
        latest = monthly.sort_values(['year', 'month']).iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_val = f"{int(latest['new_car_registered']):,}" if pd.notna(latest.get('new_car_registered')) else "N/A"
            st.metric("Latest New Car Reg.", new_val)
        with col2:
            used_val = f"{int(latest['used_car_registered']):,}" if pd.notna(latest.get('used_car_registered')) else "N/A"
            st.metric("Latest Used Car Reg.", used_val)
        with col3:
            yoy = latest.get('new_car_yoy_pct')
            yoy_str = f"{yoy:.1f}%" if pd.notna(yoy) else "N/A"
            st.metric("New Car YoY", yoy_str)
        with col4:
            yoy2 = latest.get('used_car_yoy_pct')
            yoy2_str = f"{yoy2:.1f}%" if pd.notna(yoy2) else "N/A"
            st.metric("Used Car YoY", yoy2_str)

        st.markdown("---")

        # New vs Used Car Monthly Trend
        st.markdown("#### 📈 New Car vs Used Car Registration Trend")
        monthly_sorted = monthly.sort_values(['year', 'month']).copy()
        monthly_sorted['period'] = monthly_sorted.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)

        fig = go.Figure()
        if 'new_car_registered' in monthly_sorted.columns:
            fig.add_trace(go.Scatter(x=monthly_sorted['period'], y=monthly_sorted['new_car_registered'],
                                     name='New Car', mode='lines+markers',
                                     line=dict(color='#1a73e8', width=2)))
        if 'used_car_registered' in monthly_sorted.columns:
            fig.add_trace(go.Scatter(x=monthly_sorted['period'], y=monthly_sorted['used_car_registered'],
                                     name='Used Car', mode='lines+markers',
                                     line=dict(color='#ea4335', width=2)))
        fig.update_layout(title="Monthly Registration: New vs Used",
                          xaxis_title="Period", yaxis_title="Units",
                          hovermode='x unified', height=400)
        st.plotly_chart(fig, use_container_width=True)

        # YoY change trend
        st.markdown("#### 📊 Year-over-Year Change")
        fig2 = go.Figure()
        if 'new_car_yoy_pct' in monthly_sorted.columns:
            fig2.add_trace(go.Scatter(x=monthly_sorted['period'], y=monthly_sorted['new_car_yoy_pct'],
                                      name='New Car YoY%', mode='lines+markers',
                                      line=dict(color='#1a73e8', width=2)))
        if 'used_car_yoy_pct' in monthly_sorted.columns:
            fig2.add_trace(go.Scatter(x=monthly_sorted['period'], y=monthly_sorted['used_car_yoy_pct'],
                                      name='Used Car YoY%', mode='lines+markers',
                                      line=dict(color='#ea4335', width=2)))
        fig2.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="100% (flat)")
        fig2.update_layout(title="Year-over-Year Registration Change (%)",
                           xaxis_title="Period", yaxis_title="YoY %",
                           hovermode='x unified', height=350)
        st.plotly_chart(fig2, use_container_width=True)

    # Sales rankings
    if not rankings.empty:
        st.markdown("---")
        st.markdown("#### 🏆 Used Car Sales Rankings")

        # Select report month
        report_months = rankings.groupby(['report_year', 'report_month']).size().reset_index()
        report_months['label'] = report_months.apply(lambda r: f"{int(r['report_year'])}-{int(r['report_month']):02d}", axis=1)
        selected = st.selectbox("Select Report Month", report_months['label'].tolist(),
                                index=len(report_months)-1)
        sel_parts = selected.split('-')
        sel_y, sel_m = int(sel_parts[0]), int(sel_parts[1])

        sel_rankings = rankings[(rankings['report_year'] == sel_y) & (rankings['report_month'] == sel_m)]

        cat_tabs = st.tabs(["🇯🇵 Domestic Body Type", "🇯🇵 Domestic Model",
                            "🌍 Import Body Type", "🌍 Import Model"])
        cat_map = {
            0: 'domestic_body_type',
            1: 'domestic_model',
            2: 'imported_body_type',
            3: 'imported_model',
        }

        for i, cat in cat_map.items():
            with cat_tabs[i]:
                sub = sel_rankings[sel_rankings['category'] == cat].sort_values('rank')
                if sub.empty:
                    st.info("No data for this category.")
                else:
                    # Display ranking table
                    display_df = sub[['rank', 'name']].copy()
                    display_df.columns = ['Rank', 'Name']
                    if 'extra' in sub.columns:
                        try:
                            import json as _json
                            extras = []
                            for _, row in sub.iterrows():
                                try:
                                    e = _json.loads(row['extra']) if row['extra'] else []
                                    extras.append(' | '.join(e) if e else '')
                                except:
                                    extras.append('')
                            display_df['Detail'] = extras
                        except:
                            pass
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    # Bar chart
                    if len(sub) > 0:
                        fig = px.bar(sub, x='rank', y='name', orientation='h',
                                     title=f"{cat.replace('_', ' ').title()} Ranking",
                                     height=max(300, len(sub) * 30))
                        fig.update_layout(yaxis={'categoryorder': 'total ascending'},
                                          xaxis_title="Rank", yaxis_title="", showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)


def chart_import_export():
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
        "\U0001F6A2 Export Overview",
        "\U0001F4E5 Import Overview",
        "\U0001F310 Overseas Production",
        "\U0001F3ED Production & Sales"
    ])

    # ====== Tab 1: Export Overview ======
    with ie_tab1:
        st.markdown("#### \U0001F4CA Export Overview (New + Used)")

        # --- Chart 1: New Car Export + Used Car Export by year ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**\u65B0\u8ECA\u51FA\u53E3\u53F0\u6570\u63A8\u79FB (JAMA)**")
            if not export_type_df.empty:
                et_pivot = export_type_df[export_type_df['vehicle_type'] != '\u5408\u8BA1'].pivot_table(
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
            st.markdown("**\u4E2D\u53E4\u8E66\u51FA\u53E3 (jumv.net)**")
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
        st.markdown("#### \u4ED5\u5411\u5730\u5225\u51FA\u53E3\u63A8\u79FB (Destination Region)")
        if not new_car_export_df.empty:
            nce_pivot = new_car_export_df[new_car_export_df['region'] != '\u5408\u8BA1'].pivot_table(
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
        st.markdown("#### EV / HV \u51FA\u53E3\u8D8B\u52BF (EV Trend)")
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
        st.markdown("**\u4ED5\u5411\u5730\u5225\u51FA\u53E3\u30C7\u30FC\u30BF**")
        if not new_car_export_df.empty:
            display_df = new_car_export_df.pivot_table(
                index='year', columns='region', values='units', aggfunc='sum'
            ).reset_index()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ====== Tab 2: Import Overview ======
    with ie_tab2:
        st.markdown("#### \u8FDB\u53E3\u8F66\u54C1\u724C\u522B\u6708\u6B21\u63A8\u79FB (Top10 Brands)")

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
        st.markdown("#### \u8FDB\u53E3 vs \u56FD\u4EA7\u5BF9\u6BD4 (Import vs Domestic)")
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
        st.markdown("#### \u8F38\u5165\u8ECA\u8CA9\u58F2\u53F0\u6570\u63A8\u79FB (2019-2024)")
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
        st.markdown("#### \u81EA\u52D5\u8ECA\u8F38\u5165\u53F0\u6570 (\u901A\u95A2\u5B9F\u7E3E - by Country)")
        if not import_customs_df.empty:
            ic_pivot = import_customs_df[import_customs_df['country'] != '\u5408\u8BA1'].pivot_table(
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
        st.markdown("#### \u6D77\u5916\u751F\u4EA7\u30C7\u30FC\u30BF (Overseas Production)")

        # --- Chart 6: Overseas production by region (annual) ---
        if not overseas_annual_df.empty:
            op_pivot = overseas_annual_df[overseas_annual_df['region'] != '\u5408\u8BA1'].pivot_table(
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
                    q1_display = q1_data[q1_data['region'] != '\u5408\u8A08'].copy()
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
                    annual_display = annual_data[annual_data['region'] != '\u5408\u8A08'].copy()
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
                q1_compare = q1_data[q1_data['region'].isin(['\u30A2\u30B8\u30A2', '\u6B27\u5DDE', '\u5317\u7C73', '\u4E2D\u5357\u7C73', '\u30A2\u30D5\u30EA\u30AB', '\u5408\u8A08'])].copy()
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
            st.markdown('<div class="section-title">🇯🇵 JADA Sales — New Car Sales</div>', unsafe_allow_html=True)
            st.caption("Data: JADA (Brand Registration) + Zenkeijikyo (K-car) · Updated monthly")
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
    # ====== Data Freshness Summary ======
    render_data_summary(df_raw)
    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
        "💰 Price", "🏭 Brands", "📊 Scatter",
        "🚙 Vehicle Class", "📈 Year Trend", "🔮 Forecast",
        "🗺️ Region", "🇯🇵 JADA Sales",
        "⚡ Powertrain", "🆚 Domestic vs Import",
        "🚢 Export Stats", "📋 Market Report",
        "🌐 Import & Export"
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
        st.markdown('<div class="section-title">🇯🇵 JADA Sales — New Car Sales</div>', unsafe_allow_html=True)
        st.caption("Data: JADA (Brand Registration) + Zenkeijikyo (K-car) · Updated monthly")
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

    with tab9:
        st.markdown('<div class="section-title">Powertrain & Transmission Analysis</div>', unsafe_allow_html=True)
        chart_powertrain(df)

    with tab10:
        st.markdown('<div class="section-title">Domestic vs Import — Deep Comparison</div>', unsafe_allow_html=True)
        chart_domestic_vs_import(df)

    with tab11:
        st.markdown('<div class="section-title">Japan Used Car Export Statistics</div>', unsafe_allow_html=True)
        chart_export_statistics()

    with tab12:
        st.markdown('<div class="section-title">Monthly Market Report — Registration & Rankings</div>', unsafe_allow_html=True)
        chart_market_report()

    with tab13:
        st.markdown('<div class="section-title">Japan Auto Market — Import & Export Overview</div>', unsafe_allow_html=True)
        chart_import_export()

    st.markdown("""
    <div class="gradient-divider"></div>
    <div style="text-align:center; color:#5f6368; font-size:0.85em; padding:12px 0;">
        🇯🇵 Japan Used Car Market Analytics · Source: carsensor.net + JADA + Zenkeijikyo + jumv.net + Kurumaerabi + JAMA + JAIA · Stack: Playwright + Pandas + SQLite + Prophet + Streamlit<br>
        📦 13 Tabs: Price · Brands · Scatter · Vehicle Class · Year Trend · Forecast · Region · JADA Sales · Powertrain · Domestic vs Import · Export Stats · Market Report · Import & Export
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

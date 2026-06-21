"""
Japan Used Car Market Intelligence Dashboard
Real-time monitoring of prices, brand distribution, and market trends
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import os

# Resolve DB path relative to project root
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
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
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
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    except Exception:
        df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()
    return df


def render_kpi_cards(df):
    price_col = 'price_vehicle'
    total = len(df)
    avg_price = df[price_col].mean()
    n_brands = df['brand_clean'].nunique() if 'brand_clean' in df.columns else 0
    kcar_pct = (df['vehicle_class'] == 'K-car (<=660cc)').mean() * 100 if 'vehicle_class' in df.columns else 0

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
            <div class="kpi-card {cls}">
                <p>{icon}</p>
                <h2>{value}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)


def chart_price_distribution(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & (df[price_col] < 2000)].copy()

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.histogram(df_p, x=price_col, nbins=60,
                           title="Price Distribution",
                           color_discrete_sequence=['#1a73e8'],
                           opacity=0.75)
        fig.add_vline(x=df_p[price_col].mean(), line_dash="dash", line_color="#ea4335",
                      annotation_text=f"Mean: {df_p[price_col].mean():.0f}")
        fig.add_vline(x=df_p[price_col].median(), line_dash="dot", line_color="#34a853",
                      annotation_text=f"Median: {df_p[price_col].median():.0f}")
        fig.update_layout(xaxis_title="Price (man-yen)", yaxis_title="Count",
                         hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Price Range Breakdown")
        price_bins = [0, 50, 100, 150, 200, 300, 500, 10000]
        labels = ['<50', '50-100', '100-150', '150-200', '200-300', '300-500', '500+']
        df_p2 = df_p.copy()
        df_p2['range'] = pd.cut(df_p2[price_col], bins=price_bins, labels=labels)
        bin_stats = df_p2.groupby('range', observed=True).agg(
            count=(price_col, 'count'),
            avg_price=(price_col, 'mean'),
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

    brand_counts = df_p['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()

    tab1, tab2 = st.tabs(["📈 Price Range by Brand", "🥧 Market Share"])

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
                             yaxis_title="Price (man-yen)",
                             showlegend=True, height=500)
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


def chart_vehicle_class(df):
    price_col = 'price_vehicle'

    tab1, tab2 = st.tabs(["📊 Class Comparison", "🚗 K-car Deep Dive"])

    with tab1:
        df_p = df[(df[price_col] > 0) & df['vehicle_class'].notna()].copy()

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
        The perfect solution for Japan's dense cities and narrow streets.
        """)

        df_kcar = df[(df['vehicle_class'] == 'K-car (<=660cc)') & (df[price_col] > 0)].copy()

        if len(df_kcar) > 0:
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("K-car Count", f"{len(df_kcar)}")
            with k2: st.metric("Avg Price", f"{df_kcar[price_col].mean():.1f} man-yen")
            with k3: st.metric("Lowest Price", f"{df_kcar[price_col].min():.1f} man-yen")
            with k4: st.metric("Market Share", f"{len(df_kcar)/len(df)*100:.1f}%")

            kcar_brands = df_kcar['brand_clean'].value_counts().head(6)
            fig = px.bar(x=kcar_brands.index, y=kcar_brands.values,
                        title="K-car Brand Distribution",
                        color=kcar_brands.values, color_continuous_scale='Greens',
                        labels={'x': 'Brand', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)


def chart_year_trend(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)].copy()

    year_stats = df_p.groupby('year_ce').agg(
        avg_price=(price_col, 'mean'),
        median_price=(price_col, 'median'),
        count=(price_col, 'count'),
        p25=(price_col, lambda x: x.quantile(0.25)),
        p75=(price_col, lambda x: x.quantile(0.75)),
    ).reset_index()

    fig = go.Figure()

    # P25-P75 band
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p75'],
        mode='lines', line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p25'],
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(26,115,232,0.15)', name='P25-P75 Range'
    ))

    # Average line
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers', name='Average',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=8, color=year_stats['count'], colorscale='YlOrRd',
                    showscale=True, colorbar=dict(title='Count'))
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['median_price'],
        mode='lines+markers', name='Median',
        line=dict(color='#34a853', width=2, dash='dot')
    ))

    fig.update_layout(
        title="Price Trend by Model Year (P25-P75 band + count heatmap)",
        xaxis_title="Model Year", yaxis_title="Price (man-yen)",
        hovermode="x unified", height=500
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_prefecture(df):
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['prefecture'].notna()].copy()

    pref_stats = df_p.groupby('prefecture').agg(
        avg_price=(price_col, 'mean'),
        count=(price_col, 'count'),
    ).reset_index().sort_values('avg_price', ascending=False)

    fig = px.bar(pref_stats, x='prefecture', y='avg_price',
                title="Average Price by Prefecture",
                color='count', color_continuous_scale='Viridis',
                labels={'prefecture': 'Prefecture', 'avg_price': 'Avg Price (man-yen)', 'count': 'Listings'})
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def data_explorer(df):
    display_cols = ['brand_clean', 'model', 'price_vehicle', 'year_ce', 'mileage_wan_km',
                    'displacement_cc', 'vehicle_class', 'prefecture', 'brand_origin']
    available = [c for c in display_cols if c in df.columns]

    col1, col2 = st.columns(2)
    with col1:
        brands = sorted(df['brand_clean'].dropna().unique()) if 'brand_clean' in df.columns else []
        sel_brand = st.multiselect("Filter by brand", brands, default=[], key='exp_brand')
    with col2:
        if 'vehicle_class' in df.columns:
            classes = sorted(df['vehicle_class'].dropna().unique())
            sel_class = st.multiselect("Filter by class", classes, default=[], key='exp_class')
        else:
            sel_class = []

    df_exp = df[available].copy()
    if sel_brand:
        df_exp = df_exp[df_exp['brand_clean'].isin(sel_brand)]
    if sel_class:
        df_exp = df_exp[df_exp['vehicle_class'].isin(sel_class)]

    st.dataframe(df_exp, use_container_width=True, height=400)
    st.caption(f"Showing {len(df_exp)} / {len(df)} records")


def main():
    st.markdown("""
    <div style="text-align:center; padding: 12px 0;">
        <h1 style="font-size:2.2em; margin:0;">🇯🇵 Japan Used Car Market Analytics</h1>
        <p style="color:#5f6368; font-size:1.05em; margin:6px 0 0;">
            Dynamic monitoring of car prices · Brand distribution · Market trends · Source: <a href="https://www.carsensor.net/usedcar/">carsensor.net</a>
        </p>
    </div>
    <div class="gradient-divider"></div>
    """, unsafe_allow_html=True)

    df = load_data()
    if len(df) == 0:
        st.warning("No data available. Run `python src/crawler.py` first.")
        return

    # ====== Sidebar ======
    with st.sidebar:
        st.markdown("## 🔍 Global Filters")
        price_col = 'price_vehicle'

        if price_col in df.columns:
            price_min = float(df[price_col].min())
            price_max = float(df[price_col].max())
            price_range = st.slider("Price Range (man-yen)", price_min, price_max,
                                    (price_min, price_max), step=10.0)
            df = df[(df[price_col] >= price_range[0]) & (df[price_col] <= price_range[1])]

        if 'year_ce' in df.columns:
            year_min = int(df['year_ce'].min())
            year_max = int(df['year_ce'].max())
            year_range = st.slider("Model Year Range", year_min, year_max, (year_min, year_max))
            df = df[(df['year_ce'] >= year_range[0]) & (df['year_ce'] <= year_range[1])]

        if 'brand_origin' in df.columns:
            brand_origins = df['brand_origin'].unique().tolist()
            sel_origins = st.multiselect("Brand Origin", brand_origins, default=brand_origins)
            df = df[df['brand_origin'].isin(sel_origins)]

        st.markdown("---")
        st.caption(f"Filtered: {len(df)} vehicles")

    # ====== KPI ======
    render_kpi_cards(df)
    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # ====== Tabs ======
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Price Analysis", "🏭 Brand Analysis", "🚙 Vehicle Class",
        "📈 Year Trend", "🗺️ Region Analysis", "📋 Data Explorer"
    ])

    with tab1:
        st.markdown('<div class="section-title">Price Distribution & Range Statistics</div>', unsafe_allow_html=True)
        chart_price_distribution(df)

    with tab2:
        st.markdown('<div class="section-title">Brand Price Range & Market Share</div>', unsafe_allow_html=True)
        chart_brand_analysis(df)

    with tab3:
        st.markdown('<div class="section-title">Vehicle Class Analysis — K-car Spotlight</div>', unsafe_allow_html=True)
        chart_vehicle_class(df)

    with tab4:
        st.markdown('<div class="section-title">Price Trend by Model Year</div>', unsafe_allow_html=True)
        chart_year_trend(df)

    with tab5:
        st.markdown('<div class="section-title">Regional Price Analysis</div>', unsafe_allow_html=True)
        chart_prefecture(df)

    with tab6:
        st.markdown('<div class="section-title">Data Explorer</div>', unsafe_allow_html=True)
        data_explorer(df)

    st.markdown("""
    <div class="gradient-divider"></div>
    <div style="text-align:center; color:#5f6368; font-size:0.85em; padding:12px 0;">
        🇯🇵 Japan Used Car Market Analytics · Source: carsensor.net · Stack: Playwright + Pandas + SQLite + Prophet + Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

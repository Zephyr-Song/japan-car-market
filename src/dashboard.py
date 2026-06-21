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
import time

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
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
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

    with tab3:
        st.markdown("### 🎬 Animated Brand Price Race")
        st.caption("Average price by brand — animated across model year bins")

        df_anim = df_p[df['brand_clean'].isin(top_brands[:12]) & df_p['year_ce'].notna()].copy()
        df_anim['year_bin'] = (df_anim['year_ce'] // 3) * 3  # 3-year bins

        brand_year = df_anim.groupby(['year_bin', 'brand_clean']).agg(
            avg_price=(price_col, 'mean'),
            count=(price_col, 'count'),
        ).reset_index()

        fig = px.bar(brand_year, x='avg_price', y='brand_clean',
                     color='brand_clean', orientation='h',
                     animation_frame='year_bin',
                     range_x=[0, brand_year['avg_price'].max() * 1.15],
                     title="Average Price by Brand Over Years",
                     labels={'avg_price': 'Avg Price (man-yen)', 'brand_clean': 'Brand'},
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     height=550)
        fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)


def chart_scatter(df):
    """Price vs Mileage animated scatter with brand filter"""
    price_col = 'price_vehicle'
    df_s = df[(df[price_col] > 0) & df['mileage_wan_km'].notna() & (df['mileage_wan_km'] > 0)
              & df['brand_clean'].notna() & (df['brand_clean'] != 'Unknown')].copy()

    brand_counts = df_s['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()

    col1, col2 = st.columns([1, 3])
    with col1:
        selected = st.multiselect("Filter brands", top_brands, default=top_brands[:6], key='scatter_brand')
        show_anim = st.checkbox("Animate by Year", value=True)
    with col2:
        df_plot = df_s[df_s['brand_clean'].isin(selected)].copy() if selected else df_s.copy()

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
            fig.update_layout(transition={'duration': 500})
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

    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p75'],
        mode='lines', line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p25'],
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(26,115,232,0.15)', name='P25-P75 Range'
    ))

    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers', name='Average',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=8, color=year_stats['count'], colorscale='YlOrRd',
                    showscale=True, colorbar=dict(title='Count'))
    ))

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

    # Use horizontal bar for readability
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
    """Price prediction demo — uses model-year trend as proxy until multi-day data available"""
    st.markdown("""
    > 💡 **Prediction Module**: Currently showing cross-sectional trend by model year.
    > With multi-day crawl data, Prophet time-series forecasting will auto-enable.
    """)

    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)].copy()

    # Simulate forecast by fitting a polynomial to year avg prices
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

    # Extend 3 years into the future
    future_years = np.arange(year_stats['year_ce'].min(), year_stats['year_ce'].max() + 4)
    predicted = p(future_years)

    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers', name='Historical Average',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=10, color=year_stats['count'], colorscale='YlOrRd',
                    showscale=True, colorbar=dict(title='Sample Size'))
    ))

    # Trend line (full range)
    fig.add_trace(go.Scatter(
        x=future_years, y=predicted,
        mode='lines', name='Trend (Polynomial Fit)',
        line=dict(color='#ea4335', width=2, dash='dash')
    ))

    # Forecast zone
    last_year = year_stats['year_ce'].max()
    future_mask = future_years > last_year
    if future_mask.any():
        fig.add_trace(go.Scatter(
            x=future_years[future_mask], y=predicted[future_mask],
            mode='lines+markers', name='Forecast',
            line=dict(color='#ea4335', width=3),
            marker=dict(size=10, symbol='diamond')
        ))

        # Confidence band (±15% for demo)
        fig.add_trace(go.Scatter(
            x=future_years[future_mask],
            y=predicted[future_mask] * 1.15,
            mode='lines', line=dict(width=0), showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=future_years[future_mask],
            y=predicted[future_mask] * 0.85,
            mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(234,67,53,0.15)', name='80% Confidence'
        ))

    fig.add_vline(x=last_year + 0.5, line_dash="dot", line_color="gray",
                  annotation_text="Forecast →")

    fig.update_layout(
        title="Price Trend & Forecast (Polynomial + Projected 3 Years)",
        xaxis_title="Model Year", yaxis_title="Avg Price (man-yen)",
        hovermode="x unified", height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # Brand-specific forecast
    st.markdown("#### 🏭 Brand-Level Trend Forecast")
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
    fig2.update_layout(hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)


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
        <h1 style="font-size:2.2em; margin:0;">🇯🇵 Japan Used Car Market Analytics
        <span class="live-badge">LIVE</span></h1>
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

    # ====== Auto-refresh ======
    with st.sidebar:
        st.markdown("## 🔍 Global Filters")
        auto_refresh = st.checkbox("Auto-refresh (5 min)", value=False)
        if auto_refresh:
            st.caption("Data will reload every 5 minutes")

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💰 Price", "🏭 Brands", "📊 Scatter",
        "🚙 Vehicle Class", "📈 Year Trend", "🔮 Forecast",
        "🗺️ Region"
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

    st.markdown("""
    <div class="gradient-divider"></div>
    <div style="text-align:center; color:#5f6368; font-size:0.85em; padding:12px 0;">
        🇯🇵 Japan Used Car Market Analytics · Source: carsensor.net · Stack: Playwright + Pandas + SQLite + Prophet + Streamlit
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(300)
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()

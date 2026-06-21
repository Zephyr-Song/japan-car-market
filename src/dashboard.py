"""
🇯🇵 日本二手车市场智能分析系统 — Streamlit Dashboard
动态监控汽车价格、品牌分布以及市场变化趋势
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

DB_PATH = "data/japan_car_market.db"

st.set_page_config(
    page_title="日本二手车市场智能分析",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====== 自定义 CSS 动态效果 ======
st.markdown("""
<style>
    /* KPI 卡片动效 */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    .kpi-card h2 { margin:0; font-size:2.2em; font-weight:800; }
    .kpi-card p { margin:4px 0 0; opacity:0.9; font-size:0.95em; }

    .kpi-red { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); box-shadow: 0 4px 15px rgba(245,87,108,0.4); }
    .kpi-green { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); box-shadow: 0 4px 15px rgba(79,172,254,0.4); }
    .kpi-gold { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); box-shadow: 0 4px 15px rgba(253,160,133,0.4); }

    /* 区块标题 */
    .section-title {
        font-size: 1.6em;
        font-weight: 700;
        border-left: 4px solid #1a73e8;
        padding-left: 12px;
        margin: 32px 0 16px;
    }

    /* 动态渐变分割线 */
    .gradient-divider {
        height: 3px;
        background: linear-gradient(90deg, #1a73e8, #ea4335, #fbbc04, #34a853);
        border-radius: 2px;
        margin: 24px 0;
    }

    /* 数据表 hover */
    .stDataFrame table { transition: all 0.2s; }
    .stDataFrame tr:hover { background-color: #e8f0fe !important; }

    /* 侧边栏 */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    except:
        df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()
    return df


def render_kpi_cards(df):
    """动态 KPI 指标卡片"""
    price_col = 'price_vehicle' if 'price_vehicle' in df.columns else 'price_total'

    cols = st.columns(4)
    kpis = [
        ("🚗", f"{len(df):,}", "台车在售", ""),
        ("💰", f"{df[price_col].mean():.1f}", "万円 均价", "kpi-red"),
        ("🏭", f"{df['brand_clean'].nunique() if 'brand_clean' in df.columns else 0}", "个品牌", "kpi-green"),
        ("🇯🇵", f"{(df['vehicle_class']=='軽自動車(K-car)').mean()*100:.1f}%" if 'vehicle_class' in df.columns else "—", "K-car占比", "kpi-gold"),
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
    """价格分布 — 交互式直方图 + 动态区间统计"""
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & (df[price_col] < 2000)]

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.histogram(df_p, x=price_col, nbins=60,
                           title="价格分布直方图",
                           color_discrete_sequence=['#1a73e8'],
                           opacity=0.75)
        fig.add_vline(x=df_p[price_col].mean(), line_dash="dash", line_color="#ea4335",
                      annotation_text=f"均值: {df_p[price_col].mean():.0f}万円")
        fig.add_vline(x=df_p[price_col].median(), line_dash="dot", line_color="#34a853",
                      annotation_text=f"中位数: {df_p[price_col].median():.0f}万円")
        fig.update_layout(xaxis_title="价格 (万円)", yaxis_title="车辆数",
                         hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 价格区间动态统计
        st.markdown("#### 📊 价格区间统计")
        price_bins = [0, 50, 100, 150, 200, 300, 500, 5000]
        labels = ['<50', '50-100', '100-150', '150-200', '200-300', '300-500', '500+']
        df_p2 = df_p.copy()
        df_p2['区间'] = pd.cut(df_p2[price_col], bins=price_bins, labels=labels)
        bin_stats = df_p2.groupby('区间').agg(
            数量=('price_vehicle', 'count'),
            均价=('price_vehicle', 'mean'),
        )

        for label, row in bin_stats.iterrows():
            pct = row['数量'] / len(df_p) * 100
            bar_color = "🟢" if pct > 20 else "🔵" if pct > 10 else "⚪"
            st.markdown(f"**{bar_color} {label}万円**: {int(row['数量'])}台 ({pct:.1f}%) · 均价{row['均价']:.0f}万円")


def chart_brand_analysis(df):
    """品牌分析 — 动态箱线图 + 市场份额"""
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['brand_clean'].notna()]

    # 品牌选择器
    brand_counts = df_p['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()

    tab1, tab2 = st.tabs(["📈 价格区间对比", "🥧 市场份额"])

    with tab1:
        selected = st.multiselect("选择品牌（最多8个）", top_brands,
                                   default=top_brands[:8], key='brand_box')

        if selected:
            df_sel = df_p[df_p['brand_clean'].isin(selected)]
            fig = go.Figure()
            for brand in selected:
                brand_data = df_sel[df_sel['brand_clean'] == brand][price_col]
                fig.add_trace(go.Box(y=brand_data, name=brand, boxpoints='outliers',
                                     marker_size=3, line_width=2))
            fig.update_layout(title="品牌价格区间箱线图",
                             yaxis_title="价格 (万円)",
                             showlegend=True, height=500)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # 旭日图
        df_p2 = df_p.copy()
        df_p2['origin'] = df_p2['brand_clean'].apply(
            lambda b: '国産(日本)' if b in ['Toyota','Honda','Nissan','Suzuki','Daihatsu','Mazda','Subaru','Mitsubishi','Lexus'] else '輸入車(进口)'
        )

        # 按起源→品牌 构建层级
        sunburst_data = df_p2.groupby(['origin', 'brand_clean']).size().reset_index(name='count')

        fig = px.sunburst(sunburst_data, path=['origin', 'brand_clean'], values='count',
                          title="品牌市场构成 — 旭日图",
                          color='count', color_continuous_scale='RdYlBu_r')
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)


def chart_vehicle_class(df):
    """车辆级别分析 — K-car 专题"""
    price_col = 'price_vehicle'

    tab1, tab2 = st.tabs(["📊 级别对比", "🚗 K-car 专题"])

    with tab1:
        df_p = df[(df[price_col] > 0) & df['vehicle_class'].notna()]

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=("各级别数量占比", "各级别均价对比"))

        # 饼图
        class_counts = df_p['vehicle_class'].value_counts()
        fig.add_trace(go.Pie(labels=class_counts.index, values=class_counts.values,
                             hole=0.4, marker_colors=px.colors.qualitative.Set2), row=1, col=1)

        # 柱状图
        class_avg = df_p.groupby('vehicle_class')[price_col].mean().reindex(class_counts.index)
        fig.add_trace(go.Bar(x=class_avg.index, y=class_avg.values,
                            marker_color=['#16a34a','#1a73e8','#fbbc04','#ea4335','#8b5cf6']),
                      row=1, col=2)

        fig.update_layout(height=450, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### 🇯🇵 軽自動車 (K-car) — 日本独有的汽车文化")
        st.markdown("""
        K-car 是日本特有的微型车分类，排量 ≤660cc，享受**减税、保险优惠**和**无需停车证明**等政策。
        是日本城市通勤和狭窄街道的完美解决方案。
        """)

        df_kcar = df[(df['vehicle_class'] == '軽自動車(K-car)') & (df[price_col] > 0)]

        if len(df_kcar) > 0:
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("K-car 数量", f"{len(df_kcar)}台")
            with k2: st.metric("均价", f"{df_kcar[price_col].mean():.1f}万円")
            with k3: st.metric("最低价", f"{df_kcar[price_col].min():.1f}万円")
            with k4: st.metric("市场占比", f"{len(df_kcar)/len(df)*100:.1f}%")

            # K-car 品牌分布
            kcar_brands = df_kcar['brand_clean'].value_counts().head(6)
            fig = px.bar(x=kcar_brands.index, y=kcar_brands.values,
                        title="K-car 品牌分布",
                        color=kcar_brands.values, color_continuous_scale='Greens',
                        labels={'x':'品牌','y':'数量'})
            st.plotly_chart(fig, use_container_width=True)


def chart_year_trend(df):
    """年式-价格动态趋势"""
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)]

    year_stats = df_p.groupby('year_ce').agg(
        avg_price=(price_col, 'mean'),
        median_price=(price_col, 'median'),
        count=(price_col, 'count'),
        p25=(price_col, lambda x: x.quantile(0.25)),
        p75=(price_col, lambda x: x.quantile(0.75)),
    ).reset_index()

    fig = go.Figure()

    # P25-P75 区间填充
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p75'],
        mode='lines', line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['p25'],
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(26,115,232,0.15)', name='P25-P75区间'
    ))

    # 均价线
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['avg_price'],
        mode='lines+markers', name='均价',
        line=dict(color='#1a73e8', width=3),
        marker=dict(size=8, color=year_stats['count'], colorscale='YlOrRd',
                    showscale=True, colorbar=dict(title='数据量'))
    ))

    # 中位数线
    fig.add_trace(go.Scatter(
        x=year_stats['year_ce'], y=year_stats['median_price'],
        mode='lines+markers', name='中位数',
        line=dict(color='#34a853', width=2, dash='dot')
    ))

    fig.update_layout(
        title="年式-价格动态趋势（P25-P75区间 + 数据量热力）",
        xaxis_title="生产年份", yaxis_title="价格 (万円)",
        hovermode="x unified", height=500
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_prefecture(df):
    """地区分析"""
    price_col = 'price_vehicle'
    df_p = df[(df[price_col] > 0) & df['prefecture'].notna()]

    pref_stats = df_p.groupby('prefecture').agg(
        avg_price=(price_col, 'mean'),
        count=(price_col, 'count'),
    ).reset_index().sort_values('avg_price', ascending=False)

    fig = px.bar(pref_stats, x='prefecture', y='avg_price',
                title="各都道府县均价排名",
                color='count', color_continuous_scale='Viridis',
                labels={'prefecture':'都道府县','avg_price':'均价(万円)','count':'数据量'})
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def data_explorer(df):
    """数据探索器"""
    display_cols = ['brand_clean', 'model', 'price_vehicle', 'year_ce', 'mileage_wan_km',
                    'displacement_cc', 'vehicle_class', 'prefecture', 'brand_type']
    available = [c for c in display_cols if c in df.columns]

    # 筛选
    col1, col2 = st.columns(2)
    with col1:
        brands = sorted(df['brand_clean'].dropna().unique()) if 'brand_clean' in df.columns else []
        sel_brand = st.multiselect("品牌筛选", brands, default=[], key='exp_brand')
    with col2:
        if 'vehicle_class' in df.columns:
            classes = sorted(df['vehicle_class'].dropna().unique())
            sel_class = st.multiselect("级别筛选", classes, default=[], key='exp_class')
        else:
            sel_class = []

    df_exp = df[available].copy()
    if sel_brand:
        df_exp = df_exp[df_exp['brand_clean'].isin(sel_brand)]
    if sel_class:
        df_exp = df_exp[df_exp['vehicle_class'].isin(sel_class)]

    st.dataframe(df_exp, use_container_width=True, height=400)
    st.caption(f"显示 {len(df_exp)} / {len(df)} 条记录")


def main():
    # 标题
    st.markdown("""
    <div style="text-align:center; padding: 16px 0;">
        <h1 style="font-size:2.4em; margin:0;">🇯🇵 日本二手车市场智能分析</h1>
        <p style="color:#5f6368; font-size:1.1em; margin:8px 0 0;">
            动态监控汽车价格 · 品牌分布 · 市场变化趋势 · 数据源: <a href="https://www.carsensor.net/usedcar/">carsensor.net</a>
        </p>
    </div>
    <div class="gradient-divider"></div>
    """, unsafe_allow_html=True)

    df = load_data()
    if len(df) == 0:
        st.warning("⚠️ 暂无数据，请先运行爬虫: `python src/crawler.py`")
        return

    # ====== 侧边栏 ======
    with st.sidebar:
        st.markdown("## 🔍 全局筛选")
        price_col = 'price_vehicle'

        # 价格范围
        if price_col in df.columns:
            price_min, price_max = float(df[price_col].min()), float(df[price_col].max())
            price_range = st.slider("价格范围 (万円)", price_min, price_max,
                                    (price_min, price_max), step=10.0)
            df = df[(df[price_col] >= price_range[0]) & (df[price_col] <= price_range[1])]

        # 年式范围
        if 'year_ce' in df.columns:
            year_min, year_max = int(df['year_ce'].min()), int(df['year_ce'].max())
            year_range = st.slider("年式范围", year_min, year_max, (year_min, year_max))
            df = df[(df['year_ce'] >= year_range[0]) & (df['year_ce'] <= year_range[1])]

        # 品牌类型
        if 'brand_type' in df.columns:
            brand_types = df['brand_type'].unique()
            sel_types = st.multiselect("品牌类型", brand_types, default=list(brand_types))
            df = df[df['brand_type'].isin(sel_types)]

        st.markdown("---")
        st.caption(f"筛选后: {len(df)} 台车")

    # ====== KPI ======
    render_kpi_cards(df)
    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # ====== 标签页 ======
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 价格分析", "🏭 品牌分析", "🚙 车辆级别",
        "📈 年式趋势", "🗺️ 地区分析", "📋 数据探索"
    ])

    with tab1:
        st.markdown('<div class="section-title">价格分布与区间统计</div>', unsafe_allow_html=True)
        chart_price_distribution(df)

    with tab2:
        st.markdown('<div class="section-title">品牌价格区间与市场份额</div>', unsafe_allow_html=True)
        chart_brand_analysis(df)

    with tab3:
        st.markdown('<div class="section-title">车辆级别分析 — K-car专题</div>', unsafe_allow_html=True)
        chart_vehicle_class(df)

    with tab4:
        st.markdown('<div class="section-title">年式-价格动态趋势</div>', unsafe_allow_html=True)
        chart_year_trend(df)

    with tab5:
        st.markdown('<div class="section-title">地区价格分析</div>', unsafe_allow_html=True)
        chart_prefecture(df)

    with tab6:
        st.markdown('<div class="section-title">数据探索器</div>', unsafe_allow_html=True)
        data_explorer(df)

    # 页脚
    st.markdown("""
    <div class="gradient-divider"></div>
    <div style="text-align:center; color:#5f6368; font-size:0.9em; padding:16px 0;">
        🇯🇵 日本二手车市场智能分析系统 · 数据源: carsensor.net · 技术栈: Playwright + Pandas + SQLite + Prophet + Streamlit
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

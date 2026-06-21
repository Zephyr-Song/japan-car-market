"""
Streamlit 可视化 Dashboard
参考德国汽车市场分析系统方法论
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_PATH = "data/japan_car_market.db"

st.set_page_config(
    page_title="🇯🇵 日本汽车市场智能分析系统",
    page_icon="🚗",
    layout="wide"
)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    except:
        df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()
    return df


def main():
    st.title("🇯🇵 日本汽车市场智能分析系统")
    st.caption("数据源: carsensor.net | 技术栈: Playwright + Pandas + SQLite + Prophet + Streamlit")

    df = load_data()

    if len(df) == 0:
        st.warning("⚠️ 暂无数据，请先运行爬虫: `python src/crawler.py`")
        return

    # ===== 侧边栏 =====
    st.sidebar.header("🔍 筛选条件")

    # 品牌筛选
    brands = sorted(df['brand_clean'].unique()) if 'brand_clean' in df.columns else sorted(df['brand'].dropna().unique())
    selected_brands = st.sidebar.multiselect("品牌", brands, default=brands[:5])

    # 价格范围
    price_col = 'price_vehicle' if 'price_vehicle' in df.columns else 'price_total'
    if price_col in df.columns:
        price_min, price_max = float(df[price_col].min()), float(df[price_col].max())
        price_range = st.sidebar.slider("价格范围 (万円)", price_min, price_max, (price_min, price_max))

    # 车辆级别
    if 'vehicle_class' in df.columns:
        classes = df['vehicle_class'].unique()
        selected_classes = st.sidebar.multiselect("车辆级别", classes, default=list(classes))

    # ===== 主页 =====

    # 概览指标
    st.header("📊 市场概览")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总车辆数", f"{len(df):,}")
    with col2:
        if price_col in df.columns:
            st.metric("平均价格", f"{df[price_col].mean():.1f} 万円")
    with col3:
        if 'brand_clean' in df.columns:
            st.metric("品牌数量", f"{df['brand_clean'].nunique()}")
    with col4:
        if 'prefecture' in df.columns:
            st.metric("覆盖地区", f"{df['prefecture'].nunique()}")

    st.divider()

    # 价格分布
    st.header("💰 价格分析")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("价格分布直方图")
        if price_col in df.columns:
            df_plot = df[(df[price_col] > 0) & (df[price_col] < 5000)]
            fig = px.histogram(df_plot, x=price_col, nbins=50,
                             title="二手车价格分布",
                             labels={price_col: "价格 (万円)"},
                             color_discrete_sequence=['steelblue'])
            fig.add_vline(x=df_plot[price_col].mean(), line_dash="dash",
                         line_color="red", annotation_text=f"平均: {df_plot[price_col].mean():.0f}万円")
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("品牌平均价格 (Top 15)")
        if 'brand_clean' in df.columns and price_col in df.columns:
            brand_avg = df[df[price_col] > 0].groupby('brand_clean')[price_col].agg(
                平均价格='mean', 数据量='count'
            ).sort_values('平均价格', ascending=False)
            brand_avg = brand_avg[brand_avg['数据量'] >= 3].head(15)

            fig = px.bar(brand_avg, x=brand_avg.index, y='平均价格',
                        title="品牌平均价格对比",
                        labels={'x': '品牌', '平均价格': '平均价格 (万円)'},
                        color='平均价格', color_continuous_scale='OrRd')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 车辆级别分析（日本特色）
    st.header("🚙 车辆级别分析")
    if 'vehicle_class' in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            class_counts = df['vehicle_class'].value_counts()
            fig = px.pie(values=class_counts.values, names=class_counts.index,
                        title="车辆级别占比",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if price_col in df.columns:
                class_avg = df[df[price_col] > 0].groupby('vehicle_class')[price_col].mean().sort_values()
                fig = px.bar(x=class_avg.index, y=class_avg.values,
                           title="各级别平均价格",
                           labels={'x': '级别', 'y': '平均价格 (万円)'},
                           color=class_avg.values, color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 地区分析
    st.header("🗺️ 地区分析")
    if 'prefecture' in df.columns and price_col in df.columns:
        pref_stats = df[df[price_col] > 0].groupby('prefecture')[price_col].agg(
            平均价格='mean', 数据量='count'
        ).sort_values('平均价格', ascending=False).head(15)

        fig = px.bar(pref_stats, x=pref_stats.index, y='平均价格',
                    title="各都道府县平均价格 (Top 15)",
                    labels={'x': '都道府县', '平均价格': '平均价格 (万円)'},
                    color='数据量', color_continuous_scale='Viridis')
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 数据表
    st.header("📋 数据浏览")
    display_cols = ['brand_clean', 'model', 'price_vehicle', 'year_ce', 'mileage_wan_km',
                    'displacement_cc', 'vehicle_class', 'prefecture']
    available_cols = [c for c in display_cols if c in df.columns]
    if available_cols:
        st.dataframe(df[available_cols].head(100), use_container_width=True)

    st.caption("© Japan Car Market Analysis System | Powered by Playwright + Pandas + Prophet + Streamlit")


if __name__ == "__main__":
    main()

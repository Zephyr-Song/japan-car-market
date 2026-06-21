"""
数据分析模块
参考德国汽车市场分析系统方法论
"""

import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "data/japan_car_market.db"
OUTPUT_DIR = "data/analysis"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'MS Gothic', 'Yu Gothic']
plt.rcParams['axes.unicode_minus'] = False


def load_clean_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    conn.close()
    return df


def analyze_price_statistics(df):
    """价格统计分析"""
    print("\n=== 价格统计分析 ===")
    stats = df['price_vehicle'].describe()
    print(stats.to_string())

    # 最低/平均/最高价格
    min_price = df.loc[df['price_vehicle'].idxmin()]
    max_price = df.loc[df['price_vehicle'].idxmax()]
    print(f"\n最低价: {min_price['price_vehicle']}万円 | {min_price['brand_clean']} {min_price['model']}")
    print(f"最高价: {max_price['price_vehicle']}万円 | {max_price['brand_clean']} {max_price['model']}")

    return stats


def analyze_brand_comparison(df):
    """品牌对比分析"""
    print("\n=== 品牌平均价格对比 ===")
    # 过滤有效价格数据
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]

    brand_avg = df_price.groupby('brand_clean')['price_vehicle'].agg(
        平均价格='mean',
        数据量='count'
    ).sort_values('平均价格', ascending=False)

    # 只保留数据量>=5的品牌
    brand_avg = brand_avg[brand_avg['数据量'] >= 5]
    print(brand_avg.head(20).to_string())

    return brand_avg


def analyze_vehicle_class(df):
    """车辆级别分析（K-car vs 普通车）"""
    print("\n=== 车辆级别价格分析 ===")
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]

    class_stats = df_price.groupby('vehicle_class')['price_vehicle'].agg(
        平均价格='mean',
        中位数='median',
        数据量='count'
    ).sort_values('平均价格')
    print(class_stats.to_string())

    return class_stats


def analyze_by_prefecture(df):
    """按都道府县分析"""
    print("\n=== 按地区平均价格 ===")
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & df['prefecture'].notna()]

    pref_stats = df_price.groupby('prefecture')['price_vehicle'].agg(
        平均价格='mean',
        数据量='count'
    ).sort_values('平均价格', ascending=False)

    print(pref_stats.head(15).to_string())
    return pref_stats


def plot_price_distribution(df):
    """绘制价格分布图"""
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & (df['price_vehicle'] < 5000)]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(df_price['price_vehicle'], bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax.set_xlabel('价格 (万円)', fontsize=12)
    ax.set_ylabel('车辆数量', fontsize=12)
    ax.set_title('日本二手车价格分布', fontsize=14)
    ax.axvline(df_price['price_vehicle'].mean(), color='red', linestyle='--',
                label=f'平均价格: {df_price["price_vehicle"].mean():.1f}万円')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/price_distribution.png', dpi=150)
    plt.close()
    print(f"✅ 价格分布图已保存: {OUTPUT_DIR}/price_distribution.png")


def plot_brand_avg_price(df):
    """绘制品牌平均价格对比图"""
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]
    brand_avg = df_price.groupby('brand_clean')['price_vehicle'].agg(
        平均价格='mean', 数据量='count'
    ).sort_values('平均价格', ascending=False)
    brand_avg = brand_avg[brand_avg['数据量'] >= 5].head(15)

    fig, ax = plt.subplots(figsize=(14, 7))
    bars = ax.bar(range(len(brand_avg)), brand_avg['平均价格'], color='coral', edgecolor='black')
    ax.set_xticks(range(len(brand_avg)))
    ax.set_xticklabels(brand_avg.index, rotation=45, ha='right')
    ax.set_xlabel('品牌', fontsize=12)
    ax.set_ylabel('平均价格 (万円)', fontsize=12)
    ax.set_title('日本二手车市场：品牌平均价格对比 (Top 15)', fontsize=14)
    ax.grid(axis='y', alpha=0.3)

    # 标注数值
    for i, (bar, (brand, row)) in enumerate(zip(bars, brand_avg.iterrows())):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f"{row['平均价格']:.0f}", ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/brand_avg_price.png', dpi=150)
    plt.close()
    print(f"✅ 品牌价格对比图已保存: {OUTPUT_DIR}/brand_avg_price.png")


def plot_vehicle_class(df):
    """绘制车辆级别分布图"""
    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]

    class_counts = df_price['vehicle_class'].value_counts()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 数量分布
    ax1.bar(range(len(class_counts)), class_counts.values, color='skyblue', edgecolor='black')
    ax1.set_xticks(range(len(class_counts)))
    ax1.set_xticklabels(class_counts.index, rotation=15, ha='right')
    ax1.set_ylabel('车辆数量')
    ax1.set_title('日本二手车：车辆级别数量分布')
    ax1.grid(axis='y', alpha=0.3)

    # 平均价格
    class_avg = df_price.groupby('vehicle_class')['price_vehicle'].mean().reindex(class_counts.index)
    ax2.bar(range(len(class_avg)), class_avg.values, color='lightcoral', edgecolor='black')
    ax2.set_xticks(range(len(class_avg)))
    ax2.set_xticklabels(class_avg.index, rotation=15, ha='right')
    ax2.set_ylabel('平均价格 (万円)')
    ax2.set_title('日本二手车：各级别平均价格')
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/vehicle_class_analysis.png', dpi=150)
    plt.close()
    print(f"✅ 车辆级别分析图已保存: {OUTPUT_DIR}/vehicle_class_analysis.png")


def plot_year_distribution(df):
    """绘制年式分布图"""
    df_year = df[df['year_ce'].notna() & (df['year_ce'] >= 1990)]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.hist(df_year['year_ce'], bins=30, color='mediumseagreen', edgecolor='black', alpha=0.8)
    ax.set_xlabel('生产年份', fontsize=12)
    ax.set_ylabel('车辆数量', fontsize=12)
    ax.set_title('日本二手车：年式分布', fontsize=14)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/year_distribution.png', dpi=150)
    plt.close()
    print(f"✅ 年式分布图已保存: {OUTPUT_DIR}/year_distribution.png")


def main():
    print("=" * 60)
    print("日本汽车市场数据分析系统 - 数据分析模块")
    print("=" * 60)

    df = load_clean_data()
    print(f"\n加载清洗后数据: {len(df)} 条记录")

    # 统计分析
    analyze_price_statistics(df)
    analyze_brand_comparison(df)
    analyze_vehicle_class(df)
    analyze_by_prefecture(df)

    # 可视化
    print("\n=== 生成可视化图表 ===")
    plot_price_distribution(df)
    plot_brand_avg_price(df)
    plot_vehicle_class(df)
    plot_year_distribution(df)

    print(f"\n✅ 分析完成！图表保存至: {OUTPUT_DIR}/")
    print(f"下一步: 运行 python src/forecast.py 进行趋势预测")
    print(f"        或运行 streamlit run src/dashboard.py 启动可视化系统")


if __name__ == "__main__":
    main()

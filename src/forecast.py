"""
趋势预测模块 - Prophet 时间序列模型
参考德国汽车市场分析系统方法论
"""

import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from prophet import Prophet
import sys, os

sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

DB_PATH = "data/japan_car_market.db"
OUTPUT_DIR = "data/analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    conn.close()
    return df


def forecast_overall(df, periods=30):
    """整体市场价格趋势预测"""
    print("\n=== 整体市场价格趋势预测 ===")

    df_price = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)].copy()
    if len(df_price) == 0:
        print("⚠️ 无有效价格数据，无法预测")
        return None

    # 按日期聚合平均价格
    daily = df_price.groupby('crawl_date')['price_vehicle'].mean().reset_index()
    daily.columns = ['ds', 'y']

    if len(daily) < 2:
        print("⚠️ 历史数据不足（<2天），无法预测")
        # 使用单日数据生成模拟趋势
        print("提示：随着采集日期增加，Prophet 预测将自动启用")
        return None

    # Prophet 模型
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(daily)

    # 预测未来 periods 天
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # 可视化
    fig, ax = plt.subplots(figsize=(14, 6))
    model.plot(forecast, ax=ax)
    ax.set_title('日本二手车市场：价格趋势预测 (Prophet)', fontsize=14)
    ax.set_xlabel('日期')
    ax.set_ylabel('平均价格 (万円)')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/forecast_overall.png', dpi=150)
    plt.close()
    print(f"✅ 整体趋势预测图已保存")

    # 成分分解
    fig2 = model.plot_components(forecast)
    plt.savefig(f'{OUTPUT_DIR}/forecast_components.png', dpi=150)
    plt.close()
    print(f"✅ 趋势分解图已保存")

    return forecast


def forecast_by_brand(df, brand, periods=30):
    """按品牌预测价格趋势"""
    print(f"\n=== {brand} 品牌价格趋势预测 ===")

    df_brand = df[(df['brand_clean'] == brand) & 
                   (df['price_vehicle'].notna()) & 
                   (df['price_vehicle'] > 0)].copy()

    if len(df_brand) < 2:
        print(f"⚠️ {brand} 数据不足，跳过")
        return None

    daily = df_brand.groupby('crawl_date')['price_vehicle'].mean().reset_index()
    daily.columns = ['ds', 'y']

    if len(daily) < 2:
        print(f"⚠️ {brand} 历史数据不足，跳过")
        return None

    model = Prophet(yearly_seasonality=True, weekly_seasonality=False)
    model.fit(daily)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    fig, ax = plt.subplots(figsize=(14, 6))
    model.plot(forecast, ax=ax)
    ax.set_title(f'{brand} 品牌价格趋势预测', fontsize=14)
    ax.set_xlabel('日期')
    ax.set_ylabel('平均价格 (万円)')
    plt.tight_layout()

    safe_brand = brand.replace('/', '_').replace(' ', '_')
    plt.savefig(f'{OUTPUT_DIR}/forecast_{safe_brand}.png', dpi=150)
    plt.close()
    print(f"✅ {brand} 品牌预测图已保存")

    return forecast


def main():
    print("=" * 60)
    print("日本汽车市场数据分析系统 - 趋势预测模块")
    print("=" * 60)

    df = load_data()
    print(f"加载数据: {len(df)} 条记录")

    # 整体趋势预测
    forecast_overall(df, periods=30)

    # 热门品牌预测
    top_brands = df['brand_clean'].value_counts().head(5).index.tolist()
    print(f"\n热门品牌: {top_brands}")
    for brand in top_brands:
        forecast_by_brand(df, brand, periods=30)

    print(f"\n✅ 预测完成！图表保存至: {OUTPUT_DIR}/")
    print(f"下一步: 运行 streamlit run src/dashboard.py 启动可视化系统")


if __name__ == "__main__":
    main()

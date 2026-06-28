"""
价格预测模块 v2 - 截面回归模型 (P0 修复)
==========================================
问题: Prophet 需要连续时间序列, 但当前只有单日快照数据, 无法使用。
修复: 改用截面回归模型, 用车辆特征预测价格, 对二手车场景更实用。

特征工程:
  - vehicle_age: 车龄 (2026 - 年式)
  - mileage_numeric: 里程 (万km → 数值)
  - displacement_numeric: 排量 (CC/L → 数值)
  - transmission_auto: 是否自动挡 (二值)
  - brand_*: 品牌 one-hot
  - category_*: 分类 one-hot

模型: RandomForestRegressor (鲁棒, 处理非线性关系)
输出: 特征重要性 + 示例预测 + 模型评估
"""

import sqlite3
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

DB_PATH = "data/japan_car_market.db"
OUTPUT_DIR = "data/analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 日本年号 → 西元
def era_to_ce(year_str):
    if not year_str or not isinstance(year_str, str):
        return None
    m = re.match(r'(\d{4})', year_str)
    if m:
        y = int(m.group(1))
        if 1900 <= y <= 2100:
            return y
    # 令和 R0N = 2018+N
    m = re.search(r'R(\d{2})', year_str)
    if m:
        return 2018 + int(m.group(1))
    # 平成 H0N = 1988+N
    m = re.search(r'H(\d{2})', year_str)
    if m:
        return 1988 + int(m.group(1))
    # 昭和 S0N = 1925+N
    m = re.search(r'S(\d{2})', year_str)
    if m:
        return 1925 + int(m.group(1))
    return None


def parse_mileage(mileage_str):
    if not mileage_str or not isinstance(mileage_str, str):
        return None
    m = re.search(r'([\d.]+)\s*万\s*km', mileage_str)
    if m:
        return float(m.group(1)) * 10000
    m = re.search(r'([\d.]+)\s*km', mileage_str)
    if m:
        return float(m.group(1))
    return None


def parse_displacement(disp_str):
    if not disp_str or not isinstance(disp_str, str):
        return None
    m = re.search(r'([\d.]+)\s*CC', disp_str, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r'([\d.]+)\s*L', disp_str, re.I)
    if m:
        return float(m.group(1)) * 1000
    return None


def load_and_featurize():
    """加载数据并做特征工程"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars", conn)
    conn.close()

    print(f"原始数据: {len(df)} 条")

    if len(df) == 0:
        print("⚠️ 无数据, 请先运行 crawler.py")
        return None

    # 过滤异常价格
    df = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]
    df = df[df['price_vehicle'] <= 5000]  # 过滤 >5000万円
    print(f"过滤后: {len(df)} 条")

    # 特征工程
    df['vehicle_age'] = df['year'].apply(era_to_ce)
    df['vehicle_age'] = df['vehicle_age'].apply(lambda y: 2026 - y if y else None)
    df = df[df['vehicle_age'].notna() & (df['vehicle_age'] >= 0) & (df['vehicle_age'] <= 50)]

    df['mileage_numeric'] = df['mileage'].apply(parse_mileage)
    df['displacement_numeric'] = df['displacement'].apply(parse_displacement)

    df['transmission_auto'] = df['transmission'].apply(
        lambda x: 1 if isinstance(x, str) and ('AT' in x or 'CVT' in x or '自' in x) else 0
    )

    print(f"特征工程后: {len(df)} 条")
    print(f"  有车龄: {df['vehicle_age'].notna().sum()}")
    print(f"  有里程: {df['mileage_numeric'].notna().sum()}")
    print(f"  有排量: {df['displacement_numeric'].notna().sum()}")

    return df


def train_price_model(df):
    """训练价格预测模型"""
    print("\n=== 训练价格预测模型 (RandomForest) ===")

    # 准备特征
    feature_cols = ['vehicle_age', 'mileage_numeric', 'displacement_numeric', 'transmission_auto']
    categorical_cols = ['brand', 'category']

    # 只保留有足够数据的品牌/分类
    brand_counts = df['brand'].value_counts()
    top_brands = brand_counts[brand_counts >= 10].index.tolist()
    df_model = df[df['brand'].isin(top_brands)].copy()

    cat_counts = df_model['category'].value_counts()
    top_cats = cat_counts[cat_counts >= 10].index.tolist()
    df_model = df_model[df_model['category'].isin(top_cats)].copy()

    print(f"  建模数据: {len(df_model)} 条")
    print(f"  品牌数: {len(top_brands)} (出现≥10次)")
    print(f"  分类数: {len(top_cats)}")

    if len(df_model) < 50:
        print("⚠️ 数据量不足 (需要≥50条), 跳过训练")
        return None, None, None

    # 目标变量
    y = df_model['price_vehicle']

    # 分类特征 one-hot
    X_cat = df_model[['brand', 'category']]
    cat_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_cat_encoded = cat_encoder.fit_transform(X_cat)

    # 数值特征
    X_num = df_model[feature_cols].fillna(0).values

    # 合并特征
    X = np.hstack([X_num, X_cat_encoded])

    # 训练/测试分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 模型
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # 评估
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\n  模型评估:")
    print(f"    MAE:  {mae:.1f} 万円")
    print(f"    RMSE: {rmse:.1f} 万円")
    print(f"    R²:   {r2:.3f}")

    # 特征重要性
    feature_names = feature_cols + list(cat_encoder.get_feature_names_out(['brand', 'category']))
    importances = model.feature_importances_
    top_n = min(20, len(feature_names))
    top_idx = np.argsort(importances)[-top_n:]

    print(f"\n  特征重要性 (Top {top_n}):")
    for i in top_idx[::-1]:
        print(f"    {feature_names[i]}: {importances[i]:.3f}")

    # 可视化特征重要性
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(range(top_n), importances[top_idx])
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feature_names[i] for i in top_idx])
    ax.set_xlabel('特征重要性')
    ax.set_title('二手车价格预测 - 特征重要性 (RandomForest)')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/feature_importance.png', dpi=150)
    plt.close()
    print(f"✅ 特征重要性图已保存: {OUTPUT_DIR}/feature_importance.png")

    return model, cat_encoder, feature_names


def example_predictions(df, model, cat_encoder, feature_names):
    """示例预测: 随机选几辆车, 对比实际价格和预测价格"""
    print("\n=== 示例预测 ===")

    feature_cols = ['vehicle_age', 'mileage_numeric', 'displacement_numeric', 'transmission_auto']
    sample = df.sample(min(10, len(df)), random_state=42)

    results = []
    for _, row in sample.iterrows():
        # 构造特征向量
        X_num = np.array([[row['vehicle_age'] or 0, row['mileage_numeric'] or 0,
                           row['displacement_numeric'] or 0, row['transmission_auto']]])
        X_cat = cat_encoder.transform([[row['brand'], row['category']]])
        X = np.hstack([X_num, X_cat])
        pred = model.predict(X)[0]

        results.append({
            'brand': row['brand'],
            'model': row['model'][:30],
            'year': row['year'],
            'mileage': row['mileage'],
            'actual': row['price_vehicle'],
            'predicted': round(pred, 1),
            'diff': round(row['price_vehicle'] - pred, 1)
        })

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # 保存
    results_df.to_csv(f'{OUTPUT_DIR}/example_predictions.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 示例预测已保存: {OUTPUT_DIR}/example_predictions.csv")

    return results_df


def depreciation_curve(df):
    """绘制折旧曲线: 车龄 vs 平均价格 (按品牌)"""
    print("\n=== 计算折旧曲线 ===")

    df_curve = df[(df['vehicle_age'].notna()) & (df['price_vehicle'].notna())].copy()
    df_curve = df_curve[df_curve['price_vehicle'] <= 2000]  # 过滤异常

    top_brands = df_curve['brand'].value_counts().head(6).index.tolist()

    fig, ax = plt.subplots(figsize=(12, 7))

    for brand in top_brands:
        df_b = df_curve[df_curve['brand'] == brand]
        if len(df_b) < 10:
            continue
        grouped = df_b.groupby('vehicle_age')['price_vehicle'].agg(['mean', 'count']).reset_index()
        grouped = grouped[grouped['count'] >= 3]  # 至少3台车
        if len(grouped) >= 2:
            ax.plot(grouped['vehicle_age'], grouped['mean'], marker='o', label=brand, linewidth=2)

    ax.set_xlabel('车龄 (年)')
    ax.set_ylabel('平均价格 (万円)')
    ax.set_title('日本二手车市场: 主要品牌折旧曲线')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/depreciation_curve.png', dpi=150)
    plt.close()
    print(f"✅ 折旧曲线已保存: {OUTPUT_DIR}/depreciation_curve.png")


def main():
    print("=" * 60)
    print("日本汽车市场 - 价格预测模块 v2 (截面回归)")
    print("=" * 60)

    df = load_and_featurize()
    if df is None or len(df) == 0:
        return

    model, cat_encoder, feature_names = train_price_model(df)

    if model is not None:
        example_predictions(df, model, cat_encoder, feature_names)

    depreciation_curve(df)

    print(f"\n✅ 分析完成! 结果保存至: {OUTPUT_DIR}/")
    print(f"   特征重要性: feature_importance.png")
    print(f"   折旧曲线:   depreciation_curve.png")
    print(f"   示例预测:   example_predictions.csv")


if __name__ == "__main__":
    main()

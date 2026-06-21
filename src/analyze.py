"""
数据分析模块 - 高级可视化版
生成6张专业分析图表 + 1张综合仪表盘
"""

import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys, os

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "data/japan_car_market.db"
OUTPUT_DIR = "data/analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 专业配色方案
COLORS = {
    'primary': '#1a73e8',
    'secondary': '#ea4335',
    'accent': '#fbbc04',
    'success': '#34a853',
    'dark': '#202124',
    'gray': '#5f6368',
    'light': '#f8f9fa',
    # 品牌色系
    'toyota': '#eb0a1e',
    'honda': '#cc0000',
    'nissan': '#c3002f',
    'luxury': '#8b5cf6',
    'import': '#0891b2',
    'kcar': '#16a34a',
}

BRAND_COLORS = {
    'Mercedes-Benz': '#333333', 'BMW': '#0066b1', 'Jeep': '#5c8a2f',
    'Audi': '#bb0a30', 'Lexus': '#1a1a1a', 'Volvo': '#003057',
    'Peugeot': '#002f6c', 'MINI': '#9e1b32', 'VW': '#001e50',
    'Mitsubishi': '#e60012', 'Subaru': '#0d53a0', 'Toyota': '#eb0a1e',
    'Honda': '#cc0000', 'Nissan': '#c3002f', 'Suzuki': '#e4002b',
    'Mazda': '#910047', 'Daihatsu': '#d7001e', 'Fiat': '#8b0000',
}

plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'Yu Gothic'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#ffffff',
    'axes.facecolor': '#f8f9fa',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': '#cccccc',
})


def load_clean_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM used_cars_cleaned", conn)
    conn.close()
    return df


def plot_1_price_distribution(df):
    """图1: 价格分布 - 双轴直方图 + 累积分布"""
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & (df['price_vehicle'] < 2000)]

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # 直方图
    n, bins, patches = ax1.hist(df_p['price_vehicle'], bins=60, alpha=0.75,
                                 color=COLORS['primary'], edgecolor='white', linewidth=0.5)

    # 按价格区间着色
    for patch, left_edge in zip(patches, bins[:-1]):
        if left_edge < 100:
            patch.set_facecolor(COLORS['success'])
        elif left_edge < 200:
            patch.set_facecolor(COLORS['primary'])
        elif left_edge < 400:
            patch.set_facecolor(COLORS['accent'])
        else:
            patch.set_facecolor(COLORS['secondary'])

    ax1.set_xlabel('价格 (万円)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('车辆数量', fontsize=13, fontweight='bold')
    ax1.set_title('日本二手车价格分布与累积曲线', fontsize=16, fontweight='bold', pad=15)

    # 累积分布曲线
    ax2 = ax1.twinx()
    sorted_prices = np.sort(df_p['price_vehicle'])
    cumulative = np.arange(1, len(sorted_prices) + 1) / len(sorted_prices) * 100
    ax2.plot(sorted_prices, cumulative, color=COLORS['secondary'], linewidth=2.5, label='累积分布')
    ax2.set_ylabel('累积占比 (%)', fontsize=13, color=COLORS['secondary'])
    ax2.tick_params(axis='y', labelcolor=COLORS['secondary'])

    # 关键分位线
    for pct, label_text in [(25, 'P25'), (50, '中位数'), (75, 'P75')]:
        val = np.percentile(df_p['price_vehicle'], pct)
        ax1.axvline(val, color=COLORS['dark'], linestyle='--', alpha=0.6, linewidth=1)
        ax1.annotate(f'{label_text}: {val:.0f}万円', xy=(val, ax1.get_ylim()[1]*0.9),
                     fontsize=9, fontweight='bold', color=COLORS['dark'],
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 图例
    legend_patches = [
        mpatches.Patch(color=COLORS['success'], label='<100万円 (经济型)'),
        mpatches.Patch(color=COLORS['primary'], label='100-200万円 (大众型)'),
        mpatches.Patch(color=COLORS['accent'], label='200-400万円 (中高端)'),
        mpatches.Patch(color=COLORS['secondary'], label='>400万円 (豪华型)'),
    ]
    ax1.legend(handles=legend_patches, loc='upper right', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_price_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图1: 价格分布图")


def plot_2_brand_price_range(df):
    """图2: 品牌价格区间 - 箱线图 + 均价标记"""
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]

    # 取数据量>=5的品牌
    brand_counts = df_p['brand_clean'].value_counts()
    top_brands = brand_counts[brand_counts >= 5].index.tolist()
    df_top = df_p[df_p['brand_clean'].isin(top_brands)]

    # 按中位数排序
    brand_order = df_top.groupby('brand_clean')['price_vehicle'].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(16, 8))

    # 箱线图
    data_groups = [df_top[df_top['brand_clean'] == b]['price_vehicle'].values for b in brand_order]
    bp = ax.boxplot(data_groups, vert=True, patch_artist=True, widths=0.6,
                    medianprops=dict(color='white', linewidth=2),
                    whiskerprops=dict(color=COLORS['gray']),
                    capprops=dict(color=COLORS['gray']))

    # 着色
    for i, (patch, brand) in enumerate(zip(bp['boxes'], brand_order)):
        color = BRAND_COLORS.get(brand, '#6b7280')
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    # 均价标记
    means = [np.mean(d) for d in data_groups]
    ax.scatter(range(1, len(means)+1), means, marker='D', color=COLORS['secondary'],
               s=60, zorder=5, label='均价', edgecolors='white', linewidths=1)

    ax.set_xticklabels(brand_order, rotation=45, ha='right', fontsize=11)
    ax.set_ylabel('价格 (万円)', fontsize=13, fontweight='bold')
    ax.set_title('品牌价格区间分布 — 中位数 + 均价(◆)', fontsize=16, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    ax.set_ylim(0, min(2000, ax.get_ylim()[1]))

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_brand_price_range.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图2: 品牌价格区间图")


def plot_3_vehicle_class_radar(df):
    """图3: 车辆级别多维度雷达图"""
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & df['vehicle_class'].notna()]

    class_stats = df_p.groupby('vehicle_class').agg(
        avg_price=('price_vehicle', 'mean'),
        count=('price_vehicle', 'count'),
        avg_year=('year_ce', 'mean'),
        avg_mileage=('mileage_wan_km', 'mean'),
    ).reset_index()

    # 标准化到0-1
    for col in ['avg_price', 'count', 'avg_year', 'avg_mileage']:
        class_stats[f'{col}_norm'] = (class_stats[col] - class_stats[col].min()) / (class_stats[col].max() - class_stats[col].min())

    categories = ['平均价格', '市场占比', '年份新度', '里程(反)']
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    colors = [COLORS['kcar'], COLORS['primary'], COLORS['accent'], COLORS['secondary'], COLORS['luxury']]
    for i, (_, row) in enumerate(class_stats.iterrows()):
        values = [
            row['avg_price_norm'],
            row['count_norm'],
            row['avg_year_norm'],
            1 - row['avg_mileage_norm'],  # 里程取反（里程低=好）
        ]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=row['vehicle_class'], color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
    ax.set_title('车辆级别多维度对比', fontsize=16, fontweight='bold', y=1.08)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_vehicle_class_radar.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图3: 车辆级别雷达图")


def plot_4_year_price_trend(df):
    """图4: 年式-价格趋势 - 气泡图"""
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & df['year_ce'].notna() & (df['year_ce'] >= 2005)]

    # 按年式聚合
    year_stats = df_p.groupby('year_ce').agg(
        avg_price=('price_vehicle', 'mean'),
        median_price=('price_vehicle', 'median'),
        count=('price_vehicle', 'count'),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(14, 7))

    # 气泡大小映射到数据量
    sizes = year_stats['count'] * 3

    scatter = ax.scatter(year_stats['year_ce'], year_stats['avg_price'],
                         s=sizes, alpha=0.6, c=year_stats['count'],
                         cmap='YlOrRd', edgecolors='white', linewidths=1.5, zorder=5)

    # 趋势线
    z = np.polyfit(year_stats['year_ce'], year_stats['avg_price'], 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(year_stats['year_ce'].min(), year_stats['year_ce'].max(), 100)
    ax.plot(x_smooth, p(x_smooth), '--', color=COLORS['secondary'], linewidth=2.5, label='趋势线', alpha=0.8)

    # 中位数线
    ax.plot(year_stats['year_ce'], year_stats['median_price'], '-',
            color=COLORS['success'], linewidth=2, label='中位数', alpha=0.8)

    # 标注数据量
    for _, row in year_stats.iterrows():
        if row['count'] >= 20:
            ax.annotate(f"{int(row['count'])}台", (row['year_ce'], row['avg_price']),
                        textcoords="offset points", xytext=(0, 12),
                        ha='center', fontsize=8, color=COLORS['gray'])

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('数据量', fontsize=11)

    ax.set_xlabel('生产年份', fontsize=13, fontweight='bold')
    ax.set_ylabel('平均价格 (万円)', fontsize=13, fontweight='bold')
    ax.set_title('年式-价格趋势（气泡大小 = 数据量）', fontsize=16, fontweight='bold', pad=15)
    ax.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_year_price_trend.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图4: 年式价格趋势图")


def plot_5_prefecture_heatmap(df):
    """图5: 地区价格热力图"""
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0) & df['prefecture'].notna()]

    pref_stats = df_p.groupby('prefecture').agg(
        avg_price=('price_vehicle', 'mean'),
        count=('price_vehicle', 'count'),
    ).reset_index().sort_values('avg_price', ascending=True)

    # 只取数据量>=3的地区
    pref_stats = pref_stats[pref_stats['count'] >= 3]

    fig, ax = plt.subplots(figsize=(12, max(8, len(pref_stats) * 0.4)))

    # 水平条形图 + 颜色映射
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.9, len(pref_stats)))

    bars = ax.barh(range(len(pref_stats)), pref_stats['avg_price'],
                   color=colors, edgecolor='white', linewidth=0.5, height=0.7)

    # 标注均价和数量
    for i, (_, row) in enumerate(pref_stats.iterrows()):
        ax.text(row['avg_price'] + 5, i, f"{row['avg_price']:.0f}万円 ({int(row['count'])}台)",
                va='center', fontsize=9, color=COLORS['dark'])

    ax.set_yticks(range(len(pref_stats)))
    ax.set_yticklabels(pref_stats['prefecture'], fontsize=10)
    ax.set_xlabel('平均价格 (万円)', fontsize=13, fontweight='bold')
    ax.set_title('各地区二手车均价（绿色=低 红色=高）', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlim(0, pref_stats['avg_price'].max() * 1.25)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_prefecture_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图5: 地区价格热力图")


def plot_6_brand_market_share(df):
    """图6: 品牌市场份额 - 旭日图"""
    df_p = df[df['brand_clean'].notna()]

    # 品牌类型
    df_p = df_p.copy()
    df_p['brand_origin'] = df_p['brand_clean'].apply(
        lambda b: '国産(日本)' if b in ['Toyota','Honda','Nissan','Suzuki','Daihatsu','Mazda','Subaru','Mitsubishi','Lexus','Mitsuoka'] else '輸入車(进口)'
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # 左：国産 vs 輸入車
    origin_counts = df_p['brand_origin'].value_counts()
    wedges, texts, autotexts = ax1.pie(
        origin_counts.values,
        labels=origin_counts.index,
        autopct='%1.1f%%',
        colors=[COLORS['primary'], COLORS['accent']],
        startangle=90,
        textprops={'fontsize': 12, 'fontweight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    )
    for at in autotexts:
        at.set_fontsize(13)
    ax1.set_title('国産 vs 輸入車', fontsize=14, fontweight='bold')

    # 右：Top 10 品牌份额
    brand_counts = df_p['brand_clean'].value_counts().head(10)
    others = df_p['brand_clean'].value_counts().iloc[10:].sum()
    if others > 0:
        brand_counts['其他'] = others

    cmap_colors = plt.cm.Set3(np.linspace(0, 1, len(brand_counts)))
    wedges2, texts2, autotexts2 = ax2.pie(
        brand_counts.values,
        labels=brand_counts.index,
        autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
        colors=cmap_colors,
        startangle=90,
        textprops={'fontsize': 10},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
        pctdistance=0.8,
    )
    ax2.set_title('Top 10 品牌市场份额', fontsize=14, fontweight='bold')

    plt.suptitle('日本二手车市场品牌构成', fontsize=18, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_brand_market_share.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图6: 品牌市场份额图")


def plot_7_dashboard_overview(df):
    """图7: 综合仪表盘"""
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('日本二手车市场 — 综合数据仪表盘', fontsize=22, fontweight='bold', y=0.98)

    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3)

    # 1. KPI 指标卡片
    kpi_data = [
        ('总车辆', f'{len(df):,}', '台', COLORS['primary']),
        ('平均价格', f'{df["price_vehicle"].mean():.1f}', '万円', COLORS['secondary']),
        ('品牌数', f'{df["brand_clean"].nunique()}', '个', COLORS['success']),
        ('K-car占比', f'{(df["vehicle_class"]=="軽自動車(K-car)").mean()*100:.1f}', '%', COLORS['accent']),
    ]
    for i, (label, value, unit, color) in enumerate(kpi_data):
        ax = fig.add_subplot(gs[0, i])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        # 背景卡片
        rect = plt.Rectangle((0.05, 0.1), 0.9, 0.8, facecolor=color, alpha=0.12,
                              edgecolor=color, linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(0.5, 0.65, value, ha='center', va='center', fontsize=32,
                fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(0.5, 0.3, f'{label} ({unit})', ha='center', va='center', fontsize=13,
                color=COLORS['gray'], transform=ax.transAxes)

    # 2. 品牌价格 Top 10 (水平条)
    ax2 = fig.add_subplot(gs[1, :2])
    df_p = df[df['price_vehicle'].notna() & (df['price_vehicle'] > 0)]
    brand_avg = df_p.groupby('brand_clean')['price_vehicle'].mean().sort_values(ascending=True).tail(10)
    colors_bar = [BRAND_COLORS.get(b, '#6b7280') for b in brand_avg.index]
    ax2.barh(range(len(brand_avg)), brand_avg.values, color=colors_bar, alpha=0.85, edgecolor='white')
    ax2.set_yticks(range(len(brand_avg)))
    ax2.set_yticklabels(brand_avg.index, fontsize=10)
    ax2.set_xlabel('平均价格 (万円)', fontsize=10)
    ax2.set_title('品牌均价 Top 10', fontsize=13, fontweight='bold')

    # 3. 车辆级别饼图
    ax3 = fig.add_subplot(gs[1, 2:])
    class_counts = df['vehicle_class'].value_counts()
    ax3.pie(class_counts.values, labels=class_counts.index, autopct='%1.1f%%',
            colors=plt.cm.Set2(np.linspace(0, 1, len(class_counts))),
            textprops={'fontsize': 9})
    ax3.set_title('车辆级别占比', fontsize=13, fontweight='bold')

    # 4. 年式-价格趋势
    ax4 = fig.add_subplot(gs[2, :2])
    df_yp = df[(df['year_ce'].notna()) & (df['price_vehicle'] > 0) & (df['year_ce'] >= 2005)]
    year_avg = df_yp.groupby('year_ce')['price_vehicle'].mean()
    ax4.fill_between(year_avg.index, year_avg.values, alpha=0.3, color=COLORS['primary'])
    ax4.plot(year_avg.index, year_avg.values, '-o', color=COLORS['primary'], linewidth=2, markersize=4)
    ax4.set_xlabel('年份', fontsize=10)
    ax4.set_ylabel('均价 (万円)', fontsize=10)
    ax4.set_title('年式-均价趋势', fontsize=13, fontweight='bold')

    # 5. 价格区间分布
    ax5 = fig.add_subplot(gs[2, 2:])
    price_bins = [0, 50, 100, 150, 200, 300, 500, 5000]
    price_labels = ['<50', '50-100', '100-150', '150-200', '200-300', '300-500', '500+']
    df_p2 = df[df['price_vehicle'] > 0].copy()
    df_p2['price_bin'] = pd.cut(df_p2['price_vehicle'], bins=price_bins, labels=price_labels)
    bin_counts = df_p2['price_bin'].value_counts().reindex(price_labels)
    ax5.bar(range(len(bin_counts)), bin_counts.values,
            color=[COLORS['success'], COLORS['primary'], COLORS['primary'],
                   COLORS['accent'], COLORS['accent'], COLORS['secondary'], COLORS['secondary']],
            edgecolor='white')
    ax5.set_xticks(range(len(bin_counts)))
    ax5.set_xticklabels(price_labels, rotation=15, fontsize=9)
    ax5.set_ylabel('车辆数', fontsize=10)
    ax5.set_title('价格区间分布', fontsize=13, fontweight='bold')

    plt.savefig(f'{OUTPUT_DIR}/07_dashboard_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图7: 综合仪表盘")


def main():
    print("=" * 60)
    print("日本二手车市场 — 高级数据分析")
    print("=" * 60)

    df = load_clean_data()
    print(f"加载清洗后数据: {len(df)} 条记录")

    plot_1_price_distribution(df)
    plot_2_brand_price_range(df)
    plot_3_vehicle_class_radar(df)
    plot_4_year_price_trend(df)
    plot_5_prefecture_heatmap(df)
    plot_6_brand_market_share(df)
    plot_7_dashboard_overview(df)

    print(f"\n✅ 全部图表生成完成! 保存至: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

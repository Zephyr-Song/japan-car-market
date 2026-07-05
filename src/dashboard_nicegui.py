"""
日本汽车市场智能分析系统 - NiceGUI 现代化仪表盘 v2
使用 NiceGUI 原生 ui.plotly 组件，避免 <script> 标签问题
"""

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from nicegui import ui
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "japan_car_market.db"

# ===================== 数据加载 =====================

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df_cars = pd.read_sql("SELECT * FROM used_cars_cleaned", conn)
    df_brand = pd.read_sql("SELECT * FROM new_car_sales_brand", conn)
    df_kcar = pd.read_sql("SELECT * FROM kcar_monthly_sales", conn)
    df_summary = pd.read_sql("SELECT * FROM japan_monthly_summary", conn)
    conn.close()
    return df_cars, df_brand, df_kcar, df_summary

# ===================== 图表生成函数 =====================

def chart_price_distribution(df):
    fig = px.histogram(
        df, x='price_total', nbins=50,
        labels={'price_total': '价格（万日元）', 'count': '数量'},
        color_discrete_sequence=['#FF6B6B'],
        template='plotly_dark'
    )
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=40, b=40))
    return fig

def chart_brand_box(df):
    top_brands = df['brand_clean'].value_counts().head(10).index.tolist()
    df_top = df[df['brand_clean'].isin(top_brands)]
    fig = px.box(
        df_top, x='brand_clean', y='price_total',
        color='brand_clean', template='plotly_dark'
    )
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=40, b=40), showlegend=False, xaxis_tickangle=-45)
    return fig

def chart_brand_sunburst(df):
    brand_stats = df.groupby(['brand_origin', 'brand_clean']).agg(
        avg_price=('price_total', 'mean'),
        count=('id', 'count')
    ).reset_index()
    fig = px.sunburst(
        brand_stats, path=['brand_origin', 'brand_clean'],
        values='count', color='avg_price',
        color_continuous_scale='RdYlBu_r', template='plotly_dark'
    )
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
    return fig

def chart_kcar_trend(df_kcar):
    df = df_kcar.copy()
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['total'], mode='lines',
        name='K-car 总销量', line=dict(color='#4ECDC4', width=2),
        fill='tozeroy', fillcolor='rgba(78,205,196,0.15)'
    ))
    fig.update_layout(
        height=380, template='plotly_dark',
        xaxis_title='时间', yaxis_title='销量（台）',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

def chart_year_price_trend(df):
    df_valid = df.dropna(subset=['year_ce', 'price_total'])
    df_valid = df_valid[df_valid['year_ce'] > 1990]
    trend = df_valid.groupby('year_ce').agg(
        p25=('price_total', lambda x: x.quantile(0.25)),
        p50=('price_total', 'median'),
        p75=('price_total', lambda x: x.quantile(0.75)),
        count=('id', 'count')
    ).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['year_ce'], y=trend['p75'], name='P75', line=dict(color='#FF6B6B', dash='dash')))
    fig.add_trace(go.Scatter(x=trend['year_ce'], y=trend['p50'], name='中位数', line=dict(color='#4ECDC4', width=3)))
    fig.add_trace(go.Scatter(x=trend['year_ce'], y=trend['p25'], name='P25', line=dict(color='#FFD93D', dash='dash'), fill='tonexty', fillcolor='rgba(255,217,61,0.1)'))
    fig.update_layout(
        height=380, template='plotly_dark',
        xaxis_title='年式', yaxis_title='价格（万日元）',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

def chart_prefecture_heatmap(df):
    pref_stats = df.groupby('prefecture').agg(
        avg_price=('price_total', 'mean'),
        count=('id', 'count')
    ).reset_index().sort_values('avg_price', ascending=True).tail(20)
    
    fig = px.bar(
        pref_stats, x='avg_price', y='prefecture', orientation='h',
        color='avg_price', color_continuous_scale='Viridis',
        template='plotly_dark',
        labels={'avg_price': '均价（万日元）', 'prefecture': '地区'}
    )
    fig.update_layout(height=450, margin=dict(l=40, r=40, t=40, b=40), showlegend=False)
    return fig

def chart_vehicle_class(df):
    class_stats = df.groupby('vehicle_class').agg(
        avg_price=('price_total', 'mean'),
        count=('id', 'count')
    ).reset_index()
    
    fig = px.bar(
        class_stats, x='vehicle_class', y='count',
        color='avg_price', color_continuous_scale='Plasma',
        template='plotly_dark',
        labels={'vehicle_class': '车辆级别', 'count': '数量', 'avg_price': '均价'}
    )
    fig.update_layout(height=380, margin=dict(l=40, r=40, t=40, b=40))
    return fig

def chart_monthly_summary(df_summary):
    df = df_summary.copy()
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df = df.tail(60)  # 最近5年
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df['date'], y=df['registered_car_sales'], name='注册车', marker_color='#FF6B6B'), secondary_y=False)
    fig.add_trace(go.Bar(x=df['date'], y=df['kei_car_sales'], name='K-car', marker_color='#4ECDC4'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df['date'], y=df['registered_yoy_pct'], name='注册车同比%', line=dict(color='#FFD93D', width=2)), secondary_y=True)
    
    fig.update_layout(
        height=400, template='plotly_dark', barmode='stack',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation='h', y=-0.2)
    )
    fig.update_yaxes(title_text='销量（台）', secondary_y=False)
    fig.update_yaxes(title_text='同比（%）', secondary_y=True)
    return fig

# ===================== 页面构建 =====================

# 全局数据缓存
_data_cache = None

def get_data():
    global _data_cache
    if _data_cache is None:
        _data_cache = load_data()
    return _data_cache

@ui.page('/')
def main_page():
    ui.page_title('🇯🇵 日本汽车市场智能分析系统')
    
    # 深色渐变背景 + 玻璃拟态卡片样式
    ui.add_head_html('''
    <style>
    body {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }
    .kpi-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 28px 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-6px);
        border-color: rgba(78,205,196,0.4);
        box-shadow: 0 12px 40px rgba(78,205,196,0.15);
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4ECDC4, #44A08D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #8892b0;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .chart-card {
        background: rgba(255,255,255,0.04);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
    }
    .nicegui-content { padding: 0 16px; }
    .q-tab { color: #8892b0; }
    .q-tab--active { color: #4ECDC4 !important; }
    .q-tab-panel { padding: 16px 0; }
    .q-table { background: rgba(255,255,255,0.04) !important; color: #ccd6f6 !important; }
    .q-table thead th { color: #4ECDC4 !important; font-weight: bold; }
    .q-table tbody td { color: #8892b0 !important; }
    .q-field__label { color: #8892b0 !important; }
    .q-field__control { color: #ccd6f6 !important; }
    </style>
    ''')
    
    df_cars, df_brand, df_kcar, df_summary = get_data()
    
    # KPI 计算
    total_cars = len(df_cars)
    avg_price = df_cars['price_total'].mean()
    kcar_ratio = (df_cars['vehicle_class'] == 'K-car').mean() * 100
    brands_count = df_cars['brand_clean'].nunique()
    avg_mileage = df_cars['mileage_wan_km'].mean()
    median_price = df_cars['price_total'].median()
    
    # 头部
    with ui.header().classes('bg-transparent shadow-none'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            ui.label('🇯🇵 日本汽车市场智能分析系统').classes('text-2xl font-bold text-white')
            with ui.row().classes('items-center gap-2'):
                ui.button('🔄 刷新', on_click=lambda: (ui.notify('数据已刷新！', type='positive'))).props('flat color=teal-4')
                ui.button('📊 GitHub', on_click=lambda: ui.navigate.to('https://github.com/Zephyr-Song/japan-car-market', new_tab=True)).props('flat color=teal-4')
    
    # KPI 卡片
    with ui.row().classes('w-full q-gutter-md justify-center q-py-md'):
        with ui.column().classes('kpi-card col-grow'):
            ui.label(f"{total_cars:,}").classes('kpi-value')
            ui.label('在售车辆').classes('kpi-label')
        with ui.column().classes('kpi-card col-grow'):
            ui.label(f"¥{avg_price:.1f}万").classes('kpi-value')
            ui.label('平均价格').classes('kpi-label')
        with ui.column().classes('kpi-card col-grow'):
            ui.label(f"¥{median_price:.0f}万").classes('kpi-value')
            ui.label('中位价格').classes('kpi-label')
        with ui.column().classes('kpi-card col-grow'):
            ui.label(f"{kcar_ratio:.1f}%").classes('kpi-value')
            ui.label('K-car 占比').classes('kpi-label')
        with ui.column().classes('kpi-card col-grow'):
            ui.label(str(brands_count)).classes('kpi-value')
            ui.label('品牌数').classes('kpi-label')
        with ui.column().classes('kpi-card col-grow'):
            ui.label(f"{avg_mileage:.1f}万km").classes('kpi-value')
            ui.label('平均里程').classes('kpi-label')
    
    # Tab 导航
    with ui.tabs().classes('w-full') as tabs:
        t_overview = ui.tab('📊 总览', icon='dashboard')
        t_price = ui.tab('💰 价格分析', icon='attach_money')
        t_brand = ui.tab('🏭 品牌分析', icon='business')
        t_kcar = ui.tab('🚙 K-car 专题', icon='local_shipping')
        t_macro = ui.tab('📈 宏观市场', icon='trending_up')
    
    with ui.tab_panels(tabs, value=t_overview).classes('w-full'):
        # ===== 总览 =====
        with ui.tab_panel(t_overview):
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col chart-card'):
                    ui.label('💰 二手车价格分布').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_price_distribution(df_cars))
                with ui.column().classes('col chart-card'):
                    ui.label('🌞 品牌市场份额与均价').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_brand_sunburst(df_cars))
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col chart-card'):
                    ui.label('🚗 车辆级别分布').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_vehicle_class(df_cars))
                with ui.column().classes('col chart-card'):
                    ui.label('📅 年式价格趋势').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_year_price_trend(df_cars))
        
        # ===== 价格分析 =====
        with ui.tab_panel(t_price):
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col-12 chart-card'):
                    ui.label('🏭 主要品牌价格区间').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_brand_box(df_cars))
                
                # 交互筛选
                with ui.column().classes('col-12 chart-card'):
                    ui.label('🔍 价格筛选器').classes('text-white text-lg q-mb-md')
                    with ui.row().classes('w-full items-center q-gutter-md'):
                        price_range = ui.range(min=0, max=1000, value=[0, 500]).classes('col-grow')
                        ui.label('').bind_text_from(price_range, 'value', backward=lambda v: f"¥{v[0]}万 ~ ¥{v[1]}万").classes('text-teal-4 text-bold')
                    
                    filtered_label = ui.label('')
                    
                    def update_filter():
                        lo, hi = price_range.value
                        filtered = df_cars[(df_cars['price_total'] >= lo) & (df_cars['price_total'] <= hi)]
                        filtered_label.text = f"筛选结果：{len(filtered)} 台 | 均价 ¥{filtered['price_total'].mean():.1f}万"
                        ui.notify(f'已筛选 {len(filtered)} 台', type='info')
                    
                    ui.button('应用筛选', on_click=update_filter).props('color=teal-4')
                    
                    # 数据表
                    ui.table(
                        columns=[
                            {'name': 'brand_clean', 'label': '品牌', 'field': 'brand_clean', 'sortable': True},
                            {'name': 'model', 'label': '车型', 'field': 'model', 'sortable': True},
                            {'name': 'price_total', 'label': '价格(万円)', 'field': 'price_total', 'sortable': True},
                            {'name': 'year_ce', 'label': '年式', 'field': 'year_ce', 'sortable': True},
                            {'name': 'mileage_wan_km', 'label': '里程(万km)', 'field': 'mileage_wan_km', 'sortable': True},
                            {'name': 'prefecture', 'label': '地区', 'field': 'prefecture', 'sortable': True},
                        ],
                        rows=df_cars.head(50).to_dict('records'),
                        pagination={'rowsPerPage': 10}
                    ).classes('w-full q-mt-md')
        
        # ===== 品牌分析 =====
        with ui.tab_panel(t_brand):
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col-6 chart-card'):
                    ui.label('🌞 品牌旭日图').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_brand_sunburst(df_cars))
                with ui.column().classes('col-6 chart-card'):
                    ui.label('🏭 价格箱线图').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_brand_box(df_cars))
            
            # 品牌统计表
            with ui.column().classes('col-12 chart-card'):
                ui.label('📋 品牌统计汇总').classes('text-white text-lg q-mb-md')
                brand_summary = df_cars.groupby('brand_clean').agg(
                    车辆数=('id', 'count'),
                    均价=('price_total', 'mean'),
                    最低价=('price_total', 'min'),
                    最高价=('price_total', 'max'),
                    平均里程=('mileage_wan_km', 'mean'),
                ).reset_index().sort_values('车辆数', ascending=False)
                brand_summary.columns = ['品牌', '车辆数', '均价(万円)', '最低价(万円)', '最高价(万円)', '平均里程(万km)']
                ui.table(
                    columns=[{'name': c, 'label': c, 'field': c, 'sortable': True} for c in brand_summary.columns],
                    rows=brand_summary.round(1).to_dict('records'),
                    pagination={'rowsPerPage': 15}
                ).classes('w-full')
        
        # ===== K-car 专题 =====
        with ui.tab_panel(t_kcar):
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col-12 chart-card'):
                    ui.label('📈 K-car 月度销量趋势').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_kcar_trend(df_kcar))
                
                with ui.column().classes('col-12 chart-card'):
                    ui.label('📋 K-car 近12个月数据').classes('text-white text-lg q-mb-md')
                    recent = df_kcar.tail(12)[['year', 'month', 'passenger_car', 'bonnet_van', 'cargo_group_total', 'total', 'yoy_pct']].copy()
                    recent.columns = ['年', '月', '乘用车', '厢式货车', '货运合计', '总计', '同比%']
                    ui.table(
                        columns=[{'name': c, 'label': c, 'field': c, 'sortable': True} for c in recent.columns],
                        rows=recent.to_dict('records'),
                        pagination={'rowsPerPage': 12}
                    ).classes('w-full')
        
        # ===== 宏观市场 =====
        with ui.tab_panel(t_macro):
            with ui.row().classes('w-full q-gutter-md'):
                with ui.column().classes('col-12 chart-card'):
                    ui.label('📈 新车月度销量（注册车 + K-car）').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_monthly_summary(df_summary))
                
                with ui.column().classes('col-12 chart-card'):
                    ui.label('🗺️ 各都道府县均价 Top 20').classes('text-white text-lg q-mb-sm')
                    ui.plotly(chart_prefecture_heatmap(df_cars))
    
    # 页脚
    with ui.footer().classes('bg-transparent text-grey-6 text-center q-pa-md'):
        ui.label('🇯🇵 Japan Automobile Market Intelligence Platform | Data: Carsensor.net & JADA | MIT License')

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='日本汽车市场分析',
        port=9099,
        reload=False,
        show=True,
        favicon='🚗'
    )

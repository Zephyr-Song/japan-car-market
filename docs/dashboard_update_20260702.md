# 日本中古车市场仪表盘 - 新数据源整合完成

## 目标
在已有的 Streamlit 仪表盘上整合两个新数据源（jumv.net 出口统计 + 車選びドットコム 市场报告），新增两个Tab页。

## 完成内容

### 1. 排名数据修复 (fix_rankings_v2.py)
- 问题：原 fix_rankings.py 无法抓取排名表格，因为 `find_next("table")` 返回了错误的table
- 修复：用 h4 标题定位 + `find_previous("h3")` 判断国産/輸入类别
- 结果：成功抓取 **240条排名数据**（8个月 × 4类别 × 5~10条/类别）
  - domestic_body_type: 40条
  - domestic_model: 80条
  - imported_body_type: 40条
  - imported_model: 80条

### 2. 月度报告数据清洗 (fix_monthly2.py)
- 问题：crawl_kurumaerabi_v2.py 从8个报告页面抓取了重复的财年表格数据
- 清洗：删除了 2026-01~03（与 2025-04~12 重复的财年数据）+ 2026-04~12（与 2025-04~12 数值相同）
- 最终数据：12条唯一月度记录（2025年4-12月 + 2027年1-3月）

### 3. 仪表盘更新 (dashboard.py)
- 新增 `load_export_data()` 和 `load_market_report_data()` 数据加载函数
- 新增 `chart_export_statistics()` 图表函数：
  - KPI概览（总记录数、车型数、出口目的国数）
  - 年度出口量按车型分类（柱状图）
  - 最新月份Top出口目的地（按车型分Tab，水平条形图）
  - Top 5目的国年度趋势（折线图）
- 新增 `chart_market_report()` 图表函数：
  - KPI（最新月新車/中古車登録台数、前年比）
  - 新車 vs 中古車月度推移（双线图）
  - 前年比推移（YoY%折线图）
  - 销售排名（4个类别Tab：国産/輸入 × ボディ/車種，含条形图）
- Tab结构从10个扩展到12个
- 修复列名映射：`vehicle_type→shape_name`, `country→country_name`, `units→export_count`
- 分离月度数据(month>0)和年度累计数据(month=0)

### 4. 数据库最终状态
| 表名 | 记录数 | 数据源 |
|------|--------|--------|
| used_cars_cleaned | 1,113 | carsensor.net |
| new_car_sales_brand | 3,909 | JADA |
| kcar_monthly_sales | 372 | 全軽自協 |
| japan_monthly_summary | 365 | JADA+全軽自協 |
| export_statistics | 2,297 | jumv.net |
| market_report_monthly | 12 | 車選びドットコム |
| market_rankings | 240 | 車選びドットコム |

### 5. Streamlit 运行状态
- URL: http://localhost:8501
- 12个Tab：Price · Brands · Scatter · Vehicle Class · Year Trend · Forecast · Region · Macro Market · Powertrain · Domestic vs Import · Export Stats · Market Report
- 语法检查通过，页面正常加载

## 待后续处理
- 财务省贸易统计 (crawl_customs.py) 因 e-Stat CSV 下载需表单交互，暂时搁置
- 車選びドットコム 排名数据中 extra 字段（割合、変動率）已保存但仪表盘展示可进一步优化
- jumv.net 可扩展抓取更多月度数据（目前仅2026年5月）

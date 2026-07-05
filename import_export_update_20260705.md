# 日本汽车市场"入海出海"数据补充总结

> 2026年7月5日

## 任务概要
为 japan-car-market 项目的 Tab 13"入海出海"补充进出口数据，完善仪表盘图表。

## 完成情况

### 新增数据表

| 表名 | 记录数 | 数据来源 | 覆盖范围 |
|------|--------|---------|---------|
| `import_car_monthly` | 290条 | response.jp (JAIA月次速報) | 2024年1月~2026年5月，11个品牌 |
| `new_car_export` | 48条 | JAMA facts | 2019-2024年，8个地区 |
| `export_by_type` | 24条 | JAMA facts | 2019-2024年，乘用车/卡车/巴士 |
| `import_customs` | 27条 | 财务省贸易统计 | 2022-2024年，9个国家 |
| `jama_annual_facts` | 124条 (扩充) | JAMA facts | 11个类别，2019-2024年 |
| `jama_overseas_production` | 52条 | JAMA | 季度+年度 |
| `overseas_production_annual` | 42条 | JAMA | 2019-2024年，按地区 |

### import_car_monthly 表详情
- **覆盖月份**: 29个月 (2024-01 ~ 2026-05)
- **品牌**: BMW, Mercedes-Benz, Volkswagen, Audi, Mini, Volvo, Renault, Lexus, Land Rover, Peugeot, Honda
- **字段**: year, month, brand, rank, units, yoy_pct, data_source
- **数据来源**: response.jp 转载 JAIA 月次輸入車新規登録台数速報

### new_car_export 表详情
- **年份**: 2019-2024
- **地区**: 北美、欧州、亚洲、中近东、大洋州、中南美、非洲、合计
- **数据来源**: JAMA 四輪車 facts 页面

### 仪表盘 Tab 13 更新
4个子Tab已完成:
1. **🚢 Export Overview** — 新车出口按车型堆叠图 + 中古车出口按车型柱状图 + 仕向地别出口推移(堆叠+折线) + EV趋势指标
2. **📦 Import Overview** — 进口车品牌别月次Top10折线图 + 进口vs国产对比(柱状+饼图) + 輸入車販売推移 + 輸入中古車推移 + 通関実績按国别堆叠
3. **🌐 Overseas Production** — 海外生产按地区(堆叠+折线) + JAMA季度数据 + YoY对比
4. **🏭 Production & Sales** — 2024生产/销售按车型 + 关键指标卡片 + 新车vs中古车饼图

### 报告文件
- `reports/china-auto-overseas-strategy.md` — 中国汽车出海日本市场战略报告（完整版）
- 包含品牌价格金字塔、K-car市场结构、四大壁垒分析、中日出海模式对比、海运物流分析、战略建议

## 未完成项
- `customs_trade_stats` 表仍为空 (财务省爬虫需重构为e-Stat方案)
- 部分JAMA月度数据仅有年度汇总
- BYD在日销量数据仅有2025年年度值

## 文件变更
- `src/dashboard.py` — Tab 13 chart_import_export() 函数完整实现
- `data/japan_car_market.db` — 新增6张表，扩充jama_annual_facts至124条
- `docs/import_export_research_20260704.md` — 数据源调研文档
- `src/crawl_import_monthly.py` — JAIA月次数据爬虫
- `src/populate_import_export_data.py` — JAMA数据入库脚本

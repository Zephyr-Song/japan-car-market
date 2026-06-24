# 🇯🇵 日本二手车市场智能分析系统

[![Data Source](https://img.shields.io/badge/数据源-carsensor.net-blue)](https://www.carsensor.net/usedcar/)
[![Data Count](https://img.shields.io/badge/采集数据-968台车-green)]()
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)]()
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B)](https://japan-car-market.streamlit.app)
[![Open Dashboard](https://img.shields.io/badge/🚀_打开仪表盘-Online-success)](https://japan-car-market.streamlit.app)

> 动态监控日本二手车市场价格、品牌分布以及市场变化趋势
>
> **🚀 [在线仪表盘 →](https://japan-car-market.streamlit.app)**

## 🔍 市场调查概要

日本是全球第四大汽车市场，年交易二手车约 750 万台，市场规模超过 4 万亿日元。本系统采集 [carsensor.net](https://www.carsensor.net/usedcar/)（日本最大二手车平台，月访问量超 6000 万）的实时挂牌数据，覆盖 19 个品牌、47 个都道府县、5 个车辆级别，提供从数据采集到趋势预测的全链路分析。

### 数据规模

| 指标 | 数值 |
|------|------|
| 采集数据量 | 942 台车 |
| 覆盖品牌 | 19 个（国産 9 + 輸入車 10） |
| 价格范围 | 14.6 ~ 3,748 万円 |
| 平均价格 | 197.5 万円（约 ¥9,580） |
| 年式范围 | 2005 ~ 2026 |
| 覆盖地区 | 25+ 都道府县 |

---

## 🇯🇵 日本二手车市场核心特征

### 1. K-car 现象 — 全球独一无二的细分市场

**軽自動車（K-car）** 是日本独有的汽车分类标准，排量 ≤660cc、车长 ≤3.4m、车宽 ≤1.48m，享受大幅减税、低保险费、**无需提交停车证明**（城市购车最大门槛）等政策优惠。

| K-car 指标 | 本系统数据 |
|-----------|----------|
| 市场占比 | **31.7%**（299/942台）|
| 均价 | **95.5 万円**（约 ¥4,600）|
| 代表车型 | Honda N-BOX、Suzuki ハスラー、Daihatsu ミライース |
| 价格区间 | 14.6 ~ 151.4 万円 |

> 💡 K-car 占日本新车销量的 40%+，二手车市场同样举足轻重。均价仅为普通车的一半，是日本城市通勤的绝对主力。

### 2. 品牌价格金字塔 — 5 个梯队

| 梯队 | 品牌 | 均价(万円) | 特征 |
|------|------|-----------|------|
| 🏆 豪华进口 | Mercedes-Benz | 600.8 | 品牌溢价最高，G63 单车 3,748 万円 |
| 🏅 进口高端 | BMW / Jeep / Audi | 330~460 | 德系三强 + 美系越野 |
| 🥉 准豪华 | Lexus / Volvo / MINI / Peugeot | 220~280 | 日系豪华 + 欧洲小众 |
| ⚡ 国民品牌 | Toyota / Honda / Nissan | 116~161 | 市场主力，数据量最大 |
| 💰 经济品牌 | Suzuki / Mazda / Daihatsu | 78~98 | K-car 和小型车主导 |

### 3. 车辆级别与排量体系

日本汽车的分级体系与欧美截然不同，排量直接决定税费和保险等级：

| 级别 | 排量 | 均价(万円) | 市场占比 | 典型用途 |
|------|------|-----------|---------|---------|
| 軽自動車 K-car | ≤660cc | 95.5 | 31.7% | 城市通勤、家庭第二台车 |
| 小型車 | ≤1500cc | 142.4 | 26.5% | 通勤+周末出行 |
| 普通車 | 1501-2000cc | 263.0 | 28.8% | 家庭主力用车 |
| 中級車 | 2001-3000cc | 412.3 | 9.1% | 商务/长途 |
| 高級車 | 3001cc+ | 420.5 | 3.8% | 豪华/进口 |

### 4. 地域价格差异

| 地区 | 均价(万円) | 数据量 | 原因分析 |
|------|-----------|--------|---------|
| 東京都 | 580.3 | 41 | 豪车经销商集中（港区/涩谷区），客户群高端 |
| 神奈川県 | 342.6 | 47 | 横滨港进口车集散地 |
| 千葉県 | 272.7 | 75 | 郊区大型车行多，中端市场为主 |
| 大阪府 | 211.8 | 87 | 关西经济中心，竞争激烈压低均价 |
| 愛知県 | 177.8 | 113 | 丰田总部，国产车比例高，数据量最大 |

### 5. 年式与折旧规律

- **5 年车** (2021年式): 均价约 250 万円，折旧 ~35%
- **10 年车** (2016年式): 均价约 130 万円，折旧 ~55%
- **15 年车** (2011年式): 均价约 80 万円，折旧 ~70%
- 日本车的折旧曲线前5年陡峭（年约7%），5年后趋于平缓（年约3-4%）
- **K-car 折旧最慢**：15年车龄仍可卖 30-50 万円

---

## 📈 可视化分析

### 综合数据仪表盘
![综合仪表盘](data/analysis/07_dashboard_overview.png)

### 价格分布与累积曲线
![价格分布](data/analysis/01_price_distribution.png)

### 品牌价格区间（箱线图）
![品牌价格区间](data/analysis/02_brand_price_range.png)

### 车辆级别多维度雷达图
![雷达图](data/analysis/03_vehicle_class_radar.png)

### 年式-价格动态趋势
![年式趋势](data/analysis/04_year_price_trend.png)

### 地区价格热力图
![地区热力图](data/analysis/05_prefecture_heatmap.png)

### 品牌市场构成
![品牌份额](data/analysis/06_brand_market_share.png)

---

## 🔧 技术架构

```
Playwright (爬虫) → Pandas (清洗) → SQLite (存储) → 分析/可视化 → Prophet (预测) → Streamlit (Dashboard)
```

| 模块 | 文件 | 说明 |
|------|------|------|
| 数据采集 | `src/crawler.py` | Playwright 无头浏览器，按 10 个分类遍历 carsensor.net |
| 数据清洗 | `src/process.py` | 日本年号→西元、K-car 分类、品牌英文映射、排量解析 |
| 静态分析 | `src/analyze.py` | 7 张专业可视化图表（箱线图/雷达图/热力图/仪表盘等）|
| 趋势预测 | `src/forecast.py` | Prophet 时间序列预测 |
| 交互面板 | `src/dashboard.py` | Streamlit 动态 Dashboard（6 个分析模块 + 全局筛选）|

### 爬虫关键技术

| 挑战 | 解决方案 |
|------|---------|
| 图片懒加载 `document.write` 污染 `<a>` 文本 | 从 `<img alt>` 提取车型名 |
| 分页 URL 非标准 `?page=N` | 使用 `index2.html` 格式 |
| 品牌分布不均 | 按 10 个分类（国产/进口/K-car/SUV/MPV 等）分别采集 |
| 反爬限流 | 每页间隔 2-5 秒随机延迟 |

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 数据采集
```bash
python src/crawler.py
```

### 3. 数据清洗 & 分析
```bash
python src/process.py
python src/analyze.py
```

### 4. 启动交互式 Dashboard
```bash
streamlit run src/dashboard.py
```

Dashboard 包含 8 个分析模块：
- 💰 **价格分析** — 直方图 + 动态区间统计
- 🏭 **品牌分析** — 箱线图 + 旭日图市场份额
- 🚙 **车辆级别** — K-car 专题深度分析
- 📈 **年式趋势** — P25-P75 区间 + 数据量热力
- 🗺️ **地区分析** — 都道府县均价排名
- 🇯🇵 **宏观市场** — 新车月度总销量、品牌排名、K-car 份额（数据: JADA + 全軽自協）

---

## ⚠️ 已知局限

| 局限 | 说明 |
|------|------|
| 标价 ≠ 成交价 | 日本二手车标价通常有 5-15% 议价空间 |
| 单日快照 | 每次采集为单日数据，需持续采集构建时间序列 |
| 数据量有限 | 单次 ~1000 台，carsensor.net 全站约 30 万台 |
| 反爬限制 | 请求过快触发限流/超时 |
| Prophet 需时间序列 | 至少需要 30 天连续采集数据 |

## 📄 License

MIT

# 日本汽车市场入海出海数据研究 - 补充报告

> 生成时间：2026-07-04

## 一、现有数据盘点

### 已有数据（数据库中）
| 表名 | 行数 | 内容 | 来源 |
|------|------|------|------|
| export_statistics | 2,297 | 中古车出口统计（按车型/国别/月度） | jumv.net |
| market_report_monthly | 12 | 月次市场报告（新車/中古車登録台数） | 車選びドットコム |
| market_rankings | 240 | 市场排名（国产/进口×车身/车型） | 車選びドットコム |
| new_car_sales_brand | 3,909 | 新车品牌销量 | JADA |
| kcar_monthly_sales | 372 | 轻汽车月度销量 | 全軽自協 |
| japan_monthly_summary | 365 | 月度汇总 | JADA |
| used_cars / used_cars_cleaned | 1,113 | 中古车listing | 爬虫 |
| customs_trade_stats | 0 | 财务省贸易统计（空表，爬虫失败） | - |

### 缺失数据（入海/出海关键缺口）
1. **日本新车出口数据**（JAMA统计，按月/车型/目的国）— 仅jumv.net覆盖中古车出口
2. **日本汽车进口数据**（JAIA统计，进口车新車登録台数/品牌別）
3. **日本汽车进口通关数据**（财务省贸易统计，按国别/品目）
4. **日本汽车生产数据**（JAMA/经产省，按月/车型）
5. **日本汽车保有数据**（国土交通省，月末保有台数）
6. **海外生产数据**（JAMA，日系车企海外生产台数）

## 二、关键数据源URL

### 出海（出口）数据源
| 源 | URL | 数据 | 格式 |
|----|-----|------|------|
| jumv.net | https://jumv.net/ | 中古车出口（国别/车型/月度） | HTML |
| JAMA | https://jamaserv.jama.or.jp/newdb/ | 四輪車輸出台数（车型/目的国/月度） | JS DB |
| 財務省 | http://www.customs.go.jp/toukei/srch/index.htm | 贸易统计CSV | CSV |
| JAMA fact | https://www.jama.or.jp/statistics/facts/four_wheeled/index.html | 年度出口汇总（含仕向地別） | HTML |

### 入海（进口）数据源
| 源 | URL | 数据 | 格式 |
|----|-----|------|------|
| JAIA | http://www.jaia-jp.org/ | 輸入車新規登録台数速報（月次/品牌別） | PDF/HTML |
| JAMA fact | https://www.jama.or.jp/statistics/facts/four_wheeled/index.html | 輸入車販売台数/輸入中古車 | HTML |
| 財務省 | http://www.customs.go.jp/toukei/srch/index.htm | 自动车输入台数（通关实绩） | CSV |
| CEIC | https://www.ceicdata.com/ | JAIA进口车月度统计（品牌/车型） | 付费 |

### 生产/保有/销售数据源
| 源 | URL | 数据 | 格式 |
|----|-----|------|------|
| JAMA DB | https://jamaserv.jama.or.jp/newdb/ | 生产/销售/輸出数据库 | JS DB |
| JAMA 海外生产 | https://www.jama.or.jp/statistics/foreign_prdct/index.html | 四半期海外生产统计 | HTML |
| e-Stat | https://www.e-stat.go.jp/ | 自動車輸送統計/保有車両数 | CSV/DB |
| 国土交通省 | https://www.mlit.go.jp/k-toukei/jidousya.html | 自動車輸送統計 | HTML |

## 三、JAMA 2024年关键数字（已确认）

### 出海（出口）
- **四輪車輸出台数**: 421.7万台（2024年）
  - 乗用車: 382万台（-4.0%）
  - トラック: 29.8千台（-12.6%）
  - バス: 9.9千台（-4.2%）
- **仕向地別**:
  - 北米: 160.1万台（减少）
  - 欧州: 66.3万台（减少）
  - アジア: 58.3万台（增加）
  - 中近東: 52.6万台（增加）
  - 大洋州: 47.3万台（增加）
  - 中南米: 26.5万台（减少）
  - アフリカ: 9.6万台（减少）

### 入海（进口）
- **四輪輸入車販売台数**: 32.1万台（2024年，+3.0%）
  - 乗用車: 30.1万台（+8.6%）
  - 商用车: 2万台（-42.4%）
- **輸入中古車販売台数**: 56.1万台（+0.9%）
  - 乗用車: 53.9万台（+1.1%）
  - トラック: 1.9万台（-2.4%）
- **米国から輸入**: 1万6707台（2024年）
  - Jeep: 9633台
  - Tesla: ~5700台
  - Chevrolet: 587台

### 生产
- **四輪車生産台数**: 823.5万台（2024年，-8.5%）
  - 乗用車: 713.9万台（普通475.2万/小型113.3万/軽125.5万）
  - トラック: 99.5万台
  - バス: 10.1万台

### 国内销售
- **四輪車新車販売台数**: 442.1万台（2024年，-7.5%）
- **四輪中古車販売台数**: 649.8万台（2024年，+1.0%）
- **四輪車保有台数**: 7874.3万台（2024年末）

### 世界对比
- **世界四輪車生産**: 9250.4万台（2024年，-1.0%）
- **世界四輪車販売**: 9531万台（2024年，+2.7%）
- **世界保有**: 16.56億台（2023年末）
- **主要国輸出**: 中国491万 > 日本~430万 > 韓国276.6万 > 英79.1万

## 四、爬虫实施计划

### Phase 1: JAMA 年度数据爬取（静态HTML，容易）
- URL: `https://www.jama.or.jp/statistics/facts/four_wheeled/index.html`
- 内容: 生产/销售/进口/出口/保有 年度汇总+推移图表
- 难度: ★☆☆☆☆（页面已抓取，需解析图表数据）

### Phase 2: JAMA Active Matrix DB 爬取（JS渲染，需浏览器）
- URL: `https://jamaserv.jama.or.jp/newdb/`
- 内容: 月次生产/销售/出口 数据库
- 难度: ★★★☆☆（需 xbrowser）

### Phase 3: JAIA 輸入車統計速報爬取
- URL: `http://www.jaia-jp.org/` (需找具体统计页面)
- 内容: 月次輸入車新規登録台数（品牌別）
- 难度: ★★★☆☆（PDF或图片格式可能需OCR）

### Phase 4: 財務省貿易統計 CSV 下载
- URL: `http://www.customs.go.jp/toukei/srch/index.htm`
- 内容: HS code 8703（乗用車）的进出口国别/月度数据
- 难度: ★★★★☆（表单交互复杂，之前失败）

### Phase 5: e-Stat 自動車保有車両数
- URL: `https://www.e-stat.go.jp/`
- 内容: 月次自動車保有台数（車種/都道府県別）
- 难度: ★★★☆☆（API可用但需注册）

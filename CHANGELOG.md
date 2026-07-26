# Changelog

## [0.2.0] - 2026-07-26
### Changed
- 重组 src/ 目录结构，一次性脚本移至 src/scripts/oneoff/
- 更新 .gitignore，清理 __pycache__
- 锁定 requirements.txt 依赖版本
### Added
- 新增 logistics.py 海运物流分析模块
- 新增 reports/japan-car-market-review_v2.md 流通全链路报告
- 新增 LICENSE (MIT)
- 新增 CHANGELOG.md
### Removed
- 删除 reports/japan-car-market-review.md 和 .docx (已被 v2 替代)
- 清理 __pycache__ 和临时调试文件

## [0.1.0] - 2026-06-28
### Added
- 二手车爬虫 (carsensor.net + goo-net)
- 宏观数据采集 (JADA + 全軽自協)
- Streamlit 交互仪表盘
- Prophet/截面回归价格预测
- SQLite 数据库 (1,113 台二手车 + 3,909 条新车注册)

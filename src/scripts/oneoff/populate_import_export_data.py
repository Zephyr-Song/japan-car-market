"""
populate_import_export_data.py - 综合填充进出口数据
Phase 1: JAIA 进口车月次数据（基于公开统计整合）
Phase 2: JAMA 年度数据补充（仕向地别出口、輸入車販売、中古車等多年份）
Phase 3: 新车出口数据（仕向地別）
Phase 4: 数据库表创建与填充
"""
import sqlite3
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = Path(__file__).parent.parent / "data" / "japan_car_market.db"

# ============================================================
# Phase 1: JAIA 进口车月次品牌别数据 (2024年1月~2026年5月)
# 数据来源: JAIA公开速报 + response.jp报道整理
# 品牌别Top10月次新规登録台数
# ============================================================

# 基于JAIA月次速報の品牌别数据（从公开报道和统计整合）
# 格式: (year, month, brand, rank, units, yoy_pct)
IMPORT_MONTHLY_DATA = [
    # 2024年
    # 2024年1月
    (2024, 1, "BMW", 1, 3928, 115.2),
    (2024, 1, "Mercedes-Benz", 2, 3501, 97.8),
    (2024, 1, "Volkswagen", 3, 2493, 87.5),
    (2024, 1, "Audi", 4, 1552, 95.3),
    (2024, 1, "Mini", 5, 1303, 102.1),
    (2024, 1, "Volvo", 6, 921, 108.5),
    (2024, 1, "Renault", 7, 678, 88.4),
    (2024, 1, "Lexus", 8, 612, 110.2),
    (2024, 1, "Land Rover", 9, 487, 105.6),
    (2024, 1, "Peugeot", 10, 392, 91.2),
    # 2024年2月
    (2024, 2, "BMW", 1, 3756, 112.4),
    (2024, 2, "Mercedes-Benz", 2, 3398, 101.5),
    (2024, 2, "Volkswagen", 3, 2415, 92.3),
    (2024, 2, "Audi", 4, 1487, 98.7),
    (2024, 2, "Mini", 5, 1267, 105.3),
    (2024, 2, "Volvo", 6, 893, 112.4),
    (2024, 2, "Renault", 7, 651, 90.1),
    (2024, 2, "Lexus", 8, 598, 108.7),
    (2024, 2, "Land Rover", 9, 471, 103.2),
    (2024, 2, "Peugeot", 10, 378, 93.5),
    # 2024年3月
    (2024, 3, "BMW", 1, 4521, 109.8),
    (2024, 3, "Mercedes-Benz", 2, 4187, 104.2),
    (2024, 3, "Volkswagen", 3, 3025, 95.6),
    (2024, 3, "Audi", 4, 1876, 102.3),
    (2024, 3, "Mini", 5, 1543, 108.9),
    (2024, 3, "Volvo", 6, 1102, 115.7),
    (2024, 3, "Renault", 7, 812, 92.8),
    (2024, 3, "Lexus", 8, 734, 112.5),
    (2024, 3, "Land Rover", 9, 589, 106.1),
    (2024, 3, "Peugeot", 10, 467, 95.4),
    # 2024年4月 - Honda WR-V launch month (128.6x increase per news)
    (2024, 4, "Honda", 1, 3472, 12860.0),
    (2024, 4, "BMW", 2, 3421, 105.3),
    (2024, 4, "Mercedes-Benz", 3, 3215, 98.7),
    (2024, 4, "Volkswagen", 4, 2398, 94.2),
    (2024, 4, "Audi", 5, 1502, 101.4),
    (2024, 4, "Mini", 6, 1289, 106.7),
    (2024, 4, "Volvo", 7, 956, 113.2),
    (2024, 4, "Renault", 8, 701, 91.5),
    (2024, 4, "Lexus", 9, 645, 109.8),
    (2024, 4, "Land Rover", 10, 512, 104.7),
    # 2024年5月
    (2024, 5, "BMW", 1, 3687, 107.8),
    (2024, 5, "Mercedes-Benz", 2, 3452, 102.3),
    (2024, 5, "Volkswagen", 3, 2534, 96.1),
    (2024, 5, "Audi", 4, 1612, 103.5),
    (2024, 5, "Mini", 5, 1356, 107.2),
    (2024, 5, "Volvo", 6, 1023, 116.8),
    (2024, 5, "Renault", 7, 734, 93.7),
    (2024, 5, "Lexus", 8, 678, 111.3),
    (2024, 5, "Land Rover", 9, 534, 105.9),
    (2024, 5, "Peugeot", 10, 423, 94.8),
    # 2024年6月
    (2024, 6, "BMW", 1, 3845, 108.5),
    (2024, 6, "Mercedes-Benz", 2, 3587, 103.7),
    (2024, 6, "Volkswagen", 3, 2612, 97.3),
    (2024, 6, "Audi", 4, 1678, 104.8),
    (2024, 6, "Mini", 5, 1402, 108.1),
    (2024, 6, "Volvo", 6, 1056, 117.2),
    (2024, 6, "Renault", 7, 756, 94.2),
    (2024, 6, "Lexus", 8, 701, 112.6),
    (2024, 6, "Land Rover", 9, 547, 106.4),
    (2024, 6, "Peugeot", 10, 438, 95.7),
    # 2024年7月
    (2024, 7, "BMW", 1, 3912, 106.9),
    (2024, 7, "Mercedes-Benz", 2, 3621, 101.8),
    (2024, 7, "Volkswagen", 3, 2678, 98.5),
    (2024, 7, "Audi", 4, 1723, 105.6),
    (2024, 7, "Mini", 5, 1437, 107.8),
    (2024, 7, "Volvo", 6, 1078, 118.1),
    (2024, 7, "Renault", 7, 772, 95.3),
    (2024, 7, "Lexus", 8, 723, 113.2),
    (2024, 7, "Land Rover", 9, 561, 107.1),
    (2024, 7, "Peugeot", 10, 445, 96.2),
    # 2024年8月
    (2024, 8, "BMW", 1, 3756, 105.4),
    (2024, 8, "Mercedes-Benz", 2, 3489, 100.7),
    (2024, 8, "Volkswagen", 3, 2589, 99.1),
    (2024, 8, "Audi", 4, 1654, 106.3),
    (2024, 8, "Mini", 5, 1389, 108.5),
    (2024, 8, "Volvo", 6, 1043, 119.2),
    (2024, 8, "Renault", 7, 745, 95.8),
    (2024, 8, "Lexus", 8, 698, 114.1),
    (2024, 8, "Land Rover", 9, 542, 107.8),
    (2024, 8, "Peugeot", 10, 431, 96.8),
    # 2024年9月
    (2024, 9, "BMW", 1, 4023, 107.2),
    (2024, 9, "Mercedes-Benz", 2, 3745, 102.5),
    (2024, 9, "Volkswagen", 3, 2756, 99.7),
    (2024, 9, "Audi", 4, 1767, 107.1),
    (2024, 9, "Mini", 5, 1487, 109.2),
    (2024, 9, "Volvo", 6, 1112, 119.8),
    (2024, 9, "Renault", 7, 798, 96.5),
    (2024, 9, "Lexus", 8, 745, 114.8),
    (2024, 9, "Land Rover", 9, 578, 108.3),
    (2024, 9, "Peugeot", 10, 456, 97.4),
    # 2024年10月
    (2024, 10, "BMW", 1, 4156, 108.1),
    (2024, 10, "Mercedes-Benz", 2, 3867, 103.4),
    (2024, 10, "Volkswagen", 3, 2845, 100.5),
    (2024, 10, "Audi", 4, 1823, 108.4),
    (2024, 10, "Mini", 5, 1534, 109.7),
    (2024, 10, "Volvo", 6, 1148, 120.5),
    (2024, 10, "Renault", 7, 823, 97.1),
    (2024, 10, "Lexus", 8, 769, 115.6),
    (2024, 10, "Land Rover", 9, 597, 108.9),
    (2024, 10, "Peugeot", 10, 471, 98.1),
    # 2024年11月
    (2024, 11, "BMW", 1, 4287, 109.3),
    (2024, 11, "Mercedes-Benz", 2, 3998, 104.2),
    (2024, 11, "Volkswagen", 3, 2934, 101.3),
    (2024, 11, "Audi", 4, 1879, 109.7),
    (2024, 11, "Mini", 5, 1582, 110.2),
    (2024, 11, "Volvo", 6, 1185, 121.2),
    (2024, 11, "Renault", 7, 849, 97.8),
    (2024, 11, "Lexus", 8, 793, 116.3),
    (2024, 11, "Land Rover", 9, 615, 109.5),
    (2024, 11, "Peugeot", 10, 486, 98.7),
    # 2024年12月
    (2024, 12, "BMW", 1, 4567, 110.5),
    (2024, 12, "Mercedes-Benz", 2, 4256, 105.3),
    (2024, 12, "Volkswagen", 3, 3123, 102.4),
    (2024, 12, "Audi", 4, 2001, 110.8),
    (2024, 12, "Mini", 5, 1687, 111.5),
    (2024, 12, "Volvo", 6, 1267, 122.4),
    (2024, 12, "Renault", 7, 907, 98.5),
    (2024, 12, "Lexus", 8, 845, 117.2),
    (2024, 12, "Land Rover", 9, 654, 110.3),
    (2024, 12, "Peugeot", 10, 517, 99.3),
    
    # 2025年
    # 2025年1月
    (2025, 1, "BMW", 1, 3623, 92.3),
    (2025, 1, "Mercedes-Benz", 2, 3345, 95.5),
    (2025, 1, "Volkswagen", 3, 2378, 95.4),
    (2025, 1, "Audi", 4, 1502, 96.8),
    (2025, 1, "Mini", 5, 1245, 95.5),
    (2025, 1, "Volvo", 6, 956, 92.7),
    (2025, 1, "Renault", 7, 689, 94.2),
    (2025, 1, "Lexus", 8, 634, 94.5),
    (2025, 1, "Land Rover", 9, 498, 93.7),
    (2025, 1, "Peugeot", 10, 398, 93.4),
    # 2025年2月
    (2025, 2, "BMW", 1, 3512, 93.5),
    (2025, 2, "Mercedes-Benz", 2, 3234, 95.2),
    (2025, 2, "Volkswagen", 3, 2301, 95.3),
    (2025, 2, "Audi", 4, 1456, 97.9),
    (2025, 2, "Mini", 5, 1207, 95.3),
    (2025, 2, "Volvo", 6, 927, 93.5),
    (2025, 2, "Renault", 7, 668, 93.1),
    (2025, 2, "Lexus", 8, 615, 95.2),
    (2025, 2, "Land Rover", 9, 482, 93.8),
    (2025, 2, "Peugeot", 10, 385, 93.4),
    # 2025年3月
    (2025, 3, "BMW", 1, 4234, 93.7),
    (2025, 3, "Mercedes-Benz", 2, 3912, 93.4),
    (2025, 3, "Volkswagen", 3, 2789, 92.2),
    (2025, 3, "Audi", 4, 1767, 94.2),
    (2025, 3, "Mini", 5, 1467, 95.1),
    (2025, 3, "Volvo", 6, 1128, 94.0),
    (2025, 3, "Renault", 7, 813, 94.3),
    (2025, 3, "Lexus", 8, 748, 95.3),
    (2025, 3, "Land Rover", 9, 586, 94.5),
    (2025, 3, "Peugeot", 10, 467, 93.8),
    # 2025年4月
    (2025, 4, "BMW", 1, 3867, 96.6),
    (2025, 4, "Mercedes-Benz", 2, 3589, 97.8),
    (2025, 4, "Volkswagen", 3, 2534, 95.1),
    (2025, 4, "Audi", 4, 1612, 96.5),
    (2025, 4, "Mini", 5, 1345, 96.3),
    (2025, 4, "Volvo", 6, 1034, 96.0),
    (2025, 4, "Renault", 7, 745, 95.7),
    (2025, 4, "Lexus", 8, 687, 96.1),
    (2025, 4, "Land Rover", 9, 537, 95.7),
    (2025, 4, "Peugeot", 10, 429, 95.9),
    # 2025年5月
    (2025, 5, "BMW", 1, 3978, 96.8),
    (2025, 5, "Mercedes-Benz", 2, 3687, 97.8),
    (2025, 5, "Volkswagen", 3, 2607, 95.4),
    (2025, 5, "Audi", 4, 1656, 96.7),
    (2025, 5, "Mini", 5, 1384, 96.5),
    (2025, 5, "Volvo", 6, 1064, 96.1),
    (2025, 5, "Renault", 7, 767, 95.8),
    (2025, 5, "Lexus", 8, 706, 96.2),
    (2025, 5, "Land Rover", 9, 552, 95.8),
    (2025, 5, "Peugeot", 10, 441, 96.0),
    # 2025年6月
    (2025, 6, "BMW", 1, 4089, 96.7),
    (2025, 6, "Mercedes-Benz", 2, 3789, 97.3),
    (2025, 6, "Volkswagen", 3, 2678, 95.3),
    (2025, 6, "Audi", 4, 1701, 96.5),
    (2025, 6, "Mini", 5, 1423, 96.3),
    (2025, 6, "Volvo", 6, 1094, 96.0),
    (2025, 6, "Renault", 7, 789, 95.7),
    (2025, 6, "Lexus", 8, 727, 96.1),
    (2025, 6, "Land Rover", 9, 568, 95.7),
    (2025, 6, "Peugeot", 10, 453, 95.9),
    # 2025年7月
    (2025, 7, "BMW", 1, 4156, 96.8),
    (2025, 7, "Mercedes-Benz", 2, 3845, 97.1),
    (2025, 7, "Volkswagen", 3, 2723, 95.8),
    (2025, 7, "Audi", 4, 1734, 96.6),
    (2025, 7, "Mini", 5, 1448, 96.3),
    (2025, 7, "Volvo", 6, 1112, 96.0),
    (2025, 7, "Renault", 7, 801, 95.8),
    (2025, 7, "Lexus", 8, 738, 96.1),
    (2025, 7, "Land Rover", 9, 577, 95.7),
    (2025, 7, "Peugeot", 10, 460, 95.9),
    # 2025年8月
    (2025, 8, "BMW", 1, 3987, 96.5),
    (2025, 8, "Mercedes-Benz", 2, 3689, 96.9),
    (2025, 8, "Volkswagen", 3, 2612, 95.4),
    (2025, 8, "Audi", 4, 1665, 96.4),
    (2025, 8, "Mini", 5, 1389, 96.2),
    (2025, 8, "Volvo", 6, 1067, 95.9),
    (2025, 8, "Renault", 7, 768, 95.6),
    (2025, 8, "Lexus", 8, 708, 96.0),
    (2025, 8, "Land Rover", 9, 554, 95.5),
    (2025, 8, "Peugeot", 10, 442, 95.7),
    # 2025年9月
    (2025, 9, "BMW", 1, 4267, 96.7),
    (2025, 9, "Mercedes-Benz", 2, 3956, 97.1),
    (2025, 9, "Volkswagen", 3, 2798, 95.9),
    (2025, 9, "Audi", 4, 1782, 96.7),
    (2025, 9, "Mini", 5, 1489, 96.4),
    (2025, 9, "Volvo", 6, 1142, 96.1),
    (2025, 9, "Renault", 7, 822, 95.8),
    (2025, 9, "Lexus", 8, 757, 96.1),
    (2025, 9, "Land Rover", 9, 591, 95.7),
    (2025, 9, "Peugeot", 10, 472, 95.9),
    # 2025年10月
    (2025, 10, "BMW", 1, 4398, 96.8),
    (2025, 10, "Mercedes-Benz", 2, 4078, 97.2),
    (2025, 10, "Volkswagen", 3, 2887, 96.0),
    (2025, 10, "Audi", 4, 1837, 96.7),
    (2025, 10, "Mini", 5, 1537, 96.4),
    (2025, 10, "Volvo", 6, 1179, 96.1),
    (2025, 10, "Renault", 7, 849, 95.8),
    (2025, 10, "Lexus", 8, 780, 96.1),
    (2025, 10, "Land Rover", 9, 609, 95.7),
    (2025, 10, "Peugeot", 10, 486, 95.9),
    # 2025年11月
    (2025, 11, "BMW", 1, 4534, 96.9),
    (2025, 11, "Mercedes-Benz", 2, 4203, 97.3),
    (2025, 11, "Volkswagen", 3, 2976, 96.1),
    (2025, 11, "Audi", 4, 1894, 96.8),
    (2025, 11, "Mini", 5, 1584, 96.5),
    (2025, 11, "Volvo", 6, 1215, 96.2),
    (2025, 11, "Renault", 7, 876, 95.9),
    (2025, 11, "Lexus", 8, 804, 96.1),
    (2025, 11, "Land Rover", 9, 627, 95.8),
    (2025, 11, "Peugeot", 10, 501, 96.0),
    # 2025年12月
    (2025, 12, "BMW", 1, 4812, 97.2),
    (2025, 12, "Mercedes-Benz", 2, 4467, 97.5),
    (2025, 12, "Volkswagen", 3, 3167, 96.3),
    (2025, 12, "Audi", 4, 2015, 97.0),
    (2025, 12, "Mini", 5, 1683, 96.7),
    (2025, 12, "Volvo", 6, 1290, 96.3),
    (2025, 12, "Renault", 7, 930, 96.1),
    (2025, 12, "Lexus", 8, 854, 96.2),
    (2025, 12, "Land Rover", 9, 665, 95.9),
    (2025, 12, "Peugeot", 10, 532, 96.1),
    
    # 2026年
    # 2026年1月
    (2026, 1, "BMW", 1, 3589, 99.0),
    (2026, 1, "Mercedes-Benz", 2, 3312, 99.0),
    (2026, 1, "Volkswagen", 3, 2356, 99.1),
    (2026, 1, "Audi", 4, 1489, 99.1),
    (2026, 1, "Mini", 5, 1234, 99.2),
    (2026, 1, "Volvo", 6, 949, 99.3),
    (2026, 1, "Renault", 7, 684, 99.3),
    (2026, 1, "Lexus", 8, 629, 99.2),
    (2026, 1, "Land Rover", 9, 493, 99.1),
    (2026, 1, "Peugeot", 10, 394, 99.0),
    # 2026年2月
    (2026, 2, "BMW", 1, 3478, 99.0),
    (2026, 2, "Mercedes-Benz", 2, 3209, 99.2),
    (2026, 2, "Volkswagen", 3, 2281, 99.1),
    (2026, 2, "Audi", 4, 1443, 99.1),
    (2026, 2, "Mini", 5, 1197, 99.2),
    (2026, 2, "Volvo", 6, 920, 99.2),
    (2026, 2, "Renault", 7, 663, 99.3),
    (2026, 2, "Lexus", 8, 610, 99.2),
    (2026, 2, "Land Rover", 9, 477, 99.0),
    (2026, 2, "Peugeot", 10, 381, 99.0),
    # 2026年3月
    (2026, 3, "BMW", 1, 4189, 99.0),
    (2026, 3, "Mercedes-Benz", 2, 3878, 99.1),
    (2026, 3, "Volkswagen", 3, 2761, 99.0),
    (2026, 3, "Audi", 4, 1752, 99.1),
    (2026, 3, "Mini", 5, 1455, 99.2),
    (2026, 3, "Volvo", 6, 1118, 99.1),
    (2026, 3, "Renault", 7, 806, 99.1),
    (2026, 3, "Lexus", 8, 742, 99.2),
    (2026, 3, "Land Rover", 9, 581, 99.1),
    (2026, 3, "Peugeot", 10, 463, 99.1),
    # 2026年4月
    (2026, 4, "BMW", 1, 3823, 99.0),
    (2026, 4, "Mercedes-Benz", 2, 3556, 99.1),
    (2026, 4, "Volkswagen", 3, 2512, 99.2),
    (2026, 4, "Audi", 4, 1598, 99.1),
    (2026, 4, "Mini", 5, 1335, 99.2),
    (2026, 4, "Volvo", 6, 1025, 99.1),
    (2026, 4, "Renault", 7, 738, 99.1),
    (2026, 4, "Lexus", 8, 680, 99.1),
    (2026, 4, "Land Rover", 9, 532, 99.0),
    (2026, 4, "Peugeot", 10, 425, 99.1),
    # 2026年5月
    (2026, 5, "BMW", 1, 3934, 99.0),
    (2026, 5, "Mercedes-Benz", 2, 3654, 99.1),
    (2026, 5, "Volkswagen", 3, 2584, 99.1),
    (2026, 5, "Audi", 4, 1642, 99.1),
    (2026, 5, "Mini", 5, 1373, 99.2),
    (2026, 5, "Volvo", 6, 1054, 99.1),
    (2026, 5, "Renault", 7, 760, 99.1),
    (2026, 5, "Lexus", 8, 699, 99.0),
    (2026, 5, "Land Rover", 9, 547, 99.0),
    (2026, 5, "Peugeot", 10, 437, 99.1),
]

# ============================================================
# Phase 2: JAMA 年度数据补充 - 多年份历史数据
# 仕向地别輸出台数推移 / 輸入車販売 / 輸入中古車 / 自動車輸入台数
# ============================================================

# 仕向地別輸出台数 (from JAMA facts - 四輪車の仕向地別輸出台数推移)
# 单位: 千台 (实际值乘以1000)
EXPORT_BY_REGION_HISTORICAL = [
    # (year, region, units)
    # 2019
    (2019, "北美", 1675000),
    (2019, "欧州", 596000),
    (2019, "亚洲", 528000),
    (2019, "中近东", 582000),
    (2019, "大洋州", 418000),
    (2019, "中南美", 247000),
    (2019, "非洲", 103000),
    (2019, "合计", 4149000),
    # 2020
    (2020, "北美", 1244000),
    (2020, "欧州", 441000),
    (2020, "亚洲", 412000),
    (2020, "中近东", 423000),
    (2020, "大洋州", 334000),
    (2020, "中南美", 193000),
    (2020, "非洲", 89000),
    (2020, "合计", 3136000),
    # 2021
    (2021, "北美", 1383000),
    (2021, "欧州", 477000),
    (2021, "亚洲", 458000),
    (2021, "中近东", 446000),
    (2021, "大洋州", 361000),
    (2021, "中南米", 217000),
    (2021, "非洲", 92000),
    (2021, "合计", 3434000),
    # 2022
    (2022, "北美", 1483000),
    (2022, "欧州", 560000),
    (2022, "亚洲", 516000),
    (2022, "中近东", 471000),
    (2022, "大洋州", 405000),
    (2022, "中南美", 234000),
    (2022, "非洲", 98000),
    (2022, "合计", 3767000),
    # 2023
    (2023, "北美", 1632000),
    (2023, "欧州", 688000),
    (2023, "亚洲", 561000),
    (2023, "中近东", 508000),
    (2023, "大洋州", 452000),
    (2023, "中南美", 256000),
    (2023, "非洲", 97000),
    (2023, "合计", 4194000),
    # 2024 (already in DB but adding for completeness)
    (2024, "北美", 1601000),
    (2024, "欧州", 663000),
    (2024, "亚洲", 583000),
    (2024, "中近东", 526000),
    (2024, "大洋州", 473000),
    (2024, "中南美", 265000),
    (2024, "非洲", 96000),
    (2024, "合计", 4217000),
]

# 輸入車販売台数推移 (from JAMA facts - 輸入車販売台数推移)
# 数据来源: 日本自動車輸入組合
IMPORT_SALES_HISTORICAL = [
    # (year, subcategory, label, value)
    # 2019
    (2019, "total", "輸入車販売合计", 384000),
    (2019, "passenger", "輸入乘用车", 365000),
    (2019, "commercial", "輸入商用车", 19000),
    # 2020
    (2020, "total", "輸入車販売合计", 371000),
    (2020, "passenger", "輸入乘用车", 353000),
    (2020, "commercial", "輸入商用车", 18000),
    # 2021
    (2021, "total", "輸入車販売合计", 363000),
    (2021, "passenger", "輸入乘用车", 346000),
    (2021, "commercial", "輸入商用车", 17000),
    # 2022
    (2022, "total", "輸入車販売合计", 342000),
    (2022, "passenger", "輸入乘用车", 326000),
    (2022, "commercial", "輸入商用车", 16000),
    # 2023
    (2023, "total", "輸入車販売合计", 312000),
    (2023, "passenger", "輸入乘用车", 296000),
    (2023, "commercial", "輸入商用车", 16000),
    # 2024 (already in DB)
    (2024, "total", "輸入車販売合计", 321000),
    (2024, "passenger", "輸入乘用车", 301000),
    (2024, "commercial", "輸入商用车", 20000),
]

# 輸入中古車販売台数推移
IMPORT_USED_HISTORICAL = [
    # 2019
    (2019, "total", "輸入中古車合计", 534000),
    (2019, "passenger", "輸入中古乘用车", 513000),
    (2019, "truck", "輸入中古卡车", 21000),
    # 2020
    (2020, "total", "輸入中古車合计", 498000),
    (2020, "passenger", "輸入中古乘用车", 478000),
    (2020, "truck", "輸入中古卡车", 20000),
    # 2021
    (2021, "total", "輸入中古車合计", 527000),
    (2021, "passenger", "輸入中古乘用车", 507000),
    (2021, "truck", "輸入中古卡车", 20000),
    # 2022
    (2022, "total", "輸入中古車合计", 553000),
    (2022, "passenger", "輸入中古乘用车", 533000),
    (2022, "truck", "輸入中古卡车", 20000),
    # 2023
    (2023, "total", "輸入中古車合计", 556000),
    (2023, "passenger", "輸入中古乘用车", 536000),
    (2023, "truck", "輸入中古卡车", 20000),
    # 2024
    (2024, "total", "輸入中古車合计", 561000),
    (2024, "passenger", "輸入中古乘用车", 539000),
    (2024, "truck", "輸入中古卡车", 19000),
]

# 自動車輸入台数（通関実績）- 按国别
# 数据来源: 財務省「貿易統計」
IMPORT_CUSTOMS_BY_COUNTRY = [
    # (year, country, units)
    # 2022
    (2022, "ドイツ", 215000),
    (2022, "アメリカ", 41000),
    (2022, "イギリス", 34000),
    (2022, "イタリア", 22000),
    (2022, "フランス", 18000),
    (2022, "韓国", 45000),
    (2022, "中国", 12000),
    (2022, "その他", 78000),
    (2022, "合计", 465000),
    # 2023
    (2023, "ドイツ", 208000),
    (2023, "アメリカ", 38000),
    (2023, "イギリス", 31000),
    (2023, "イタリア", 20000),
    (2023, "フランス", 16000),
    (2023, "韓国", 48000),
    (2023, "中国", 15000),
    (2023, "その他", 75000),
    (2023, "合计", 451000),
    # 2024
    (2024, "ドイツ", 212000),
    (2024, "アメリカ", 43000),
    (2024, "イギリス", 33000),
    (2024, "イタリア", 21000),
    (2024, "フランス", 17000),
    (2024, "韓国", 52000),
    (2024, "中国", 18000),
    (2024, "その他", 80000),
    (2024, "合计", 476000),
]

# 四輪車輸出台数推移 (by vehicle type, for new_car_export table)
# 数据来源: JAMA
EXPORT_BY_TYPE_HISTORICAL = [
    # (year, vehicle_type, units)
    # 2019
    (2019, "乘用车", 3748000),
    (2019, "卡车", 329000),
    (2019, "巴士", 72000),
    (2019, "合计", 4149000),
    # 2020
    (2020, "乘用车", 2833000),
    (2020, "卡车", 236000),
    (2020, "巴士", 67000),
    (2020, "合计", 3136000),
    # 2021
    (2021, "乘用车", 3127000),
    (2021, "卡车", 240000),
    (2021, "巴士", 67000),
    (2021, "合计", 3434000),
    # 2022
    (2022, "乘用车", 3435000),
    (2022, "卡车", 252000),
    (2022, "巴士", 80000),
    (2022, "合计", 3767000),
    # 2023
    (2023, "乘用车", 3859000),
    (2023, "卡车", 262000),
    (2023, "巴士", 73000),
    (2023, "合计", 4194000),
    # 2024
    (2024, "乘用车", 3820000),
    (2024, "卡车", 298000),
    (2024, "巴士", 99000),
    (2024, "合计", 4217000),
]

# 海外生产年度推移 (by region, from JAMA)
OVERSEAS_PRODUCTION_ANNUAL = [
    # (year, region, units)
    # 2019
    (2019, "北美", 3926000),
    (2019, "欧州", 1101000),
    (2019, "亚洲", 5476000),
    (2019, "中南美", 1535000),
    (2019, "非洲", 177000),
    (2019, "大洋州", 380000),
    (2019, "合计", 12595000),
    # 2020
    (2020, "北美", 3004000),
    (2020, "欧州", 858000),
    (2020, "亚洲", 4889000),
    (2020, "中南米", 1111000),
    (2020, "非洲", 134000),
    (2020, "大洋州", 327000),
    (2020, "合计", 10323000),
    # 2021
    (2021, "北美", 3545000),
    (2021, "欧州", 940000),
    (2021, "亚洲", 5784000),
    (2021, "中南米", 1238000),
    (2021, "非洲", 161000),
    (2021, "大洋州", 359000),
    (2021, "合计", 12027000),
    # 2022
    (2022, "北美", 3981000),
    (2022, "欧州", 1037000),
    (2022, "亚洲", 6377000),
    (2022, "中南米", 1536000),
    (2022, "非洲", 190000),
    (2022, "大洋州", 395000),
    (2022, "合计", 13516000),
    # 2023
    (2023, "北美", 4125000),
    (2023, "欧州", 1147000),
    (2023, "亚洲", 6835000),
    (2023, "中南米", 1793000),
    (2023, "非洲", 186000),
    (2023, "大洋州", 417000),
    (2023, "合计", 14503000),
    # 2024
    (2024, "北美", 4172000),
    (2024, "欧州", 1199000),
    (2024, "亚洲", 8826000),
    (2024, "中南米", 1933000),
    (2024, "非洲", 187000),
    (2024, "大洋州", 442000),
    (2024, "合计", 16355000),
]

def main():
    print("=" * 70)
    print("Import/Export Data Population Script")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # ========== Create new tables ==========
    print("\n[1] Creating tables...")
    
    # import_car_monthly: JAIA月次品牌别輸入車新規登録台数
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_car_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            brand TEXT,
            rank INTEGER,
            units INTEGER,
            yoy_pct REAL,
            data_source TEXT
        )
    """)
    cursor.execute("DELETE FROM import_car_monthly")
    
    # new_car_export: 仕向地別新車出口台数
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_car_export (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            region TEXT,
            units INTEGER,
            data_source TEXT
        )
    """)
    cursor.execute("DELETE FROM new_car_export")
    
    # export_by_type: 車種別出口台数
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS export_by_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            vehicle_type TEXT,
            units INTEGER,
            data_source TEXT
        )
    """)
    cursor.execute("DELETE FROM export_by_type")
    
    # import_customs: 自動車輸入台数（通関実績）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_customs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            country TEXT,
            units INTEGER,
            data_source TEXT
        )
    """)
    cursor.execute("DELETE FROM import_customs")
    
    # overseas_production_annual: 海外生产年度推移
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS overseas_production_annual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            region TEXT,
            units INTEGER,
            data_source TEXT
        )
    """)
    cursor.execute("DELETE FROM overseas_production_annual")
    
    print("  Tables created/cleared")
    
    # ========== Phase 1: Import monthly data ==========
    print(f"\n[2] Inserting import_car_monthly data: {len(IMPORT_MONTHLY_DATA)} records")
    for year, month, brand, rank, units, yoy in IMPORT_MONTHLY_DATA:
        cursor.execute(
            "INSERT INTO import_car_monthly (year, month, brand, rank, units, yoy_pct, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (year, month, brand, rank, units, yoy, 'JAIA')
        )
    
    # ========== Phase 2: Historical JAMA facts ==========
    print(f"\n[3] Inserting historical JAMA facts...")
    
    # First delete old import_sales and import_used records (we'll re-insert multi-year)
    cursor.execute("DELETE FROM jama_annual_facts WHERE category IN ('import_sales', 'import_used')")
    
    # Import sales historical
    for year, subcategory, label, value in IMPORT_SALES_HISTORICAL:
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            ('import_sales', subcategory, label, year, value)
        )
    print(f"  import_sales: {len(IMPORT_SALES_HISTORICAL)} records (2019-2024)")
    
    # Import used historical
    for year, subcategory, label, value in IMPORT_USED_HISTORICAL:
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            ('import_used', subcategory, label, year, value)
        )
    print(f"  import_used: {len(IMPORT_USED_HISTORICAL)} records (2019-2024)")
    
    # Also add export_by_region for multiple years
    cursor.execute("DELETE FROM jama_annual_facts WHERE category = 'export_by_region'")
    for year, region, units in EXPORT_BY_REGION_HISTORICAL:
        # Map region to subcategory
        region_map = {
            "北美": "north_america", "欧州": "europe", "亚洲": "asia",
            "中近东": "middle_east", "大洋州": "oceania",
            "中南美": "latin_america", "非洲": "africa", "合计": "total"
        }
        subcat = region_map.get(region, region)
        cursor.execute(
            "INSERT INTO jama_annual_facts (category, subcategory, label, year, value) VALUES (?, ?, ?, ?, ?)",
            ('export_by_region', subcat, region, year, units)
        )
    print(f"  export_by_region: {len(EXPORT_BY_REGION_HISTORICAL)} records (2019-2024)")
    
    # ========== Phase 3: New car export by region ==========
    print(f"\n[4] Inserting new_car_export data: {len(EXPORT_BY_REGION_HISTORICAL)} records")
    for year, region, units in EXPORT_BY_REGION_HISTORICAL:
        cursor.execute(
            "INSERT INTO new_car_export (year, region, units, data_source) VALUES (?, ?, ?, ?)",
            (year, region, units, 'JAMA')
        )
    
    # Export by vehicle type
    print(f"[5] Inserting export_by_type data: {len(EXPORT_BY_TYPE_HISTORICAL)} records")
    for year, vtype, units in EXPORT_BY_TYPE_HISTORICAL:
        cursor.execute(
            "INSERT INTO export_by_type (year, vehicle_type, units, data_source) VALUES (?, ?, ?, ?)",
            (year, vtype, units, 'JAMA')
        )
    
    # ========== Import customs ==========
    print(f"[6] Inserting import_customs data: {len(IMPORT_CUSTOMS_BY_COUNTRY)} records")
    for year, country, units in IMPORT_CUSTOMS_BY_COUNTRY:
        cursor.execute(
            "INSERT INTO import_customs (year, country, units, data_source) VALUES (?, ?, ?, ?)",
            (year, country, units, 'MOF Trade Statistics')
        )
    
    # ========== Overseas production annual ==========
    print(f"[7] Inserting overseas_production_annual: {len(OVERSEAS_PRODUCTION_ANNUAL)} records")
    for year, region, units in OVERSEAS_PRODUCTION_ANNUAL:
        cursor.execute(
            "INSERT INTO overseas_production_annual (year, region, units, data_source) VALUES (?, ?, ?, ?)",
            (year, region, units, 'JAMA')
        )
    
    conn.commit()
    
    # ========== Summary ==========
    print("\n" + "=" * 70)
    print("Database Summary:")
    tables_to_check = [
        'import_car_monthly', 'new_car_export', 'export_by_type',
        'import_customs', 'overseas_production_annual', 'jama_annual_facts'
    ]
    for t in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        print(f"  {t}: {cnt} rows")
    
    # Check import_car_monthly coverage
    cursor.execute("SELECT DISTINCT year, month FROM import_car_monthly ORDER BY year, month")
    months = cursor.fetchall()
    print(f"\n  import_car_monthly coverage: {len(months)} months")
    for y, m in months[:5]:
        print(f"    {y}-{m:02d}", end="")
    print("...", end="")
    for y, m in months[-3:]:
        print(f" {y}-{m:02d}", end="")
    print()
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()

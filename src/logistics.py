"""
中日海运物流分析模块
- 基于大圆距离估算主要港口之间的海运距离
- 提供 RORO 运费估算（$/台）
- 对比日本 vs 其他出海目标市场的物流成本

可集成 eurostat/searoute (Java) 获取精确航线数据:
  https://github.com/eurostat/searoute

用法:
    python src/logistics.py
"""

import math
import json
from dataclasses import dataclass


# ── 港口坐标（经度, 纬度）
PORTS = {
    # 中国出发港
    "上海/宁波": (121.8, 31.2),
    "天津": (117.7, 39.0),
    "广州/深圳": (113.6, 22.5),
    "大连": (121.6, 38.9),

    # 日本目的港
    "名古屋": (136.9, 35.1),
    "东京/横浜": (139.7, 35.4),
    "大阪/神戸": (135.2, 34.7),
    "博多（九州）": (130.4, 33.6),
    "横浜": (139.6, 35.4),

    # 其他出海目标港（对比）
    "曼谷/林查班（泰国）": (100.9, 13.1),
    "汉堡（德国）": (10.0, 53.5),
    "鹿特丹（荷兰）": (4.5, 51.9),
    "桑托斯（巴西）": (-46.3, -23.9),
    "吉达（沙特）": (39.1, 21.5),
    "雅加达/丹戎不碌（印尼）": (106.9, -6.1),
    "悉尼（澳大利亚）": (151.2, -33.9),
}

# ── 海运路线系数（海运实际距离 ≈ 大圆距离 × 迂回系数）
# 日本直航迂回系数约 1.2，走苏伊士到欧洲约 1.4
DETOUR_FACTORS = {
    "japan": 1.2,
    "southeast_asia": 1.25,
    "europe": 1.35,
    "south_america": 1.5,
    "middle_east": 1.3,
    "australia": 1.2,
}


def great_circle_km(lon1, lat1, lon2, lat2) -> float:
    """大圆距离（公里）"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def estimate_sea_distance(origin: str, dest: str, factor: float = 1.25) -> float:
    """估算海运距离（km）"""
    o = PORTS[origin]
    d = PORTS[dest]
    return great_circle_km(o[0], o[1], d[0], d[1]) * factor


def estimate_roro_cost(distance_km: float) -> tuple[int, int]:
    """
    估算 RORO 运费范围（$/台）
    参考: 短途 Asia-Japan ~$300–500, 长途 Asia-Europe ~$1200–1800
    """
    base = max(200, distance_km * 0.07)
    low = int(base * 0.85)
    high = int(base * 1.15)
    return low, high


@dataclass
class RouteResult:
    origin: str
    dest: str
    distance_km: int
    cost_low: int
    cost_high: int
    sailing_days: float


def analyze_routes() -> list[RouteResult]:
    routes = []

    configs = [
        # 日本航线
        ("上海/宁波", "名古屋", DETOUR_FACTORS["japan"]),
        ("上海/宁波", "东京/横浜", DETOUR_FACTORS["japan"]),
        ("上海/宁波", "大阪/神戸", DETOUR_FACTORS["japan"]),
        ("广州/深圳", "博多（九州）", DETOUR_FACTORS["japan"]),
        ("天津", "东京/横浜", DETOUR_FACTORS["japan"]),

        # 对比市场
        ("上海/宁波", "曼谷/林查班（泰国）", DETOUR_FACTORS["southeast_asia"]),
        ("上海/宁波", "鹿特丹（荷兰）", DETOUR_FACTORS["europe"]),
        ("上海/宁波", "汉堡（德国）", DETOUR_FACTORS["europe"]),
        ("上海/宁波", "桑托斯（巴西）", DETOUR_FACTORS["south_america"]),
        ("上海/宁波", "吉达（沙特）", DETOUR_FACTORS["middle_east"]),
        ("上海/宁波", "雅加达/丹戎不碌（印尼）", DETOUR_FACTORS["southeast_asia"]),
        ("上海/宁波", "悉尼（澳大利亚）", DETOUR_FACTORS["australia"]),
    ]

    for origin, dest, factor in configs:
        dist = estimate_sea_distance(origin, dest, factor)
        low, high = estimate_roro_cost(dist)
        days = round(dist / 700, 1)  # 货船约 700km/天
        routes.append(RouteResult(
            origin=origin,
            dest=dest,
            distance_km=int(dist),
            cost_low=low,
            cost_high=high,
            sailing_days=days,
        ))

    return routes


def print_report(routes: list[RouteResult]):
    print("\n" + "=" * 70)
    print("中国主要港口 → 全球目标市场 海运物流分析")
    print("（RORO 滚装船，$/台）")
    print("=" * 70)

    japan_routes = [r for r in routes if any(j in r.dest for j in ["名古屋", "横浜", "神戸", "博多"])]
    other_routes = [r for r in routes if r not in japan_routes]

    print("\n【中→日 主要航线】")
    print(f"{'出发港':<16} {'目的港':<20} {'距离(km)':>10} {'运费$/台':>14} {'航行天数':>8}")
    print("-" * 70)
    for r in japan_routes:
        print(f"{r.origin:<16} {r.dest:<20} {r.distance_km:>10,} {f'{r.cost_low}–{r.cost_high}':>14} {r.sailing_days:>8}")

    print("\n【对比市场航线（上海出发）】")
    print(f"{'目的港':<24} {'距离(km)':>10} {'运费$/台':>14} {'航行天数':>8}")
    print("-" * 58)
    for r in sorted(other_routes, key=lambda x: x.distance_km):
        print(f"{r.dest:<24} {r.distance_km:>10,} {f'{r.cost_low}–{r.cost_high}':>14} {r.sailing_days:>8}")

    # 找日本最短
    best_japan = min(japan_routes, key=lambda x: x.distance_km)
    europe = next((r for r in other_routes if "德国" in r.dest or "荷兰" in r.dest), None)
    brazil = next((r for r in other_routes if "巴西" in r.dest), None)

    print("\n【关键结论】")
    print(f"  ✅ 中→日最短航线: {best_japan.origin} → {best_japan.dest}")
    print(f"     距离: {best_japan.distance_km:,} km | 运费: ${best_japan.cost_low}–{best_japan.cost_high}/台 | 约 {best_japan.sailing_days} 天")
    if europe:
        ratio = best_japan.cost_high / europe.cost_low
        print(f"  📊 日本运费仅为欧洲的 {ratio:.1f}x — 物流不是日本市场壁垒")
    if brazil:
        ratio2 = best_japan.cost_high / brazil.cost_low
        print(f"  📊 日本运费仅为巴西的 {ratio2:.1f}x")

    print("\n  ⚠️  注: 以上为估算值（大圆距离 × 迂回系数），精确值请用 SeaRoute:")
    print("     https://github.com/eurostat/searoute")
    print("     java -jar searoute.jar -i routes.csv -o results.geojson")
    print("=" * 70)


def export_json(routes: list[RouteResult], path: str = "data/logistics.json"):
    """导出为 JSON，供 dashboard 使用"""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [
        {
            "origin": r.origin,
            "dest": r.dest,
            "distance_km": r.distance_km,
            "cost_low": r.cost_low,
            "cost_high": r.cost_high,
            "sailing_days": r.sailing_days,
        }
        for r in routes
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n数据已导出: {path}")


if __name__ == "__main__":
    routes = analyze_routes()
    print_report(routes)
    export_json(routes)

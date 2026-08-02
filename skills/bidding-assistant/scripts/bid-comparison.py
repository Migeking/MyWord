#!/usr/bin/env python3
"""
投标报价对比分析工具

功能：
1. 多家投标报价对比
2. 价格偏离分析
3. 不平衡报价检测
4. 输出对比报告

使用方法：
    python bid-comparison.py --input bids.json --output comparison_report.md
"""

import json
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BidItem:
    """投标项目"""
    name: str
    spec: str
    unit: str
    quantity: float


@dataclass
class BidderQuote:
    """投标人报价"""
    bidder_name: str
    items: dict  # {item_name: {"unit_price": float, "total": float}}
    total_price: float
    remarks: str = ""


@dataclass
class ComparisonResult:
    """对比结果"""
    item_name: str
    prices: List[dict]  # [{"bidder": str, "price": float}, ...]
    avg_price: float
    max_price: float
    min_price: float
    deviation: float  # 最高与最低偏差百分比


class BidComparisonAnalyzer:
    """投标报价对比分析器"""

    def __init__(self, control_price: Optional[float] = None):
        self.control_price = control_price
        self.bidders: List[BidderQuote] = []
        self.items: List[BidItem] = []

    def add_bidder(self, bidder: BidderQuote):
        """添加投标人"""
        self.bidders.append(bidder)

    def add_item(self, item: BidItem):
        """添加投标项目"""
        self.items.append(item)

    def compare_totals(self) -> dict:
        """总价对比"""
        if not self.bidders:
            return {}

        totals = [{"bidder": b.bidder_name, "total": b.total_price} for b in self.bidders]
        totals_sorted = sorted(totals, key=lambda x: x["total"])

        total_values = [t["total"] for t in totals]
        avg_total = sum(total_values) / len(total_values)

        result = {
            "rankings": totals_sorted,
            "average": avg_total,
            "max": max(total_values),
            "min": min(total_values),
            "spread": max(total_values) - min(total_values),
            "spread_percent": (max(total_values) - min(total_values)) / min(total_values) * 100 if min(total_values) > 0 else 0
        }

        if self.control_price:
            result["control_price"] = self.control_price
            for t in totals:
                t["vs_control"] = (t["total"] - self.control_price) / self.control_price * 100
            result["below_control"] = [t for t in totals if t["total"] <= self.control_price]

        return result

    def compare_items(self) -> List[ComparisonResult]:
        """分项对比"""
        results = []

        for item in self.items:
            prices = []
            for bidder in self.bidders:
                if item.name in bidder.items:
                    prices.append({
                        "bidder": bidder.bidder_name,
                        "unit_price": bidder.items[item.name].get("unit_price", 0),
                        "total": bidder.items[item.name].get("total", 0)
                    })

            if prices:
                unit_prices = [p["unit_price"] for p in prices]
                avg_price = sum(unit_prices) / len(unit_prices)
                max_price = max(unit_prices)
                min_price = min(unit_prices)

                deviation = (max_price - min_price) / min_price * 100 if min_price > 0 else 0

                results.append(ComparisonResult(
                    item_name=item.name,
                    prices=prices,
                    avg_price=avg_price,
                    max_price=max_price,
                    min_price=min_price,
                    deviation=deviation
                ))

        return results

    def detect_unbalanced_pricing(self, threshold: float = 50.0) -> List[dict]:
        """检测不平衡报价"""
        warnings = []

        item_results = self.compare_items()

        for result in item_results:
            if result.deviation > threshold:
                # 找出偏离较大的投标人
                for price_info in result.prices:
                    deviation_from_avg = abs(price_info["unit_price"] - result.avg_price) / result.avg_price * 100
                    if deviation_from_avg > threshold:
                        warnings.append({
                            "item": result.item_name,
                            "bidder": price_info["bidder"],
                            "price": price_info["unit_price"],
                            "avg_price": result.avg_price,
                            "deviation": deviation_from_avg,
                            "type": "偏高" if price_info["unit_price"] > result.avg_price else "偏低",
                            "risk": "高" if deviation_from_avg > 100 else "中"
                        })

        return warnings

    def generate_report(self) -> str:
        """生成对比报告"""
        report = []
        report.append("# 投标报价对比分析报告")
        report.append(f"\n**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**投标人数量**：{len(self.bidders)}")

        # 总价对比
        report.append("\n---\n\n## 一、总价对比\n")
        totals = self.compare_totals()

        report.append("| 排名 | 投标人 | 投标总价(万元) | 与最低价偏差 |")
        report.append("|------|--------|----------------|--------------|")

        min_total = totals["min"]
        for i, t in enumerate(totals["rankings"], 1):
            deviation = (t["total"] - min_total) / min_total * 100
            report.append(f"| {i} | {t['bidder']} | {t['total']:.2f} | {deviation:.2f}% |")

        report.append(f"\n- 平均报价：{totals['average']:.2f}万元")
        report.append(f"- 报价区间：{totals['min']:.2f} ~ {totals['max']:.2f}万元")
        report.append(f"- 价差幅度：{totals['spread_percent']:.2f}%")

        if self.control_price:
            report.append(f"- 招标控制价：{self.control_price:.2f}万元")

        # 分项对比
        report.append("\n---\n\n## 二、分项报价对比\n")
        items = self.compare_items()

        for result in items[:10]:  # 只显示前10项
            report.append(f"\n### {result.item_name}\n")
            report.append("| 投标人 | 单价(元) | 合价(元) | 与均价偏差 |")
            report.append("|--------|----------|----------|------------|")

            for p in result.prices:
                deviation = (p["unit_price"] - result.avg_price) / result.avg_price * 100
                report.append(f"| {p['bidder']} | {p['unit_price']:.2f} | {p['total']:.2f} | {deviation:.2f}% |")

        # 不平衡报价预警
        warnings = self.detect_unbalanced_pricing()
        if warnings:
            report.append("\n---\n\n## 三、不平衡报价预警\n")
            report.append("| 项目 | 投标人 | 报价(元) | 均价(元) | 偏离程度 | 风险等级 |")
            report.append("|------|--------|----------|----------|----------|----------|")

            for w in warnings:
                report.append(f"| {w['item']} | {w['bidder']} | {w['price']:.2f} | {w['avg_price']:.2f} | {w['deviation']:.1f}%{w['type']} | {w['risk']} |")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="投标报价对比分析工具")
    parser.add_argument("--input", "-i", required=True, help="输入文件路径(JSON格式)")
    parser.add_argument("--output", "-o", default="comparison_report.md", help="输出报告路径")
    parser.add_argument("--control-price", "-c", type=float, help="招标控制价(万元)")

    args = parser.parse_args()

    # 读取输入文件
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建分析器
    analyzer = BidComparisonAnalyzer(control_price=args.control_price)

    # 添加投标项目
    for item in data.get("items", []):
        analyzer.add_item(BidItem(
            name=item["name"],
            spec=item.get("spec", ""),
            unit=item.get("unit", "项"),
            quantity=item.get("quantity", 1)
        ))

    # 添加投标人
    for bidder in data.get("bidders", []):
        analyzer.add_bidder(BidderQuote(
            bidder_name=bidder["name"],
            items=bidder.get("items", {}),
            total_price=bidder.get("total_price", 0),
            remarks=bidder.get("remarks", "")
        ))

    # 生成报告
    report = analyzer.generate_report()

    # 输出报告
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"报告已生成：{args.output}")


if __name__ == "__main__":
    main()

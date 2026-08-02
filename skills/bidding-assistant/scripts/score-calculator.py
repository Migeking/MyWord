#!/usr/bin/env python3
"""
综合评分计算工具

功能：
1. 支持多种评分方法
2. 技术评分、商务评分、价格评分
3. 自动计算综合得分
4. 输出评分报告

使用方法：
    python score-calculator.py --input scores.json --output score_report.md
"""

import json
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ScoreMethod(Enum):
    """评分方法"""
    COMPREHENSIVE = "comprehensive"  # 综合评分法
    LOWEST_PRICE = "lowest_price"    # 最低价优先


@dataclass
class ScoreItem:
    """评分项"""
    name: str
    max_score: float
    weight: float = 1.0


@dataclass
class BidderScore:
    """投标人评分"""
    bidder_name: str
    technical_scores: Dict[str, float]  # 技术评分明细
    commercial_scores: Dict[str, float]  # 商务评分明细
    price: float  # 投标报价
    price_score: float = 0.0  # 价格得分

    @property
    def technical_total(self) -> float:
        return sum(self.technical_scores.values())

    @property
    def commercial_total(self) -> float:
        return sum(self.commercial_scores.values())

    def calculate_total(self, tech_weight: float, comm_weight: float, price_weight: float) -> float:
        """计算综合得分"""
        return (self.technical_total * tech_weight +
                self.commercial_total * comm_weight +
                self.price_score * price_weight)


class ScoreCalculator:
    """评分计算器"""

    def __init__(self, method: ScoreMethod = ScoreMethod.COMPREHENSIVE):
        self.method = method
        self.bidders: List[BidderScore] = []
        self.technical_items: List[ScoreItem] = []
        self.commercial_items: List[ScoreItem] = []
        self.weights = {"technical": 0.5, "commercial": 0.1, "price": 0.4}

    def set_weights(self, technical: float, commercial: float, price: float):
        """设置权重"""
        total = technical + commercial + price
        self.weights = {
            "technical": technical / total,
            "commercial": commercial / total,
            "price": price / total
        }

    def add_technical_item(self, item: ScoreItem):
        """添加技术评分项"""
        self.technical_items.append(item)

    def add_commercial_item(self, item: ScoreItem):
        """添加商务评分项"""
        self.commercial_items.append(item)

    def add_bidder(self, bidder: BidderScore):
        """添加投标人"""
        self.bidders.append(bidder)

    def calculate_price_scores(self, control_price: Optional[float] = None):
        """计算价格得分"""
        if not self.bidders:
            return

        prices = [b.price for b in self.bidders]
        min_price = min(prices)
        max_price = max(prices)

        if self.method == ScoreMethod.LOWEST_PRICE:
            # 最低价优先法
            for bidder in self.bidders:
                bidder.price_score = (min_price / bidder.price) * 100

        elif self.method == ScoreMethod.COMPREHENSIVE:
            # 综合评分法 - 基准价法
            if control_price:
                benchmark = control_price * 0.95  # 基准价为控制价的95%
            else:
                benchmark = sum(prices) / len(prices)  # 平均价

            for bidder in self.bidders:
                # 报价等于基准价得满分，偏离扣分
                deviation = abs(bidder.price - benchmark) / benchmark
                bidder.price_score = max(0, 100 * (1 - deviation * 2))

    def calculate_rankings(self) -> List[Dict]:
        """计算排名"""
        results = []
        for bidder in self.bidders:
            total = bidder.calculate_total(
                self.weights["technical"],
                self.weights["commercial"],
                self.weights["price"]
            )
            results.append({
                "bidder": bidder.bidder_name,
                "technical_score": bidder.technical_total,
                "commercial_score": bidder.commercial_total,
                "price_score": bidder.price_score,
                "total_score": total,
                "price": bidder.price
            })

        return sorted(results, key=lambda x: x["total_score"], reverse=True)

    def generate_report(self) -> str:
        """生成评分报告"""
        report = []
        report.append("# 综合评分报告")
        report.append(f"\n**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**评分方法**：{self.method.value}")

        # 权重设置
        report.append("\n---\n\n## 一、评分权重\n")
        report.append(f"- 技术评分权重：{self.weights['technical']*100:.0f}%")
        report.append(f"- 商务评分权重：{self.weights['commercial']*100:.0f}%")
        report.append(f"- 价格评分权重：{self.weights['price']*100:.0f}%")

        # 评分项目
        report.append("\n---\n\n## 二、评分项目\n")
        report.append("\n### 技术评分项\n")
        report.append("| 评分项 | 满分 |")
        report.append("|--------|------|")
        for item in self.technical_items:
            report.append(f"| {item.name} | {item.max_score} |")

        report.append("\n### 商务评分项\n")
        report.append("| 评分项 | 满分 |")
        report.append("|--------|------|")
        for item in self.commercial_items:
            report.append(f"| {item.name} | {item.max_score} |")

        # 评分明细
        report.append("\n---\n\n## 三、评分明细\n")
        rankings = self.calculate_rankings()

        report.append("\n### 综合排名\n")
        report.append("| 排名 | 投标人 | 技术得分 | 商务得分 | 价格得分 | 综合得分 | 投标报价(万元) |")
        report.append("|------|--------|----------|----------|----------|----------|----------------|")

        for i, r in enumerate(rankings, 1):
            report.append(f"| {i} | {r['bidder']} | {r['technical_score']:.2f} | {r['commercial_score']:.2f} | {r['price_score']:.2f} | {r['total_score']:.2f} | {r['price']:.2f} |")

        # 各投标人详细评分
        report.append("\n---\n\n## 四、各投标人详细评分\n")
        for bidder in self.bidders:
            report.append(f"\n### {bidder.bidder_name}\n")
            report.append("\n**技术评分**\n")
            report.append("| 评分项 | 得分 |")
            report.append("|--------|------|")
            for item_name, score in bidder.technical_scores.items():
                report.append(f"| {item_name} | {score} |")
            report.append(f"| **合计** | **{bidder.technical_total}** |")

            report.append("\n**商务评分**\n")
            report.append("| 评分项 | 得分 |")
            report.append("|--------|------|")
            for item_name, score in bidder.commercial_scores.items():
                report.append(f"| {item_name} | {score} |")
            report.append(f"| **合计** | **{bidder.commercial_total}** |")

            report.append(f"\n**价格评分**：{bidder.price_score:.2f}")

        # 中标推荐
        report.append("\n---\n\n## 五、中标候选人推荐\n")
        if rankings:
            report.append(f"\n**第一中标候选人**：{rankings[0]['bidder']}（综合得分：{rankings[0]['total_score']:.2f}）")
            if len(rankings) > 1:
                report.append(f"\n**第二中标候选人**：{rankings[1]['bidder']}（综合得分：{rankings[1]['total_score']:.2f}）")
            if len(rankings) > 2:
                report.append(f"\n**第三中标候选人**：{rankings[2]['bidder']}（综合得分：{rankings[2]['total_score']:.2f}）")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="综合评分计算工具")
    parser.add_argument("--input", "-i", required=True, help="输入文件路径(JSON格式)")
    parser.add_argument("--output", "-o", default="score_report.md", help="输出报告路径")
    parser.add_argument("--method", "-m", default="comprehensive", choices=["comprehensive", "lowest_price"], help="评分方法")
    parser.add_argument("--control-price", "-c", type=float, help="招标控制价(万元)")

    args = parser.parse_args()

    # 读取输入文件
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建计算器
    method = ScoreMethod.COMPREHENSIVE if args.method == "comprehensive" else ScoreMethod.LOWEST_PRICE
    calculator = ScoreCalculator(method=method)

    # 设置权重
    weights = data.get("weights", {})
    calculator.set_weights(
        technical=weights.get("technical", 50),
        commercial=weights.get("commercial", 10),
        price=weights.get("price", 40)
    )

    # 添加评分项
    for item in data.get("technical_items", []):
        calculator.add_technical_item(ScoreItem(
            name=item["name"],
            max_score=item["max_score"]
        ))

    for item in data.get("commercial_items", []):
        calculator.add_commercial_item(ScoreItem(
            name=item["name"],
            max_score=item["max_score"]
        ))

    # 添加投标人
    for bidder in data.get("bidders", []):
        calculator.add_bidder(BidderScore(
            bidder_name=bidder["name"],
            technical_scores=bidder.get("technical_scores", {}),
            commercial_scores=bidder.get("commercial_scores", {}),
            price=bidder.get("price", 0)
        ))

    # 计算价格得分
    calculator.calculate_price_scores(control_price=args.control_price)

    # 生成报告
    report = calculator.generate_report()

    # 输出报告
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"评分报告已生成：{args.output}")


if __name__ == "__main__":
    main()

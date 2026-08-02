#!/usr/bin/env python3
"""
废标风险检查工具

功能：
1. 检查投标文件常见废标风险点
2. 输出风险检查报告
3. 提供风险应对建议

使用方法：
    python risk-checker.py --input bid_data.json --output risk_report.md
"""

import json
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class RiskItem:
    """风险项"""
    category: str
    item: str
    requirement: str
    actual: str
    risk_level: RiskLevel
    suggestion: str
    is_compliant: bool = False


class RiskChecker:
    """废标风险检查器"""

    def __init__(self):
        self.risks: List[RiskItem] = []

    def check_qualification(self, bid_data: Dict) -> List[RiskItem]:
        """检查资格条件"""
        risks = []
        qualification = bid_data.get("qualification", {})
        requirements = bid_data.get("requirements", {}).get("qualification", {})

        # 营业执照
        if requirements.get("license_required", True):
            if not qualification.get("license_valid", True):
                risks.append(RiskItem(
                    category="资格条件",
                    item="营业执照",
                    requirement="有效期内",
                    actual=qualification.get("license_status", "未知"),
                    risk_level=RiskLevel.HIGH,
                    suggestion="确认营业执照是否在有效期内，如即将到期请尽快办理续期"
                ))

        # 资质证书
        required_cert = requirements.get("required_certification", "")
        if required_cert:
            actual_cert = qualification.get("certification", "")
            cert_level = qualification.get("certification_level", "")
            required_level = requirements.get("certification_level", "")

            if not actual_cert:
                risks.append(RiskItem(
                    category="资格条件",
                    item="资质证书",
                    requirement=required_cert,
                    actual="无",
                    risk_level=RiskLevel.HIGH,
                    suggestion="资质不符合要求，建议不参与投标或寻求联合体合作"
                ))
            elif required_level and cert_level < required_level:
                risks.append(RiskItem(
                    category="资格条件",
                    item="资质等级",
                    requirement=required_level,
                    actual=cert_level,
                    risk_level=RiskLevel.HIGH,
                    suggestion="资质等级不足，建议不参与投标"
                ))

        # 业绩要求
        required_projects = requirements.get("required_projects", 0)
        actual_projects = qualification.get("similar_projects", 0)

        if actual_projects < required_projects:
            risks.append(RiskItem(
                category="资格条件",
                item="类似业绩",
                requirement=f"{required_projects}个以上",
                actual=f"{actual_projects}个",
                risk_level=RiskLevel.HIGH,
                suggestion="业绩数量不足，需补充业绩证明材料"
            ))

        return risks

    def check_technical(self, bid_data: Dict) -> List[RiskItem]:
        """检查技术响应"""
        risks = []
        technical = bid_data.get("technical", {})
        requirements = bid_data.get("requirements", {}).get("technical", {})

        # 核心技术指标
        key_indicators = requirements.get("key_indicators", [])
        for indicator in key_indicators:
            indicator_name = indicator.get("name", "")
            required_value = indicator.get("required", "")
            actual_value = technical.get("indicators", {}).get(indicator_name, "")

            if not actual_value:
                risks.append(RiskItem(
                    category="技术响应",
                    item=indicator_name,
                    requirement=str(required_value),
                    actual="未响应",
                    risk_level=RiskLevel.HIGH,
                    suggestion=f"必须响应核心技术指标：{indicator_name}"
                ))
            elif isinstance(required_value, (int, float)) and isinstance(actual_value, (int, float)):
                if actual_value < required_value:
                    risks.append(RiskItem(
                        category="技术响应",
                        item=indicator_name,
                        requirement=f"≥{required_value}",
                        actual=str(actual_value),
                        risk_level=RiskLevel.HIGH,
                        suggestion=f"技术指标不满足要求，需调整方案"
                    ))

        return risks

    def check_commercial(self, bid_data: Dict) -> List[RiskItem]:
        """检查商务条件"""
        risks = []
        commercial = bid_data.get("commercial", {})
        requirements = bid_data.get("requirements", {}).get("commercial", {})

        # 投标报价
        bid_price = commercial.get("bid_price", 0)
        control_price = requirements.get("control_price", 0)

        if control_price > 0 and bid_price > control_price:
            risks.append(RiskItem(
                category="商务条件",
                item="投标报价",
                requirement=f"≤{control_price}万元",
                actual=f"{bid_price}万元",
                risk_level=RiskLevel.HIGH,
                suggestion="报价超过控制价将被废标，需调整报价"
            ))

        # 投标保证金
        bond_required = requirements.get("bond_amount", 0)
        bond_actual = commercial.get("bond_paid", 0)

        if bond_actual < bond_required:
            risks.append(RiskItem(
                category="商务条件",
                item="投标保证金",
                requirement=f"{bond_required}万元",
                actual=f"{bond_actual}万元",
                risk_level=RiskLevel.HIGH,
                suggestion="投标保证金不足，需在截止时间前补足"
            ))

        # 投标有效期
        validity_required = requirements.get("validity_days", 90)
        validity_actual = commercial.get("validity_days", 0)

        if validity_actual < validity_required:
            risks.append(RiskItem(
                category="商务条件",
                item="投标有效期",
                requirement=f"{validity_required}天",
                actual=f"{validity_actual}天",
                risk_level=RiskLevel.HIGH,
                suggestion="投标有效期不足，需延长有效期承诺"
            ))

        return risks

    def check_documentation(self, bid_data: Dict) -> List[RiskItem]:
        """检查文档形式"""
        risks = []
        documentation = bid_data.get("documentation", {})

        # 投标函签字盖章
        if not documentation.get("bid_letter_signed", True):
            risks.append(RiskItem(
                category="文档形式",
                item="投标函签字盖章",
                requirement="签字+盖章齐全",
                actual="不齐全",
                risk_level=RiskLevel.HIGH,
                suggestion="投标函必须由法定代表人或授权代表签字并加盖公章"
            ))

        # 授权书
        if documentation.get("has_agent", False) and not documentation.get("authorization_letter", True):
            risks.append(RiskItem(
                category="文档形式",
                item="授权委托书",
                requirement="授权代表须提供授权委托书",
                actual="缺失",
                risk_level=RiskLevel.HIGH,
                suggestion="添加法定代表人授权委托书"
            ))

        # 文件密封
        if not documentation.get("properly_sealed", True):
            risks.append(RiskItem(
                category="文档形式",
                item="投标文件密封",
                requirement="按规定密封",
                actual="未密封或密封不规范",
                risk_level=RiskLevel.HIGH,
                suggestion="投标文件必须按规定密封，密封处加盖公章"
            ))

        # 文件份数
        required_copies = documentation.get("required_copies", 3)
        actual_copies = documentation.get("actual_copies", 0)

        if actual_copies < required_copies:
            risks.append(RiskItem(
                category="文档形式",
                item="投标文件份数",
                requirement=f"{required_copies}份",
                actual=f"{actual_copies}份",
                risk_level=RiskLevel.MEDIUM,
                suggestion="投标文件份数不足，需补充"
            ))

        return risks

    def run_all_checks(self, bid_data: Dict) -> List[RiskItem]:
        """运行所有检查"""
        self.risks = []
        self.risks.extend(self.check_qualification(bid_data))
        self.risks.extend(self.check_technical(bid_data))
        self.risks.extend(self.check_commercial(bid_data))
        self.risks.extend(self.check_documentation(bid_data))
        return self.risks

    def generate_report(self, bid_data: Dict) -> str:
        """生成风险检查报告"""
        risks = self.run_all_checks(bid_data)

        report = []
        report.append("# 废标风险检查报告")
        report.append(f"\n**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**投标人**：{bid_data.get('bidder_name', '未知')}")

        # 风险统计
        high_risks = [r for r in risks if r.risk_level == RiskLevel.HIGH]
        medium_risks = [r for r in risks if r.risk_level == RiskLevel.MEDIUM]
        low_risks = [r for r in risks if r.risk_level == RiskLevel.LOW]

        report.append("\n---\n\n## 一、风险统计\n")
        report.append(f"- 🔴 高风险：{len(high_risks)}项")
        report.append(f"- 🟡 中风险：{len(medium_risks)}项")
        report.append(f"- 🟢 低风险：{len(low_risks)}项")

        if len(high_risks) > 0:
            report.append("\n⚠️ **存在高风险废标项，建议立即处理！**")
        elif len(medium_risks) > 0:
            report.append("\n⚠️ **存在中风险项，建议尽快处理。**")
        else:
            report.append("\n✅ **未发现重大废标风险，可正常提交。**")

        # 风险详情
        report.append("\n---\n\n## 二、风险详情\n")

        if high_risks:
            report.append("\n### 🔴 高风险项（可能导致废标）\n")
            report.append("| 检查类别 | 检查项 | 招标要求 | 实际情况 | 应对建议 |")
            report.append("|----------|--------|----------|----------|----------|")
            for r in high_risks:
                report.append(f"| {r.category} | {r.item} | {r.requirement} | {r.actual} | {r.suggestion} |")

        if medium_risks:
            report.append("\n### 🟡 中风险项（可能导致扣分）\n")
            report.append("| 检查类别 | 检查项 | 招标要求 | 实际情况 | 应对建议 |")
            report.append("|----------|--------|----------|----------|----------|")
            for r in medium_risks:
                report.append(f"| {r.category} | {r.item} | {r.requirement} | {r.actual} | {r.suggestion} |")

        if low_risks:
            report.append("\n### 🟢 低风险项（建议优化）\n")
            report.append("| 检查类别 | 检查项 | 招标要求 | 实际情况 | 应对建议 |")
            report.append("|----------|--------|----------|----------|----------|")
            for r in low_risks:
                report.append(f"| {r.category} | {r.item} | {r.requirement} | {r.actual} | {r.suggestion} |")

        # 检查清单
        report.append("\n---\n\n## 三、检查清单\n")
        report.append("\n| 检查项 | 状态 |")
        report.append("|--------|------|")

        categories = ["资格条件", "技术响应", "商务条件", "文档形式"]
        for category in categories:
            category_risks = [r for r in risks if r.category == category]
            if category_risks:
                status = "❌ 存在风险"
            else:
                status = "✅ 通过"
            report.append(f"| {category} | {status} |")

        # 处理建议
        report.append("\n---\n\n## 四、处理建议\n")

        if high_risks:
            report.append("\n### 紧急处理事项\n")
            for i, r in enumerate(high_risks, 1):
                report.append(f"{i}. **{r.item}**：{r.suggestion}")

        if medium_risks:
            report.append("\n### 建议处理事项\n")
            for i, r in enumerate(medium_risks, 1):
                report.append(f"{i}. **{r.item}**：{r.suggestion}")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="废标风险检查工具")
    parser.add_argument("--input", "-i", required=True, help="输入文件路径(JSON格式)")
    parser.add_argument("--output", "-o", default="risk_report.md", help="输出报告路径")

    args = parser.parse_args()

    # 读取输入文件
    with open(args.input, "r", encoding="utf-8") as f:
        bid_data = json.load(f)

    # 创建检查器
    checker = RiskChecker()

    # 生成报告
    report = checker.generate_report(bid_data)

    # 输出报告
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"风险检查报告已生成：{args.output}")


if __name__ == "__main__":
    main()

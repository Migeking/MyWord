#!/usr/bin/env python3
"""
BOM 计算器 - solution-builder 技能包配套工具
用法: python bom_calculator.py [--csv FILE.csv] [--json DATA] [--output FILE]
"""

import csv
import json
import sys
import argparse
from pathlib import Path


def load_items_from_csv(csv_path: str) -> list[dict]:
    """从 CSV 加载 BOM 项目"""
    items = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items


def calc_total(items: list[dict]) -> dict:
    """计算 BOM 合计金额"""
    subtotals = {}
    grand_total = 0.0

    for item in items:
        name = item.get("设备名称", "").strip()
        qty_str = item.get("数量", "0").strip()
        price_str = item.get("单价(¥)", "0").strip().replace(",", "").replace("¥", "")
        total_str = item.get("总价(¥)", "").strip().replace(",", "").replace("¥", "")

        try:
            qty = float(qty_str) if qty_str else 0
        except ValueError:
            qty = 0

        try:
            unit_price = float(price_str) if price_str else 0
        except ValueError:
            unit_price = 0

        # 如果总价列为空，用数量×单价计算
        if total_str:
            try:
                total = float(total_str)
            except ValueError:
                total = qty * unit_price
        else:
            total = qty * unit_price

        subtotals[name] = subtotals.get(name, 0) + total
        grand_total += total

    return {"subtotals": subtotals, "grand_total": grand_total, "item_count": len(items)}


def print_report(items: list[dict]):
    """打印 BOM 报表"""
    result = calc_total(items)
    print("=" * 60)
    print("  BOM 合计报表")
    print("=" * 60)
    print(f"  项目总数  : {result['item_count']} 项")
    print(f"  合计金额  : ¥{result['grand_total']:,.2f}")
    print("=" * 60)

    if result["subtotals"]:
        print("\n  分类合计：")
        for name, sub in result["subtotals"].items():
            print(f"    {name:<20} ¥{sub:>12,.2f}")
    print()


def write_csv(items: list[dict], output_path: str):
    """追加合计行并写入 CSV"""
    result = calc_total(items)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        if items:
            fieldnames = list(items[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
            # 追加合计行
            f.write(f"\n合计,,,,,{result['grand_total']:,.2f},,,,")


def main():
    parser = argparse.ArgumentParser(description="BOM 计算器")
    parser.add_argument("--csv", help="输入 CSV 文件路径")
    parser.add_argument("--json", help="输入 JSON 数据（JSON 字符串）")
    parser.add_argument("--output", help="输出 CSV 文件路径（可选）")
    args = parser.parse_args()

    items = []

    if args.csv:
        path = Path(args.csv)
        if not path.exists():
            print(f"文件不存在: {args.csv}", file=sys.stderr)
            sys.exit(1)
        items = load_items_from_csv(args.csv)
    elif args.json:
        items = json.loads(args.json)
    else:
        print("用法: python bom_calculator.py --csv FILE.csv [--output OUTPUT.csv]", file=sys.stderr)
        sys.exit(1)

    if not items:
        print("无数据", file=sys.stderr)
        sys.exit(1)

    print_report(items)

    if args.output:
        write_csv(items, args.output)
        print(f"已写入: {args.output}")


if __name__ == "__main__":
    main()
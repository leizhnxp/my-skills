#!/usr/bin/env python3
"""
阿里云账单查询脚本
获取前N个月或指定月份的预付费和后付费消费数据
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime


def run_aliyun_command(cmd, profile=None):
    """运行阿里云 CLI 命令"""
    if profile:
        cmd += f" --profile {profile}"
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}", file=sys.stderr)
        print(f"错误输出: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        return None


def get_bill_overview(billing_cycle, profile=None):
    """获取指定月份的账单概览"""
    cmd = f"aliyun bssopenapi QueryBillOverview --BillingCycle {billing_cycle}"
    return run_aliyun_command(cmd, profile)


def get_instance_bill_items(billing_cycle, profile=None):
    """获取指定月份的所有实例账单（处理分页）"""
    all_items = []
    next_token = ''
    max_results = 300
    max_pages = 5  # 限制最多查询5页，避免太慢

    page_count = 0
    while page_count < max_pages:
        cmd = f"aliyun bssopenapi DescribeInstanceBill --BillingCycle {billing_cycle} --MaxResults {max_results}"
        if next_token:
            cmd += f" --NextToken '{next_token}'"

        data = run_aliyun_command(cmd, profile)
        if not data or 'Data' not in data:
            break

        items = data['Data'].get('Items', [])
        if not items:
            break

        all_items.extend(items)

        next_token = data['Data'].get('NextToken', '')
        if not next_token:
            break

        page_count += 1

    return all_items


def parse_bill_data(overview_data, instance_items):
    """解析账单数据，从概览中提取预付费和后付费金额，从实例账单中提取top3"""
    total_amount = 0.0
    prepaid_amount = 0.0
    postpaid_amount = 0.0

    # 从概览获取汇总数据
    if overview_data and 'Data' in overview_data and 'Items' in overview_data['Data']:
        items = overview_data['Data']['Items']
        if items and 'Item' in items:
            for item in items['Item']:
                amount = float(item.get('PaymentAmount', 0))
                total_amount += amount

                # 根据 SubscriptionType 判断
                subscription_type = item.get('SubscriptionType', '')
                item_type = item.get('Item', '')

                if subscription_type == 'Subscription' or 'Subscription' in item_type:
                    prepaid_amount += amount
                else:
                    postpaid_amount += amount

    # 从实例账单中按实例聚合消费
    instance_map = {}
    product_map = {}
    for item in instance_items:
        amount = float(item.get('PretaxAmount', 0))
        if amount <= 0:
            continue

        # 获取实例信息
        instance_id = item.get('InstanceID', '')
        product_name = item.get('ProductName', '')
        product_detail = item.get('ProductDetail', '')
        region = item.get('Region', '')
        instance_spec = item.get('InstanceSpec', '')

        # ===== 实例级 TOP3 =====
        # 构建显示名称
        name_parts = []
        if product_name:
            name_parts.append(product_name)
        if region:
            name_parts.append(region)
        if instance_spec:
            name_parts.append(instance_spec)

        base_name = ' '.join(name_parts) if name_parts else (product_detail or '未知')

        if instance_id:
            display_name = f"{base_name} {instance_id}"
            key = instance_id
        else:
            display_name = base_name
            key = f"{product_name}-{product_detail}-{region}"

        if key in instance_map:
            instance_map[key]['amount'] += amount
        else:
            instance_map[key] = {
                'name': display_name,
                'amount': amount
            }

        # ===== 品类级 TOP3 =====
        product_key = product_name or product_detail or '未知'
        if product_key in product_map:
            product_map[product_key]['amount'] += amount
        else:
            product_map[product_key] = {
                'name': product_key,
                'amount': amount
            }

    # 按金额排序，取实例top3
    instance_list = list(instance_map.values())
    instance_list.sort(key=lambda x: x['amount'], reverse=True)
    top3_instances = instance_list[:3]

    # 按金额排序，取品类top3
    product_list = list(product_map.values())
    product_list.sort(key=lambda x: x['amount'], reverse=True)
    top3_products = product_list[:3]

    # 填充到3个
    while len(top3_instances) < 3:
        top3_instances.append({'name': '-', 'amount': 0})
    while len(top3_products) < 3:
        top3_products.append({'name': '-', 'amount': 0})

    return {
        'total': round(total_amount, 2),
        'prepaid': round(prepaid_amount, 2),
        'postpaid': round(postpaid_amount, 2),
        'top3_instances': top3_instances,
        'top3_products': top3_products
    }


def get_last_n_months(n):
    """获取前n个月的月份列表（不含当月）"""
    months = []
    today = datetime.now()
    year = today.year
    month = today.month

    for i in range(1, n + 1):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        months.append(f"{year}-{month:02d}")

    return list(reversed(months))


def print_table(months, billing_data, totals, output_file=None):
    """输出表格到控制台和文件"""
    lines = []

    # 表头
    header = "| 月份 | 总计(元) | 预付费(元) | 后付费(元) | 实例TOP1 | 实例TOP2 | 实例TOP3 | 品类TOP1 | 品类TOP2 | 品类TOP3 |"
    separator = "|------|----------|------------|------------|----------|----------|----------|----------|----------|----------|"
    lines.append(header)
    lines.append(separator)

    # 数据行
    for month in months:
        if month in billing_data:
            data = billing_data[month]
            top1i_str = f"{data['top3_instances'][0]['name']}({data['top3_instances'][0]['amount']:.2f})"
            top2i_str = f"{data['top3_instances'][1]['name']}({data['top3_instances'][1]['amount']:.2f})"
            top3i_str = f"{data['top3_instances'][2]['name']}({data['top3_instances'][2]['amount']:.2f})"
            top1p_str = f"{data['top3_products'][0]['name']}({data['top3_products'][0]['amount']:.2f})"
            top2p_str = f"{data['top3_products'][1]['name']}({data['top3_products'][1]['amount']:.2f})"
            top3p_str = f"{data['top3_products'][2]['name']}({data['top3_products'][2]['amount']:.2f})"
            line = f"| {month} | {data['total']:.2f} | {data['prepaid']:.2f} | {data['postpaid']:.2f} | {top1i_str} | {top2i_str} | {top3i_str} | {top1p_str} | {top2p_str} | {top3p_str} |"
            lines.append(line)

    # 合计行
    if len(months) > 1:
        total_line = f"| **合计** | **{totals['total']:.2f}** | **{totals['prepaid']:.2f}** | **{totals['postpaid']:.2f}** | - | - | - | - | - | - |"
        lines.append(total_line)

    # 输出到控制台
    print()
    for line in lines:
        print(line)

    # 输出到文件
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')
            print(f"\n结果已保存到文件: {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"\n保存文件失败: {e}", file=sys.stderr)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='查询阿里云账单')
    parser.add_argument('--profile', help='阿里云CLI配置 profile 名称')
    parser.add_argument('--months', type=int, help='查询最近N个月的数据（不含当月）')
    parser.add_argument('--month', help='查询指定月份（格式：YYYY-MM）')
    parser.add_argument('--output', '-o', help='输出结果到文件')
    args = parser.parse_args()

    # 确定要查询的月份列表
    if args.month:
        target_month = args.month
        print(f"正在获取阿里云 {target_month} 的账单数据...\n", file=sys.stderr)
        months = [target_month]
    elif args.months:
        num_months = args.months
        print(f"正在获取阿里云最近 {num_months} 个月的账单数据...\n", file=sys.stderr)
        months = get_last_n_months(num_months)
    else:
        print("错误：必须指定 --months 或 --month 参数", file=sys.stderr)
        print("使用示例：", file=sys.stderr)
        print("  --months 3    查询最近3个月", file=sys.stderr)
        print("  --month 2026-02  查询指定月份", file=sys.stderr)
        print("  --output result.md  输出到文件", file=sys.stderr)
        sys.exit(1)

    billing_data = {}
    totals = {'total': 0, 'prepaid': 0, 'postpaid': 0}

    for month in months:
        print(f"正在查询 {month} 的账单...", file=sys.stderr)
        overview = get_bill_overview(month, args.profile)
        instance_items = get_instance_bill_items(month, args.profile)

        if overview:
            data = parse_bill_data(overview, instance_items)
            billing_data[month] = data
            totals['total'] += data['total']
            totals['prepaid'] += data['prepaid']
            totals['postpaid'] += data['postpaid']

    # 输出表格
    print_table(months, billing_data, totals, args.output)


if __name__ == '__main__':
    main()

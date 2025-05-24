#!/usr/bin/env python3
"""
检查数据库状态脚本
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_webui.internal.db import engine
from sqlalchemy import text


def check_database_status():
    """检查数据库状态"""
    print("🔍 检查数据库状态")
    print("=" * 50)

    try:
        with engine.connect() as conn:
            # 检查订阅相关的表
            print("📋 检查数据库表:")
            result = conn.execute(
                text(
                    'SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%subscription%"'
                )
            )
            tables = result.fetchall()
            for table in tables:
                print(f"  ✅ {table[0]}")

            # 检查每日积分发放记录
            print("\n📊 检查每日积分发放记录:")
            result = conn.execute(
                text("SELECT * FROM subscription_daily_credit_grants")
            )
            grants = result.fetchall()
            print(f"  总记录数: {len(grants)}")

            for grant in grants:
                grant_date = datetime.fromtimestamp(grant[4]).strftime("%Y-%m-%d")
                created_at = datetime.fromtimestamp(grant[6]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(
                    f"  - 用户: {grant[1][:12]}... | 积分: {grant[5]} | 发放日期: {grant_date} | 创建时间: {created_at}"
                )

            # 检查套餐信息
            print("\n📦 检查套餐信息:")
            result = conn.execute(
                text("SELECT id, name, credits FROM subscription_plans")
            )
            plans = result.fetchall()
            for plan in plans:
                print(f"  - 套餐: {plan[1]} (ID: {plan[0]}) | 每日积分: {plan[2]}")

            # 检查活跃订阅
            print("\n👥 检查活跃订阅:")
            current_time = int(time.time())
            result = conn.execute(
                text(
                    f'SELECT user_id, plan_id, end_date FROM subscription_subscriptions WHERE status="active" AND end_date > {current_time}'
                )
            )
            subscriptions = result.fetchall()
            print(f"  活跃订阅数: {len(subscriptions)}")
            for sub in subscriptions:
                end_date = datetime.fromtimestamp(sub[2]).strftime("%Y-%m-%d")
                print(f"  - 用户: {sub[0][:12]}... | 套餐: {sub[1]} | 到期: {end_date}")

        print("\n✅ 数据库状态检查完成")

    except Exception as e:
        print(f"❌ 检查失败: {e}")


if __name__ == "__main__":
    check_database_status()

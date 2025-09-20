#!/usr/bin/env python3
"""
MySQL连接测试脚本
验证MySQL数据库连接和基本功能
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from open_webui.internal.db import engine
    from sqlalchemy import text
    from open_webui.env import DATABASE_URL
except ImportError as e:
    log.error(f"导入项目模块失败: {e}")
    sys.exit(1)


def test_database_connection():
    """测试数据库连接"""
    log.info("开始测试数据库连接...")
    log.info(f"数据库URL: {DATABASE_URL}")

    try:
        with engine.connect() as conn:
            # 测试基本连接
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                log.info("✅ 数据库连接成功")

                # 测试数据库版本
                try:
                    result = conn.execute(text("SELECT VERSION()"))
                    version = result.fetchone()[0]
                    log.info(f"数据库版本: {version}")
                except:
                    log.info("无法获取数据库版本信息")

                return True
            else:
                log.error("❌ 数据库连接测试失败")
                return False

    except Exception as e:
        log.error(f"❌ 数据库连接失败: {e}")
        return False


def test_table_operations():
    """测试表操作"""
    log.info("开始测试表操作...")

    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # 创建测试表
                conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS test_migration (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )

                # 插入测试数据
                conn.execute(
                    text(
                        """
                    INSERT INTO test_migration (name) VALUES ('test_record')
                """
                    )
                )

                # 查询测试数据
                result = conn.execute(
                    text("SELECT * FROM test_migration WHERE name = 'test_record'")
                )
                row = result.fetchone()
                if row:
                    log.info(f"✅ 表操作测试成功，插入记录: {row}")
                else:
                    log.error("❌ 插入记录查询失败")

                # 删除测试数据
                conn.execute(
                    text("DELETE FROM test_migration WHERE name = 'test_record'")
                )

                trans.commit()
                log.info("✅ 表操作测试完成")
                return True

            except Exception as e:
                trans.rollback()
                log.error(f"❌ 表操作测试失败: {e}")
                return False

    except Exception as e:
        log.error(f"❌ 表操作测试连接失败: {e}")
        return False


def test_connection_pool():
    """测试连接池"""
    log.info("开始测试连接池...")

    try:
        # 获取多个连接
        connections = []
        for i in range(3):
            conn = engine.connect()
            connections.append(conn)
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            log.info(f"✅ 连接 {i+1} 成功")

        # 关闭所有连接
        for conn in connections:
            conn.close()

        log.info("✅ 连接池测试完成")
        return True

    except Exception as e:
        log.error(f"❌ 连接池测试失败: {e}")
        return False


def main():
    """主函数"""
    log.info("🚀 开始MySQL数据库测试...")

    tests = [
        ("数据库连接测试", test_database_connection),
        ("表操作测试", test_table_operations),
        ("连接池测试", test_connection_pool),
    ]

    failed_tests = []

    for test_name, test_func in tests:
        log.info(f"\n--- {test_name} ---")
        if not test_func():
            failed_tests.append(test_name)

    if failed_tests:
        log.error(f"\n❌ 以下测试失败: {', '.join(failed_tests)}")
        return 1
    else:
        log.info("\n🎉 所有测试通过！MySQL数据库连接正常。")
        return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
🚀 WXIAI 发版前最终检查脚本
检查所有修复内容，确保发版安全
"""

import os
import sqlite3
import json
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    for path in db_paths:
        if os.path.exists(path):
            return sqlite3.connect(path), path
    return None, None


def check_migration_status():
    """检查迁移状态"""
    print("🔍 检查数据库迁移状态...")

    conn, db_path = get_db_connection()
    if not conn:
        print("❌ 无法连接到数据库")
        return False

    print(f"📍 数据库: {db_path}")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        versions = [row[0] for row in cursor.fetchall()]

        print(f"📊 迁移版本数: {len(versions)}")
        for v in versions:
            print(f"   - {v}")

        if len(versions) > 1:
            print("⚠️  存在多重迁移头")
            return False
        elif len(versions) == 1:
            print("✅ 迁移状态正常")
            return True
        else:
            print("❌ 未找到迁移版本")
            return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    finally:
        conn.close()


def check_all_fixes():
    """检查所有修复内容"""
    print("\n🔍 检查修复内容...")

    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # 检查项目列表
    checks = [
        {
            "name": "Veo任务表enhance_prompt列",
            "sql": "PRAGMA table_info(veo_tasks)",
            "check": lambda rows: "enhance_prompt" in [row[1] for row in rows],
            "description": "修复Veo任务历史500错误",
        },
        {
            "name": "Google Images配置表",
            "sql": "SELECT name FROM sqlite_master WHERE type='table' AND name='google_images_config'",
            "check": lambda rows: len(rows) > 0,
            "description": "修复Google Images配置保存",
        },
        {
            "name": "ComfyUI配置表",
            "sql": "SELECT name FROM sqlite_master WHERE type='table' AND name='comfyui_config'",
            "check": lambda rows: len(rows) > 0,
            "description": "修复ComfyUI功能",
        },
        {
            "name": "MidJourney云存储字段",
            "sql": "PRAGMA table_info(mj_tasks)",
            "check": lambda rows: "cloud_image_url" in [row[1] for row in rows],
            "description": "修复云存储功能",
        },
        {
            "name": "Google Images积分表字段",
            "sql": "PRAGMA table_info(google_images_credits)",
            "check": lambda rows: all(
                col in [row[1] for row in rows]
                for col in ["credits_before", "credits_after", "model_name"]
            ),
            "description": "修复积分扣除功能",
        },
    ]

    all_passed = True

    for check in checks:
        try:
            cursor.execute(check["sql"])
            rows = cursor.fetchall()

            if check["check"](rows):
                print(f"   ✅ {check['name']}")
            else:
                print(f"   ❌ {check['name']} - {check['description']}")
                all_passed = False

        except Exception as e:
            print(f"   ❌ {check['name']} - 检查失败: {e}")
            all_passed = False

    conn.close()
    return all_passed


def check_code_fixes():
    """检查代码修复"""
    print("\n🔍 检查代码修复...")

    code_fixes = [
        {
            "file": "open_webui/routers/comfyui.py",
            "check": "AddCreditForm",
            "description": "ComfyUI AddCreditForm导入修复",
        }
    ]

    all_good = True

    for fix in code_fixes:
        file_path = fix["file"]
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if fix["check"] in content:
                        print(f"   ✅ {fix['description']}")
                    else:
                        print(f"   ❌ {fix['description']} - 未找到修复内容")
                        all_good = False
            except Exception as e:
                print(f"   ❌ {fix['description']} - 检查失败: {e}")
                all_good = False
        else:
            print(f"   ❌ {fix['description']} - 文件不存在: {file_path}")
            all_good = False

    return all_good


def check_critical_tables():
    """检查关键表是否存在"""
    print("\n🔍 检查关键表...")

    conn, _ = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    critical_tables = [
        "veo_config",
        "google_images_config",
        "comfyui_config",
        "veo_tasks",
        "google_images_tasks",
        "mj_tasks",
        "dreamwork_tasks",
        "veo_credits",
        "google_images_credits",
        "comfyui_credits",
    ]

    missing_tables = []

    for table in critical_tables:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
        )
        if cursor.fetchone():
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - 不存在")
            missing_tables.append(table)

    conn.close()

    if missing_tables:
        print(f"\n⚠️  缺失 {len(missing_tables)} 个关键表")
        return False
    else:
        print(f"\n✅ 所有 {len(critical_tables)} 个关键表都存在")
        return True


def create_deployment_guide():
    """创建部署指南"""
    print("\n📝 创建部署指南...")

    guide_content = f"""# 🚀 WXIAI 发版部署指南

## 发版信息
- 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 发版版本: v2.{datetime.now().strftime('%m%d')}

## 🎯 本次发版修复内容
✅ Veo任务历史500错误 (enhance_prompt列缺失)
✅ ComfyUI签名验证失败 (AddCreditForm导入错误)  
✅ Google Images配置保存失败 (表不存在)
✅ 积分系统表结构不完整 (字段缺失)
✅ 云存储字段缺失 (各AI服务任务表)

## 📋 线上更新步骤

### 1. 更新前准备
```bash
# 备份数据库
cp data/webui.db data/webui.db.backup.$(date +%Y%m%d_%H%M%S)

# 备份配置文件
cp .env .env.backup

# 停止服务
sudo systemctl stop wxiai
```

### 2. 代码更新
```bash
# 拉取最新代码
git pull origin main

# 检查更新内容
git log --oneline -10

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库迁移
```bash
# 运行迁移检查
python final_release_check.py

# 如果有多重迁移头，运行修复脚本
python fix_all_missing_tables.py

# 运行Alembic迁移
python -c "
import sys
sys.path.append('open_webui')
from alembic import command
from alembic.config import Config
cfg = Config('open_webui/alembic.ini')
command.upgrade(cfg, 'head')
"
```

### 4. 功能验证
```bash
# 运行全面测试
python test_all_ai_services.py

# 测试ComfyUI配置
python test_comfyui_config.py
```

### 5. 启动服务
```bash
# 启动服务
sudo systemctl start wxiai

# 检查状态
sudo systemctl status wxiai

# 查看日志
sudo journalctl -u wxiai -f
```

## 🆘 回滚方案
如发现问题需要回滚:
```bash
# 停止服务
sudo systemctl stop wxiai

# 回滚代码
git reset --hard HEAD~1

# 恢复数据库
cp data/webui.db.backup.YYYYMMDD_HHMMSS data/webui.db

# 重启服务
sudo systemctl start wxiai
```

## 🔍 发版后验证清单
- [ ] 用户登录注册正常
- [ ] Veo任务历史页面正常加载
- [ ] ComfyUI配置保存正常
- [ ] Google Images功能正常
- [ ] 积分充值扣费正常
- [ ] 所有AI服务正常工作

## 📞 紧急联系
如遇到问题请立即联系开发团队
"""

    with open("DEPLOYMENT_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)

    print("✅ 部署指南已创建: DEPLOYMENT_GUIDE.md")


def main():
    """主函数"""
    print("🚀 WXIAI 发版前最终检查")
    print("=" * 50)

    # 检查项目
    checks = [
        ("数据库迁移状态", check_migration_status()),
        ("修复内容验证", check_all_fixes()),
        ("代码修复验证", check_code_fixes()),
        ("关键表检查", check_critical_tables()),
    ]

    # 统计结果
    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    print(f"\n{'='*50}")
    print("📊 检查结果总结")
    print(f"{'='*50}")

    for name, result in checks:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总体结果: {passed}/{total} 项通过")

    if passed == total:
        print("\n🎉 所有检查通过！系统已准备好发版")
        create_deployment_guide()

        print("\n🚀 建议发版流程:")
        print("1. 仔细阅读 DEPLOYMENT_GUIDE.md")
        print("2. 在测试环境最后验证")
        print("3. 按照指南执行线上更新")
        print("4. 完成后验证所有功能")

        return True
    else:
        print(f"\n❌ {total - passed} 项检查未通过，暂不建议发版")
        print("\n🛠️ 建议操作:")
        print("1. 修复上述失败项目")
        print("2. 重新运行此检查脚本")
        print("3. 所有检查通过后再发版")

        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
检查不同部署场景下的配置保持情况
"""

import sqlite3
import os


def check_current_sensitive_configs():
    """检查当前敏感配置"""
    print("🔍 检查当前敏感配置状态...")

    db_paths = [
        "data/webui.db",
        "backend/data/webui.db",
        "webui.db",
        "backend/webui.db",
    ]
    conn = None

    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            print(f"📍 数据库: {path}")
            break

    if not conn:
        print("❌ 无法连接到数据库")
        return

    cursor = conn.cursor()

    # 检查各种API密钥配置
    config_checks = [
        {
            "name": "ComfyUI API配置",
            "table": "comfyui_config",
            "sensitive_fields": ["access_key", "secret_key"],
        },
        {
            "name": "Google Images API配置",
            "table": "google_images_config",
            "sensitive_fields": ["api_key", "access_key", "secret_key"],
        },
        {
            "name": "Veo API配置",
            "table": "veo_config",
            "sensitive_fields": ["api_key", "access_key", "secret_key"],
        },
        {
            "name": "云存储配置",
            "table": "cloud_storage_config",
            "sensitive_fields": ["secret_id", "secret_key", "access_key"],
        },
    ]

    sensitive_data_found = []

    for check in config_checks:
        try:
            # 检查表是否存在
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{check['table']}'"
            )
            if not cursor.fetchone():
                print(f"   ⚠️ {check['name']}: 表不存在")
                continue

            # 获取表结构
            cursor.execute(f"PRAGMA table_info({check['table']})")
            columns = [row[1] for row in cursor.fetchall()]

            # 检查是否有敏感字段
            sensitive_cols = [
                col for col in check["sensitive_fields"] if col in columns
            ]

            if sensitive_cols:
                # 检查是否有配置数据
                cursor.execute(f"SELECT * FROM {check['table']} LIMIT 1")
                row = cursor.fetchone()
                if row:
                    col_dict = dict(zip(columns, row))
                    has_sensitive_data = any(
                        col_dict.get(col) for col in sensitive_cols
                    )

                    if has_sensitive_data:
                        print(f"   🔑 {check['name']}: 包含敏感配置数据")
                        sensitive_data_found.append(check["name"])
                        for col in sensitive_cols:
                            if col_dict.get(col):
                                print(
                                    f"      - {col}: {'已配置' if col_dict[col] else '空'}"
                                )
                    else:
                        print(f"   ⚠️ {check['name']}: 表存在但无敏感数据")
                else:
                    print(f"   ⚠️ {check['name']}: 表存在但无配置记录")
            else:
                print(f"   ⚠️ {check['name']}: 无敏感字段")

        except Exception as e:
            print(f"   ❌ {check['name']}: 检查失败 - {e}")

    conn.close()

    print(f"\n📊 发现敏感配置的服务: {len(sensitive_data_found)}")
    for service in sensitive_data_found:
        print(f"   🔑 {service}")

    return sensitive_data_found


def analyze_deployment_scenarios():
    """分析部署场景"""
    print("\n📋 部署场景分析...")

    scenarios = {
        "全新部署": {
            "description": "在全新服务器上首次部署",
            "database_state": "全新空数据库",
            "config_preservation": "❌ 无任何配置",
            "required_actions": [
                "运行数据库迁移创建所有表",
                "手动配置所有API密钥",
                "配置管理员账号",
                "配置各种服务参数",
            ],
        },
        "线上更新": {
            "description": "在现有服务器上更新代码",
            "database_state": "保留现有数据库",
            "config_preservation": "✅ 配置被保留",
            "required_actions": [
                "备份现有数据库",
                "运行增量迁移",
                "验证配置完整性",
                "重启服务",
            ],
        },
        "迁移部署": {
            "description": "将现有系统迁移到新服务器",
            "database_state": "复制现有数据库",
            "config_preservation": "✅ 配置随数据库迁移",
            "required_actions": [
                "复制数据库文件",
                "更新环境配置",
                "验证网络连接",
                "测试API连通性",
            ],
        },
    }

    for scenario_name, details in scenarios.items():
        print(f"\n🎯 {scenario_name}:")
        print(f"   📝 {details['description']}")
        print(f"   💾 数据库状态: {details['database_state']}")
        print(f"   🔧 配置保留: {details['config_preservation']}")
        print(f"   📋 需要操作:")
        for action in details["required_actions"]:
            print(f"      • {action}")


def create_config_backup_script():
    """创建配置备份脚本"""
    print("\n📝 创建配置备份脚本...")

    backup_script = '''#!/usr/bin/env python3
"""
敏感配置备份和恢复脚本
"""

import sqlite3
import json
import os
from datetime import datetime

def backup_sensitive_configs():
    """备份敏感配置"""
    print("🔐 备份敏感配置...")
    
    db_paths = ['data/webui.db', 'backend/data/webui.db', 'webui.db', 'backend/webui.db']
    conn = None
    
    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            break
    
    if not conn:
        print("❌ 无法连接到数据库")
        return None
    
    cursor = conn.cursor()
    backup_data = {}
    
    # 备份各种配置表
    config_tables = [
        'comfyui_config', 'google_images_config', 'veo_config', 'cloud_storage_config'
    ]
    
    for table in config_tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            
            table_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                table_data.append(row_dict)
            
            backup_data[table] = table_data
            print(f"   ✅ 备份 {table}: {len(table_data)} 条记录")
            
        except Exception as e:
            print(f"   ⚠️ 跳过 {table}: {e}")
    
    conn.close()
    
    # 保存备份文件
    backup_filename = f"sensitive_configs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置备份已保存: {backup_filename}")
    return backup_filename

def restore_sensitive_configs(backup_file):
    """恢复敏感配置"""
    print(f"🔄 从 {backup_file} 恢复配置...")
    
    if not os.path.exists(backup_file):
        print(f"❌ 备份文件不存在: {backup_file}")
        return False
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    db_paths = ['data/webui.db', 'backend/data/webui.db', 'webui.db', 'backend/webui.db']
    conn = None
    
    for path in db_paths:
        if os.path.exists(path):
            conn = sqlite3.connect(path)
            break
    
    if not conn:
        print("❌ 无法连接到数据库")
        return False
    
    cursor = conn.cursor()
    
    for table_name, table_data in backup_data.items():
        try:
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"   ⚠️ 表 {table_name} 不存在，跳过")
                continue
            
            # 清空现有数据
            cursor.execute(f"DELETE FROM {table_name}")
            
            # 插入备份数据
            for row_data in table_data:
                columns = list(row_data.keys())
                values = list(row_data.values())
                placeholders = ','.join(['?' for _ in values])
                
                sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(sql, values)
            
            print(f"   ✅ 恢复 {table_name}: {len(table_data)} 条记录")
            
        except Exception as e:
            print(f"   ❌ 恢复 {table_name} 失败: {e}")
    
    conn.commit()
    conn.close()
    print("✅ 配置恢复完成")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) > 2:
            restore_sensitive_configs(sys.argv[2])
        else:
            print("❌ 请指定备份文件: python config_backup.py restore backup_file.json")
    else:
        backup_sensitive_configs()
'''

    with open("config_backup.py", "w", encoding="utf-8") as f:
        f.write(backup_script)

    print("✅ 配置备份脚本已创建: config_backup.py")


def create_deployment_checklist():
    """创建部署检查清单"""
    print("\n📋 创建部署检查清单...")

    checklist = f"""# 🚀 WXIAI 部署场景配置指南

## 📊 当前系统状态
检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 部署场景说明

### 1. 🆕 全新部署
**适用情况**: 在全新服务器上首次部署WXIAI

**配置状态**: ❌ 需要重新配置所有API密钥
- ComfyUI API密钥 (access_key, secret_key)
- Google Images API密钥 
- Veo API密钥
- 云存储配置
- 管理员账号密码

**部署步骤**:
```bash
# 1. 克隆代码和部署
git clone [repository]
pip install -r requirements.txt

# 2. 初始化数据库
python -c "
import sys; sys.path.append('open_webui')
from alembic import command
from alembic.config import Config
cfg = Config('open_webui/alembic.ini')  
command.upgrade(cfg, 'head')
"

# 3. 启动服务
python main.py

# 4. 配置API密钥
# 登录管理界面，逐个配置各AI服务的API密钥
```

### 2. 🔄 线上更新  
**适用情况**: 现有服务器更新代码版本

**配置状态**: ✅ 配置被保留，无需重新输入
- 数据库文件包含所有配置
- API密钥自动保留
- 用户数据完整保留

**更新步骤**:
```bash
# 1. 备份数据库
python config_backup.py
cp data/webui.db data/webui.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. 停止服务
sudo systemctl stop wxiai

# 3. 更新代码  
git pull origin main
pip install -r requirements.txt

# 4. 运行迁移
python final_release_check.py

# 5. 重启服务
sudo systemctl start wxiai
```

### 3. 🏠 迁移部署
**适用情况**: 将现有系统迁移到新服务器

**配置状态**: ✅ 随数据库文件迁移，无需重新配置

**迁移步骤**:
```bash
# 在原服务器备份
python config_backup.py
tar -czf wxiai_migration.tar.gz data/ config/ .env

# 在新服务器部署
tar -xzf wxiai_migration.tar.gz
git clone [repository]
pip install -r requirements.txt
python main.py
```

## 🔑 API密钥配置位置

### 管理界面配置路径:
1. 登录系统 → 管理员账号
2. 设置 → AI服务配置 
3. 分别配置各服务:
   - **ComfyUI设置**: 哩布API Access Key + Secret Key
   - **Google Images设置**: Google API密钥
   - **Veo设置**: Veo API密钥
   - **云存储设置**: 腾讯云COS配置

### 必需的API密钥:
- 🎨 **ComfyUI**: 哩布AI平台密钥对
- 🖼️ **Google Images**: Google API密钥
- 🎬 **Veo**: Veo AI API密钥  
- ☁️ **云存储**: 腾讯云COS Secret ID/Key

## ⚠️ 重要提醒

### 全新部署注意事项:
- ❗ 必须重新配置所有API密钥
- ❗ 需要创建管理员账号  
- ❗ 需要测试所有AI服务连通性
- ❗ 建议先在测试环境验证

### 线上更新注意事项:
- ✅ 配置自动保留，无需重新输入
- ✅ 数据和用户信息完整保留
- ⚠️ 建议先备份数据库
- ⚠️ 在低峰期执行更新

## 🆘 应急方案

### 配置丢失恢复:
```bash
# 使用配置备份恢复
python config_backup.py restore backup_file.json

# 或手动重新配置
# 登录管理界面 → 重新输入API密钥
```

### 回滚方案:
```bash
# 代码回滚
git reset --hard HEAD~1

# 数据库回滚  
cp data/webui.db.backup.YYYYMMDD data/webui.db
```
"""

    with open("DEPLOYMENT_SCENARIOS.md", "w", encoding="utf-8") as f:
        f.write(checklist)

    print("✅ 部署场景指南已创建: DEPLOYMENT_SCENARIOS.md")


def main():
    """主函数"""
    print("🔍 WXIAI 部署场景配置分析")
    print("=" * 50)

    # 检查当前配置状态
    sensitive_configs = check_current_sensitive_configs()

    # 分析部署场景
    analyze_deployment_scenarios()

    # 创建配置备份脚本
    create_config_backup_script()

    # 创建部署检查清单
    create_deployment_checklist()

    print("\n" + "=" * 50)
    print("📋 总结")
    print("=" * 50)

    if sensitive_configs:
        print(f"🔑 当前系统包含 {len(sensitive_configs)} 个服务的敏感配置")
        print("   • 线上更新: ✅ 配置自动保留")
        print("   • 全新部署: ❌ 需要重新配置")
        print("   • 迁移部署: ✅ 随数据库迁移")
    else:
        print("⚠️ 当前系统无敏感配置，所有场景都需要手动配置")

    print(f"\n📁 生成文件:")
    print("• config_backup.py - 配置备份恢复脚本")
    print("• DEPLOYMENT_SCENARIOS.md - 部署场景指南")


if __name__ == "__main__":
    main()

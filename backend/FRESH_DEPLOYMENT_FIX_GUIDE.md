# 🚨 WXIAI 全新部署表结构修复指南

## ⚠️ 问题说明

如果你在全新部署WXIAI后遇到以下错误：

- `NOT NULL constraint failed: cloud_storage_config.created_at`
- `no such table: google_images_config`
- `no such column: dreamwork_tasks.cloud_image_url`

这是由于迁移文件的问题导致的表结构不完整。

## 🛠️ 修复步骤

### 步骤1: 运行紧急修复

```bash
python emergency_fix_fresh_deployment.py
```

### 步骤2: 运行配置表修复

```bash
python fix_config_tables_final.py
```

### 步骤3: 重启应用

```bash
# 如果使用systemd
sudo systemctl restart wxiai

# 或者直接重启Python进程
```

### 步骤4: 验证功能

1. 访问管理界面
2. 测试各AI服务配置
3. 确认所有功能正常

## 🔍 修复内容清单

- ✅ cloud_storage_config表（云存储配置）
- ✅ google_images_config表（Google Images配置）
- ✅ veo_config表（Veo配置）
- ✅ 所有任务表的云存储字段
- ✅ veo_tasks.enhance_prompt列
- ✅ 所有积分表的必要字段

## 💡 预防措施

对于开发者：

1. 在空数据库上测试迁移文件
2. 使用这些修复脚本作为fallback
3. 在CI/CD中包含全新部署测试

## 📞 如有问题

如果修复后仍有问题，请提供：

1. 错误日志
2. 数据库表结构：`sqlite3 data/webui.db ".schema"`
3. 运行修复脚本的输出

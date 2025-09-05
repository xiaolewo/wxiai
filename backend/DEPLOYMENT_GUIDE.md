# 🚀 WXIAI 发版部署指南

## 发版信息

- 检查时间: 2025-09-02 22:03:57
- 发版版本: v2.0902

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

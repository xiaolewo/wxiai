# ⚡ 可灵对口型功能 - 快速启动

## 🚀 3步部署

### 1️⃣ 执行数据库迁移

```bash
cd backend/
alembic upgrade head
```

### 2️⃣ 重启应用

```bash
# 根据你的部署方式选择：
systemctl restart wxiai-backend
# 或
docker-compose restart backend
# 或
supervisorctl restart wxiai
```

### 3️⃣ 配置和测试

1. **管理配置**: 访问 `/admin/settings/kling-lip-sync`
   - 输入可灵API URL和密钥
   - 设置积分消耗
   - 测试连接

2. **功能测试**: 访问 `/lip-sync`
   - 选择中文/英文语言
   - 测试文本转对口型
   - 测试音频驱动对口型

## 🎯 核心功能

### ✅ 已实现

- **62种音色** (35中文 + 27英文)
- **动态语言切换**
- **双模式支持** (文本/音频)
- **积分系统集成**
- **实时任务状态**
- **云存储集成**

### 🔧 管理功能

- API配置管理
- 积分消耗设置
- 连接状态测试
- 功能开关控制

## 🔍 快速验证

```bash
# 运行验证脚本
python run_all_tests.py

# 手动验证API
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/kling-lip-sync/config
```

## ❓ 遇到问题？

### 迁移失败

```bash
alembic current  # 检查当前版本
alembic history  # 查看迁移历史
```

### API不工作

- 检查路由是否注册（main.py）
- 验证数据库表是否创建
- 确认服务已重启

### 前端页面404

- 确认前端已重新构建
- 检查路由文件是否存在

---

**就是这么简单！** 🎭✨

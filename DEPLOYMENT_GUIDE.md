# 🚀 可灵对口型功能 - 自动化部署指南

## ✅ 正确的部署流程

### 方案一：更新现有系统（推荐）

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 安装/更新依赖（如有必要）
cd backend/
pip install -r requirements.txt

# 3. 自动执行数据库迁移
alembic upgrade head

# 4. 重启服务
systemctl restart wxiai-backend
```

### 方案二：Docker 部署

```dockerfile
# 在 Dockerfile 中添加自动迁移
RUN alembic upgrade head
```

### 方案三：在应用启动时自动迁移

```python
# 在 backend/open_webui/main.py 的 lifespan 函数中添加：
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 现有的启动代码...

    # 自动执行数据库迁移
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        log.info("数据库迁移完成")
    except Exception as e:
        log.error(f"数据库迁移失败: {e}")

    yield
    # 关闭逻辑...
```

## 🎯 核心实现文件

### 已实现的文件清单：

```
backend/
├── open_webui/
│   ├── models/kling_lip_sync.py           ✅ 数据模型
│   ├── utils/kling_lip_sync.py            ✅ 业务逻辑
│   ├── routers/kling_lip_sync.py          ✅ API路由
│   ├── migrations/versions/xxx_add_kling_lip_sync_tables.py  ✅ 迁移文件
│   └── main.py                            ✅ 路由已注册

src/
├── lib/apis/kling-lip-sync/index.ts       ✅ 前端API
├── routes/(app)/lip-sync/+page.svelte     ✅ 主功能页面
├── lib/components/admin/Settings/KlingLipSync.svelte  ✅ 管理配置
└── routes/(app)/admin/settings/kling-lip-sync/+page.svelte  ✅ 管理页面
```

## 🔧 验证部署结果

### 1. 检查数据库表

```sql
-- 确认表已创建
.tables | grep kling_lip_sync

-- 检查默认配置
SELECT * FROM kling_lip_sync_configs WHERE id = 'default';
```

### 2. 检查 API 端点

```bash
# 管理员配置接口
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/v1/kling-lip-sync/config

# 用户功能接口
curl -H "Authorization: Bearer USER_TOKEN" \
     http://localhost:8000/api/v1/kling-lip-sync/tasks
```

### 3. 检查前端页面

- 访问 `/lip-sync` - 用户功能页面
- 访问 `/admin/settings/kling-lip-sync` - 管理配置页面

## 🎭 功能特性确认

### ✅ 核心功能

- 35个中文音色 + 27个英文音色
- 语言切换自动更新音色选项
- 文本转对口型 + 音频驱动对口型
- 实时任务状态轮询
- 积分系统集成
- 云存储集成

### ✅ 管理功能

- API配置（URL、密钥）
- 积分消耗设置
- 连接测试
- 功能开关

## 🚨 如果遇到问题

### 迁移失败

```bash
# 检查迁移状态
alembic current

# 查看迁移历史
alembic history

# 手动回滚（如必要）
alembic downgrade -1
```

### 路由问题

确认 `backend/open_webui/main.py` 包含：

```python
from open_webui.routers import kling_lip_sync
app.include_router(kling_lip_sync.router, prefix="/api/v1/kling-lip-sync", tags=["kling-lip-sync"])
```

### 前端问题

确认构建输出包含新页面：

```bash
npm run build
ls -la dist/  # 检查是否包含新的路由文件
```

---

**这才是现代应用的正确部署方式** - 使用标准工具，集成到现有流程，无需额外脚本！🎉

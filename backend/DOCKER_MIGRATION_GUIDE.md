# Docker环境即梦字段迁移指南

## 方案一：进入容器执行迁移（推荐）

### 1. 找到运行中的容器

```bash
docker ps | grep webui
# 或者
docker ps | grep backend
```

### 2. 进入容器执行迁移

```bash
# 进入容器（替换 CONTAINER_ID 或 CONTAINER_NAME）
docker exec -it CONTAINER_ID bash

# 在容器内执行迁移
cd /app  # 或者你的应用目录
python run_jimeng_migration.py

# 退出容器
exit
```

### 示例：

```bash
# 假设容器名为 webui-backend
docker exec -it webui-backend python run_jimeng_migration.py
```

## 方案二：通过docker-compose执行

### 如果使用docker-compose：

```bash
# 进入服务容器
docker-compose exec backend python run_jimeng_migration.py

# 或者
docker-compose exec webui python run_jimeng_migration.py
```

## 方案三：使用docker run执行一次性迁移

### 如果容器已停止或需要单独执行：

```bash
# 使用相同的镜像和配置运行迁移
docker run --rm \
  -v /path/to/your/data:/app/data \
  -v /path/to/your/database:/app/database \
  --network your_network \
  your_image_name python run_jimeng_migration.py
```

## 方案四：手动SQL执行

### 1. 进入数据库容器（如果数据库在单独容器中）

```bash
# 进入数据库容器
docker exec -it DATABASE_CONTAINER_ID bash

# 连接数据库
sqlite3 /path/to/webui.db
```

### 2. 执行SQL

```sql
-- 添加缺失字段
ALTER TABLE jimeng_tasks ADD COLUMN watermark BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE jimeng_config ADD COLUMN default_watermark BOOLEAN NOT NULL DEFAULT FALSE;

-- 验证字段添加
.schema jimeng_tasks
.schema jimeng_config

-- 退出
.quit
```

## 方案五：通过Web界面执行（如果有管理面板）

某些部署可能提供管理界面，可以通过Web执行SQL命令。

## 验证迁移成功

### 1. 检查容器日志

```bash
docker logs CONTAINER_ID | grep -i jimeng
```

### 2. 测试API端点

```bash
# 测试即梦配置接口
curl http://your-domain/api/v1/jimeng/config/user

# 测试任务创建
curl -X POST http://your-domain/api/v1/jimeng/submit/text-to-video \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "duration": "5"}'
```

## 常见Docker容器名称

根据不同的部署方式，容器名称可能是：

- `open-webui`
- `webui`
- `backend`
- `wxiai-backend`
- `app`
- 或自定义名称

## 故障排除

### 1. 找不到迁移脚本

如果容器内没有迁移脚本，可以先复制进去：

```bash
docker cp run_jimeng_migration.py CONTAINER_ID:/app/
docker exec -it CONTAINER_ID python run_jimeng_migration.py
```

### 2. 权限问题

```bash
# 以root身份进入容器
docker exec -it --user root CONTAINER_ID bash
```

### 3. Python路径问题

```bash
# 在容器内设置PYTHONPATH
docker exec -it CONTAINER_ID bash -c "cd /app && PYTHONPATH=. python run_jimeng_migration.py"
```

## 重要提示

1. **备份数据库**：执行迁移前建议备份数据库
2. **停机维护**：建议在低峰期执行，可能需要短暂停机
3. **测试环境**：如果有测试环境，先在测试环境验证迁移
4. **回滚准备**：准备回滚方案以防出现问题

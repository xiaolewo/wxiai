# 即梦字段迁移指南

## 问题描述

线上数据库的 `jimeng_tasks` 表缺少 `watermark` 字段，导致任务查询时出现以下错误：

```
(sqlite3.OperationalError) no such column: jimeng_tasks.watermark
```

## 解决方案

### 1. 自动迁移（推荐）

运行迁移脚本添加缺失字段：

```bash
# 在生产环境中执行
python run_jimeng_migration.py
```

### 2. 手动SQL执行

如果自动迁移失败，可以手动执行以下SQL：

```sql
-- 添加 watermark 字段到 jimeng_tasks 表
ALTER TABLE jimeng_tasks ADD COLUMN watermark BOOLEAN NOT NULL DEFAULT FALSE;

-- 添加 default_watermark 字段到 jimeng_config 表
ALTER TABLE jimeng_config ADD COLUMN default_watermark BOOLEAN NOT NULL DEFAULT FALSE;
```

### 3. 使用 Alembic 迁移（如果可用）

```bash
alembic upgrade f4e8b6c2a1d9
```

## 验证迁移

迁移完成后，验证字段是否添加成功：

```sql
-- 检查 jimeng_tasks 表结构
PRAGMA table_info(jimeng_tasks);

-- 检查 jimeng_config 表结构
PRAGMA table_info(jimeng_config);
```

## 预期结果

迁移成功后，`jimeng_tasks` 表应包含以下字段：

- `watermark` (BOOLEAN, NOT NULL, DEFAULT FALSE)
- `cloud_video_url` (TEXT, 可选)

`jimeng_config` 表应包含：

- `default_watermark` (BOOLEAN, NOT NULL, DEFAULT FALSE)

## 本地环境说明

本地环境使用只读数据库副本，无法执行写入操作。这是正常的。
实际的迁移需要在生产环境的可写数据库中执行。

## 部署后功能

迁移完成后，以下功能将正常工作：

- ✅ 即梦任务创建
- ✅ 任务状态查询
- ✅ 水印功能设置
- ✅ 云存储视频URL
- ✅ 完整的即梦视频生成工作流

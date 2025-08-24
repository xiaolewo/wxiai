-- 即梦字段手动迁移SQL脚本
-- 如果自动迁移脚本无法运行，可以直接执行这些SQL语句

-- ================================
-- 1. 添加 jimeng_tasks 表的缺失字段
-- ================================

-- 添加 watermark 字段
ALTER TABLE jimeng_tasks ADD COLUMN watermark BOOLEAN NOT NULL DEFAULT FALSE;

-- 验证 jimeng_tasks 表结构
.schema jimeng_tasks

-- ================================
-- 2. 添加 jimeng_config 表的缺失字段  
-- ================================

-- 添加 default_watermark 字段
ALTER TABLE jimeng_config ADD COLUMN default_watermark BOOLEAN NOT NULL DEFAULT FALSE;

-- 验证 jimeng_config 表结构
.schema jimeng_config

-- ================================
-- 3. 验证字段是否添加成功
-- ================================

-- 检查 jimeng_tasks 表结构
PRAGMA table_info(jimeng_tasks);

-- 检查 jimeng_config 表结构
PRAGMA table_info(jimeng_config);

-- ================================
-- 4. 测试查询 (可选)
-- ================================

-- 测试 watermark 字段查询
SELECT id, watermark FROM jimeng_tasks LIMIT 5;

-- 测试 default_watermark 字段查询
SELECT id, default_watermark FROM jimeng_config LIMIT 1;
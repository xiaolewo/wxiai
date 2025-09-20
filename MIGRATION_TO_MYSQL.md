# 从SQLite迁移到MySQL完整指南

本指南将帮助您将项目从SQLite数据库迁移到MySQL数据库。

## 📋 迁移前准备

### 1. 环境要求

- MySQL 8.0或更高版本
- Python 3.10或更高版本
- 已安装的项目依赖

### 2. 备份现有数据

在开始迁移之前，请务必备份现有的SQLite数据库：

```bash
# 备份SQLite数据库
cp backend/data/webui.db backup_webui.db
```

## 🚀 迁移步骤

### 步骤1: 配置环境变量

创建或更新 `.env` 文件，配置MySQL连接信息：

```bash
# 复制MySQL配置示例
cp .env.mysql .env

# 或者手动编辑.env文件，添加以下内容：
DATABASE_TYPE=mysql
DATABASE_USER=wxiai_user
DATABASE_PASSWORD=wxiai_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=wxiai_db

# 连接池设置（可选）
DATABASE_POOL_SIZE=10
DATABASE_POOL_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

### 步骤2: 启动MySQL服务

使用Docker启动MySQL服务（推荐）：

```bash
# 使用提供的docker-compose文件启动MySQL
docker-compose -f docker-compose.mysql.yaml up -d mysql

# 或者使用系统已安装的MySQL服务
sudo systemctl start mysql
```

### 步骤3: 创建数据库和用户

如果使用系统MySQL服务，需要手动创建数据库和用户：

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE wxiai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER 'wxiai_user'@'%' IDENTIFIED BY 'wxiai_password';
GRANT ALL PRIVILEGES ON wxiai_db.* TO 'wxiai_user'@'%';
FLUSH PRIVILEGES;
```

### 步骤4: 初始化MySQL数据库

运行MySQL初始化脚本：

```bash
cd backend/
python scripts/init_mysql_db.py
```

### 步骤5: 数据迁移

如果需要迁移现有数据，可以使用以下方法：

#### 方法1: 使用mysqldump（推荐）

```bash
# 导出SQLite数据为SQL格式（需要先安装sqlite3工具）
sqlite3 backend/data/webui.db .dump > sqlite_dump.sql

# 转换SQL格式为MySQL兼容格式（需要手动调整）
# 然后导入到MySQL
mysql -u wxiai_user -p wxiai_db < mysql_compatible_dump.sql
```

#### 方法2: 使用自定义迁移脚本

创建一个数据迁移脚本：

```bash
cd backend/
python scripts/migrate_data_sqlite_to_mysql.py
```

### 步骤6: 启动应用

使用MySQL配置启动应用：

```bash
cd backend/
bash start_mysql.sh
```

或者使用Docker启动完整环境：

```bash
docker-compose -f docker-compose.mysql.yaml up -d
```

## 🧪 验证迁移结果

### 1. 检查数据库连接

```bash
# 检查应用日志
docker logs open-webui

# 或者直接检查MySQL连接
mysql -u wxiai_user -p -h localhost wxiai_db -e "SHOW TABLES;"
```

### 2. 验证数据完整性

```sql
-- 检查关键表是否存在
SHOW TABLES LIKE '%config%';
SHOW TABLES LIKE '%user%';
SHOW TABLES LIKE '%chat%';

-- 检查表结构
DESCRIBE users;
DESCRIBE configs;
```

### 3. 测试应用功能

1. 访问Web界面
2. 登录并测试基本功能
3. 检查AI服务是否正常工作
4. 验证积分系统是否正常

## 🗑️ 清理SQLite相关文件

迁移成功后，可以清理SQLite相关文件：

```bash
cd backend/
python scripts/cleanup_sqlite.py
```

## 🔧 故障排除

### 常见问题

1. **连接失败**
   - 检查MySQL服务是否正在运行
   - 验证数据库用户和密码
   - 确认防火墙设置

2. **字符编码问题**
   - 确保MySQL使用utf8mb4字符集
   - 检查连接参数中的charset设置

3. **权限问题**
   - 确保数据库用户有足够权限
   - 检查MySQL的bind-address设置

### 日志查看

```bash
# 查看应用日志
tail -f backend/data/logs/app.log

# 查看MySQL日志
tail -f /var/log/mysql/error.log
```

## 📈 性能优化建议

1. **连接池配置**

   ```bash
   DATABASE_POOL_SIZE=20
   DATABASE_POOL_MAX_OVERFLOW=30
   ```

2. **MySQL配置优化**

   ```ini
   [mysqld]
   innodb_buffer_pool_size = 1G
   max_connections = 500
   query_cache_size = 128M
   ```

3. **定期维护**
   - 定期优化表结构
   - 清理无用数据
   - 监控数据库性能

## 🔄 回滚到SQLite（如果需要）

如果迁移失败，可以回滚到SQLite：

```bash
# 恢复备份的SQLite数据库
cp backup_webui.db backend/data/webui.db

# 恢复.env文件
cp .env.sqlite .env

# 启动应用
cd backend/
bash start.sh
```

## 📚 相关文档

- [MySQL配置说明](MYSQL_CONFIGURATION.md)
- [Docker部署指南](DEPLOYMENT_GUIDE.md)
- [性能优化指南](PERFORMANCE_OPTIMIZATION.md)

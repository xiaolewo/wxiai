# 数据库迁移指南

本项目支持从SQLite迁移到MySQL或PostgreSQL数据库。以下是完整的迁移指南。

## 📋 支持的数据库类型

1. **SQLite** (默认) - 适用于开发和小型部署
2. **MySQL** (推荐) - 适用于生产环境
3. **PostgreSQL** - 适用于企业级部署

## 🚀 从SQLite迁移到MySQL

### 1. 准备工作

```bash
# 备份现有SQLite数据库
cp backend/data/webui.db backup_webui.db

# 复制MySQL配置示例
cp .env.mysql .env
```

### 2. 配置MySQL环境

编辑 `.env` 文件，配置MySQL连接信息：

```bash
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

### 3. 启动MySQL服务

使用Docker启动MySQL（推荐）：

```bash
docker-compose -f docker-compose.mysql.yaml up -d mysql
```

或者使用系统MySQL服务：

```bash
sudo systemctl start mysql
```

### 4. 创建数据库和用户

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

### 5. 初始化MySQL数据库

```bash
cd backend/
python scripts/init_mysql_db.py
```

### 6. 迁移数据

```bash
cd backend/
python scripts/migrate_data_sqlite_to_mysql.py
```

### 7. 验证迁移

```bash
cd backend/
python scripts/test_mysql_connection.py
```

### 8. 启动应用

```bash
cd backend/
bash start_mysql.sh
```

## 🔄 从SQLite迁移到PostgreSQL

### 1. 准备工作

```bash
# 备份现有SQLite数据库
cp backend/data/webui.db backup_webui.db

# 复制PostgreSQL配置示例（如果存在）
cp .env.postgresql .env
```

### 2. 配置PostgreSQL环境

编辑 `.env` 文件，配置PostgreSQL连接信息：

```bash
DATABASE_TYPE=postgresql
DATABASE_USER=wxiai_user
DATABASE_PASSWORD=wxiai_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=wxiai_db
```

### 3. 启动PostgreSQL服务

使用Docker启动PostgreSQL（推荐）：

```bash
docker-compose -f docker-compose.postgresql.yaml up -d postgresql
```

或者使用系统PostgreSQL服务：

```bash
sudo systemctl start postgresql
```

### 4. 创建数据库和用户

```bash
# 切换到postgres用户
sudo -u postgres psql

# 创建数据库
CREATE DATABASE wxiai_db WITH ENCODING='UTF8';

# 创建用户
CREATE USER wxiai_user WITH PASSWORD 'wxiai_password';

# 授权
GRANT ALL PRIVILEGES ON DATABASE wxiai_db TO wxiai_user;
```

### 5. 初始化PostgreSQL数据库

```bash
cd backend/
python scripts/init_postgresql_db.py
```

### 6. 迁移数据

```bash
cd backend/
python scripts/migrate_data_sqlite_to_postgresql.py
```

### 7. 验证迁移

```bash
cd backend/
python scripts/test_postgresql_connection.py
```

### 8. 启动应用

```bash
cd backend/
bash start_postgresql.sh
```

## 🧪 测试数据库连接

使用提供的测试脚本验证数据库连接：

```bash
cd backend/
python scripts/test_mysql_connection.py
# 或
python scripts/test_postgresql_connection.py
```

## 🗑️ 清理SQLite相关文件

迁移成功后，可以清理SQLite相关文件：

```bash
cd backend/
python scripts/cleanup_sqlite.py
```

## 🔧 故障排除

### 常见问题

1. **连接失败**
   - 检查数据库服务是否正在运行
   - 验证数据库用户和密码
   - 确认防火墙设置

2. **字符编码问题**
   - 确保数据库使用UTF-8字符集
   - 检查连接参数中的charset设置

3. **权限问题**
   - 确保数据库用户有足够权限
   - 检查数据库的绑定地址设置

### 日志查看

```bash
# 查看应用日志
tail -f backend/data/logs/app.log

# 查看数据库日志
tail -f /var/log/mysql/error.log
# 或
tail -f /var/log/postgresql/postgresql-*.log
```

## 📚 相关文档

- [MySQL配置说明](MYSQL_CONFIGURATION.md)
- [PostgreSQL配置说明](POSTGRESQL_CONFIGURATION.md)
- [Docker部署指南](DEPLOYMENT_GUIDE.md)
- [性能优化指南](PERFORMANCE_OPTIMIZATION.md)

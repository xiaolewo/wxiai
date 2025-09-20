# 使用MySQL数据库配置

本项目支持使用MySQL作为数据库后端。以下是配置和使用MySQL的步骤：

## 1. 环境变量配置

创建 `.env` 文件并配置以下环境变量：

```bash
# MySQL Database Configuration
DATABASE_TYPE=mysql
DATABASE_USER=wxiai_user
DATABASE_PASSWORD=wxiai_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=wxiai_db

# Connection pool settings for MySQL
DATABASE_POOL_SIZE=10
DATABASE_POOL_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

## 2. 使用Docker Compose (推荐)

使用我们提供的 `docker-compose.mysql.yaml` 文件来启动包含MySQL的完整环境：

```bash
# 复制MySQL环境配置文件
cp .env.mysql .env

# 启动服务
docker-compose -f docker-compose.mysql.yaml up -d
```

## 3. 手动配置MySQL

如果使用已有的MySQL服务器，请确保：

1. 创建数据库：

   ```sql
   CREATE DATABASE wxiai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. 创建用户并授权：
   ```sql
   CREATE USER 'wxiai_user'@'%' IDENTIFIED BY 'wxiai_password';
   GRANT ALL PRIVILEGES ON wxiai_db.* TO 'wxiai_user'@'%';
   FLUSH PRIVILEGES;
   ```

## 4. 初始化数据库

运行数据库初始化脚本：

```bash
cd backend/
python scripts/init_mysql_db.py
```

## 5. 启动应用

```bash
cd backend/
bash start.sh
```

## 注意事项

1. 确保MySQL服务正在运行
2. 确保防火墙允许相应的端口通信
3. 在生产环境中，请使用强密码并配置适当的安全策略
4. 定期备份数据库以防止数据丢失

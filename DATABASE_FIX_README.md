# 数据库表结构修复说明

## 问题描述

在运行应用程序时遇到了以下错误：

```
sqlite3.OperationalError: no such column: prompt.access_control
[SQL: SELECT prompt.command AS prompt_command, prompt.user_id AS prompt_user_id, prompt.title AS prompt_title, prompt.content AS prompt_content, prompt.timestamp AS prompt_timestamp, prompt.access_control AS prompt_access_control
FROM prompt ORDER BY prompt.timestamp DESC]
```

以及：

```
sqlite3.OperationalError: no such column: chat.pinned
[SQL: SELECT chat.id AS chat_id, chat.user_id AS chat_user_id, chat.title AS chat_title, chat.chat AS chat_chat, chat.created_at AS chat_created_at, chat.updated_at AS chat_updated_at, chat.share_id AS chat_share_id, chat.archived AS chat_archived, chat.pinned AS chat_pinned, chat.meta AS chat_meta, chat.folder_id AS chat_folder_id
FROM chat
WHERE chat.user_id = ? AND chat.pinned = 1 AND chat.archived = 0 ORDER BY chat.updated_at DESC]
```

这表明数据库表结构与应用程序代码期望的结构不匹配。

## 问题原因

1. 数据库表结构过时，缺少新版本代码需要的列
2. 数据库迁移未正确执行
3. 应用程序版本与数据库结构不匹配

## 解决方案

我们创建了数据库修复脚本来解决这个问题：

### 1. fix_prompt_table.py

专门修复prompt表的access_control列缺失问题

### 2. fix_chat_table.py

专门修复chat表的pinned、meta和folder_id列缺失问题

### 3. fix_all_tables.py

全面检查和修复所有表的结构问题

## 修复的表和列

### prompt表

- ✅ access_control (TEXT)

### chat表

- ✅ pinned (INTEGER DEFAULT 0)
- ✅ meta (TEXT)
- ✅ folder_id (TEXT)

### user表

- ✅ phone (TEXT)

### tool表

- ✅ access_control (TEXT)

## 修复步骤

1. 运行 `fix_prompt_table.py` 脚本修复prompt表:

   ```bash
   cd backend/
   python scripts/fix_prompt_table.py
   ```

2. 运行 `fix_chat_table.py` 脚本修复chat表:

   ```bash
   cd backend/
   python scripts/fix_chat_table.py
   ```

3. 运行 `fix_all_tables.py` 脚本进行全面检查:
   ```bash
   cd backend/
   python scripts/fix_all_tables.py
   ```

## 验证结果

修复后，数据库表结构与应用程序代码期望的结构匹配，错误已解决。

## 预防措施

1. 定期运行数据库迁移脚本
2. 在升级应用程序版本时确保数据库结构同步更新
3. 使用alembic等工具管理数据库迁移

## 注意事项

1. 在生产环境中执行修复脚本前，请务必备份数据库
2. 确保应用程序已停止运行后再执行修复脚本
3. 修复完成后重启应用程序以确保更改生效

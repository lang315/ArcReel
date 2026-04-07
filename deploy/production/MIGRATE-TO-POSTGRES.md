[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Migrating from SQLite to PostgreSQL

This document applies to scenarios where ArcReel is already deployed with the default SQLite and you want to switch to PostgreSQL.

## Prerequisites

- Docker and Docker Compose are installed
- ArcReel is currently running with SQLite (database file located at `projects/.arcreel.db`)

## Migration Steps

### 1. Stop the ArcReel service

```bash
# If running via Docker
docker compose down

# If running directly from the command line, stop the uvicorn process
```

### 2. Back up the SQLite database

```bash
cp projects/.arcreel.db projects/.arcreel.db.bak
```

### 3. Configure environment variables

Add the following variable to `.env` (used for PostgreSQL container initialization in docker-compose):

```env
POSTGRES_PASSWORD=your_database_password
```

> `DATABASE_URL` does not need to be set manually — it is automatically assembled from `POSTGRES_PASSWORD` in `docker-compose.yml`.

### 4. Start PostgreSQL

Start only the database service first:

```bash
docker compose up -d postgres
```

Wait for the health check to pass:

```bash
docker compose ps  # confirm postgres status is healthy
```

### 5. Migrate data

Use pgloader inside the ArcReel container to migrate data directly from SQLite to PostgreSQL:

```bash
docker compose run --rm arcreel bash -c "
  apt-get update && apt-get install -y --no-install-recommends pgloader &&
  pgloader sqlite:///app/projects/.arcreel.db \
           postgresql://arcreel:\${POSTGRES_PASSWORD}@postgres:5432/arcreel
"
```

> pgloader automatically handles type and syntax differences between SQLite and PostgreSQL (booleans, timestamp formats, etc.)
> and skips existing table schemas, importing data only.

### 6. Verify data

```bash
docker compose exec postgres psql -U arcreel -d arcreel -c "
  SELECT 'tasks' AS tbl, COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

Compare with record counts in SQLite:

```bash
sqlite3 projects/.arcreel.db "
  SELECT 'tasks', COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

### 7. Start the full service

```bash
docker compose up -d
```

Visit `http://<your-IP>:1241` to verify the service is running correctly.

---

## Rolling Back to SQLite

If you need to revert:

1. Stop the service: `docker compose down`
2. Restore the backup: `cp projects/.arcreel.db.bak projects/.arcreel.db`
3. Remove `POSTGRES_PASSWORD` from `.env` and start without the PostgreSQL configuration in `docker-compose.yml`

---

<a name="chinese"></a>

# 从 SQLite 迁移到 PostgreSQL

本文档适用于已使用默认 SQLite 部署 ArcReel、希望切换到 PostgreSQL 的场景。

## 前置条件

- 已安装 Docker 和 Docker Compose
- ArcReel 当前使用 SQLite 运行（数据库文件位于 `projects/.arcreel.db`）

## 迁移步骤

### 1. 停止 ArcReel 服务

```bash
# 如果通过 Docker 运行
docker compose down

# 如果通过命令行直接运行，停止 uvicorn 进程
```

### 2. 备份 SQLite 数据库

```bash
cp projects/.arcreel.db projects/.arcreel.db.bak
```

### 3. 配置环境变量

在 `.env` 中新增以下变量（用于 docker-compose 中 PostgreSQL 容器的初始化）：

```env
POSTGRES_PASSWORD=你的数据库密码
```

> `DATABASE_URL` 无需手动设置，已在 `docker-compose.yml` 中通过 `POSTGRES_PASSWORD` 自动拼接。

### 4. 启动 PostgreSQL

先只启动数据库服务：

```bash
docker compose up -d postgres
```

等待健康检查通过：

```bash
docker compose ps  # 确认 postgres 状态为 healthy
```

### 5. 迁移数据

在 ArcReel 容器内使用 pgloader 将 SQLite 数据直接迁移到 PostgreSQL：

```bash
docker compose run --rm arcreel bash -c "
  apt-get update && apt-get install -y --no-install-recommends pgloader &&
  pgloader sqlite:///app/projects/.arcreel.db \
           postgresql://arcreel:\${POSTGRES_PASSWORD}@postgres:5432/arcreel
"
```

> pgloader 会自动处理 SQLite 与 PostgreSQL 之间的类型和语法差异（布尔值、时间格式等），
> 并跳过已存在的表结构，只导入数据。

### 6. 验证数据

```bash
docker compose exec postgres psql -U arcreel -d arcreel -c "
  SELECT 'tasks' AS tbl, COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

对比 SQLite 中的记录数：

```bash
sqlite3 projects/.arcreel.db "
  SELECT 'tasks', COUNT(*) FROM tasks
  UNION ALL
  SELECT 'api_calls', COUNT(*) FROM api_calls
  UNION ALL
  SELECT 'agent_sessions', COUNT(*) FROM agent_sessions
  UNION ALL
  SELECT 'api_keys', COUNT(*) FROM api_keys;
"
```

### 7. 启动完整服务

```bash
docker compose up -d
```

访问 `http://<你的IP>:1241` 验证服务正常。

---

## 回滚到 SQLite

如果需要回退：

1. 停止服务：`docker compose down`
2. 恢复备份：`cp projects/.arcreel.db.bak projects/.arcreel.db`
3. 移除 `.env` 中的 `POSTGRES_PASSWORD`，不使用 `docker-compose.yml` 中的 PostgreSQL 配置启动

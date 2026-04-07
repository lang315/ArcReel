[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Contributing Guide

Contributions of code, bug reports, and feature suggestions are welcome!

## Local Development Environment

```bash
# Prerequisites: Python 3.12+, Node.js 20+, uv, pnpm, ffmpeg

# Install dependencies
uv sync
cd frontend && pnpm install && cd ..

# Initialize the database
uv run alembic upgrade head

# Start the backend (Terminal 1)
uv run uvicorn server.app:app --reload --port 1241

# Start the frontend (Terminal 2)
cd frontend && pnpm dev

# Visit http://localhost:5173
```

## Running Tests

```bash
# Backend tests
python -m pytest

# Frontend typecheck + tests
cd frontend && pnpm check
```

## Code Quality

**Lint & Format (ruff):**

```bash
uv run ruff check . && uv run ruff format .
```

- Rule set: `E`/`F`/`I`/`UP`, ignoring `E402` and `E501`
- line-length: 120
- Enforced in CI: `ruff check . && ruff format --check .`

**Test Coverage:**

- CI requires ≥80%
- `asyncio_mode = "auto"` (no need to manually mark async tests)

## Commit Convention

Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: description of new feature
fix: description of bug fix
refactor: description of refactoring
docs: documentation changes
chore: build/tooling changes
```

---

<a name="chinese"></a>

# 贡献指南

欢迎贡献代码、报告 Bug 或提出功能建议！

## 本地开发环境

```bash
# 前置要求：Python 3.12+, Node.js 20+, uv, pnpm, ffmpeg

# 安装依赖
uv sync
cd frontend && pnpm install && cd ..

# 初始化数据库
uv run alembic upgrade head

# 启动后端 (终端 1)
uv run uvicorn server.app:app --reload --port 1241

# 启动前端 (终端 2)
cd frontend && pnpm dev

# 访问 http://localhost:5173
```

## 运行测试

```bash
# 后端测试
python -m pytest

# 前端类型检查 + 测试
cd frontend && pnpm check
```

## 代码质量

**Lint & Format（ruff）：**

```bash
uv run ruff check . && uv run ruff format .
```

- 规则集：`E`/`F`/`I`/`UP`，忽略 `E402` 和 `E501`
- line-length：120
- CI 中强制检查：`ruff check . && ruff format --check .`

**测试覆盖率：**

- CI 要求 ≥80%
- `asyncio_mode = "auto"`（无需手动标记 async 测试）

## 提交规范

Commit message 采用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: 新增功能描述
fix: 修复问题描述
refactor: 重构描述
docs: 文档变更
chore: 构建/工具变更
```

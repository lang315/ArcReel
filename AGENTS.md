[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Language Policy
- **Responses to users must be in Chinese**: All replies, task lists, and planning documents must be written in Chinese.

## Project Overview

ArcReel is an AI video generation platform that converts novels into short videos. Three-tier architecture:

```
frontend/ (React SPA)  →  server/ (FastAPI)  →  lib/ (core library)
  React 19 + Tailwind       routing + SSE         Gemini API
  wouter routing            agent_runtime/         GenerationQueue
  zustand state mgmt        (Claude Agent SDK)     ProjectManager
```

## Development Commands

```bash
# Backend
uv run python -m pytest                              # tests (-v single file / -k keyword / --cov coverage)
uv run ruff check . && uv run ruff format .          # lint + format
uv sync                                              # install dependencies
uv run alembic upgrade head                          # database migration
uv run alembic revision --autogenerate -m "desc"     # generate migration

# Frontend (cd frontend &&)
pnpm build       # production build (includes typecheck)
pnpm check       # typecheck + test
```

## Architecture Highlights

### Backend API Routes

All APIs are under `/api/v1`, routes defined in `server/routers/`:
- `projects.py` — project CRUD, overview generation
- `generate.py` — storyboard/video/character/clue generation (enqueued to task queue)
- `assistant.py` — Claude Agent SDK session management (SSE streaming)
- `agent_chat.py` — agent conversation interaction
- `tasks.py` — task queue status (SSE streaming)
- `project_events.py` — project event SSE push
- `files.py` — file upload and static assets
- `versions.py` — asset version history and rollback
- `characters.py` / `clues.py` — character/clue management
- `usage.py` — API usage statistics
- `cost_estimation.py` — cost estimation (project/episode/single shot)
- `auth.py` / `api_keys.py` — authentication and API key management
- `system_config.py` — system configuration
- `providers.py` — preset provider configuration management (list, read/write, connection test)
- `custom_providers.py` — custom provider CRUD, model management and discovery, connection test

### server/services/ — Business Service Layer

- `generation_tasks.py` — storyboard/video/character/clue generation task orchestration
- `project_archive.py` — project export (ZIP packaging)
- `project_events.py` — project change event publishing
- `jianying_draft_service.py` — Jianying draft export
- `cost_estimation.py` — cost estimation calculation and actual cost summary

### lib/ Core Modules

- **{gemini,ark,grok,openai}_shared** — provider SDK factories and shared utilities
- **image_backends/** / **video_backends/** / **text_backends/** — multi-provider media generation backends, Registry + Factory pattern (gemini/ark/grok/openai)
- **custom_provider/** — custom provider support: backend wrapping, model discovery, factory creation (OpenAI/Google compatible)
- **MediaGenerator** (`media_generator.py`) — combines backend + VersionManager + UsageTracker
- **GenerationQueue** (`generation_queue.py`) — async task queue, SQLAlchemy ORM backend, lease-based concurrency control
- **GenerationWorker** (`generation_worker.py`) — background worker, separate image/video concurrency channels
- **ProjectManager** (`project_manager.py`) — project filesystem operations and data management
- **StatusCalculator** (`status_calculator.py`) — computes status fields at read time, no redundant state stored
- **UsageTracker** (`usage_tracker.py`) — API usage tracking
- **CostCalculator** (`cost_calculator.py`) — cost calculation
- **TextGenerator** (`text_generator.py`) — text generation tasks
- **retry** (`retry.py`) — generic exponential backoff retry decorator, shared across provider backends

### lib/config/ — Provider Configuration System

ConfigService (`service.py`) → Repository (persistence + key masking) → Resolver (resolution). `registry.py` maintains the preset provider registry (PROVIDER_REGISTRY).

### lib/db/ — SQLAlchemy Async ORM Layer

- `engine.py` — async engine + session factory (`DATABASE_URL` defaults to `sqlite+aiosqlite`)
- `models/` — ORM models: Task / ApiCall / ApiKey / AgentSession / Config / Credential / User / CustomProvider / CustomProviderModel
- `repositories/` — async repositories: Task / Usage / Session / ApiKey / Credential / CustomProvider

Database file: `projects/.arcreel.db` (development SQLite)

### Agent Runtime (Claude Agent SDK Integration)

`server/agent_runtime/` wraps the Claude Agent SDK:
- `AssistantService` (`service.py`) — orchestrates Claude SDK sessions
- `SessionManager` — session lifecycle + SSE subscriber pattern
- `StreamProjector` — builds real-time assistant replies from streaming events

### Frontend

- React 19 + TypeScript + Tailwind CSS 4
- Routing: `wouter` (not React Router)
- State management: `zustand` (stores in `frontend/src/stores/`)
- Path alias: `@/` → `frontend/src/`
- Vite proxy: `/api` → `http://127.0.0.1:1241`

## Key Design Patterns

### Data Layering

| Data Type | Storage Location | Strategy |
|-----------|-----------------|----------|
| Character/clue definitions | `project.json` | Single source of truth; script only references names |
| Episode metadata (episode/title/script_file) | `project.json` | Write-synced when script is saved |
| Statistical fields (scenes_count / status / progress) | Not stored | `StatusCalculator` computes and injects at read time |

### Real-time Communication

- Assistant: `/api/v1/assistant/sessions/{id}/stream` — SSE streaming replies
- Project events: `/api/v1/projects/{name}/events/stream` — SSE push for project changes
- Task queue: frontend polls `/api/v1/tasks` for status

### Task Queue

All generation tasks (storyboard/video/character/clue) are uniformly enqueued through GenerationQueue and processed asynchronously by GenerationWorker.
`generation_queue_client.py`'s `enqueue_and_wait()` wraps enqueue + wait for completion.

### Pydantic Data Models

`lib/script_models.py` defines `NarrationSegment` and `DramaScene`, used for script validation.
`lib/data_validator.py` validates the structure and reference integrity of `project.json` and episode JSON files.

## Agent Runtime Environment

Agent-specific configuration (skills, agents, system prompts) is located in the `agent_runtime_profile/` directory,
physically separated from the development-time `.claude/` directory.

### Skill Maintenance

```bash
# Trigger rate evaluation (requires anthropic SDK: uv pip install anthropic)
PYTHONPATH=~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator:$PYTHONPATH \
  uv run python -m scripts.run_eval \
  --eval-set <eval-set.json> \
  --skill-path agent_runtime_profile/.claude/skills/<skill-name> \
  --model sonnet --runs-per-query 2 --verbose
```

#### Gotchas

- **SKILL.md and script must stay in sync**: When modifying a skill script, update SKILL.md accordingly, and vice versa — both must remain consistent.

## Environment Configuration

Copy `.env.example` to `.env` and set authentication parameters (`AUTH_USERNAME`/`AUTH_PASSWORD`/`AUTH_TOKEN_SECRET`).
API keys, backend selection, model configuration, etc. are managed through the WebUI settings page (`/settings`).
External tool dependency: `ffmpeg` (video concatenation and post-processing).

### Code Quality

**ruff** (lint + format):
- Rule sets: `E`/`F`/`I`/`UP`, ignoring `E402` (existing pattern) and `E501` (managed by formatter)
- line-length: 120
- Excludes `.worktrees` and `.claude/worktrees` directories
- Enforced in CI: `ruff check . && ruff format --check .`

**pytest**:
- `asyncio_mode = "auto"` (no need to manually mark async tests)
- Test coverage scope: `lib/` and `server/`, CI requires ≥80%
- Shared fixtures in `tests/conftest.py`, factories in `tests/factories.py`, fakes in `tests/fakes.py`
- Test dependencies in `[dependency-groups] dev`, installed by default with `uv sync`, excluded in production images via `--no-dev`

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **ArcReel** (9421 symbols, 22885 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/ArcReel/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/ArcReel/context` | Codebase overview, check index freshness |
| `gitnexus://repo/ArcReel/clusters` | All functional areas |
| `gitnexus://repo/ArcReel/processes` | All execution flows |
| `gitnexus://repo/ArcReel/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

---

<a name="chinese"></a>

# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 语言规范
- **回答用户必须使用中文**：所有回复、任务清单及计划文件，均须使用中文

## 项目概述

ArcReel 是一个 AI 视频生成平台，将小说转化为短视频。三层架构：

```
frontend/ (React SPA)  →  server/ (FastAPI)  →  lib/ (核心库)
  React 19 + Tailwind       路由分发 + SSE        Gemini API
  wouter 路由               agent_runtime/        GenerationQueue
  zustand 状态管理          (Claude Agent SDK)     ProjectManager
```

## 开发命令

```bash
# 后端
uv run python -m pytest                              # 测试（-v 单文件 / -k 关键字 / --cov 覆盖率）
uv run ruff check . && uv run ruff format .          # lint + format
uv sync                                              # 安装依赖
uv run alembic upgrade head                          # 数据库迁移
uv run alembic revision --autogenerate -m "desc"     # 生成迁移

# 前端（cd frontend &&）
pnpm build       # 生产构建 (含 typecheck)
pnpm check       # typecheck + test
```

## 架构要点

### 后端 API 路由

所有 API 在 `/api/v1` 下，路由定义在 `server/routers/`：
- `projects.py` — 项目 CRUD、概述生成
- `generate.py` — 分镜/视频/角色/线索生成（入队到任务队列）
- `assistant.py` — Claude Agent SDK 会话管理（SSE 流式）
- `agent_chat.py` — 智能体对话交互
- `tasks.py` — 任务队列状态（SSE 流式）
- `project_events.py` — 项目事件 SSE 推送
- `files.py` — 文件上传与静态资源
- `versions.py` — 资源版本历史与回滚
- `characters.py` / `clues.py` — 角色/线索管理
- `usage.py` — API 用量统计
- `cost_estimation.py` — 费用预估（项目/单集/单镜头）
- `auth.py` / `api_keys.py` — 认证与 API 密钥管理
- `system_config.py` — 系统配置
- `providers.py` — 预置供应商配置管理（列表、读写、连接测试）
- `custom_providers.py` — 自定义供应商 CRUD、模型管理与发现、连接测试

### server/services/ — 业务服务层

- `generation_tasks.py` — 分镜/视频/角色/线索生成任务编排
- `project_archive.py` — 项目导出（ZIP 打包）
- `project_events.py` — 项目变更事件发布
- `jianying_draft_service.py` — 剪映草稿导出
- `cost_estimation.py` — 费用预估计算与实际费用汇总

### lib/ 核心模块

- **{gemini,ark,grok,openai}_shared** — 各供应商 SDK 工厂与共享工具
- **image_backends/** / **video_backends/** / **text_backends/** — 多供应商媒体生成后端，Registry + Factory 模式（gemini/ark/grok/openai）
- **custom_provider/** — 自定义供应商支持：后端包装、模型发现、工厂创建（OpenAI/Google 兼容）
- **MediaGenerator** (`media_generator.py`) — 组合后端 + VersionManager + UsageTracker
- **GenerationQueue** (`generation_queue.py`) — 异步任务队列，SQLAlchemy ORM 后端，lease-based 并发控制
- **GenerationWorker** (`generation_worker.py`) — 后台 Worker，分 image/video 两条并发通道
- **ProjectManager** (`project_manager.py`) — 项目文件系统操作和数据管理
- **StatusCalculator** (`status_calculator.py`) — 读时计算状态字段，不存储冗余状态
- **UsageTracker** (`usage_tracker.py`) — API 用量追踪
- **CostCalculator** (`cost_calculator.py`) — 费用计算
- **TextGenerator** (`text_generator.py`) — 文本生成任务
- **retry** (`retry.py`) — 通用指数退避重试装饰器，各供应商后端复用

### lib/config/ — 供应商配置系统

ConfigService（`service.py`）→ Repository（持久化 + 密钥脱敏）→ Resolver（解析）。`registry.py` 维护预置供应商注册表（PROVIDER_REGISTRY）。

### lib/db/ — SQLAlchemy Async ORM 层

- `engine.py` — 异步引擎 + session factory（`DATABASE_URL` 默认 `sqlite+aiosqlite`）
- `models/` — ORM 模型：Task / ApiCall / ApiKey / AgentSession / Config / Credential / User / CustomProvider / CustomProviderModel
- `repositories/` — 异步 Repository：Task / Usage / Session / ApiKey / Credential / CustomProvider

数据库文件：`projects/.arcreel.db`（开发 SQLite）

### Agent Runtime（Claude Agent SDK 集成）

`server/agent_runtime/` 封装 Claude Agent SDK：
- `AssistantService` (`service.py`) — 编排 Claude SDK 会话
- `SessionManager` — 会话生命周期 + SSE 订阅者模式
- `StreamProjector` — 从流式事件构建实时助手回复

### 前端

- React 19 + TypeScript + Tailwind CSS 4
- 路由：`wouter`（非 React Router）
- 状态管理：`zustand`（stores 在 `frontend/src/stores/`）
- 路径别名：`@/` → `frontend/src/`
- Vite 代理：`/api` → `http://127.0.0.1:1241`

## 关键设计模式

### 数据分层

| 数据类型 | 存储位置 | 策略 |
|---------|---------|------|
| 角色/线索定义 | `project.json` | 单一真相源，剧本中仅引用名称 |
| 剧集元数据（episode/title/script_file） | `project.json` | 剧本保存时写时同步 |
| 统计字段（scenes_count / status / progress） | 不存储 | `StatusCalculator` 读时计算注入 |

### 实时通信

- 助手：`/api/v1/assistant/sessions/{id}/stream` — SSE 流式回复
- 项目事件：`/api/v1/projects/{name}/events/stream` — SSE 推送项目变更
- 任务队列：前端轮询 `/api/v1/tasks` 获取状态

### 任务队列

所有生成任务（分镜/视频/角色/线索）统一通过 GenerationQueue 入队，由 GenerationWorker 异步处理。
`generation_queue_client.py` 的 `enqueue_and_wait()` 封装入队 + 等待完成。

### Pydantic 数据模型

`lib/script_models.py` 定义 `NarrationSegment` 和 `DramaScene`，用于剧本验证。
`lib/data_validator.py` 验证 `project.json` 和剧集 JSON 的结构与引用完整性。

## 智能体运行环境

智能体专用配置（skills、agents、系统 prompt）位于 `agent_runtime_profile/` 目录，
与开发态 `.claude/` 物理分离。

### Skill 维护

```bash
# 触发率评估（需要 anthropic SDK：uv pip install anthropic）
PYTHONPATH=~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator:$PYTHONPATH \
  uv run python -m scripts.run_eval \
  --eval-set <eval-set.json> \
  --skill-path agent_runtime_profile/.claude/skills/<skill-name> \
  --model sonnet --runs-per-query 2 --verbose
```

#### Gotchas

- **SKILL.md 与脚本同步**：修改 skill 脚本时需同步更新 SKILL.md，反之亦然，二者必须保持一致

## 环境配置

复制 `.env.example` 到 `.env`，设置认证参数（`AUTH_USERNAME`/`AUTH_PASSWORD`/`AUTH_TOKEN_SECRET`）。
API Key、后端选择、模型配置等通过 WebUI 配置页（`/settings`）管理。
外部工具依赖：`ffmpeg`（视频拼接与后期处理）。

### 代码质量

**ruff**（lint + format）：
- 规则集：`E`/`F`/`I`/`UP`，忽略 `E402`（既有模式）和 `E501`（由 formatter 管理）
- line-length：120
- 排除 `.worktrees`、`.claude/worktrees` 目录
- CI 中强制检查：`ruff check . && ruff format --check .`

**pytest**：
- `asyncio_mode = "auto"`（无需手动标记 async 测试）
- 测试覆盖范围：`lib/` 和 `server/`，CI 要求 ≥80%
- 共用 fixtures 在 `tests/conftest.py`，工厂在 `tests/factories.py`，fakes 在 `tests/fakes.py`
- test 依赖在 `[dependency-groups] dev` 中，`uv sync` 默认安装，生产镜像通过 `--no-dev` 排除

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **ArcReel** (9421 symbols, 22885 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/ArcReel/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/ArcReel/context` | Codebase overview, check index freshness |
| `gitnexus://repo/ArcReel/clusters` | All functional areas |
| `gitnexus://repo/ArcReel/processes` | All execution flows |
| `gitnexus://repo/ArcReel/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

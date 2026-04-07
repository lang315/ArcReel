[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Complete Getting Started Tutorial

This tutorial guides you from scratch to converting a novel into a short video using ArcReel.

## What You Will Learn

1. **Environment Setup** — Obtain API keys
2. **Deploy the Service** — Deploy via Docker
3. **Full Workflow** — Every step from novel to video
4. **Advanced Tips** — Regeneration, cost control, local development

## Estimated Time

- Environment setup: 10–20 minutes (first time only)
- Generating a 1-minute video: approximately 30 minutes

## Cost Estimate

ArcReel supports multiple providers (Gemini, Volcano Ark, Grok, OpenAI, and custom providers). The following uses Gemini as an example:

| Type | Model | Unit Price | Notes |
|------|-------|------------|-------|
| Image generation | Nano Banana Pro | $0.134/image (1K/2K) | High quality, suitable for character design images |
| Image generation | Nano Banana 2 | $0.067/image (1K) | Faster and cheaper, suitable for storyboard images |
| Video generation | Veo 3.1 | $0.40/sec (1080p with audio) | High quality |
| Video generation | Veo 3.1 Fast | $0.15/sec (1080p with audio) | Faster and cheaper |
| Video generation | Veo 3.1 Lite | Lower | Lightweight model, AI Studio only |

> 💡 **Example** (Gemini): A short video with 10 scenes (8 seconds each)
> - Images: 3 character design images (Pro) + 10 storyboard images (Flash) = $0.40 + $0.67 = $1.07
> - Video: 80 sec × $0.15 (Fast mode) = $12
> - **Total approximately $13**

> 🎁 **New user benefit**: New Google Cloud users receive **$300 in free credits**, valid for 90 days — enough to generate a large number of videos!
>
> For other providers' costs, please refer to their official pricing pages. ArcReel provides real-time cost tracking on the settings page.

---

## Chapter 1: Environment Setup

### 1.1 Obtain Image/Video Generation Provider API Keys

ArcReel supports multiple providers — configure **at least one** to get started:

| Provider | Where to Get | Notes |
|----------|-------------|-------|
| **Gemini** (Google) | [AI Studio](https://aistudio.google.com/apikey) | Requires paid tier; new users automatically receive $300 credit |
| **Volcano Ark** | [Volcano Engine Console](https://console.volcengine.com/ark) | Billed per token/image (CNY) |
| **Grok** (xAI) | [xAI Console](https://console.x.ai/) | Billed per image/second (USD) |
| **OpenAI** | [OpenAI Platform](https://platform.openai.com/) | Billed per image/second (USD) |

You can also add **custom providers** (any OpenAI-compatible / Google-compatible API) through the settings page after deployment.

> ⚠️ API keys are sensitive information. Keep them safe and do not share them with others or upload them to public repositories.

### 1.2 Obtain an Anthropic API Key

ArcReel has a built-in AI assistant based on the Claude Agent SDK, which handles key tasks such as script creation and intelligent conversational guidance.

**Option A: Use the Official Anthropic API**

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Register an account and create an API key
3. Configure it on the Web UI settings page

**Option B: Use a Third-Party Anthropic-Compatible API**

If you cannot access the Anthropic API directly, you can configure on the settings page:

- **Base URL** — Enter the address of a relay service or compatible API
- **Model** — Specify the model name to use (e.g., `claude-sonnet-4-6`)
- You can also configure the default models and Subagent models separately for Haiku / Sonnet / Opus

### 1.3 Prepare a Server

**Server requirements:**

- OS: Linux / macOS / Windows WSL
- Memory: 2 GB+ recommended
- Docker and Docker Compose installed

**Install Docker (if not already installed):**

```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Verify after re-login
docker --version
docker compose version
```

---

## Chapter 2: Deploy the Service

### 2.1 Download and Start

#### Option A: Default Deployment (SQLite, recommended for getting started)

```bash
# 1. Clone the project
git clone https://github.com/ArcReel/ArcReel.git
cd ArcReel/deploy

# 2. Create the environment variable file
cp .env.example .env

# 3. Start the service
docker compose up -d
```

#### Option B: Production Deployment (PostgreSQL, recommended for production use)

```bash
cd ArcReel/deploy/production

# Create the environment variable file (set POSTGRES_PASSWORD)
cp .env.example .env

docker compose up -d
```

After the containers finish starting, visit **http://your-server-ip:1241** in your browser.

### 2.2 Initial Configuration

1. Log in with the default account (username `admin`; password set via `AUTH_PASSWORD` in `.env` — if not set, it is auto-generated on first startup and written back to `.env`)
2. Go to the **Settings page** (`/settings`)
3. Configure the **Anthropic API Key** (powers the AI assistant); supports custom Base URL and model
4. Configure at least one image/video **provider API Key** (Gemini / Volcano Ark / Grok / OpenAI), or add a custom provider
5. Adjust model selection, rate limits, and other parameters as needed

> 💡 All configuration items can be modified on the settings page — no need to manually edit configuration files.

---

## Chapter 3: Full Workflow

The following steps are completed in the Web UI workbench.

### 3.1 Create a Project

1. Click "New Project" on the project list page
2. Enter a project name (e.g., "My Novel")
3. Upload the novel text file (.txt format)

### 3.2 Generate the Storyboard Script

Open the AI assistant panel on the right side of the project workbench and have the assistant generate a script through conversation:

- The AI will automatically analyze the novel content and break it down into segments suitable for video
- Each segment includes a scene description, the characters appearing, and important props/locations (clues)

**Review point**: Check whether the script structure is reasonable and whether characters and clues are correctly identified.

### 3.3 Generate Character Design Images

The AI generates design images for each character to maintain consistent character appearance across all subsequent scenes.

**Review point**: Check whether the character appearance matches the novel description; regenerate if unsatisfactory.

### 3.4 Generate Clue Design Images

The AI generates reference images for important props and scene elements (e.g., keepsakes, specific locations).

**Review point**: Check whether the clue design meets expectations.

### 3.5 Generate Storyboard Images

The AI generates a static image for each scene based on the script, automatically referencing character and clue design images to ensure consistency.

**Review point**: Check scene composition, character consistency, and atmosphere.

### 3.6 Generate Video Clips

Storyboard images serve as the starting frame; the selected video provider (Veo 3.1 / Seedance / Grok / Sora 2, etc.) generates 4–8 second dynamic video clips.

Generation tasks enter an asynchronous task queue; you can monitor progress in real time on the task monitor panel. Image and Video channels run concurrently and independently, with RPM rate limiting to stay within API quotas.

**Review point**: Preview each video clip; regenerate individual clips if unsatisfactory.

### 3.7 Compose the Final Video

All clips are concatenated via FFmpeg, with transition effects and background music added, to produce the final video.

The default output is **9:16 portrait** format, suitable for publishing to short video platforms.

---

## Chapter 4: Advanced Tips

### 4.1 Version History and Rollback

Each time assets are regenerated, the system automatically saves a historical version. In the timeline view of the workbench, you can browse historical versions and roll back with one click.

### 4.2 Cost Control

**View cost statistics:**

API call counts and cost details can be viewed on the settings page.

**Tips to reduce spending:**

- Carefully review the output at each stage to reduce rework
- Generate a small number of scenes to test results first, then generate in bulk
- Using Fast mode for video generation saves approximately 60% in costs
- Use Flash model for storyboard images and Pro model for character design images

### 4.3 Project Import/Export

Projects support archive packaging for easy backup and migration:

- **Export**: Package the entire project (including all assets) into an archive file
- **Import**: Restore a project from an archive file

---

## Chapter 5: Frequently Asked Questions

### Q: Docker fails to start?

1. Confirm the Docker service is running: `systemctl status docker`
2. Check if port 1241 is occupied: `ss -tlnp | grep 1241`
3. View container logs: `docker compose logs` (run in the corresponding `deploy/` or `deploy/production/` directory)

### Q: API calls failing?

1. Confirm the API key for the corresponding provider is correctly entered on the settings page
2. Gemini users must confirm that the paid tier is enabled (the free tier does not support image/video generation)
3. Check whether the server's network can access the corresponding provider's API service
4. Check in the provider's console whether API usage has exceeded the limit

### Q: Characters look different across scenes?

1. Make sure to generate character design images first
2. Check the quality of character design images; regenerate if unsatisfactory
3. The system will automatically use character design images as references to ensure consistency in subsequent scenes

### Q: Video generation is very slow?

Video generation typically takes 1–3 minutes per clip — this is normal. Factors that affect speed:

- Video duration (4 seconds vs. 8 seconds)
- API server load
- Network conditions

The task queue supports concurrent processing, so multiple video clips can be generated simultaneously.

### Q: What if generation is interrupted?

The task queue supports checkpoint resumption. When generation is re-triggered, the system automatically skips already-completed clips and processes only the remaining ones.

---

## Next Steps

Congratulations on completing the getting-started tutorial! You can now:

- 💰 View [Google GenAI Cost Reference](google-genai-docs/Google视频&图片生成费用参考.md) and [Volcano Ark Cost Reference](ark-docs/火山方舟费用参考.md) for detailed pricing
- 🐛 Encountered an issue? Submit an [Issue](https://github.com/ArcReel/ArcReel/issues)
- 💬 Scan the QR code to join the Feishu group for help and updates:

<img src="assets/feishu-qr.png" alt="飞书交流群二维码" width="280">

If you find the project useful, please give it a ⭐ Star!

---

<a name="chinese"></a>

# 完整入门教程

本教程指导你从零开始，使用 ArcReel 将小说转换为短视频。

## 你将学到

1. **环境准备** — 获取 API 密钥
2. **部署服务** — 通过 Docker 部署
3. **完整流程** — 从小说到视频的每一步操作
4. **进阶技巧** — 重新生成、费用控制、本地开发

## 预计耗时

- 环境准备：10-20 分钟（仅首次需要）
- 生成一个 1 分钟视频：约 30 分钟

## 费用预估

ArcReel 支持多个供应商（Gemini、火山方舟、Grok、OpenAI 及自定义供应商），以下以 Gemini 为例：

| 类型 | 模型 | 单价 | 说明 |
|------|------|------|------|
| 图片生成 | Nano Banana Pro | $0.134/张 (1K/2K) | 高质量，适合角色设计图 |
| 图片生成 | Nano Banana 2 | $0.067/张 (1K) | 更快更便宜，适合分镜图 |
| 视频生成 | Veo 3.1 | $0.40/秒 (1080p 含音频) | 高质量 |
| 视频生成 | Veo 3.1 Fast | $0.15/秒 (1080p 含音频) | 更快更便宜 |
| 视频生成 | Veo 3.1 Lite | 更低 | 轻量模型，仅 AI Studio |

> 💡 **示例**（Gemini）：一个包含 10 个场景（每场景 8 秒）的短视频
> - 图片：3 张角色设计（Pro）+ 10 张分镜（Flash）= $0.40 + $0.67 = $1.07
> - 视频：80 秒 × $0.15（Fast 模式）= $12
> - **总计约 $13**

> 🎁 **新用户福利**：Google Cloud 新用户可获得 **$300 免费赠金**，有效期 90 天，足够生成大量视频！
>
> 其他供应商费用请参考各自官方定价页面，ArcReel 在设置页提供实时费用追踪。

---

## 第一章：环境准备

### 1.1 获取图片/视频生成供应商 API 密钥

ArcReel 支持多个供应商，**至少配置一个**即可开始使用：

| 供应商 | 获取地址 | 说明 |
|--------|---------|------|
| **Gemini** (Google) | [AI Studio](https://aistudio.google.com/apikey) | 需付费层级，新用户自动获 $300 赠金 |
| **火山方舟** | [火山引擎控制台](https://console.volcengine.com/ark) | 按 token/张数计费 (CNY) |
| **Grok** (xAI) | [xAI Console](https://console.x.ai/) | 按张/秒计费 (USD) |
| **OpenAI** | [OpenAI Platform](https://platform.openai.com/) | 按张/秒计费 (USD) |

也可以在部署后通过设置页添加**自定义供应商**（任何 OpenAI 兼容 / Google 兼容 API）。

> ⚠️ API 密钥是敏感信息，请妥善保管，不要分享给他人或上传到公开仓库。

### 1.2 获取 Anthropic API 密钥

ArcReel 内置基于 Claude Agent SDK 的 AI 助手，负责剧本创作、智能对话引导等关键环节。

**方式 A：使用 Anthropic 官方 API**

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账号并创建 API 密钥
3. 后续在 Web UI 设置页配置

**方式 B：使用第三方 Anthropic 兼容 API**

如果无法直接访问 Anthropic API，可在设置页配置：

- **Base URL** — 填写中转服务或兼容 API 的地址
- **Model** — 指定使用的模型名称（如 `claude-sonnet-4-6`）
- 还可分别配置 Haiku / Sonnet / Opus 的默认模型和 Subagent 模型

### 1.3 准备服务器

**服务器要求：**

- 操作系统：Linux / MacOS / Windows WSL
- 内存：建议 2GB+
- 已安装 Docker 和 Docker Compose

**安装 Docker（如未安装）：**

```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 重新登录后验证
docker --version
docker compose version
```

---

## 第二章：部署服务

### 2.1 下载并启动

#### 方式 A：默认部署（SQLite，推荐入门）

```bash
# 1. 克隆项目
git clone https://github.com/ArcReel/ArcReel.git
cd ArcReel/deploy

# 2. 创建环境变量文件
cp .env.example .env

# 3. 启动服务
docker compose up -d
```

#### 方式 B：生产部署（PostgreSQL，推荐正式使用）

```bash
cd ArcReel/deploy/production

# 创建环境变量文件（需设置 POSTGRES_PASSWORD）
cp .env.example .env

docker compose up -d
```

等待容器启动完成后，在浏览器访问 **http://你的服务器IP:1241**

### 2.2 首次配置

1. 使用默认账号登录（用户名 `admin`，密码在 `.env` 中通过 `AUTH_PASSWORD` 设置；未设置则首次启动时自动生成并回写到 `.env`）
2. 进入 **设置页**（`/settings`）
3. 配置 **Anthropic API Key**（驱动 AI 助手），支持自定义 Base URL 和模型
4. 配置至少一个图片/视频**供应商 API Key**（Gemini / 火山方舟 / Grok / OpenAI），或添加自定义供应商
5. 根据需要调整模型选择、速率限制等参数

> 💡 所有配置项都可以在设置页修改，无需手动编辑配置文件。

---

## 第三章：完整流程

以下步骤在 Web UI 工作台中完成。

### 3.1 创建项目

1. 在项目列表页点击「新建项目」
2. 输入项目名称（如「我的小说」）
3. 上传小说文本文件（.txt 格式）

### 3.2 生成分镜剧本

在项目工作台右侧打开 AI 助手面板，通过对话让助手生成剧本：

- AI 会自动分析小说内容，将其拆分为适合视频的片段
- 每个片段包含画面描述、出场角色、重要道具/场景（线索）

**审核点**：检查剧本结构是否合理，角色和线索是否识别正确。

### 3.3 生成角色设计图

AI 为每个角色生成设计图，用于保持后续所有场景中的角色外观一致。

**审核点**：检查角色形象是否符合小说描述，不满意可重新生成。

### 3.4 生成线索设计图

AI 为重要道具和场景元素（如信物、特定地点）生成参考图。

**审核点**：检查线索设计是否符合预期。

### 3.5 生成分镜图片

AI 根据剧本生成每个场景的静态图片，自动引用角色和线索设计图确保一致性。

**审核点**：检查场景构图、角色一致性、氛围是否正确。

### 3.6 生成视频片段

分镜图片作为起始帧，通过所选视频供应商（Veo 3.1 / Seedance / Grok / Sora 2 等）生成 4-8 秒的动态视频片段。

生成任务进入异步任务队列，你可以在任务监控面板实时查看进度。Image 和 Video 通道独立并发，RPM 限速确保不超 API 配额。

**审核点**：预览每个视频片段，不满意可单独重新生成。

### 3.7 合成最终视频

所有片段通过 FFmpeg 拼接，添加转场效果和背景音乐，输出最终视频。

默认输出 **9:16 竖屏**格式，适合发布到短视频平台。

---

## 第四章：进阶技巧

### 4.1 版本历史与回滚

每次重新生成素材时，系统自动保存历史版本。在工作台的时间线视图中，可以浏览历史版本并一键回滚。

### 4.2 控制费用

**查看费用统计：**

在设置页可查看 API 调用次数和费用明细。

**减少开支的技巧：**

- 仔细审核每个阶段的输出，减少返工
- 先生成少量场景测试效果，满意后再批量生成
- 视频生成使用 Fast 模式可节省约 60% 费用
- 分镜图使用 Flash 模型，角色设计图使用 Pro 模型

### 4.3 项目导入/导出

项目支持打包归档，方便备份和迁移：

- **导出**：将整个项目（含所有素材）打包为归档文件
- **导入**：从归档文件恢复项目

---

## 第五章：常见问题

### Q: Docker 启动失败？

1. 确认 Docker 服务正在运行：`systemctl status docker`
2. 检查端口 1241 是否被占用：`ss -tlnp | grep 1241`
3. 查看容器日志：`docker compose logs`（在对应的 `deploy/` 或 `deploy/production/` 目录下执行）

### Q: API 调用失败？

1. 确认设置页中对应供应商的 API Key 填写正确
2. Gemini 用户需确认已启用付费层级（免费层级不支持图片/视频生成）
3. 检查服务器网络是否可以访问对应供应商的 API 服务
4. 在供应商控制台查看 API 使用量是否超限

### Q: 角色在不同场景中长得不一样？

1. 确保先生成角色设计图
2. 检查角色设计图质量，不满意要先重新生成
3. 系统会自动使用角色设计图作为参考，确保后续场景一致

### Q: 视频生成很慢？

视频生成通常需要 1-3 分钟/片段，这是正常的。影响因素：

- 视频时长（4 秒 vs 8 秒）
- API 服务器负载
- 网络状况

任务队列支持并发处理，多个视频片段可同时生成。

### Q: 生成中断了怎么办？

任务队列支持断点续传。重新触发生成时，系统会自动跳过已完成的片段，只处理剩余部分。

---

## 下一步

恭喜你完成了入门教程！接下来你可以：

- 💰 查看 [Google GenAI 费用说明](google-genai-docs/Google视频&图片生成费用参考.md) 和 [火山方舟费用说明](ark-docs/火山方舟费用参考.md) 了解详细定价
- 🐛 遇到问题？提交 [Issue](https://github.com/ArcReel/ArcReel/issues) 反馈
- 💬 扫码加入飞书交流群，获取帮助和最新动态：

<img src="assets/feishu-qr.png" alt="飞书交流群二维码" width="280">

如果觉得项目有用，请给个 ⭐ Star 支持一下！

[🇬🇧 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Known Issues

Technical debt identified during multi-provider video generation integration (#98). These do not affect functional correctness and are recorded here for future iterations.

---

## ~~1. UsageRepository cost routing logic leak~~ ✅ Fixed

**Fix:** `CostCalculator.calculate_cost()` uses a unified entry point that routes explicitly by `(call_type, provider)`, with the Repository called only once. Gemini video no longer implicitly falls through.

---

## ~~2. CostCalculator cost structure asymmetry~~ ✅ Fixed

**Fix:** Resolved together with Issue 1. The `calculate_cost()` unified entry point hides the differences in rate dictionary structures across providers.

---

## 3. VideoGenerationRequest parameter bloat

**Location:** `lib/video_backends/base.py` — `VideoGenerationRequest`

**Current state:** Backend-specific fields are mixed into the shared dataclass (`negative_prompt` is Veo-specific, `service_tier`/`seed` are Seedance-specific), relying on the convention "each backend ignores unsupported fields" via comments.

**Assessment:** Only 3 backends with 3 specific fields — the complexity of introducing per-backend config classes is not worth it. Refactor when a 4th backend is added.

---

## ~~4. SystemConfigManager secret block repetition pattern~~ ✅ Fixed

**Fix:** Replaced ~8 identical if/else secret blocks in `_apply_to_env()` with a tuple + loop.

---

## 5. UsageRepository finish_call double DB round-trip

**Location:** `lib/db/repositories/usage_repo.py` — `finish_call()`

**Current state:** First does a `SELECT` to read the full row (to get `provider`, `call_type`, etc. for cost calculation), then does an `UPDATE` to write results back. Two serial database round-trips per task.

**Assessment:** Video generation takes minutes — DB round-trip impact is negligible. Eliminating this requires modifying 3 callers (MediaGenerator, TextGenerator, UsageTracker), which is disproportionate risk.

---

## 6. UsageRepository.finish_call() parameter bloat

**Location:** `lib/db/repositories/usage_repo.py` — `finish_call()`, `lib/usage_tracker.py` — `finish_call()`

**Current state:** `finish_call()` already has 9 keyword parameters, and `UsageTracker.finish_call()` mirrors them 1:1 by pass-through.

**Assessment:** Coupled with Issue 5; low benefit to fix independently. Refactor together with Issue 5.

---

## ~~7. call_type bare string lacks type constraints~~ ✅ Fixed

**Fix:** Python side defines `CallType = Literal["image", "video", "text"]` (`lib/providers.py`); frontend defines the corresponding `CallType` type (`frontend/src/types/provider.ts`); unified in interface signatures.

---

## ~~8. UsageRepository query method filter construction repetition~~ ✅ Fixed

**Fix:** Promoted `_base_filters()` to a class method `_build_filters()`, shared by the three query methods.

---

## ~~9. update_project backend field missing provider validity check~~ ✅ Fixed

**Fix:** Extracted shared validation function `validate_backend_value()` (`server/routers/_validators.py`), used by both `update_project()` and `patch_system_config()` to reject invalid provider/model values and return 400.

---

## ~~10. test_text_backends test file asyncio.to_thread patch repetition~~ ✅ Fixed

**Fix:** Extracted `sync_to_thread` fixture in `tests/test_text_backends/conftest.py`, shared across test files.

---

<a name="chinese"></a>

# 已知问题

多供应商视频生成接入（#98）过程中发现的存量技术债，不影响功能正确性，记录以便后续迭代。

---

## ~~1. UsageRepository 费用路由逻辑泄漏~~ ✅ 已修复

**修复：** `CostCalculator.calculate_cost()` 统一入口按 `(call_type, provider)` 显式路由，Repository 只调一次。Gemini video 不再隐式 fallthrough。

---

## ~~2. CostCalculator 费用结构不对称~~ ✅ 已修复

**修复：** 随 Issue 1 一并解决。`calculate_cost()` 统一入口隐藏了各供应商的费率字典结构差异。

---

## 3. VideoGenerationRequest 参数膨胀

**位置：** `lib/video_backends/base.py` — `VideoGenerationRequest`

**现状：** 共享 dataclass 中混入了后端特有字段（`negative_prompt` 为 Veo 特有，`service_tier`/`seed` 为 Seedance 特有），靠注释"各 Backend 忽略不支持的字段"约定。

**评估：** 仅 3 个后端 3 个特有字段，引入 per-backend config 类的复杂度不值得。待第 4 个后端接入时再重构。

---

## ~~4. SystemConfigManager secret 块重复模式~~ ✅ 已修复

**修复：** 将 `_apply_to_env()` 中 ~8 个相同模式的 if/else secret 块替换为元组 + 循环。

---

## 5. UsageRepository finish_call 双次 DB 往返

**位置：** `lib/db/repositories/usage_repo.py` — `finish_call()`

**现状：** 先 `SELECT` 读取整行（取 `provider`、`call_type` 等字段计算费用），再 `UPDATE` 写回结果。对每个任务两次串行数据库往返。

**评估：** 视频生成耗时分钟级，DB 往返影响极小。消除需改动 3 个调用方（MediaGenerator、TextGenerator、UsageTracker），风险不对称。

---

## 6. UsageRepository.finish_call() 参数膨胀

**位置：** `lib/db/repositories/usage_repo.py` — `finish_call()`，`lib/usage_tracker.py` — `finish_call()`

**现状：** `finish_call()` 已有 9 个 keyword 参数，且 `UsageTracker.finish_call()` 1:1 镜像透传。

**评估：** 与 Issue 5 耦合，单独改收益低。待 Issue 5 一并重构。

---

## ~~7. call_type 裸字符串缺乏类型约束~~ ✅ 已修复

**修复：** Python 端定义 `CallType = Literal["image", "video", "text"]`（`lib/providers.py`），前端定义对应 `CallType` 类型（`frontend/src/types/provider.ts`），在接口签名中统一使用。

---

## ~~8. UsageRepository 查询方法 filter 构建重复~~ ✅ 已修复

**修复：** 将 `_base_filters()` 提升为类方法 `_build_filters()`，三个查询方法共享。

---

## ~~9. update_project 后端字段缺少 provider 合法性校验~~ ✅ 已修复

**修复：** 提取共享校验函数 `validate_backend_value()`（`server/routers/_validators.py`），`update_project()` 和 `patch_system_config()` 共同使用，拒绝非法 provider/model 值并返回 400。

---

## ~~10. test_text_backends 测试文件 asyncio.to_thread patch 重复~~ ✅ 已修复

**修复：** 在 `tests/test_text_backends/conftest.py` 中提取 `sync_to_thread` fixture，各测试文件共享。

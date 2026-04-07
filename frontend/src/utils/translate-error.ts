import i18n from "@/i18n";

// ---------------------------------------------------------------------------
// translateApiError
//
// Maps backend Chinese error detail strings to localised messages via the
// "errors" i18n namespace.  The backend always returns Chinese strings in
// HTTPException.detail; this utility tries to match them and returns the
// translated string in the active language.
// ---------------------------------------------------------------------------

/** Pattern entry: a substring or regex to match, and the errors-namespace key. */
const ERROR_KEY_MAP: Array<{ pattern: RegExp | string; key: string }> = [
  // Auth
  { pattern: "用户名或密码错误", key: "wrongCredentials" },
  { pattern: "认证已过期", key: "authExpired" },

  // Projects
  { pattern: "不存在或未初始化", key: "projectNotInitialized" },

  // Sessions
  { pattern: "会话或项目不存在", key: "sessionOrProjectNotFound" },
  { pattern: "SDK 会话创建超时", key: "sdkSessionTimeout" },
  { pattern: /会话 '.+' 不存在/, key: "sessionNotFound" },
  { pattern: "answers 不能为空", key: "answersEmpty" },

  // Files
  { pattern: "禁止访问项目目录外的文件", key: "fileAccessDenied" },
  { pattern: "无效的图片文件，无法解析", key: "invalidImageFile" },
  { pattern: "文件编码错误，无法读取", key: "fileEncodingError" },
  { pattern: "无效的上传类型", key: "invalidUploadType" },
  { pattern: "不支持的文件类型", key: "unsupportedFileType" },
  { pattern: /文件不存在/, key: "fileNotFound" },

  // Characters
  { pattern: /角色 '.+' 不存在/, key: "characterNotFound" },

  // Clues
  { pattern: /线索 '.+' 不存在/, key: "clueNotFound" },
  { pattern: "线索类型必须是 'prop' 或 'location'", key: "invalidClueType" },
  { pattern: "重要程度必须是 'major' 或 'minor'", key: "invalidClueImportance" },

  // Custom providers
  { pattern: "供应商不存在", key: "providerNotFound" },
  { pattern: "已启用的模型必须填写 model_id", key: "modelIdRequired" },
  { pattern: "model_id 重复", key: "modelIdDuplicate" },
  { pattern: "模型发现失败", key: "modelDiscoveryFailed" },
  { pattern: "至少需要提供一个更新字段", key: "atLeastOneFieldRequired" },

  // API keys
  { pattern: /API Key .+ 不存在/, key: "apiKeyNotFound" },
  { pattern: "API Key 无权执行此操作", key: "apiKeyUnauthorized" },
  { pattern: "已存在", key: "apiKeyNameExists" },

  // Cost estimation
  { pattern: "费用估算失败", key: "costEstimationFailed" },

  // Generic project not found (keep after more specific ones)
  { pattern: /项目 '.+' 不存在/, key: "projectNotFound" },
];

/**
 * Translate a backend API error detail to the active UI language.
 *
 * @param detail - The `detail` field from a FastAPI HTTPException response.
 *   May be a string, an array (Pydantic validation errors), or anything else.
 * @returns A localised error string.
 */
export function translateApiError(detail: unknown): string {
  if (typeof detail !== "string") {
    if (Array.isArray(detail) && detail.length > 0) {
      // Pydantic validation error array – join the msg fields
      return detail
        .map((e: unknown) =>
          typeof e === "string" ? e : (e as { msg?: string })?.msg ?? "",
        )
        .filter(Boolean)
        .join("; ");
    }
    return String(detail ?? i18n.t("errors:unknownError"));
  }

  for (const { pattern, key } of ERROR_KEY_MAP) {
    const matched =
      typeof pattern === "string" ? detail.includes(pattern) : pattern.test(detail);
    if (matched) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return i18n.t(`errors:${key}` as any);
    }
  }

  // Fallback: return the original Chinese string unchanged
  return detail;
}

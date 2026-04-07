import i18n from "@/i18n";

// ---------------------------------------------------------------------------
// cn – lightweight className concatenation utility.
// Filters out falsy values and joins the rest with spaces.
// ---------------------------------------------------------------------------

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

// ---------------------------------------------------------------------------
// getRoleLabel – maps a turn role to a localised display label.
// ---------------------------------------------------------------------------

export function getRoleLabel(role: string): string {
  const t = i18n.t.bind(i18n);
  switch (role) {
    case "assistant":
      return t("copilot:roleAssistant");
    case "user":
      return t("copilot:roleUser");
    case "tool":
      return t("copilot:roleTool");
    case "tool_result":
      return t("copilot:roleToolResult");
    case "skill_content":
      return "Skill";
    case "result":
      return t("copilot:roleResult");
    case "system":
      return t("copilot:roleSystem");
    case "stream_event":
      return t("copilot:roleStreamEvent");
    case "unknown":
      return t("copilot:roleMessage");
    default:
      return role || t("copilot:roleMessage");
  }
}

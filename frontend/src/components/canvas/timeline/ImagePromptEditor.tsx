import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown } from "lucide-react";
import { AutoTextarea } from "@/components/ui/AutoTextarea";
import { CompactInput } from "@/components/ui/CompactInput";
import { DropdownPill } from "@/components/ui/DropdownPill";
import { SHOT_TYPES } from "@/types";
import type { ImagePrompt, ShotType } from "@/types";

interface ImagePromptEditorProps {
  prompt: ImagePrompt;
  onUpdate: (patch: Partial<ImagePrompt>) => void;
}

/** Structured editor for ImagePrompt fields with collapsible composition section. */
export function ImagePromptEditor({
  prompt,
  onUpdate,
}: ImagePromptEditorProps) {
  const { t } = useTranslation(["canvas"]);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <AutoTextarea
        value={prompt.scene}
        onChange={(v) => onUpdate({ scene: v })}
        placeholder={t("segment.imagePromptPlaceholder")}
      />

      {/* Collapsible composition fields */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="inline-flex items-center gap-1 self-start text-[10px] text-gray-500 hover:text-gray-400"
      >
        <ChevronDown
          className={`h-3 w-3 transition-transform ${collapsed ? "-rotate-90" : ""}`}
        />
        {t("imagePrompt.composition")}
      </button>

      {!collapsed && (
        <div className="flex flex-col gap-2 pl-1">
          <DropdownPill
label={t("imagePrompt.shot")}
            value={prompt.composition.shot_type}
            options={SHOT_TYPES}
            onChange={(v: ShotType) =>
              onUpdate({
                composition: { ...prompt.composition, shot_type: v },
              })
            }
          />
          <CompactInput
label={t("imagePrompt.lighting")}
            value={prompt.composition.lighting}
            onChange={(v) =>
              onUpdate({
                composition: { ...prompt.composition, lighting: v },
              })
            }
placeholder={t("imagePrompt.lightingPlaceholder")}
          />
          <CompactInput
label={t("imagePrompt.ambiance")}
            value={prompt.composition.ambiance}
            onChange={(v) =>
              onUpdate({
                composition: { ...prompt.composition, ambiance: v },
              })
            }
placeholder={t("imagePrompt.ambiancePlaceholder")}
          />
        </div>
      )}
    </div>
  );
}

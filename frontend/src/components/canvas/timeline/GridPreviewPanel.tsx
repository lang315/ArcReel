import { useState, useEffect } from "react";
import {
  ChevronRight,
  RefreshCw,
  Loader2,
  Grid2x2,
  Film,
  AlertCircle,
  CheckCircle2,
  Clock,
  Scissors,
  ArrowRight,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import { API } from "@/api";
import type { GridGeneration, FrameCell } from "@/types/grid";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GridPreviewPanelProps {
  projectName: string;
  gridId: string | null;
  sceneIds: string[];
  onRegenerate: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type GridStatus = GridGeneration["status"];

function StatusBadge({ status }: { status: GridStatus }) {
  const { t } = useTranslation(["canvas"]);
  const configs: Record<
    GridStatus,
    { label: string; icon: React.ReactNode; cls: string }
  > = {
    pending: {
      label: t("grid.statusPending"),
      icon: <Clock className="h-3 w-3" />,
      cls: "bg-gray-800/80 text-gray-400 border-gray-700/50",
    },
    generating: {
      label: t("grid.statusGenerating"),
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      cls: "bg-blue-950/60 text-blue-300 border-blue-700/40",
    },
    splitting: {
      label: t("grid.statusSplitting"),
      icon: <Scissors className="h-3 w-3" />,
      cls: "bg-violet-950/60 text-violet-300 border-violet-700/40",
    },
    completed: {
      label: t("grid.statusCompleted"),
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "bg-emerald-950/60 text-emerald-400 border-emerald-700/40",
    },
    failed: {
      label: t("grid.statusFailed"),
      icon: <AlertCircle className="h-3 w-3" />,
      cls: "bg-red-950/60 text-red-400 border-red-700/40",
    },
  };

  const { label, icon, cls } = configs[status];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium tracking-wide ${cls}`}
    >
      {icon}
      {label}
    </span>
  );
}

const FRAME_TYPE_CLS = {
  first: "bg-amber-900/50 text-amber-300 border-amber-700/40",
  transition: "bg-sky-900/50 text-sky-300 border-sky-700/40",
  placeholder: "bg-gray-800/80 text-gray-500 border-gray-700/40",
} as const;

function FrameTypeBadge({ type }: { type: FrameCell["frame_type"] }) {
  const { t } = useTranslation(["canvas"]);
  const labelMap = {
    first: t("grid.frameFirst"),
    transition: t("grid.frameTransition"),
    placeholder: t("grid.framePlaceholder"),
  } as const;
  const label = labelMap[type];
  const cls = FRAME_TYPE_CLS[type];
  return (
    <span
      className={`inline-flex items-center rounded border px-1 py-px text-[9px] font-semibold uppercase tracking-wider ${cls}`}
    >
      {label}
    </span>
  );
}

/** Derive a display name from scene id by truncating for readability. */
function sceneShortId(id: string): string {
  if (!id) return "—";
  const parts = id.split("_");
  if (parts.length >= 2) return `${parts[parts.length - 2]}_${parts[parts.length - 1]}`;
  return id.length > 10 ? `…${id.slice(-8)}` : id;
}

// ---------------------------------------------------------------------------
// FrameChainList
// ---------------------------------------------------------------------------

function FrameChainList({ frames }: { frames: FrameCell[] }) {
  const { t } = useTranslation(["canvas"]);
  if (frames.length === 0) {
    return (
      <div className="py-4 text-center text-xs text-gray-600">{t("grid.noFrameChain")}</div>
    );
  }

  return (
    <div className="flex flex-col gap-px overflow-hidden rounded-md border border-gray-800/60">
      {/* Header row */}
      <div className="grid grid-cols-[2rem_1fr_auto_auto] items-center gap-2 border-b border-gray-800/60 bg-gray-900/50 px-3 py-1.5">
        <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
          #
        </span>
        <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
          {t("grid.sceneMapping")}
        </span>
        <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
          {t("grid.type")}
        </span>
        <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
          {t("grid.position")}
        </span>
      </div>

      {frames.map((frame, idx) => (
        <motion.div
          key={frame.index}
          initial={{ opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.02, duration: 0.2 }}
          className={`grid grid-cols-[2rem_1fr_auto_auto] items-center gap-2 px-3 py-2 text-xs transition-colors hover:bg-gray-800/30 ${
            idx % 2 === 0 ? "bg-gray-900/20" : "bg-transparent"
          }`}
        >
          {/* Index */}
          <span className="font-mono text-[11px] font-semibold tabular-nums text-gray-500">
            {String(frame.index + 1).padStart(2, "0")}
          </span>

          {/* Scene mapping */}
          <div className="flex min-w-0 items-center gap-1.5">
            {frame.prev_scene_id ? (
              <span
                className="truncate font-mono text-[10px] text-gray-400"
                title={frame.prev_scene_id}
              >
                {sceneShortId(frame.prev_scene_id)}
              </span>
            ) : null}
            {frame.prev_scene_id && frame.next_scene_id ? (
              <ArrowRight className="h-2.5 w-2.5 shrink-0 text-gray-600" />
            ) : null}
            {frame.next_scene_id ? (
              <span
                className="truncate font-mono text-[10px] text-amber-400/80"
                title={frame.next_scene_id}
              >
                {sceneShortId(frame.next_scene_id)}
              </span>
            ) : null}
            {!frame.prev_scene_id && !frame.next_scene_id ? (
              <span className="text-[10px] text-gray-600">—</span>
            ) : null}
          </div>

          {/* Frame type badge */}
          <FrameTypeBadge type={frame.frame_type} />

          {/* Grid position */}
          <span className="font-mono text-[10px] tabular-nums text-gray-600">
            R{frame.row + 1}C{frame.col + 1}
          </span>
        </motion.div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// GridPreviewPanel
// ---------------------------------------------------------------------------

export function GridPreviewPanel({
  projectName,
  gridId,
  sceneIds,
  onRegenerate,
}: GridPreviewPanelProps) {
  const { t } = useTranslation(["canvas"]);
  const [expanded, setExpanded] = useState(false);
  const [grid, setGrid] = useState<GridGeneration | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch grid data when expanded and gridId is available
  useEffect(() => {
    if (!expanded || !gridId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    API.getGrid(projectName, gridId)
      .then((data) => {
        if (!cancelled) {
          setGrid(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("grid.loadFailed"));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [expanded, gridId, projectName]);

  const imageUrl =
    grid?.grid_image_path
      ? API.getFileUrl(projectName, grid.grid_image_path)
      : null;

  return (
    <div className="mt-2.5 overflow-hidden rounded-lg border border-amber-900/20 bg-amber-950/10">
      {/* Toggle header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-amber-900/10 focus:outline-none"
      >
        <motion.span
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: 0.18, ease: "easeInOut" }}
          className="text-amber-600/70"
        >
          <ChevronRight className="h-3.5 w-3.5" />
        </motion.span>

        <Film className="h-3.5 w-3.5 text-amber-500/60" />

        <span className="text-xs font-medium text-amber-400/70">{t("grid.preview")}</span>

        {gridId && grid ? (
          <span className="ml-1">
            <StatusBadge status={grid.status} />
          </span>
        ) : gridId ? (
          <span className="ml-1 text-[10px] text-gray-600">
            {sceneIds.length} {t("grid.scenes")}
          </span>
        ) : (
          <span className="ml-1 text-[10px] text-gray-600">{t("grid.notGenerated")}</span>
        )}

        {/* Grid info pill */}
        {grid && (
          <span className="ml-auto flex items-center gap-1 font-mono text-[10px] text-gray-500">
            <Grid2x2 className="h-3 w-3" />
            {grid.rows}×{grid.cols}
          </span>
        )}
      </button>

      {/* Collapsible content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="panel-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="border-t border-amber-900/20 px-3 py-3">
              {/* No grid yet */}
              {!gridId ? (
                <div className="flex flex-col items-center gap-2 py-6 text-center">
                  <Grid2x2 className="h-8 w-8 text-gray-700" />
                  <p className="text-xs text-gray-600">{t("grid.notGeneratedYet")}</p>
                  <p className="text-[10px] text-gray-700">
                    {t("grid.clickGenerateHint")}
                  </p>
                </div>
              ) : loading ? (
                /* Loading state */
                <div className="flex items-center justify-center gap-2 py-8">
                  <Loader2 className="h-4 w-4 animate-spin text-amber-500/50" />
                  <span className="text-xs text-gray-600">{t("grid.loadingData")}</span>
                </div>
              ) : error ? (
                /* Error state */
                <div className="flex items-center gap-2 rounded-md border border-red-900/30 bg-red-950/20 px-3 py-2.5">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-500/70" />
                  <span className="text-xs text-red-400/80">{error}</span>
                </div>
              ) : grid ? (
                /* Grid loaded */
                <div className="flex flex-col gap-4">
                  {/* Top bar: status + meta + regen button */}
                  <div className="flex items-center gap-2">
                    <StatusBadge status={grid.status} />
                    <span className="text-[10px] text-gray-600">
                      {grid.model}
                    </span>
                    {grid.error_message && (
                      <span
                        className="truncate text-[10px] text-red-400/70"
                        title={grid.error_message}
                      >
                        {grid.error_message}
                      </span>
                    )}
                    <div className="ml-auto">
                      <motion.button
                        type="button"
                        onClick={onRegenerate}
                        className="inline-flex items-center gap-1 rounded border border-amber-800/30 bg-amber-950/30 px-2 py-1 text-[10px] font-medium text-amber-400/80 transition-colors hover:bg-amber-900/40 hover:text-amber-300"
                        whileTap={{ scale: 0.95 }}
                      >
                        <RefreshCw className="h-3 w-3" />
                        {t("grid.regenerate")}
                      </motion.button>
                    </div>
                  </div>

                  {/* Main content: image + frame chain */}
                  <div className="grid grid-cols-[auto_1fr] gap-3">
                    {/* Composite grid image */}
                    <div className="flex flex-col gap-1.5">
                      <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
                        {t("grid.compositeImage")}
                      </span>
                      {imageUrl ? (
                        <div className="overflow-hidden rounded-md border border-gray-800/50 bg-gray-900/50">
                          <img
                            src={imageUrl}
                            alt={t("grid.compositeImageAlt")}
                            className="block w-40 object-cover"
                            style={{ imageRendering: "pixelated" }}
                          />
                          {/* Grid overlay indicator */}
                          <div className="border-t border-gray-800/60 px-2 py-1">
                            <span className="font-mono text-[9px] text-gray-600">
                              {t("grid.cellCount", { count: grid.cell_count })} · {grid.grid_size}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex h-24 w-40 items-center justify-center rounded-md border border-gray-800/40 bg-gray-900/30">
                          <span className="text-[10px] text-gray-700">
                            {grid.status === "generating" || grid.status === "pending"
                              ? t("grid.generating")
                              : t("grid.noImage")}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Frame chain */}
                    <div className="flex min-w-0 flex-col gap-1.5">
                      <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600">
                        {t("grid.frameChainMapping", { count: grid.frame_chain.length })}
                      </span>
                      <div className="max-h-52 overflow-y-auto rounded-md scrollbar-thin">
                        <FrameChainList frames={grid.frame_chain} />
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

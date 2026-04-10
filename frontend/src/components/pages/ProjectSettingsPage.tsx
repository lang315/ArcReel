import { useParams, useLocation } from "wouter";
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { ArrowLeft } from "lucide-react";
import { API } from "@/api";
import { useAppStore } from "@/stores/app-store";
import { ProviderModelSelect } from "@/components/ui/ProviderModelSelect";
import { PROVIDER_NAMES } from "@/components/ui/ProviderIcon";
import { getProviderModels, getCustomProviderModels, lookupSupportedDurations, DEFAULT_DURATIONS } from "@/utils/provider-models";
import type { CustomProviderInfo, ProviderInfo } from "@/types";

export function ProjectSettingsPage() {
  const { t } = useTranslation("settings");
  const { t: tc } = useTranslation();
  const params = useParams<{ projectName: string }>();
  const projectName = params.projectName || "";
  const [, navigate] = useLocation();

  const [options, setOptions] = useState<{
    video_backends: string[];
    image_backends: string[];
    text_backends: string[];
    provider_names?: Record<string, string>;
  } | null>(null);
  const [globalDefaults, setGlobalDefaults] = useState<{
    video: string;
    image: string;
  }>({ video: "", image: "" });

  const allProviderNames = useMemo(
    () => ({ ...PROVIDER_NAMES, ...(options?.provider_names ?? {}) }),
    [options],
  );

  // Project-level overrides (from project.json)
  // "" means "follow global default"
  const [videoBackend, setVideoBackend] = useState<string>("");
  const [imageBackend, setImageBackend] = useState<string>("");
  const [audioOverride, setAudioOverride] = useState<boolean | null>(null);
  const [textScript, setTextScript] = useState<string>("");
  const [textOverview, setTextOverview] = useState<string>("");
  const [textStyle, setTextStyle] = useState<string>("");
  const [aspectRatio, setAspectRatio] = useState<string>("");
  const [generationMode, setGenerationMode] = useState<"single" | "grid">("single");
  const [defaultDuration, setDefaultDuration] = useState<number | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [customProviders, setCustomProviders] = useState<CustomProviderInfo[]>([]);
  const [saving, setSaving] = useState(false);
  const initialRef = useRef({
    videoBackend: "", imageBackend: "", audioOverride: null as boolean | null,
    textScript: "", textOverview: "", textStyle: "",
    aspectRatio: "", generationMode: "single" as "single" | "grid",
    defaultDuration: null as number | null,
  });

  useEffect(() => {
    let disposed = false;

    Promise.all([
      API.getSystemConfig(),
      API.getProject(projectName),
      getProviderModels().catch(() => [] as ProviderInfo[]),
      getCustomProviderModels().catch(() => [] as CustomProviderInfo[]),
    ]).then(([configRes, projectRes, providerList, customProviderList]) => {
      if (disposed) return;

      setOptions({
        video_backends: configRes.options?.video_backends ?? [],
        image_backends: configRes.options?.image_backends ?? [],
        text_backends: configRes.options?.text_backends ?? [],
        provider_names: configRes.options?.provider_names,
      });
      setGlobalDefaults({
        video: configRes.settings?.default_video_backend ?? "",
        image: configRes.settings?.default_image_backend ?? "",
      });
      setProviders(providerList);
      setCustomProviders(customProviderList);

      const project = projectRes.project as unknown as Record<string, unknown>;
      const vb = (project.video_backend as string | undefined) ?? "";
      const ib = (project.image_backend as string | undefined) ?? "";
      const rawAudio = project.video_generate_audio;
      const ao = typeof rawAudio === "boolean" ? rawAudio : null;
      const ts = (project.text_backend_script as string | undefined) ?? "";
      const to = (project.text_backend_overview as string | undefined) ?? "";
      const tst = (project.text_backend_style as string | undefined) ?? "";

      const ar = typeof project.aspect_ratio === "string"
        ? project.aspect_ratio
        : "";
      const gm = (project.generation_mode as "single" | "grid" | undefined) ?? "single";
      const dd = project.default_duration != null ? (project.default_duration as number) : null;

      setVideoBackend(vb);
      setImageBackend(ib);
      setAudioOverride(ao);
      setTextScript(ts);
      setTextOverview(to);
      setTextStyle(tst);
      setAspectRatio(ar);
      setGenerationMode(gm);
      setDefaultDuration(dd);
      initialRef.current = {
        videoBackend: vb, imageBackend: ib, audioOverride: ao,
        textScript: ts, textOverview: to, textStyle: tst,
        aspectRatio: ar, generationMode: gm, defaultDuration: dd,
      };
    });

    return () => { disposed = true; };
  }, [projectName]);

  const effectiveVideoBackend = videoBackend || globalDefaults.video;
  const supportedDurations = useMemo(
    () => lookupSupportedDurations(providers, effectiveVideoBackend, customProviders),
    [providers, effectiveVideoBackend, customProviders],
  );

  // Derive effective default duration during render — if current value
  // is not in the model's supported list, treat it as "auto" (null).
  const effectiveDefaultDuration =
    supportedDurations && defaultDuration !== null && !supportedDurations.includes(defaultDuration)
      ? null
      : defaultDuration;

  const handleVideoBackendChange = useCallback((value: string) => {
    setVideoBackend(value);
    // When video model changes, reset default duration so the UI
    // re-evaluates against the new model's supported durations.
    const effective = value || globalDefaults.video;
    const durations = lookupSupportedDurations(providers, effective, customProviders);
    if (durations && defaultDuration !== null && !durations.includes(defaultDuration)) {
      setDefaultDuration(null);
    }
  }, [globalDefaults.video, providers, customProviders, defaultDuration]);

  const isDirty =
    videoBackend !== initialRef.current.videoBackend ||
    imageBackend !== initialRef.current.imageBackend ||
    audioOverride !== initialRef.current.audioOverride ||
    textScript !== initialRef.current.textScript ||
    textOverview !== initialRef.current.textOverview ||
    textStyle !== initialRef.current.textStyle ||
    aspectRatio !== initialRef.current.aspectRatio ||
    generationMode !== initialRef.current.generationMode ||
    defaultDuration !== initialRef.current.defaultDuration;

  useEffect(() => {
    if (!isDirty) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  const guardedNavigate = useCallback((path: string) => {
    if (isDirty && !window.confirm(t("projectSettings.unsavedWarning"))) return;
    navigate(path);
  }, [isDirty, navigate, t]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await API.updateProject(projectName, {
        video_backend: videoBackend || null,
        image_backend: imageBackend || null,
        video_generate_audio: audioOverride,
        text_backend_script: textScript || null,
        text_backend_overview: textOverview || null,
        text_backend_style: textStyle || null,
        aspect_ratio: aspectRatio || undefined,
        generation_mode: generationMode,
        default_duration: defaultDuration,
      } as Record<string, unknown>);
      initialRef.current = {
        videoBackend, imageBackend, audioOverride,
        textScript, textOverview, textStyle,
        aspectRatio, generationMode, defaultDuration,
      };
      useAppStore.getState().pushToast(t("projectSettings.saved"), "success");
    } catch (e: unknown) {
      useAppStore.getState().pushToast(e instanceof Error ? e.message : t("projectSettings.saveFailed"), "error");
    } finally {
      setSaving(false);
    }
  }, [videoBackend, imageBackend, audioOverride, textScript, textOverview, textStyle, aspectRatio, generationMode, defaultDuration, projectName, t]);

  return (
    <div className="fixed inset-0 z-50 bg-gray-950 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-800 bg-gray-950/95 px-6 py-4 backdrop-blur">
        <button
          onClick={() => guardedNavigate(`/app/projects/${projectName}`)}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          aria-label={t("projectSettings.backAriaLabel")}
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-semibold text-gray-100">{t("projectSettings.title")}</h1>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-2xl px-6 py-8 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">{t("projectSettings.modelConfig")}</h2>
          <p className="mt-1 text-sm text-gray-500">
            {t("projectSettings.modelConfigDesc")}
          </p>
        </div>

        {options && (
          <>
            {/* Video model override */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <div className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.videoModel")}</div>
              <ProviderModelSelect
                value={videoBackend}
                options={options.video_backends}
                providerNames={allProviderNames}
                onChange={handleVideoBackendChange}
                allowDefault
                defaultHint={
                  globalDefaults.video ? t("projectSettings.currentGlobal", { model: globalDefaults.video }) : undefined
                }
              />
            </div>

            {/* Aspect ratio */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <fieldset>
                <legend className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.aspectRatio")}</legend>
                <div className="flex gap-3">
                  {(["9:16", "16:9"] as const).map((ar) => (
                    <label
                      key={ar}
                      className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-indigo-500 ${
                        aspectRatio === ar
                          ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                          : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                      }`}
                    >
                      <input
                        type="radio"
                        name="aspectRatio"
                        value={ar}
                        checked={aspectRatio === ar}
                        onChange={() => {
                          setAspectRatio(ar);
                          if (initialRef.current.aspectRatio && ar !== initialRef.current.aspectRatio) {
                            useAppStore.getState().pushToast(
                              t("projectSettings.aspectRatioWarning"),
                              "warning",
                            );
                          }
                        }}
                        className="sr-only"
                      />
                      {ar === "9:16" ? t("projectSettings.portrait") : t("projectSettings.landscape")}
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            {/* Generation mode */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <fieldset>
                <legend className="mb-1 text-sm font-medium text-gray-100">{t("projectSettings.generationMode")}</legend>
                <p className="mb-3 text-xs text-gray-500">
                  {t("projectSettings.generationModeDesc")}
                </p>
                <div className="flex gap-3">
                  {([
                    { value: "single" as const, label: t("projectSettings.singleMode") },
                    { value: "grid" as const, label: t("projectSettings.gridMode") },
                  ]).map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-indigo-500 ${
                        generationMode === opt.value
                          ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                          : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                      }`}
                    >
                      <input
                        type="radio"
                        name="generationMode"
                        value={opt.value}
                        checked={generationMode === opt.value}
                        onChange={() => setGenerationMode(opt.value)}
                        className="sr-only"
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            {/* Default duration */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <div className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.defaultDuration")}</div>
              <p className="mb-2 text-xs text-gray-500">
                {t("projectSettings.defaultDurationDesc")}
              </p>
              <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={t("projectSettings.defaultDurationAriaLabel")}>
                <button
                  type="button"
                  role="radio"
                  aria-checked={effectiveDefaultDuration === null}
                  onClick={() => setDefaultDuration(null)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                    effectiveDefaultDuration === null
                      ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                      : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  {tc("auto")}
                </button>
                {(supportedDurations ?? DEFAULT_DURATIONS).map((d) => (
                  <button
                    key={d}
                    type="button"
                    role="radio"
                    aria-checked={effectiveDefaultDuration === d}
                    onClick={() => setDefaultDuration(d)}
                    className={`rounded-lg border px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                      effectiveDefaultDuration === d
                        ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                        : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                    }`}
                  >
                    {d}s
                  </button>
                ))}
              </div>
            </div>

            {/* Image model override */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <div className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.imageModel")}</div>
              <ProviderModelSelect
                value={imageBackend}
                options={options.image_backends}
                providerNames={allProviderNames}
                onChange={setImageBackend}
                allowDefault
                defaultHint={
                  globalDefaults.image ? t("projectSettings.currentGlobal", { model: globalDefaults.image }) : undefined
                }
              />
            </div>

            {/* Audio override */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <div className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.generateAudio")}</div>
              <fieldset className="flex gap-4">
                <legend className="sr-only">{t("projectSettings.generateAudioLegend")}</legend>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input type="radio" name="audio" value="" checked={audioOverride === null}
                    onChange={() => setAudioOverride(null)} />
                  {tc("followGlobal")}
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input type="radio" name="audio" value="true" checked={audioOverride === true}
                    onChange={() => setAudioOverride(true)} />
                  {tc("enabled")}
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input type="radio" name="audio" value="false" checked={audioOverride === false}
                    onChange={() => setAudioOverride(false)} />
                  {tc("disabled")}
                </label>
              </fieldset>
            </div>
            {/* Text model overrides */}
            <div className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
              <div className="mb-3 text-sm font-medium text-gray-100">{t("projectSettings.textModel")}</div>
              <p className="mb-2 text-xs text-gray-500">{t("projectSettings.textModelDesc")}</p>
              <div className="space-y-3">
                {([
                  [textScript, setTextScript, t("projectSettings.scriptGeneration")] as const,
                  [textOverview, setTextOverview, t("projectSettings.overviewGeneration")] as const,
                  [textStyle, setTextStyle, t("projectSettings.styleAnalysis")] as const,
                ]).map(([value, setter, label]) => (
                  <div key={label}>
                    <div className="mb-1 text-xs text-gray-400">{label}</div>
                    <ProviderModelSelect
                      value={value}
                      options={options.text_backends}
                      providerNames={allProviderNames}
                      onChange={setter}
                      allowDefault
                      defaultHint={t("projectSettings.defaultHint")}
                      aria-label={label}
                    />
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {!options && (
          <div className="text-sm text-gray-500">{t("projectSettings.loadingConfig")}</div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-indigo-600 px-6 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
          >
            {saving ? tc("saving") : tc("save")}
          </button>
          <button
            onClick={() => guardedNavigate(`/app/projects/${projectName}`)}
            className="rounded-lg border border-gray-700 px-6 py-2 text-sm text-gray-300 hover:bg-gray-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950"
          >
            {tc("cancel")}
          </button>
        </div>
      </div>
    </div>
  );
}

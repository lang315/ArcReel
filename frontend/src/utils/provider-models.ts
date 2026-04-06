import { API } from "@/api";
import type { ProviderInfo } from "@/types";

export const DEFAULT_DURATIONS: readonly number[] = [4, 6, 8];

let _cache: ProviderInfo[] | null = null;
let _promise: Promise<ProviderInfo[]> | null = null;

/** Fetch (or return cached) provider list including models. */
export async function getProviderModels(): Promise<ProviderInfo[]> {
  if (_cache) return _cache;
  if (!_promise) {
    _promise = API.getProviders()
      .then((res) => {
        _cache = res.providers;
        _promise = null;
        return _cache;
      })
      .catch((err) => {
        _promise = null;
        throw err;
      });
  }
  return _promise;
}

/** Invalidate cache (call after provider config changes). */
export function invalidateProviderModelsCache(): void {
  _cache = null;
  _promise = null;
}

/**
 * Given a video backend string like "gemini-aistudio/veo-3.1-generate-preview",
 * look up supported_durations from the provider models data.
 * Returns undefined if provider/model not found.
 */
export function lookupSupportedDurations(
  providers: ProviderInfo[],
  videoBackend: string,
): number[] | undefined {
  const slashIdx = videoBackend.indexOf("/");
  if (slashIdx === -1) return undefined;
  const providerId = videoBackend.slice(0, slashIdx);
  const modelId = videoBackend.slice(slashIdx + 1);
  const provider = providers.find((p) => p.id === providerId);
  const model = provider?.models?.[modelId];
  return model?.supported_durations?.length
    ? model.supported_durations
    : undefined;
}

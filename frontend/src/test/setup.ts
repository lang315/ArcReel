import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Mock react-i18next so existing tests don't need real translation files
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      // Return the last segment of the key for readability
      const base = key.includes(":") ? key.split(":").pop()! : key;
      if (opts && typeof opts === "object") {
        return Object.entries(opts).reduce(
          (s, [k, v]) => s.replace(new RegExp(`\\{\\{${k}\\}\\}`, "g"), String(v)),
          base,
        );
      }
      return base;
    },
    i18n: { language: "zh", changeLanguage: vi.fn() },
  }),
  Trans: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: { type: "3rdParty" as const, init: vi.fn() },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.clearAllTimers();
  vi.useRealTimers();
  window.localStorage.clear();
  document.body.innerHTML = "";
});

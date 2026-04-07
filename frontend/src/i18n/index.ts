import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// --- Chinese (default) ---
import zhCommon from "./locales/zh/common.json";
import zhAuth from "./locales/zh/auth.json";
import zhLayout from "./locales/zh/layout.json";
import zhProjects from "./locales/zh/projects.json";
import zhSettings from "./locales/zh/settings.json";
import zhCanvas from "./locales/zh/canvas.json";
import zhCopilot from "./locales/zh/copilot.json";
import zhErrors from "./locales/zh/errors.json";

// --- English ---
import enCommon from "./locales/en/common.json";
import enAuth from "./locales/en/auth.json";
import enLayout from "./locales/en/layout.json";
import enProjects from "./locales/en/projects.json";
import enSettings from "./locales/en/settings.json";
import enCanvas from "./locales/en/canvas.json";
import enCopilot from "./locales/en/copilot.json";
import enErrors from "./locales/en/errors.json";

// --- Vietnamese ---
import viCommon from "./locales/vi/common.json";
import viAuth from "./locales/vi/auth.json";
import viLayout from "./locales/vi/layout.json";
import viProjects from "./locales/vi/projects.json";
import viSettings from "./locales/vi/settings.json";
import viCanvas from "./locales/vi/canvas.json";
import viCopilot from "./locales/vi/copilot.json";
import viErrors from "./locales/vi/errors.json";

export const defaultNS = "common" as const;

export const resources = {
  zh: {
    common: zhCommon,
    auth: zhAuth,
    layout: zhLayout,
    projects: zhProjects,
    settings: zhSettings,
    canvas: zhCanvas,
    copilot: zhCopilot,
    errors: zhErrors,
  },
  en: {
    common: enCommon,
    auth: enAuth,
    layout: enLayout,
    projects: enProjects,
    settings: enSettings,
    canvas: enCanvas,
    copilot: enCopilot,
    errors: enErrors,
  },
  vi: {
    common: viCommon,
    auth: viAuth,
    layout: viLayout,
    projects: viProjects,
    settings: viSettings,
    canvas: viCanvas,
    copilot: viCopilot,
    errors: viErrors,
  },
} as const;

export const supportedLanguages = [
  { code: "zh", label: "中文" },
  { code: "en", label: "English" },
  { code: "vi", label: "Tiếng Việt" },
] as const;

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "zh",
    defaultNS,
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ["localStorage"],
      lookupLocalStorage: "arcreel_language",
      caches: ["localStorage"],
    },
  });

export default i18n;

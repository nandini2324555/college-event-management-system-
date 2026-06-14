import en from "./en.json";
import te from "./te.json";

export const DEFAULT_LANGUAGE = "en";
export const LANGUAGE_STORAGE_KEY = "college_event_language";

export const SUPPORTED_LANGUAGES = [
  { code: "en" },
  { code: "te" }
];

const translations = {
  en,
  te
};

function getValueFromPath(object, path) {
  return path.split(".").reduce((value, key) => {
    if (value === undefined || value === null) {
      return undefined;
    }

    return value[key];
  }, object);
}

export function isSupportedLanguage(language) {
  return Object.prototype.hasOwnProperty.call(translations, language);
}

export function getSavedLanguage() {
  if (typeof window === "undefined") {
    return DEFAULT_LANGUAGE;
  }

  const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);

  return isSupportedLanguage(savedLanguage) ? savedLanguage : DEFAULT_LANGUAGE;
}

export function saveLanguage(language) {
  if (!isSupportedLanguage(language) || typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
}

export function setDocumentLanguage(language) {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.lang = isSupportedLanguage(language) ? language : DEFAULT_LANGUAGE;
}

export function getTranslation(language) {
  return translations[language] || translations[DEFAULT_LANGUAGE];
}

export function t(key, language = DEFAULT_LANGUAGE, values = {}) {
  const translation = getTranslation(language);
  const englishTranslation = getTranslation(DEFAULT_LANGUAGE);
  const translatedValue = getValueFromPath(translation, key) ?? getValueFromPath(englishTranslation, key) ?? key;

  return Object.entries(values).reduce((result, [placeholder, value]) => {
    return result.split(`{{${placeholder}}}`).join(value ?? "");
  }, translatedValue);
}

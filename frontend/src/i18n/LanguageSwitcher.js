import {
  DEFAULT_LANGUAGE,
  saveLanguage,
  setDocumentLanguage,
  SUPPORTED_LANGUAGES,
  t
} from "./index";

function LanguageSwitcher({ language, onLanguageChange }) {
  const currentLanguage = language || DEFAULT_LANGUAGE;

  function handleChange(event) {
    const nextLanguage = event.target.value;

    saveLanguage(nextLanguage);
    setDocumentLanguage(nextLanguage);
    onLanguageChange(nextLanguage);
  }

  return (
    <div className="language-switcher">
      <label htmlFor="language-select">{t("language", currentLanguage)}</label>
      <select id="language-select" value={currentLanguage} onChange={handleChange}>
        {SUPPORTED_LANGUAGES.map(({ code }) => (
          <option key={code} value={code}>
            {t(`languages.${code}`, currentLanguage)}
          </option>
        ))}
      </select>
    </div>
  );
}

export default LanguageSwitcher;

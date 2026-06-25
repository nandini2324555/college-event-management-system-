import { useEffect, useState } from "react";
import LanguageSwitcher from "./i18n/LanguageSwitcher";
import {
  DEFAULT_LANGUAGE,
  getSavedLanguage,
  setDocumentLanguage,
  t
} from "./i18n";

function App() {
  const [events, setEvents] = useState([]);
  const [language, setLanguage] = useState(() => getSavedLanguage());
  const [loading, setLoading] = useState(true);
  const [eventsError, setEventsError] = useState(false);
  const currentLanguage = language || DEFAULT_LANGUAGE;

  useEffect(() => {
    setDocumentLanguage(language);
  }, [language]);

  useEffect(() => {
    setLoading(true);
    setEventsError(false);

    fetch("https://college-event-management-system-3-b58b.onrender.com/events")
      .then(res => res.json())
      .then(data => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setEventsError(true))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="app-container">
      <div className="app-header">
        <h1>{t("appTitle", currentLanguage)}</h1>
        <LanguageSwitcher
          language={currentLanguage}
          onLanguageChange={setLanguage}
        />
      </div>

      {loading ? (
        <p>{t("loadingEvents", currentLanguage)}</p>
      ) : eventsError ? (
        <p>{t("errorLoadingEvents", currentLanguage)}</p>
      ) : events.length === 0 ? (
        <p>{t("noEventsFound", currentLanguage)}</p>
      ) : (
        events.map((event, index) => {
          const eventName = event.name || event.title;
          const eventLocation = event.location || event.description;

          return (
            <div key={index} className="event-card-inline">
              <h3>{eventName}</h3>
              <p>{event.date}</p>
              <p>{eventLocation}</p>
            </div>
          );
        })
      )}
    </div>
  );
}

export default App;

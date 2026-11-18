import type { Country, CountryCode } from "../api/types";
import { countryName, t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

interface Props {
  locale: Locale;
  countries: Country[];
  country: CountryCode;
  countryMessage: TranslationKey;
  onCountry: (country: CountryCode) => void;
  onLocale: (locale: Locale) => void;
}

/** Keep global country and language independent of the selected place draft. */
export function WorkspaceHeader({
  locale,
  countries,
  country,
  countryMessage,
  onCountry,
  onLocale,
}: Props) {
  const tr = (key: TranslationKey) => t(locale, key);
  return (
    <header className="masthead">
      <div className="brand" aria-label="MelliAtlas">
        <span className="brand-icon" aria-hidden="true">
          ✳
        </span>
        Melli<span className="brand-accent">Atlas</span>
      </div>
      <div className="header-context">
        <h1>{tr("workspacePlacesHeading")}</h1>
        <p>{tr("introduction")}</p>
      </div>
      <div className="header-actions">
        <label htmlFor="country">{tr("country")}</label>
        <select
          id="country"
          value={country}
          disabled={countries.length === 0}
          onChange={(event) => onCountry(event.target.value)}
        >
          {countries.length === 0 && (
            <option value="">{tr("selectCountry")}</option>
          )}
          {countries.map((item) => (
            <option key={item.code} value={item.code}>
              {countryName(locale, item.code, item.name)}
            </option>
          ))}
        </select>
        <details className="workspace-settings">
          <summary>{tr("workspaceSettings")}</summary>
          <div className="workspace-settings-content">
            <label htmlFor="language">{tr("language")}</label>
            <select
              id="language"
              value={locale}
              onChange={(event) =>
                onLocale(event.target.value === "en" ? "en" : "ru")
              }
            >
              <option value="ru">RU</option>
              <option value="en">EN</option>
            </select>
            <span className="header-version">MVP · W01</span>
          </div>
        </details>
      </div>
      {countries.length === 0 && (
        <span className="header-error" role="status">
          {tr(countryMessage)}
        </span>
      )}
    </header>
  );
}

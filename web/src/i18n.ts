/** Small typed UI vocabulary. Provider evidence remains verbatim and attributed. */
export type Locale = "ru" | "en";

const en = {
  headerContext: "Apiary placement planning",
  syntheticMode: "Synthetic source",
  setup: "01 / SETUP",
  heading: "Where should the apiary move this season?",
  introduction:
    "Compare forage periods with reported field treatments and ecological restrictions.",
  syntheticTitle: "Fictional data only.",
  syntheticDisclaimer:
    "This illustrates the workflow, not a forecast, warning or safety clearance.",
  country: "Country",
  language: "Language",
  referenceHeading: "Reference geography",
  referenceHelp:
    "Administrative boundaries are independent of synthetic study results.",
  referenceRegion: "Referenced region",
  referenceDistrict: "Supported district",
  referenceSelectRegion: "Select a region",
  referenceSelectDistrict: "No district selected",
  referenceDistrictLoading: "Loading districts…",
  referenceDistrictUnsupported:
    "District depth is unsupported for this region (HTTP 409).",
  referenceDistrictUnavailable:
    "District catalog unavailable; coverage is unverified.",
  referenceDistrictEmpty: "No districts listed; coverage is unverified.",
  referenceDistrictAvailable: "District catalog returned by the API.",
  referenceGeometryLoading: "Loading boundary…",
  referenceGeometryMissing: "No validated geometry for this territory.",
  referenceGeometryInvalid: "The reference geometry is marked invalid.",
  referenceGeometryUnavailable: "Cannot load a validated boundary.",
  referenceGeometryAvailable:
    "Showing reference boundary, not an analysis result.",
  referenceVersion: "Reference version",
  territory: "Territory",
  scenario: "Analysis source",
  selectCountry: "Loading countries…",
  countriesEmpty: "No countries are available from the API.",
  selectTerritory: "Select a territory",
  selectScenario: "Select an available scenario",
  noScenarios:
    "No executable scenarios are available for the selected country or territory.",
  loadingScenarios: "Loading available scenarios…",
  scenarioFailure: "Cannot load available scenarios: {reason}",
  loadingCountries: "Loading country list…",
  loadingRegions: "Checking regional catalog…",
  countriesFailure: "Cannot load countries: {reason}",
  regionsFailure: "Cannot load regions: {reason}",
  emptyRegions:
    "No verified regions are listed. This does not confirm complete geographic coverage.",
  availableRegions: "Regions from the current API reference are shown.",
  unavailableRegions:
    "Regional boundaries and listings are not available (HTTP 503). Synthetic sources are listed separately.",
  season: "Placement period",
  seasonStart: "Season start",
  seasonEnd: "Season end",
  seasonRange: "Available scenario period: {start} — {end}",
  seasonNoSource: "Choose an available scenario to set the season range.",
  startingPoint: "Starting point",
  pointHelp:
    "Optional: click the map. Coordinates are sent only in the POST body and are not stored in the browser.",
  pointSelected: "Point selected ({lat}, {lon})",
  clear: "Clear",
  run: "Investigate placement",
  running: "Investigation running…",
  submitHelp:
    "Select an available country, territory, scenario and a valid season.",
  reopen: "Open by ID",
  reopenPlaceholder: "Investigation UUID",
  open: "Open",
  reopenHelp:
    "By default, the server retains completed results in memory until restart.",
  mapSpace: "02 / GEOGRAPHY",
  mapHeading: "Apiary stops map",
  mapLabel: "Investigation map",
  basemap: "Online basemap",
  basemapPrivacy:
    "When enabled, the external tile provider receives requested map tile coordinates.",
  mapProposed: "Proposed stop",
  mapSelected: "Selected",
  mapNote:
    "Synthetic site coordinates are fictional. Click the map to choose a starting point.",
  mapStartingPoint: "Your point (current request only)",
  planReady: "Provisional plan prepared",
  noPlan: "No supported plan",
  status: "Status: {status}",
  stopsCount: "{count} stops · {moves} relocations",
  awaiting: "Awaiting analysis",
  timelineLabel: "Apiary stop timeline",
  timelineHeading: "Season and relocations",
  timelineEmpty:
    "No planned stops yet. Their periods will appear after an investigation.",
  timelineStop: "Stop {index}, {start} — {end}",
  forageLow: "Low forage",
  forageMedium: "Medium forage",
  forageHigh: "High forage",
  ecologyExcluded: "Excluded (fictional)",
  ecologyCaution: "Caution (fictional)",
  ecologyUnknown: "Unknown coverage",
  ecologyEligible: "Eligible",
  evidenceLabel: "Evidence and limitations",
  why: "Why this stop?",
  evidenceEmpty:
    "Source reports, screening results and alternative reasons will appear after the investigation.",
  noEvidenceIsNotSafe:
    "Missing treatment reports never prove the absence of risk.",
  evidenceHeading: "Decision evidence",
  evidenceSynthetic: "FIXTURE · synthetic evidence",
  investigation: "Investigation {id} · {status}",
  selectedSite: "Stop:",
  treatments: "Reported treatments",
  noTreatment:
    "No separate treatment finding is recorded for this stop. This does not establish safety.",
  proposedWindow: "Reported period: {start} — {end}",
  source: "Source: {source}, record {record}",
  product: "Product: {name}; crop: {crop}; reported bee hazard class: {hazard}",
  missingValue: "not reported",
  unknownValue: "unknown",
  approximateDistance: "Approximate distance: {distance} km",
  avoidedSites: "Alternatives were considered instead of: {sites}",
  ecology: "Ecology",
  rules: "Rules: {value}",
  evidenceIds: "Evidence: {value}",
  noneDefined: "not defined",
  noneReported: "not reported",
  noEcology: "No separate ecological assessment is recorded for this stop.",
  decisions: "Decision trace",
  sourcesAndLimits: "Sources and limitations",
  footer:
    "MelliAtlas · Experimental decision support. Does not certify absence of pesticide exposure, legal permission or site safety.",
  proximityIntersection: "Inside reported field",
  proximityNear: "Near reported field",
  proximityOutside: "Outside screening radius",
  proximityUnknownGeometry: "Geometry unavailable",
  proximityOutsidePeriod: "Outside reported period",
  proximityUnknownPeriod: "Period unavailable",
  errorAborted: "Request cancelled",
  errorMissing:
    "Investigation not found. In-memory results may be lost after a server restart.",
  errorInvalid:
    "The API rejected the investigation. Check the season and scenario.",
  errorDepth: "The selected territory catalog depth is not supported.",
  errorUnavailable:
    "Storage or reference data is unavailable. Missing data is not evidence of safety.",
  errorOther: "Request failed: {code}",
  pending:
    "Processing is still underway. Reopen the investigation by ID later.",
  failed:
    "Investigation processing failed. Diagnostic information is available in the response.",
  insufficient:
    "Investigation completed, but there are not enough assessed stops for a plan.",
} as const;

const ru: Record<keyof typeof en, string> = {
  headerContext: "Моделирование размещения пасеки",
  syntheticMode: "Синтетический источник",
  setup: "01 / ПОДГОТОВКА",
  heading: "Где разместить пасеку в этом сезоне?",
  introduction:
    "Сопоставьте периоды медосбора с сообщениями об обработке полей и экологическими ограничениями.",
  syntheticTitle: "Только вымышленные данные.",
  syntheticDisclaimer:
    "Это демонстрация механизма, не прогноз, оповещение или подтверждение безопасности.",
  country: "Страна",
  language: "Язык",
  referenceHeading: "Географический справочник",
  referenceHelp:
    "Административные границы загружаются отдельно от синтетического исследования.",
  referenceRegion: "Проверенный регион",
  referenceDistrict: "Поддерживаемый район",
  referenceSelectRegion: "Выберите регион",
  referenceSelectDistrict: "Без выбора района",
  referenceDistrictLoading: "Загрузка районов…",
  referenceDistrictUnsupported:
    "Районы этого региона не поддерживаются (HTTP 409).",
  referenceDistrictUnavailable:
    "Список районов недоступен; полнота данных не подтверждена.",
  referenceDistrictEmpty:
    "Районы не перечислены; полнота данных не подтверждена.",
  referenceDistrictAvailable: "Список районов получен от API.",
  referenceGeometryLoading: "Загрузка границы…",
  referenceGeometryMissing:
    "Для выбранной территории нет проверенной геометрии.",
  referenceGeometryInvalid: "Геометрия отмечена как некорректная.",
  referenceGeometryUnavailable: "Невозможно загрузить проверенную границу.",
  referenceGeometryAvailable:
    "Отображается граница из справочника, не результат анализа.",
  referenceVersion: "Версия справочника",
  territory: "Территория",
  scenario: "Источник анализа",
  selectCountry: "Получаем список стран…",
  countriesEmpty: "API не предоставляет список стран.",
  selectTerritory: "Выберите территорию",
  selectScenario: "Выберите доступный сценарий",
  noScenarios:
    "Для выбранной страны или территории нет доступных сценариев анализа.",
  loadingScenarios: "Получаем доступные сценарии…",
  scenarioFailure: "Не удалось загрузить сценарии: {reason}",
  loadingCountries: "Получаем сведения о странах…",
  loadingRegions: "Проверяем справочник регионов…",
  countriesFailure: "Список стран недоступен: {reason}",
  regionsFailure: "Не удалось загрузить регионы: {reason}",
  emptyRegions:
    "Справочник не содержит подтверждённых регионов. Это не сведения о полном покрытии.",
  availableRegions: "Показаны регионы из текущего API-справочника.",
  unavailableRegions:
    "Границы и перечень регионов пока не загружены (HTTP 503). Синтетические источники доступны отдельно.",
  season: "Период размещения",
  seasonStart: "Начало сезона",
  seasonEnd: "Конец сезона",
  seasonRange: "Допустимый период сценария: {start} — {end}",
  seasonNoSource: "Выберите доступный сценарий для установки периода.",
  startingPoint: "Исходная точка",
  pointHelp:
    "Необязательно: нажмите на карту. Точка передаётся только в теле запроса и не сохраняется в браузере.",
  pointSelected: "Точка выбрана ({lat}, {lon})",
  clear: "Очистить",
  run: "Исследовать размещение",
  running: "Анализ выполняется…",
  submitHelp:
    "Выберите доступную страну, территорию, сценарий и допустимый сезон.",
  reopen: "Открыть по ID",
  reopenPlaceholder: "UUID исследования",
  open: "Открыть",
  reopenHelp: "По умолчанию сервер хранит результаты в памяти до перезапуска.",
  mapSpace: "02 / ПРОСТРАНСТВО",
  mapHeading: "Карта стоянок",
  mapLabel: "Карта исследования",
  basemap: "Онлайн-подложка",
  basemapPrivacy:
    "При включении сторонний сервис получает координаты запрошенных картографических тайлов.",
  mapProposed: "Предлагаемая стоянка",
  mapSelected: "Выбрана",
  mapNote:
    "Координаты демонстрационных стоянок вымышлены. Нажмите на карту, чтобы выбрать исходную точку.",
  mapStartingPoint: "Ваша точка (только для текущего запроса)",
  planReady: "Предварительный план сформирован",
  noPlan: "План не сформирован",
  status: "Состояние: {status}",
  stopsCount: "{count} стоянки · {moves} перемещения",
  awaiting: "Ожидаем анализ",
  timelineLabel: "Сезонная шкала стоянок",
  timelineHeading: "Сезон и перемещения",
  timelineEmpty:
    "Пока нет рассчитанных стоянок. После исследования здесь появятся их интервалы.",
  timelineStop: "Стоянка {index}, {start} — {end}",
  forageLow: "Низкий потенциал медосбора",
  forageMedium: "Средний потенциал медосбора",
  forageHigh: "Высокий потенциал медосбора",
  ecologyExcluded: "Исключена (фиктивно)",
  ecologyCaution: "Требует внимания (фиктивно)",
  ecologyUnknown: "Покрытие неизвестно",
  ecologyEligible: "Подходит",
  evidenceLabel: "Сведения и ограничения",
  why: "Почему предлагается стоянка",
  evidenceEmpty:
    "После исследования здесь появятся исходные сообщения, результаты проверки и причины выбора альтернатив.",
  noEvidenceIsNotSafe:
    "Отсутствие сведений об обработках никогда не означает отсутствие риска.",
  evidenceHeading: "Основания решения",
  evidenceSynthetic: "FIXTURE · синтетические данные",
  investigation: "Исследование {id} · {status}",
  selectedSite: "Стоянка:",
  treatments: "Химические обработки",
  noTreatment:
    "Для выбранной стоянки нет отдельного уведомления в результатах. Это не подтверждение безопасности.",
  proposedWindow: "Заявленный период: {start} — {end}",
  source: "Источник: {source}, запись {record}",
  product:
    "Препарат: {name}; культура: {crop}; заявленный класс опасности для пчёл: {hazard}",
  missingValue: "не указан",
  unknownValue: "неизвестен",
  approximateDistance: "Приблизительное расстояние: {distance} км",
  avoidedSites:
    "После проверки обработок рассмотрены альтернативы вместо: {sites}",
  ecology: "Экология",
  rules: "Правила: {value}",
  evidenceIds: "Доказательства: {value}",
  noneDefined: "не определены",
  noneReported: "не указаны",
  noEcology: "Для этой стоянки нет отдельной экологической оценки.",
  decisions: "История решений",
  sourcesAndLimits: "Источники и ограничения",
  footer:
    "MelliAtlas · Экспериментальная система поддержки решений. Не подтверждает отсутствие химического воздействия, законность размещения или безопасность стоянки.",
  proximityIntersection: "Совпадает с полем",
  proximityNear: "Рядом с указанным полем",
  proximityOutside: "Вне радиуса предварительной проверки",
  proximityUnknownGeometry: "Геометрия неизвестна",
  proximityOutsidePeriod: "Вне указанного периода",
  proximityUnknownPeriod: "Период неизвестен",
  errorAborted: "Запрос отменён",
  errorMissing:
    "Исследование не найдено. Результат в памяти сервера мог исчезнуть после перезапуска.",
  errorInvalid:
    "API отклонил параметры исследования. Проверьте сезон и выбранный сценарий.",
  errorDepth: "Выбранная глубина каталога территорий не поддерживается.",
  errorUnavailable:
    "Хранилище или справочник временно недоступен. Отсутствие данных не означает безопасность.",
  errorOther: "Ошибка запроса: {code}",
  pending:
    "Обработка ещё продолжается. Можно повторно открыть исследование по ID.",
  failed:
    "Выполнение исследования завершилось ошибкой. Подробности доступны в диагностике ответа.",
  insufficient:
    "Исследование завершено, но для плана недостаточно проверенных стоянок.",
};

export type TranslationKey = keyof typeof en;
const resources: Record<Locale, Record<TranslationKey, string>> = { en, ru };

/** Format UI-controlled text; never interpolate untrusted content as markup. */
export function t(
  locale: Locale,
  key: TranslationKey,
  values: Record<string, string | number> = {},
): string {
  return resources[locale][key].replace(
    /\{([a-zA-Z]+)\}/g,
    (match, name: string) =>
      Object.prototype.hasOwnProperty.call(values, name)
        ? String(values[name])
        : match,
  );
}

/** Resolve future ISO country codes without maintaining a browser-side country switch. */
export function countryName(
  locale: Locale,
  code: string,
  fallback: string,
): string {
  return (
    new Intl.DisplayNames([locale], { type: "region" }).of(code) ?? fallback
  );
}

/** Small typed UI vocabulary. Provider evidence remains verbatim and attributed. */
export type Locale = "ru" | "en";

const en = {
  analysisAction: "Analyze selected area",
  analysisSelectRegion: "Select a region first.",
  analysisMissingBoundary:
    "Administrative boundaries are not installed. Import a reviewed geographic dataset before analyzing this area.",
  analysisNarrowArea:
    "This area is too large. Choose a district or click within the selected boundary to focus on a local point.",
  analysisPointOutside: "Click inside the selected territory boundary.",
  analysisResultsTitle: "Preliminary area findings",
  analysisAwaiting:
    "Choose an area and run the analysis to query available sources together.",
  analysisWorking: "Retrieving treatment notices and weather…",
  analysisNoProviders: "No external data sources are enabled for this country.",
  analysisSourcesUnavailable: "Source capabilities could not be retrieved.",
  analysisPartialDisclaimer:
    "Preliminary source inspection only. Saturn returns a region-wide first page, not verified complete coverage of the chosen area. No pesticide drift or safety assessment has been performed.",
  analysisSaturnCount:
    "{count} notices in the sampled response; {skipped} unrecognized entries.",
  analysisSaturnPartial:
    "Reported regional total: {total}. Further pages and local filtering have not been assessed.",
  analysisForecastHours: "Hourly weather forecast ({count} h)",
  analysisSaturnRegionUnmapped:
    "The region has no verified Saturn mapping yet. Weather results can still be used.",
  analysisSaturnNotSupported:
    "Saturn is not available for this country or is disabled by the server.",
  analysisWeatherNotEnabled: "Weather source is disabled by the server.",
  headerContext: "Environmental source explorer",
  syntheticMode: "Synthetic source",
  setup: "01 / SETUP",
  heading: "Find nectar-rich foraging areas",
  introduction: "Geospatial analytics for migratory beekeeping",
  syntheticTitle: "Fictional data only.",
  syntheticDisclaimer:
    "This illustrates the workflow, not a forecast, warning or safety clearance.",
  country: "Country",
  language: "Language",
  referenceHeading: "Location",
  referenceHelp:
    "Select a country, region and optionally a district from the independent geographic directory.",
  referenceRegion: "Region",
  referenceDistrict: "District",
  referenceSelectRegion: "Select a region",
  referenceSelectDistrict: "No district selected",
  referenceDistrictLoading: "Loading districts…",
  referenceDistrictUnsupported:
    "Districts are not yet imported for this region.",
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
  liveSourcesHeading: "Live data sources",
  liveSourcesHelp:
    "Choose a region from the independent administrative directory for Saturn; weather uses a selected map point.",
  liveSourcesJump: "Open live data sources",
  liveSourcesAvailability:
    "Only providers enabled on the server will appear. Missing data cannot be interpreted as no risk.",
  demoWorkflowHeading: "Optional fictional investigation",
  demoWorkflowUnavailable:
    "Fictional planning is disabled. Live sources remain usable without a scenario, territory or season.",
  saturnTitle: "Saturn: public treatment notices",
  saturnCode: "Saturn region mapping",
  saturnSelectRegion:
    "Select a Russian region in the left panel before loading Saturn notices.",
  saturnCodeHint:
    "The backend resolves the selected region using verified Saturn mappings; an unmapped region is not queried.",
  saturnRead: "Read one live page",
  saturnNext: "Read next page",
  saturnLoading: "Reading the public portal…",
  saturnUnmapped:
    "This region has no verified Saturn subject mapping. No request was sent to Saturn.",
  saturnError: "Saturn read failed: {reason}. Data availability is unknown.",
  saturnCount:
    "Page {page} · {count} identified notices · {skipped} unrecognized entries",
  saturnEmpty:
    "No identified notices on this page. This does not prove that no treatments are planned.",
  saturnWarning:
    "Experimental, unverified public reports. No automatic refresh, completeness guarantee, or validated drift model.",
  saturnField: "Field record {record}; plan {plan}",
  saturnDates: "Reported period: {start} — {end}",
  saturnProduct: "Product {name}; crop {crop}; bee hazard class {hazard}",
  saturnCaptured: "Read at {time}; source {source}",
  saturnMissing: "not reported",
  saturnGeometry: "Field geometry is not provided or not valid.",
  saturnMore:
    "Additional provider pages may exist. This display is not a complete register.",
  weatherTitle: "Weather forecast · Open-Meteo",
  weatherHelp:
    "Select a point on the map. Clicking Read shares its coordinates with Open-Meteo through the backend.",
  weatherRead: "Read 24-hour forecast",
  weatherLoading: "Reading weather forecast…",
  weatherError: "Weather unavailable: {reason}. No forecast can be inferred.",
  weatherWarning:
    "Model forecast, not measured wind or pesticide drift. Does not establish safety.",
  weatherGrid: "Forecast grid: {lat}, {lon} · Retrieved: {time}",
  weatherAttribution: "Weather data by Open-Meteo.com (CC BY 4.0)",
  weatherTime: "Time (UTC)",
  weatherWind: "Wind km/h",
  weatherDirection: "Direction °",
  weatherGusts: "Gusts km/h",
  weatherRain: "Precipitation mm",
  weatherMissing: "n/a",
  territory: "Territory",
  scenario: "Analysis source",
  selectCountry: "Loading countries…",
  countriesEmpty: "No countries are available from the API.",
  selectTerritory: "Select a territory",
  selectScenario: "Select an available scenario",
  noScenarios: "No executable fictional scenarios are available.",
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
    "Region directory unavailable. If PostgreSQL is configured, check its connection, migrations and seed.",
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
  mapHeading: "Selected area map",
  mapLabel: "Investigation map",
  basemap: "Online basemap",
  basemapPrivacy:
    "When enabled, the external tile provider receives requested map tile coordinates.",
  mapProposed: "Proposed stop",
  mapSelected: "Selected",
  mapNote:
    "Click the selected territory to mark a local point. Online map tiles are optional.",
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
  analysisAction: "Проанализировать выбранную местность",
  analysisSelectRegion: "Сначала выберите область или регион.",
  analysisMissingBoundary:
    "Границы ещё не импортированы в географическую базу. Для анализа нужен проверенный географический слой.",
  analysisNarrowArea:
    "Территория слишком большая. Выберите район или нажмите внутри его границы на карте, чтобы указать локальную точку.",
  analysisPointOutside: "Укажите точку внутри выбранной территории.",
  analysisResultsTitle: "Предварительные сведения по местности",
  analysisAwaiting:
    "Выберите местность и запустите анализ для загрузки доступных источников одним действием.",
  analysisWorking: "Получаем сообщения об обработках и прогноз погоды…",
  analysisNoProviders:
    "Для выбранной страны ни один реальный источник не включён на сервере.",
  analysisSourcesUnavailable: "Не удалось узнать список доступных источников.",
  analysisPartialDisclaimer:
    "Предварительные сведения. Сатурн возвращает только первую страницу по всей области, а не полное покрытие выбранной местности. Перенос пестицидов и безопасность не рассчитаны.",
  analysisSaturnCount:
    "В полученной выборке {count} сообщений, не распознано: {skipped}.",
  analysisSaturnPartial:
    "Всего записей по области по версии источника: {total}. Остальные страницы и фильтрация по местности ещё не проверены.",
  analysisForecastHours: "Почасовой прогноз ({count} ч)",
  analysisSaturnRegionUnmapped:
    "Для этой области пока нет проверенного кода Сатурна. Прогноз погоды остаётся доступен.",
  analysisSaturnNotSupported:
    "Сатурн недоступен для выбранной страны или отключён на сервере.",
  analysisWeatherNotEnabled: "Погодный источник отключён на сервере.",
  headerContext: "Исследование данных для пчеловода",
  syntheticMode: "Синтетический источник",
  setup: "01 / ПОДГОТОВКА",
  heading: "Поиск медоносных угодий",
  introduction: "Гео-аналитика для кочевого пчеловодства",
  syntheticTitle: "Только вымышленные данные.",
  syntheticDisclaimer:
    "Это демонстрация механизма, не прогноз, оповещение или подтверждение безопасности.",
  country: "Страна",
  language: "Язык",
  referenceHeading: "Местность",
  referenceHelp:
    "Выберите область и при необходимости район. Их границы берутся из собственного географического справочника.",
  referenceRegion: "Область / регион",
  referenceDistrict: "Район",
  referenceSelectRegion: "Выберите регион",
  referenceSelectDistrict: "Без выбора района",
  referenceDistrictLoading: "Загрузка районов…",
  referenceDistrictUnsupported:
    "Районы для этой области пока не загружены в географический справочник.",
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
  liveSourcesHeading: "Реальные источники данных",
  liveSourcesHelp:
    "Для Сатурн выбери регион из независимого справочника; для погоды достаточно точки на карте.",
  liveSourcesJump: "Перейти к реальным источникам",
  liveSourcesAvailability:
    "Показываются только источники, включённые на сервере. Отсутствие данных не означает отсутствие риска.",
  demoWorkflowHeading: "Необязательное демонстрационное исследование",
  demoWorkflowUnavailable:
    "Демонстрационный планировщик отключён. Для реальных источников сценарий, территория и сезон не требуются.",
  saturnTitle: "Сатурн: сообщения об обработках",
  saturnCode: "Сопоставление региона с Сатурн",
  saturnSelectRegion:
    "Сначала выбери регион России в левой панели, затем загрузи уведомления Сатурн.",
  saturnCodeHint:
    "Backend сопоставляет регион с проверенным кодом Сатурн. Если соответствие отсутствует, запрос не выполняется.",
  saturnRead: "Загрузить одну страницу",
  saturnNext: "Загрузить следующую",
  saturnLoading: "Чтение публичного портала…",
  saturnUnmapped:
    "Для региона нет проверенного соответствия в Сатурн. Запрос на портал не отправлен.",
  saturnError: "Ошибка чтения Сатурн: {reason}. Доступность данных неизвестна.",
  saturnCount:
    "Страница {page} · найдено {count} сообщений · не распознано {skipped}",
  saturnEmpty:
    "На этой странице нет распознанных сообщений. Это не доказывает отсутствия обработок.",
  saturnWarning:
    "Экспериментальные, непроверенные сообщения. Без автообновления, гарантии полноты или расчёта ветрового переноса.",
  saturnField: "Поле {record}; план {plan}",
  saturnDates: "Указанный период: {start} — {end}",
  saturnProduct:
    "Препарат {name}; культура {crop}; класс опасности для пчёл {hazard}",
  saturnCaptured: "Получено {time}; источник {source}",
  saturnMissing: "не указано",
  saturnGeometry: "Геометрия поля отсутствует или невалидна.",
  saturnMore:
    "Могут существовать другие страницы. Отображение не является полным реестром.",
  weatherTitle: "Прогноз погоды · Open-Meteo",
  weatherHelp:
    "Выбери точку на карте. По кнопке «Загрузить» её координаты будут переданы в Open-Meteo через backend.",
  weatherRead: "Загрузить прогноз на 24 часа",
  weatherLoading: "Получаем прогноз погоды…",
  weatherError: "Прогноз недоступен: {reason}. Нельзя делать вывод о погоде.",
  weatherWarning:
    "Модельный прогноз, не измеренный ветер и не оценка переноса пестицидов. Безопасность не установлена.",
  weatherGrid: "Сетка прогноза: {lat}, {lon} · Получено: {time}",
  weatherAttribution: "Данные погоды: Open-Meteo.com (CC BY 4.0)",
  weatherTime: "Время (UTC)",
  weatherWind: "Ветер км/ч",
  weatherDirection: "Направление °",
  weatherGusts: "Порывы км/ч",
  weatherRain: "Осадки мм",
  weatherMissing: "нет данных",
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
    "Справочник регионов недоступен. Если настроен PostgreSQL, проверьте подключение, миграции и данные.",
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
  mapHeading: "Карта выбранной местности",
  mapLabel: "Карта исследования",
  basemap: "Онлайн-подложка",
  basemapPrivacy:
    "При включении сторонний сервис получает координаты запрошенных картографических тайлов.",
  mapProposed: "Предлагаемая стоянка",
  mapSelected: "Выбрана",
  mapNote:
    "Нажмите на карту внутри выбранной местности, чтобы уточнить точку. Онлайн-подложка необязательна.",
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

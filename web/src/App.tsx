import { useCallback, useEffect, useRef, useState } from "react";
import {
  getInvestigation,
  listCountries,
  listRegions,
  startInvestigation,
} from "./api/client";
import type { ApiResult } from "./api/client";
import type {
  Country,
  CountryCode,
  Investigation,
  Position,
  Territory,
} from "./api/types";
import { EvidencePanel } from "./components/EvidencePanel";
import { MapPanel } from "./components/MapPanel";
import { Timeline } from "./components/Timeline";

const DEMO_TERRITORY = "demo:smolensk";
const DEMO_FIXTURE_TERRITORY = "ru:region:smolensk";
const DEMO_SCENARIO = "synthetic-ru-2026-v04-ecology-treatment";
const MAX_POLLS = 24;

interface Notice {
  kind: "error" | "info";
  message: string;
}

function failure<T>(result: Extract<ApiResult<T>, { kind: "error" }>): Notice {
  if (result.code === "ABORTED")
    return { kind: "info", message: "Запрос отменён" };
  if (result.status === 404)
    return {
      kind: "error",
      message:
        "Исследование не найдено. Результат в памяти сервера мог исчезнуть после перезапуска.",
    };
  if (result.status === 422)
    return {
      kind: "error",
      message:
        "API отклонил параметры исследования. Проверьте сезон и выбранный сценарий.",
    };
  if (result.status === 409)
    return {
      kind: "error",
      message: "Выбранная глубина каталога территорий не поддерживается.",
    };
  if (result.status === 503)
    return {
      kind: "error",
      message:
        "Хранилище или справочник временно недоступен. Отсутствие данных не означает безопасность.",
    };
  return { kind: "error", message: `${result.message} (${result.code})` };
}

async function pause(
  milliseconds: number,
  signal: AbortSignal,
): Promise<boolean> {
  if (signal.aborted) return false;
  return new Promise((resolve) => {
    const handle = setTimeout(() => finish(true), milliseconds);
    const onAbort = () => finish(false);
    function finish(completed: boolean) {
      clearTimeout(handle);
      signal.removeEventListener("abort", onAbort);
      resolve(completed);
    }
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

export default function App() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [country, setCountry] = useState<CountryCode>("RU");
  const [regions, setRegions] = useState<Territory[]>([]);
  const [referenceMessage, setReferenceMessage] = useState(
    "Получаем сведения о территориях…",
  );
  const [territory, setTerritory] = useState(DEMO_TERRITORY);
  const [seasonStart, setSeasonStart] = useState("2026-05-01");
  const [seasonEnd, setSeasonEnd] = useState("2026-08-15");
  const [point, setPoint] = useState<Position | null>(null);
  const [result, setResult] = useState<Investigation | null>(null);
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);
  const [showTiles, setShowTiles] = useState(false);
  const [reopenId, setReopenId] = useState("");
  const activeRequest = useRef<AbortController | null>(null);
  const sequence = useRef(0);

  const cancel = useCallback(() => {
    sequence.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void listCountries(controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "ok") setCountries(response.data);
      else
        setReferenceMessage(
          `Список стран недоступен: ${failure(response).message}`,
        );
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setRegions([]);
    setReferenceMessage("Проверяем справочник регионов…");
    void listRegions(country, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "ok") {
        setRegions(response.data);
        setReferenceMessage(
          response.data.length === 0
            ? "Справочник не содержит подтверждённых регионов. Это не сведения о полном покрытии."
            : "Показаны регионы из текущего API-справочника.",
        );
      } else {
        setReferenceMessage(
          response.status === 503
            ? "Границы и перечень регионов пока не загружены (HTTP 503). Демо доступно отдельно."
            : `Не удалось загрузить регионы: ${failure(response).message}`,
        );
      }
    });
    return () => controller.abort();
  }, [country]);

  useEffect(() => () => cancel(), [cancel]);

  const chooseCountry = (next: CountryCode) => {
    cancel();
    setCountry(next);
    setTerritory(next === "RU" ? DEMO_TERRITORY : "");
    setResult(null);
    setSelectedSite(null);
    setNotice(null);
    setBusy(false);
    setPoint(null);
  };

  const run = async (
    id: number,
    controller: AbortController,
    first: Investigation,
  ) => {
    let snapshot = first;
    setResult(snapshot);
    for (
      let attempt = 0;
      attempt < MAX_POLLS &&
      (snapshot.status === "QUEUED" || snapshot.status === "RUNNING");
      attempt++
    ) {
      if (!(await pause(700, controller.signal))) return;
      const updated = await getInvestigation(snapshot.id, controller.signal);
      if (controller.signal.aborted || sequence.current !== id) return;
      if (updated.kind === "error") {
        setNotice(failure(updated));
        setBusy(false);
        return;
      }
      snapshot = updated.data;
      setResult(snapshot);
    }
    if (controller.signal.aborted || sequence.current !== id) return;
    setBusy(false);
    setSelectedSite(snapshot.plan?.stops[0]?.site_id ?? null);
    if (snapshot.status === "QUEUED" || snapshot.status === "RUNNING") {
      setNotice({
        kind: "info",
        message:
          "Обработка ещё продолжается. Можно повторно открыть исследование по ID.",
      });
    } else if (snapshot.status === "FAILED") {
      setNotice({
        kind: "error",
        message:
          "Выполнение исследования завершилось ошибкой. Подробности доступны в диагностике ответа.",
      });
    } else if (!snapshot.plan) {
      setNotice({
        kind: "info",
        message:
          "Исследование завершено, но для плана недостаточно проверенных стоянок.",
      });
    } else {
      setNotice(null);
    }
  };

  const begin = async (mode: "submit" | "reopen") => {
    cancel();
    const id = sequence.current;
    const controller = new AbortController();
    activeRequest.current = controller;
    setBusy(true);
    setResult(null);
    setSelectedSite(null);
    setNotice(null);
    const response =
      mode === "submit"
        ? await startInvestigation(
            {
              country: "RU",
              territory_id: DEMO_FIXTURE_TERRITORY,
              scenario_id: DEMO_SCENARIO,
              season_start: seasonStart,
              season_end: seasonEnd,
              ...(point !== null ? { starting_point: point } : {}),
            },
            controller.signal,
          )
        : await getInvestigation(reopenId.trim(), controller.signal);
    if (controller.signal.aborted || sequence.current !== id) return;
    if (response.kind === "error") {
      setBusy(false);
      setNotice(failure(response));
      return;
    }
    await run(id, controller, response.data);
  };

  const canSubmit =
    country === "RU" &&
    territory === DEMO_TERRITORY &&
    seasonStart >= "2026-05-01" &&
    seasonEnd <= "2026-08-15" &&
    seasonStart <= seasonEnd &&
    !busy;
  const stops = result?.plan?.stops ?? [];

  return (
    <div className="app-shell">
      <header className="masthead">
        <div className="brand">
          <span className="brand-icon" aria-hidden="true">
            ✳
          </span>
          <span>
            Melli<span className="brand-accent">Atlas</span>
          </span>
        </div>
        <div className="header-context">
          <span className="status-dot" /> Моделирование размещения пасеки{" "}
          <span className="header-separator">/</span> Демонстрационный режим
        </div>
        <span className="header-version">MVP · W01</span>
      </header>
      <div className="workspace">
        <aside className="controls" aria-label="Параметры исследования">
          <div className="eyebrow">01 / ПОДГОТОВКА</div>
          <h1>Где разместить пасеку в этом сезоне?</h1>
          <p className="lead">
            Сопоставьте периоды медосбора с сообщениями об обработке полей и
            экологическими ограничениями.
          </p>
          <div className="demo-notice" role="note">
            <strong>Только вымышленные данные.</strong> Это демонстрация
            механизма, не прогноз, оповещение или подтверждение безопасности.
          </div>
          <div className="form-group">
            <label htmlFor="country">Страна</label>
            <select
              id="country"
              value={country}
              onChange={(event) =>
                chooseCountry(event.target.value === "BY" ? "BY" : "RU")
              }
            >
              {(countries.length > 0
                ? countries
                : [
                    {
                      code: "RU" as const,
                      name: "Россия (список API недоступен)",
                    },
                    {
                      code: "BY" as const,
                      name: "Беларусь (список API недоступен)",
                    },
                  ]
              ).map((item) => (
                <option key={item.code} value={item.code}>
                  {item.code === "RU" ? "Россия" : "Беларусь"}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="territory">Территория</label>
            <select
              id="territory"
              value={territory}
              onChange={(event) => {
                cancel();
                setTerritory(event.target.value);
                setResult(null);
                setNotice(null);
                setBusy(false);
              }}
            >
              {country === "RU" && (
                <option value={DEMO_TERRITORY}>
                  Демо · Смоленская область (фиктивная)
                </option>
              )}
              <option value="">Выберите подтверждённый регион</option>
              {regions.map((item) => (
                <option value={item.id} key={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <p className="field-help" role="status">
              {referenceMessage}
            </p>
          </div>
          <div className="form-group">
            <label>Период размещения</label>
            <div className="date-range">
              <input
                aria-label="Начало сезона"
                type="date"
                value={seasonStart}
                onChange={(event) => setSeasonStart(event.target.value)}
              />
              <span>—</span>
              <input
                aria-label="Конец сезона"
                type="date"
                value={seasonEnd}
                onChange={(event) => setSeasonEnd(event.target.value)}
              />
            </div>
            <p className="field-help">
              Демо поддерживает май — август 2026 года.
            </p>
          </div>
          <div className="form-group">
            <label>Исходная точка</label>
            <p className="field-help">
              Необязательно: нажмите на карту. Точка передаётся только в теле
              запроса и не сохраняется в браузере.
            </p>
            {point && (
              <div className="point-row">
                <span>
                  Точка выбрана ({point.latitude.toFixed(3)},{" "}
                  {point.longitude.toFixed(3)})
                </span>
                <button type="button" onClick={() => setPoint(null)}>
                  Очистить
                </button>
              </div>
            )}
          </div>
          <button
            type="button"
            className="primary-button"
            disabled={!canSubmit}
            onClick={() => void begin("submit")}
          >
            {busy ? "Анализ выполняется…" : "Исследовать размещение"}
            <span aria-hidden="true">↗</span>
          </button>
          {!canSubmit && !busy && (
            <p className="field-help">
              Фиктивное исследование пока доступно только для демонстрационной
              территории RU.
            </p>
          )}
          <div className="reopen">
            <label htmlFor="reopen-id">Открыть по ID</label>
            <div className="reopen-row">
              <input
                id="reopen-id"
                placeholder="UUID исследования"
                value={reopenId}
                onChange={(event) => setReopenId(event.target.value)}
              />
              <button
                type="button"
                disabled={busy || !/^[0-9a-fA-F-]{36}$/.test(reopenId.trim())}
                onClick={() => void begin("reopen")}
              >
                Открыть
              </button>
            </div>
            <p className="field-help">
              По умолчанию сервер хранит результаты в памяти до перезапуска.
            </p>
          </div>
        </aside>

        <main className="canvas-column">
          <section className="map-section" aria-label="Карта исследования">
            <div className="section-header">
              <div>
                <span className="eyebrow">02 / ПРОСТРАНСТВО</span>
                <h2>Карта стоянок</h2>
              </div>
              <label className="tile-switch">
                <input
                  type="checkbox"
                  checked={showTiles}
                  onChange={(event) => setShowTiles(event.target.checked)}
                />{" "}
                Онлайн-подложка{" "}
                <span
                  className="tile-info"
                  title="При включении сторонний сервис получает координаты запрошенных картографических тайлов."
                >
                  ⓘ
                </span>
              </label>
            </div>
            <MapPanel
              stops={stops}
              selectedId={selectedSite}
              startingPoint={point}
              showTiles={showTiles}
              onSelect={setSelectedSite}
              onPoint={setPoint}
            />
          </section>
          {notice && (
            <div className={`message message-${notice.kind}`} role="status">
              {notice.message}
            </div>
          )}
          {result && (
            <div className="result-banner" aria-live="polite">
              <strong>
                {result.status === "COMPLETED"
                  ? result.plan
                    ? "Предварительный план сформирован"
                    : "План не сформирован"
                  : `Состояние: ${result.status}`}
              </strong>
              <span>
                {result.plan
                  ? `${result.plan.stops.length} стоянки · ${result.plan.relocations} перемещения`
                  : (result.outcome ?? "Ожидаем анализ")}
              </span>
              <span className="result-id">ID: {result.id}</span>
            </div>
          )}
          <Timeline
            stops={stops}
            seasonStart={result?.request.season_start ?? seasonStart}
            seasonEnd={result?.request.season_end ?? seasonEnd}
            selectedId={selectedSite}
            onSelect={setSelectedSite}
          />
        </main>
        <EvidencePanel result={result} selectedId={selectedSite} />
      </div>
      <footer className="footer-note">
        MelliAtlas · Экспериментальная система поддержки решений. Не
        подтверждает отсутствие химического воздействия, законность размещения
        или безопасность стоянки.
      </footer>
    </div>
  );
}

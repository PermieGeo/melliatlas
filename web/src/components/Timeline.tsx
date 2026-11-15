import type { Stop } from "../api/types";

interface Props {
  stops: Stop[];
  seasonStart: string;
  seasonEnd: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
}
function percent(start: string, end: string, value: string): number {
  const origin = Date.parse(`${start}T00:00:00Z`);
  const limit = Date.parse(`${end}T00:00:00Z`);
  const point = Date.parse(`${value}T00:00:00Z`);
  if (![origin, limit, point].every(Number.isFinite) || limit <= origin)
    return 0;
  return Math.min(
    100,
    Math.max(0, ((point - origin) / (limit - origin)) * 100),
  );
}
export function Timeline({
  stops,
  seasonStart,
  seasonEnd,
  selectedId,
  onSelect,
}: Props) {
  return (
    <section className="timeline" aria-label="Сезонная шкала стоянок">
      <div className="timeline-heading">
        <h2>Сезон и перемещения</h2>
        <span className="muted">
          {seasonStart} — {seasonEnd}
        </span>
      </div>
      {stops.length === 0 ? (
        <p className="empty-small">
          Пока нет рассчитанных стоянок. После исследования здесь появятся их
          интервалы.
        </p>
      ) : (
        <div className="timeline-list">
          {stops.map((stop, index) => {
            const left = percent(seasonStart, seasonEnd, stop.start);
            const end = percent(seasonStart, seasonEnd, stop.end);
            return (
              <button
                type="button"
                className={`timeline-item ${selectedId === stop.site_id ? "is-selected" : ""}`}
                key={stop.site_id}
                onClick={() => onSelect(stop.site_id)}
                aria-pressed={selectedId === stop.site_id}
                aria-label={`Стоянка ${index + 1}, ${stop.start} — ${stop.end}`}
              >
                <span className="timeline-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="timeline-detail">
                  <span className="timeline-dates">
                    {stop.start} — {stop.end}
                  </span>
                  <span className="timeline-track">
                    <span
                      className="timeline-span"
                      style={{
                        left: `${left}%`,
                        width: `${Math.max(2, end - left)}%`,
                      }}
                    />
                  </span>
                </span>
                <span className="timeline-forage">{stop.forage_level}</span>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

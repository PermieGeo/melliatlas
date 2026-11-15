import type { Investigation } from "../api/types";

interface Props {
  result: Investigation | null;
  selectedId: string | null;
}
const proximityNames: Record<string, string> = {
  FIELD_INTERSECTION: "Совпадает с полем",
  NEAR_REPORTED_FIELD: "Рядом с указанным полем",
  OUTSIDE_SCREEN_RADIUS: "Вне радиуса предварительной проверки",
  UNKNOWN_GEOMETRY: "Геометрия неизвестна",
  OUTSIDE_STATED_PERIOD: "Вне указанного периода",
  UNKNOWN_PERIOD: "Период неизвестен",
};

export function EvidencePanel({ result, selectedId }: Props) {
  if (result === null) {
    return (
      <aside className="evidence-panel" aria-label="Сведения и ограничения">
        <h2>Почему предлагается стоянка</h2>
        <p className="muted">
          После исследования здесь появятся исходные сообщения, результаты
          проверки и причины выбора альтернатив.
        </p>
        <p className="warning-text">
          Отсутствие сведений об обработках никогда не означает отсутствие
          риска.
        </p>
      </aside>
    );
  }
  const assessment = result.replanning?.assessments.find(
    (entry) => entry.site_id === selectedId,
  );
  const screenings =
    result.treatment_review?.screenings.filter(
      (entry) => entry.site_id === selectedId,
    ) ?? [];
  return (
    <aside className="evidence-panel" aria-label="Сведения и ограничения">
      <div className="evidence-heading">
        <h2>Основания решения</h2>
        <span className="tag tag-synthetic">
          FIXTURE · синтетические данные
        </span>
      </div>
      <p className="muted">
        Исследование {result.id.slice(0, 8)} · {result.status}
      </p>
      {selectedId && (
        <p className="selected-caption">
          Стоянка: <strong>{selectedId}</strong>
        </p>
      )}

      <section className="evidence-section">
        <h3>Химические обработки</h3>
        {screenings.length === 0 ? (
          <p className="muted">
            Для выбранной стоянки нет отдельного уведомления в результатах. Это
            не подтверждение безопасности.
          </p>
        ) : (
          screenings.map((entry) => (
            <div
              className="evidence-record"
              key={`${entry.site_id}:${entry.source_record_id}`}
            >
              <strong>
                {proximityNames[entry.proximity] ?? entry.proximity}
              </strong>
              <p>
                Заявленный период:{" "}
                {entry.scheduled_start?.slice(0, 10) ?? "неизвестен"} —{" "}
                {entry.scheduled_end?.slice(0, 10) ?? "неизвестен"}
              </p>
              <p>
                Источник: <code>{entry.source_id}</code>, запись{" "}
                <code>{entry.source_record_id}</code>
              </p>
              {entry.products.map((product, index) => (
                <p key={index}>
                  Препарат: {product.name ?? "не указан"}; культура:{" "}
                  {product.crop ?? "не указана"}; заявленный класс опасности для
                  пчёл: {product.bee_hazard_class ?? "неизвестен"}
                </p>
              ))}
              {entry.approximate_distance_km !== null && (
                <p>
                  Приблизительное расстояние:{" "}
                  {entry.approximate_distance_km.toFixed(1)} км
                </p>
              )}
              {entry.warnings.map((warning) => (
                <p className="warning-text" key={warning}>
                  {warning}
                </p>
              ))}
            </div>
          ))
        )}
        {result.treatment_review &&
          result.treatment_review.avoided_site_ids.length > 0 && (
            <p className="warning-text">
              После проверки обработок рассмотрены альтернативы вместо:{" "}
              {result.treatment_review.avoided_site_ids.join(", ")}
            </p>
          )}
      </section>

      <section className="evidence-section">
        <h3>Экология</h3>
        {assessment ? (
          <div className="evidence-record">
            <span className="tag">{assessment.status}</span>
            {assessment.reasons.map((reason) => (
              <p key={reason}>{reason}</p>
            ))}
            {assessment.unknowns.map((unknown) => (
              <p className="warning-text" key={unknown}>
                {unknown}
              </p>
            ))}
            <p className="muted">
              Правила: {assessment.rule_ids.join(", ") || "не определены"}
            </p>
            <p className="muted">
              Доказательства:{" "}
              {assessment.evidence_ids.join(", ") || "не указаны"}
            </p>
          </div>
        ) : (
          <p className="muted">
            Для этой стоянки нет отдельной экологической оценки.
          </p>
        )}
      </section>

      <section className="evidence-section">
        <h3>История решений</h3>
        <ol className="decision-list">
          {(result.replanning?.decisions ?? []).map((decision, index) => (
            <li key={`${decision.kind}:${index}`}>
              <strong>{decision.kind}</strong> · {decision.note}
              {decision.evidence_ids.length > 0 && (
                <span className="muted">
                  {" "}
                  · {decision.evidence_ids.join(", ")}
                </span>
              )}
            </li>
          ))}
        </ol>
      </section>

      <section className="evidence-section">
        <h3>Источники и ограничения</h3>
        <ul className="evidence-list">
          {result.evidence.map((entry) => (
            <li key={entry.id}>
              <code>{entry.id}</code> · {entry.source_id} · {entry.uncertainty}
            </li>
          ))}
          {result.limitations.map((item) => (
            <li key={item} className="warning-text">
              {item}
            </li>
          ))}
        </ul>
      </section>
    </aside>
  );
}

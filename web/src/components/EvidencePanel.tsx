import type { EcologyStatus, Investigation, Proximity } from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** Source-attributed evidence view; unknown or missing findings never imply clearance. */
interface Props {
  locale: Locale;
  result: Investigation | null;
  selectedId: string | null;
}

const ecologyKeys: Record<EcologyStatus, TranslationKey> = {
  EXCLUDED: "ecologyExcluded",
  CAUTION: "ecologyCaution",
  UNKNOWN: "ecologyUnknown",
  ELIGIBLE: "ecologyEligible",
};

const proximityKeys: Record<Proximity, TranslationKey> = {
  FIELD_INTERSECTION: "proximityIntersection",
  NEAR_REPORTED_FIELD: "proximityNear",
  OUTSIDE_SCREEN_RADIUS: "proximityOutside",
  UNKNOWN_GEOMETRY: "proximityUnknownGeometry",
  OUTSIDE_STATED_PERIOD: "proximityOutsidePeriod",
  UNKNOWN_PERIOD: "proximityUnknownPeriod",
};

/** Presents server-authored observations verbatim while translating all UI chrome. */
export function EvidencePanel({ result, selectedId, locale }: Props) {
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);
  if (result === null) {
    return (
      <aside className="evidence-panel" aria-label={tr("evidenceLabel")}>
        <h2>{tr("why")}</h2>
        <p className="muted">{tr("evidenceEmpty")}</p>
        <p className="warning-text">{tr("noEvidenceIsNotSafe")}</p>
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
    <aside className="evidence-panel" aria-label={tr("evidenceLabel")}>
      <div className="evidence-heading">
        <h2>{tr("evidenceHeading")}</h2>
        {result.synthetic && (
          <span className="tag tag-synthetic">{tr("evidenceSynthetic")}</span>
        )}
      </div>
      <p className="muted">
        {tr("investigation", {
          id: result.id.slice(0, 8),
          status: result.status,
        })}
      </p>
      {selectedId && (
        <p className="selected-caption">
          {tr("selectedSite")} <strong>{selectedId}</strong>
        </p>
      )}
      <section className="evidence-section">
        <h3>{tr("treatments")}</h3>
        {screenings.length === 0 ? (
          <p className="muted">{tr("noTreatment")}</p>
        ) : (
          screenings.map((entry) => (
            <div
              className="evidence-record"
              key={`${entry.site_id}:${entry.source_id}:${entry.source_record_id}`}
            >
              <strong>{tr(proximityKeys[entry.proximity])}</strong>
              <p>
                {tr("proposedWindow", {
                  start:
                    entry.scheduled_start?.slice(0, 10) ?? tr("unknownValue"),
                  end: entry.scheduled_end?.slice(0, 10) ?? tr("unknownValue"),
                })}
              </p>
              <p>
                {tr("source", {
                  source: entry.source_id,
                  record: entry.source_record_id,
                })}
              </p>
              {entry.products.map((product, index) => (
                <p key={index}>
                  {tr("product", {
                    name: product.name ?? tr("missingValue"),
                    crop: product.crop ?? tr("missingValue"),
                    hazard: product.bee_hazard_class ?? tr("unknownValue"),
                  })}
                </p>
              ))}
              {entry.approximate_distance_km !== null && (
                <p>
                  {tr("approximateDistance", {
                    distance: entry.approximate_distance_km.toFixed(1),
                  })}
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
              {tr("avoidedSites", {
                sites: result.treatment_review.avoided_site_ids.join(", "),
              })}
            </p>
          )}
      </section>
      <section className="evidence-section">
        <h3>{tr("ecology")}</h3>
        {assessment ? (
          <div className="evidence-record">
            <span className="tag">{tr(ecologyKeys[assessment.status])}</span>
            {assessment.reasons.map((reason) => (
              <p key={reason}>{reason}</p>
            ))}
            {assessment.unknowns.map((unknown) => (
              <p className="warning-text" key={unknown}>
                {unknown}
              </p>
            ))}
            <p className="muted">
              {tr("rules", {
                value: assessment.rule_ids.join(", ") || tr("noneDefined"),
              })}
            </p>
            <p className="muted">
              {tr("evidenceIds", {
                value: assessment.evidence_ids.join(", ") || tr("noneReported"),
              })}
            </p>
          </div>
        ) : (
          <p className="muted">{tr("noEcology")}</p>
        )}
      </section>
      <section className="evidence-section">
        <h3>{tr("decisions")}</h3>
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
        <h3>{tr("sourcesAndLimits")}</h3>
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

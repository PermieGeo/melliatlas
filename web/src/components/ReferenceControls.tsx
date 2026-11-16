import type { Territory } from "../api/types";
import type { TerritoryNavigation } from "../hooks/useTerritoryReference";
import type { Locale, TranslationKey } from "../i18n";
import { t } from "../i18n";

interface Props {
  locale: Locale;
  regions: Territory[];
  navigation: TerritoryNavigation;
  catalogMessage: TranslationKey;
}

/** Navigate only API-backed administrative references, separate from synthetic studies. */
export function ReferenceControls({
  locale,
  regions,
  navigation,
  catalogMessage,
}: Props) {
  const tr = (key: Parameters<typeof t>[1]) => t(locale, key);
  return (
    <section
      className="reference-navigation"
      aria-label={tr("referenceHeading")}
    >
      <h3>{tr("referenceHeading")}</h3>
      <p className="field-help">{tr("referenceHelp")}</p>
      {catalogMessage !== "availableRegions" && (
        <p className="field-help" role="status">
          {tr(catalogMessage)}
        </p>
      )}
      <div className="form-group">
        <label htmlFor="reference-region">{tr("referenceRegion")}</label>
        <select
          id="reference-region"
          value={navigation.regionId}
          disabled={regions.length === 0}
          onChange={(event) => navigation.selectRegion(event.target.value)}
        >
          <option value="">{tr("referenceSelectRegion")}</option>
          {regions.map((region) => (
            <option key={region.id} value={region.id}>
              {region.name}
            </option>
          ))}
        </select>
      </div>
      {navigation.regionId && (
        <div className="form-group">
          <label htmlFor="reference-district">{tr("referenceDistrict")}</label>
          <select
            id="reference-district"
            value={navigation.districtId}
            disabled={navigation.districts.length === 0}
            onChange={(event) => navigation.selectDistrict(event.target.value)}
          >
            <option value="">{tr("referenceSelectDistrict")}</option>
            {navigation.districts.map((district) => (
              <option key={district.id} value={district.id}>
                {district.name}
              </option>
            ))}
          </select>
          {navigation.districtMessage !== "referenceDistrictAvailable" && (
            <p className="field-help" role="status">
              {tr(navigation.districtMessage)}
            </p>
          )}
        </div>
      )}
      {navigation.geometryMessage !== "referenceGeometryAvailable" && (
        <p className="field-help" role="status">
          {tr(navigation.geometryMessage)}
        </p>
      )}
      {navigation.geometry && (
        <p className="reference-provenance">
          {tr("referenceVersion")}: {navigation.geometry.reference_id} ·
          EPSG:4326
        </p>
      )}
    </section>
  );
}

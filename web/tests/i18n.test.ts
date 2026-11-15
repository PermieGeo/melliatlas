import { expect, it } from "vitest";
import { countryName, t } from "../src/i18n";

it("localizes UI labels and future country codes without embedding a country-name switch", () => {
  expect(t("ru", "country")).toBe("Страна");
  expect(t("en", "country")).toBe("Country");
  expect(
    t("en", "seasonRange", { start: "2030-01-01", end: "2030-12-31" }),
  ).toContain("2030-12-31");
  expect(countryName("en", "PL", "Poland")).toBe("Poland");
  expect(countryName("ru", "PL", "Poland")).toBe("Польша");
});

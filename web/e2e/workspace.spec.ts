import { expect, test } from "@playwright/test";
import fixture from "../tests/fixtures/combined.json";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/territories/countries")) {
      await route.fulfill({
        json: [
          { code: "RU", name: "Russia" },
          { code: "BY", name: "Belarus" },
        ],
      });
    } else if (url.pathname.endsWith("/territories/regions")) {
      await route.fulfill({
        status: 503,
        json: {
          error: {
            code: "TERRITORY_REFERENCE_UNAVAILABLE",
            message: "No catalog",
          },
        },
      });
    } else if (url.pathname === "/api/v1/investigations/scenarios") {
      await route.fulfill({
        json:
          url.searchParams.get("country") === "RU"
            ? [
                {
                  id: "synthetic-ru-2026-v04-ecology-treatment",
                  name: "Ecology and reported treatments (fictional)",
                  country: "RU",
                  territory_id: "ru:region:smolensk",
                  territory_name: "Smolensk region (fictional)",
                  source_mode: "SYNTHETIC",
                  season_start: "2026-05-01",
                  season_end: "2026-08-15",
                  is_default: true,
                },
              ]
            : [],
      });
    } else if (
      url.pathname === "/api/v1/investigations" &&
      route.request().method() === "POST"
    ) {
      await route.fulfill({
        status: 202,
        json: {
          ...fixture,
          status: "QUEUED",
          outcome: null,
          plan: null,
          replanning: null,
          treatment_review: null,
          evidence: [],
        },
      });
    } else if (url.pathname.startsWith("/api/v1/investigations/")) {
      await route.fulfill({ json: fixture });
    } else {
      await route.fulfill({ status: 404 });
    }
  });
});

test("shows a fictional map/timeline investigation without external map tiles", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("tile.openstreetmap.org"))
      external.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByText(/Только вымышленные данные/)).toBeVisible();
  await expect(
    page.getByText(/Границы и перечень регионов пока не загружены/),
  ).toBeVisible();
  await page.getByRole("button", { name: /Исследовать размещение/ }).click();
  await expect(
    page.getByText("Предварительный план сформирован"),
  ).toBeVisible();
  await page.getByRole("button", { name: /Стоянка 2,/ }).click();
  await expect(page.getByText(/Стоянка: fixture-site-beta/)).toBeVisible();
  expect(external).toEqual([]);
  expect(new URL(page.url()).search).toBe("");
});

test("works as a readable narrow-screen workflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Где разместить пасеку/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Исследовать размещение/ }),
  ).toBeVisible();
  await expect(page.getByLabel("Сезонная шкала стоянок")).toBeVisible();
});

import { expect, test } from "@playwright/test";
import fixture from "../tests/fixtures/combined.json";

test.beforeEach(async ({ page }) => {
  // Do not contact third-party tile servers during local browser tests.
  await page.route(/https:\/\/[a-c]\.tile\.openstreetmap\.org\//, (route) =>
    route.abort(),
  );
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

test("keeps the fictional map/timeline readable when online tiles fail", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("tile.openstreetmap.org"))
      external.push(request.url());
  });
  await page.goto("/");
  await page.getByText("Демо-сценарии").click();
  await expect(page.getByText(/Только вымышленные данные/)).toBeVisible();
  await expect(page.getByText(/Справочник регионов недоступен/)).toBeVisible();
  await page.getByRole("button", { name: /Исследовать размещение/ }).click();
  await expect(
    page.getByText("Предварительный план сформирован"),
  ).toBeVisible();
  await page.getByRole("button", { name: /Стоянка 2,/ }).click();
  await expect(page.getByText(/Стоянка: fixture-site-beta/)).toBeVisible();
  expect(external.length).toBeGreaterThan(0);
  await expect(
    page.getByRole("checkbox", { name: "Онлайн-подложка" }),
  ).toHaveCount(0);
  expect(new URL(page.url()).search).toBe("");
});

test("works as a readable narrow-screen workflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Поиск медоносных угодий/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Проанализировать выбранную местность" }),
  ).toBeVisible();
  await expect(page.getByLabel("Сезонная шкала стоянок")).toHaveCount(0);
});

test("fits imported region and district boundaries and restores the last viewport", async ({
  page,
}) => {
  const region = {
    id: "ru:region:smolensk",
    country: "RU",
    kind: "region",
    name: "Смоленская область",
    parent_id: null,
    reference_id: "reviewed-boundaries-v1",
    valid_on: "2026-01-01",
    geometry_status: "available",
  };
  const district = {
    ...region,
    id: "ru:district:smolensk-pilot",
    kind: "district",
    name: "Проверенный район",
    parent_id: region.id,
  };
  await page.route("**/api/v1/territories/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/countries")) {
      await route.fulfill({ json: [{ code: "RU", name: "Russia" }] });
    } else if (url.pathname.endsWith("/regions")) {
      await route.fulfill({ json: [region] });
    } else if (url.pathname.endsWith("/districts")) {
      await route.fulfill({ json: [district] });
    } else if (url.pathname.includes("/geometry/")) {
      const selectedDistrict = decodeURIComponent(url.pathname).endsWith(
        district.id,
      );
      const coords = selectedDistrict
        ? [
            [32, 54],
            [32.3, 54],
            [32.3, 54.3],
            [32, 54.3],
            [32, 54],
          ]
        : [
            [30, 53],
            [35, 53],
            [35, 57],
            [30, 57],
            [30, 53],
          ];
      await route.fulfill({
        json: {
          territory_id: selectedDistrict ? district.id : region.id,
          reference_id: region.reference_id,
          coordinate_system: "EPSG:4326",
          geometry: { type: "Polygon", coordinates: [coords] },
        },
      });
    } else {
      await route.fulfill({ status: 404 });
    }
  });
  await page.goto("/");
  await page.getByLabel("Область / регион").selectOption(region.id);
  await expect(page.getByLabel("Район")).toBeEnabled();
  await expect
    .poll(() =>
      page.evaluate(() =>
        Number(
          JSON.parse(
            localStorage.getItem("melliatlas.map.viewport.v1") ?? "null",
          ).zoom,
        ),
      ),
    )
    .toBeGreaterThan(4);
  const regionZoom = await page.evaluate(() =>
    Number(
      JSON.parse(localStorage.getItem("melliatlas.map.viewport.v1") ?? "null")
        .zoom,
    ),
  );
  await page.getByLabel("Район").selectOption(district.id);
  await expect
    .poll(() =>
      page.evaluate(() =>
        Number(
          JSON.parse(
            localStorage.getItem("melliatlas.map.viewport.v1") ?? "null",
          ).zoom,
        ),
      ),
    )
    .toBeGreaterThan(regionZoom);
  const savedZoom = await page.evaluate(() =>
    Number(
      JSON.parse(localStorage.getItem("melliatlas.map.viewport.v1") ?? "null")
        .zoom,
    ),
  );
  await page.reload();
  await expect
    .poll(() => page.locator(".leaflet-tile[src]").first().getAttribute("src"))
    .toContain(`/${savedZoom}/`);
  await expect(
    page.getByRole("checkbox", { name: "Онлайн-подложка" }),
  ).toHaveCount(0);
});

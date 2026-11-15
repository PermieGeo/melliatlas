# Agricultural treatment notice sources — recovery and access review

**Reviewed:** 2026-11-15. **Status:** Historical technical evidence and candidates only; **no live automated ingestion or public redistribution is approved**. This is not a verified feed-coverage register, compliance assessment, or permission record.

## Russia: FGIS Saturn / Beekeeper Portal

The publicly described [Beekeeper Portal](https://bee.fgis-saturn.ru/) is a human-readable publication channel for planned pesticide and agrochemical treatments. Public viewing without registration has been reported by [Rosselkhoznadzor](https://www.garant.ru/products/ipo/prime/doc/411652129/) and the [March 2026 notification](https://www.garant.ru/products/ipo/prime/doc/413900975/). None of these observations confirms an approved machine API, rate limit, bulk-reuse license, or successful authorized live call from MelliAtlas.

The historical 2026-11-13 TypeScript MelliAtlas snapshot is a **reference implementation**, not the current backend or evidence of current endpoint availability. It distinguishes:

| Historical shape | What it may establish when independently verified | What it does **not** establish |
| --- | --- | --- |
| `/backend/beemaster/planapplybees` | Field-specific planned-treatment claims, dated revisions, product names/bee hazard classes, sometimes a directly attached polygon | A completed application, genuine safety condition, complete district coverage, license to republish |
| `/backend/beemaster/query` | Paginated map-index IDs and point centers, under observed viewport/UpdateMap filters | A treatment event, application-date filter, or field polygon |
| `/backend/beemaster/district/{regionCode}` | Provider district IDs/names and navigation-center hints | Official administrative geometry, canonical territory ID or verified coverage |
| `/backend/beemaster/geojson-polygons` | A possible geometry response when captured and reviewed | A verified join to a plan or application without independent identity evidence |
| `/backend/beemaster/acr/{fieldId}` | A possible field-detail response when captured and reviewed | Independent verification of an index/geometry association |

The historical host `bee-saturn.ru`, request headers, request bodies, region code `55`, and server-specific query filters are **not pinned as current production contracts**. The later `bee.fgis-saturn.ru` public hostname must not be assumed to serve those same paths. The historical code includes strict pagination validation, immutable raw-page versions, source-wide throttling, operator-only bounded requests, a restricted HTTP fetcher with redirect/DNS/TLS rules, per-field geometry validation, and human review statuses. These are useful design precedents; copying the old transport unchanged would bypass present-day contract and access verification.

### Next verification steps before an opt-in live source

1. Obtain a current, independently documented source contract or an explicitly authorized and sanitized capture, including host, route, method, credentials, pagination, date semantics, revisions, region/district mapping, geometry identity and availability.
2. Review permitted machine access, reuse and public display rights; retain the dated source, reviewer and revocation state. Public visibility alone is not approval.
3. Implement only the verified and explicitly enabled requests through a fixed-destination, resource-bounded, audited operator transport. The ordinary beekeeper map must never start downloads on viewport changes.
4. Persist immutable original source evidence with parser version, field identity, retrieval/publication/application timestamps, deduplication and coverage/freshness metadata. Do not publish source claims as verified events or assume an empty page proves complete coverage.
5. Compare notice geometry and time with apiary presence. Evaluate wind direction and forecast validity only after selecting a defensible weather source and uncertainty model; a fixed radial watch distance is not a safe boundary.

## Public websites and announcements: additional candidates

Historical candidate publications from the earlier source register (not current warnings):

- **Smolensk Municipal Okrug:** [Kozinsky greenhouse notice](https://smol-ray.smolensk.ru/news/ooo-kozinskij-teplichnyj-kombinat-informiruet-o-provedenii-rabot-po-himicheskoj-obrabotke-selskohozyajstvennyh-kultur-v-smolenskom-municipalnom-okruge/) (2025-05-08, historical HTML; settlement precision only).
- **Glinkovsky Okrug:** [Glinkovsky Vestnik, issue 31](https://glinka.admin-smolensk.ru/files/313/glinkovskij-vestnik-31-01.pdf) (2025-08-01, historical PDF notice; no verified polygon).
- **Smolensk Oblast agriculture ministry:** [announcement with external table](https://selhoz.admin-smolensk.ru/news/bryanskaya-myasnaya-kompaniya-informiruet-pchelovodov-ob-obrabotkah-polej/) (2026-05-05, HTML with third-party attachment requiring separate review).

No candidate above is approved for crawling, storing source attachments or public redistribution. Legal and technical checks must be recorded per publisher and attachment host, with source-claimed location precision retained. Belarus needs its **own** approved publication, news, chat or forum source inventory; Saturn is not a Belarusian source. Private groups and chats need additional consent and privacy review.

## Current Python increment

`backend/src/melliatlas/sources/saturn.py` implements only bounded **offline fixture** normalization of the historical treatment-page shape. `backend/src/melliatlas/analyzers/api.py` screens candidate site/time windows against that normalized evidence with conservative uncertainty. There is **no live connector, scheduled poller, PostGIS treatment store, weather drift model, or public hazard warning** in this increment. The earlier snapshot's actual provider response samples and technical test cases remain historical reference material; do not copy any real/private captured payload into project fixtures.

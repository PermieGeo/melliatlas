# First-order ISO subdivision seed attribution

`iso3166-2-regions.json` is a normalized subset of subdivision codes and
Romanized names from **iso-codes 4.18.0**, available from
https://salsa.debian.org/iso-codes-team/iso-codes.

Original iso-codes project copyright holders include Alastair McKinstry,
Christian Perrier, and Dr. Tobias Quathamer. The Debian package states
**LGPL-2.1-or-later** for its dataset. A copy of LGPL-2.1 is included as
`LGPL-2.1.txt`. The Russian display-name column is independently localized
for MelliAtlas and is not represented as an official name translation.

Only 83 RU and 7 BY ISO subdivision records are included. This is not a
statement about current sovereignty, legal administrative boundaries, district
coverage, or the ability to display a verified region polygon. The ISO code
is a canonical MelliAtlas region-key input, not a Saturn subject identifier.

The independently captured Saturn operator reference dated 2026-11-11
provides an example source mapping for Smolensk (`subject_id=55`,
`oktmoCode=66000000`). That mapping belongs only in the separate
`melliatlas_source_saturn` table. The other source identifiers are intentionally
not inferred from this data.

-- Add an optional reviewed Russian display name without changing source identity.
-- Only the source names shown in the Smolensk pilot are backfilled.
ALTER TABLE melliatlas_admin_geometry ADD COLUMN IF NOT EXISTS name_ru TEXT;

ALTER TABLE melliatlas_admin_geometry
    DROP CONSTRAINT IF EXISTS admin_geometry_name_ru_nonempty;
ALTER TABLE melliatlas_admin_geometry
    ADD CONSTRAINT admin_geometry_name_ru_nonempty CHECK (name_ru IS NULL OR length(btrim(name_ru)) > 0);

UPDATE melliatlas_admin_geometry AS area
SET name_ru = localized.name_ru
FROM (VALUES
    ('demidovsky district', 'Демидовский район'),
    ('dorogobuzhsky district', 'Дорогобужский район'),
    ('dukhovshchinsky district', 'Духовщинский район'),
    ('gagarinsky district', 'Гагаринский район'),
    ('glinkovsky district', 'Глинковский район'),
    ('kardymovsky district', 'Кардымовский район'),
    ('khislavichsky district', 'Хиславичский район'),
    ('kholm-zhirkovsky district', 'Холм-Жирковский район'),
    ('krasninsky district', 'Краснинский район'),
    ('monastyrshchinsky district', 'Монастырщинский район'),
    ('novoduginsky district', 'Новодугинский район'),
    ('pochinkovsky district', 'Починковский район'),
    ('roslavlsky district', 'Рославльский район'),
    ('rudnyansky district', 'Руднянский район'),
    ('safonovsky district', 'Сафоновский район'),
    ('shumyachsky district', 'Шумячский район'),
    ('smolensk', 'Смоленск'),
    ('smolensky district', 'Смоленский район'),
    ('sychyovsky district', 'Сычёвский район'),
    ('tyomkinsky district', 'Тёмкинский район'),
    ('ugransky district', 'Угранский район'),
    ('velizhsky district', 'Велижский район'),
    ('vyazemsky district', 'Вяземский район'),
    ('yartsevsky district', 'Ярцевский район'),
    ('yelninsky district', 'Ельнинский район'),
    ('yershichsky district', 'Ершичский район'),
    ('городской округ десногорск', 'городской округ Десногорск'),
    ('городской округ лесногорск', 'городской округ Лесногорск'),
    ('demidovskiy district', 'Демидовский район'),
    ('dorogobuzhskiy district', 'Дорогобужский район'),
    ('dukhovshhinskiy district', 'Духовщинский район'),
    ('kholm-zhirkovskiy district', 'Холм-Жирковский район'),
    ('roslavlskiy district', 'Рославльский район'),
    ('sychevsky district', 'Сычёвский район'),
    ('shumiatchsky district', 'Шумячский район')
) AS localized(source_name, name_ru)
WHERE area.region_id = 'ru:region:smo' AND area.kind = 'district'
  AND lower(btrim(area.name)) = localized.source_name
  AND area.name_ru IS NULL;

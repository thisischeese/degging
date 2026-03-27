\echo [load_cafe_menu_search_vectors] starting

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_search_text text;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_vector vector(64);

DO $$
DECLARE
    menu_vector_type text;
BEGIN
    SELECT format_type(attribute.atttypid, attribute.atttypmod)
    INTO menu_vector_type
    FROM pg_attribute AS attribute
    WHERE attribute.attrelid = to_regclass('cafe_menus')
      AND attribute.attname = 'menu_vector'
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped;

    IF menu_vector_type IS DISTINCT FROM 'vector(64)' THEN
        RAISE EXCEPTION
            'cafe_menus.menu_vector must be vector(64), found %',
            COALESCE(menu_vector_type, 'NULL');
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_raw_lines;
CREATE TEMP TABLE temp_menu_vector_raw_lines (
    line_no bigserial PRIMARY KEY,
    line_text text NOT NULL
);

\echo [load_cafe_menu_search_vectors] copying /tmp/menu_search_vectors.json
\copy temp_menu_vector_raw_lines (line_text) FROM '/tmp/menu_search_vectors.json' WITH (FORMAT text)

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_payload;
CREATE TEMP TABLE temp_menu_vector_payload AS
SELECT string_agg(line_text, E'\n' ORDER BY line_no)::jsonb AS payload
FROM temp_menu_vector_raw_lines;

DO $$
DECLARE
    payload_type text;
BEGIN
    SELECT jsonb_typeof(payload)
    INTO payload_type
    FROM temp_menu_vector_payload;

    IF payload_type IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION
            'Expected top-level JSON array in /tmp/menu_search_vectors.json, got %',
            COALESCE(payload_type, 'NULL');
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_source;
CREATE TEMP TABLE temp_menu_vector_source AS
SELECT
    items.ordinality::integer AS source_row_no,
    items.item AS source_item,
    items.item ->> 'menu_id' AS menu_id_text,
    items.item ->> 'menu_search_text' AS menu_search_text,
    items.item -> 'menu_vector' AS menu_vector_json
FROM temp_menu_vector_payload AS payload
CROSS JOIN LATERAL jsonb_array_elements(payload.payload) WITH ORDINALITY AS items(item, ordinality);

DO $$
DECLARE
    offending_rows text;
BEGIN
    SELECT string_agg(source_row_no::text, ', ' ORDER BY source_row_no)
    INTO offending_rows
    FROM temp_menu_vector_source
    WHERE jsonb_typeof(source_item) IS DISTINCT FROM 'object';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each JSON array element must be an object. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(%s)', source_row_no, COALESCE(menu_id_text, 'NULL')),
               ', '
               ORDER BY source_row_no
           )
    INTO offending_rows
    FROM temp_menu_vector_source
    WHERE menu_id_text IS NULL
       OR menu_id_text !~ '^\d+$';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Invalid menu_id values in source JSON. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(source_row_no::text, ', ' ORDER BY source_row_no)
    INTO offending_rows
    FROM temp_menu_vector_source
    WHERE menu_search_text IS NULL
       OR btrim(menu_search_text) = '';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each menu_search_text must be a non-empty string. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(source_row_no::text, ', ' ORDER BY source_row_no)
    INTO offending_rows
    FROM temp_menu_vector_source
    WHERE menu_vector_json IS NULL
       OR jsonb_typeof(menu_vector_json) IS DISTINCT FROM 'array';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each menu_vector must be a JSON array. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(len=%s)', source_row_no, jsonb_array_length(menu_vector_json)),
               ', '
               ORDER BY source_row_no
           )
    INTO offending_rows
    FROM temp_menu_vector_source
    WHERE jsonb_typeof(menu_vector_json) = 'array'
      AND jsonb_array_length(menu_vector_json) <> 64;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each menu_vector must contain exactly 64 elements. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(elem=%s,type=%s)', source_row_no, ordinality, value_type),
               ', '
               ORDER BY source_row_no, ordinality
           )
    INTO offending_rows
    FROM (
        SELECT
            source.source_row_no,
            element.ordinality,
            jsonb_typeof(element.value) AS value_type
        FROM temp_menu_vector_source AS source
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE
                WHEN jsonb_typeof(source.menu_vector_json) = 'array'
                    THEN source.menu_vector_json
                ELSE '[]'::jsonb
            END
        ) WITH ORDINALITY AS element(value, ordinality)
        WHERE jsonb_typeof(element.value) IS DISTINCT FROM 'number'
        ORDER BY source.source_row_no, element.ordinality
        LIMIT 20
    ) AS invalid_elements;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each menu_vector element must be numeric. Sample offending elements: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(count=%s)', menu_id_text, duplicate_count),
               ', '
               ORDER BY menu_id_text
           )
    INTO offending_rows
    FROM (
        SELECT menu_id_text, COUNT(*) AS duplicate_count
        FROM temp_menu_vector_source
        GROUP BY menu_id_text
        HAVING COUNT(*) > 1
    ) AS duplicates;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Duplicate menu_id values found in source JSON: %',
            offending_rows;
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_stage;
CREATE TEMP TABLE temp_menu_vector_stage AS
SELECT
    menu_id_text::integer AS menu_id,
    btrim(regexp_replace(menu_search_text, '\s+', ' ', 'g')) AS menu_search_text,
    (
        '['
        || (
            SELECT string_agg(element.value, ',' ORDER BY element.ordinality)
            FROM jsonb_array_elements_text(menu_vector_json) WITH ORDINALITY AS element(value, ordinality)
        )
        || ']'
    )::vector(64) AS menu_vector
FROM temp_menu_vector_source;

ALTER TABLE temp_menu_vector_stage
    ADD PRIMARY KEY (menu_id);

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_matched;
CREATE TEMP TABLE temp_menu_vector_matched AS
SELECT stage.menu_id
FROM temp_menu_vector_stage AS stage
JOIN cafe_menus
    ON cafe_menus.menu_id = stage.menu_id;

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_missing;
CREATE TEMP TABLE temp_menu_vector_missing AS
SELECT stage.menu_id
FROM temp_menu_vector_stage AS stage
LEFT JOIN cafe_menus
    ON cafe_menus.menu_id = stage.menu_id
WHERE cafe_menus.menu_id IS NULL;

DROP TABLE IF EXISTS pg_temp.temp_menu_vector_updated;
CREATE TEMP TABLE temp_menu_vector_updated AS
WITH updated_rows AS (
    UPDATE cafe_menus
    SET
        menu_search_text = stage.menu_search_text,
        menu_vector = stage.menu_vector
    FROM temp_menu_vector_stage AS stage
    WHERE cafe_menus.menu_id = stage.menu_id
      AND (
          cafe_menus.menu_search_text IS DISTINCT FROM stage.menu_search_text
          OR cafe_menus.menu_vector IS DISTINCT FROM stage.menu_vector
      )
    RETURNING cafe_menus.menu_id
)
SELECT menu_id
FROM updated_rows;

\echo [load_cafe_menu_search_vectors] returning summary counts
SELECT
    (SELECT COUNT(*) FROM temp_menu_vector_stage) AS source_count,
    (SELECT COUNT(*) FROM temp_menu_vector_matched) AS matched_count,
    (SELECT COUNT(*) FROM temp_menu_vector_updated) AS updated_count,
    (SELECT COUNT(*) FROM temp_menu_vector_missing) AS missing_count;

\echo [load_cafe_menu_search_vectors] returning missing menu_ids
SELECT menu_id
FROM temp_menu_vector_missing
ORDER BY menu_id;

COMMIT;

\echo [load_cafe_menu_search_vectors] completed

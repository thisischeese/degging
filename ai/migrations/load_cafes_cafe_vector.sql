-- Load cafe_vectors.json into cafes.cafe_vector (vector(64)).
--
-- Run this script with psql because it uses \copy:
--   docker cp ./cafe_vectors.json <pg_container>:/tmp/cafe_vectors.json
--   docker cp ./migrations/load_cafes_cafe_vector.sql <pg_container>:/tmp/load_cafes_cafe_vector.sql
--   docker exec -i <pg_container> env PGPASSWORD=degging501 \
--     psql -U postgres -d degging -v ON_ERROR_STOP=1 -f /tmp/load_cafes_cafe_vector.sql
--
-- Suggested checks before and after execution:
--   SELECT COUNT(*) AS non_null_vectors_before
--   FROM cafes
--   WHERE cafe_vector IS NOT NULL;
--
--   SELECT COUNT(*) AS non_null_vectors_after
--   FROM cafes
--   WHERE cafe_vector IS NOT NULL
--     AND vector_dims(cafe_vector) = 64;

\echo [load_cafes_cafe_vector] starting

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE cafes
    ADD COLUMN IF NOT EXISTS cafe_vector vector(64);

DO $$
DECLARE
    cafe_vector_type text;
BEGIN
    SELECT format_type(attribute.atttypid, attribute.atttypmod)
    INTO cafe_vector_type
    FROM pg_attribute AS attribute
    WHERE attribute.attrelid = to_regclass('cafes')
      AND attribute.attname = 'cafe_vector'
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped;

    IF cafe_vector_type IS DISTINCT FROM 'vector(64)' THEN
        RAISE EXCEPTION
            'cafes.cafe_vector must be vector(64), found %',
            COALESCE(cafe_vector_type, 'NULL');
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_raw_lines;
CREATE TEMP TABLE temp_cafe_vector_raw_lines (
    line_no bigserial PRIMARY KEY,
    line_text text NOT NULL
);

\echo [load_cafes_cafe_vector] copying /tmp/cafe_vectors.json
\copy temp_cafe_vector_raw_lines (line_text) FROM '/tmp/cafe_vectors.json' WITH (FORMAT text)

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_payload;
CREATE TEMP TABLE temp_cafe_vector_payload AS
SELECT string_agg(line_text, E'\n' ORDER BY line_no)::jsonb AS payload
FROM temp_cafe_vector_raw_lines;

DO $$
DECLARE
    payload_type text;
BEGIN
    SELECT jsonb_typeof(payload)
    INTO payload_type
    FROM temp_cafe_vector_payload;

    IF payload_type IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION
            'Expected top-level JSON array in /tmp/cafe_vectors.json, got %',
            COALESCE(payload_type, 'NULL');
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_source;
CREATE TEMP TABLE temp_cafe_vector_source AS
SELECT
    items.ordinality::integer AS source_row_no,
    items.item AS source_item,
    items.item ->> 'cafe_id' AS cafe_id_text,
    items.item -> 'cafe_vector' AS cafe_vector_json
FROM temp_cafe_vector_payload AS payload
CROSS JOIN LATERAL jsonb_array_elements(payload.payload) WITH ORDINALITY AS items(item, ordinality);

DO $$
DECLARE
    offending_rows text;
BEGIN
    SELECT string_agg(source_row_no::text, ', ' ORDER BY source_row_no)
    INTO offending_rows
    FROM temp_cafe_vector_source
    WHERE jsonb_typeof(source_item) IS DISTINCT FROM 'object';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each JSON array element must be an object. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(%s)', source_row_no, COALESCE(cafe_id_text, 'NULL')),
               ', '
               ORDER BY source_row_no
           )
    INTO offending_rows
    FROM temp_cafe_vector_source
    WHERE cafe_id_text IS NULL
       OR cafe_id_text !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Invalid cafe_id values in source JSON. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(source_row_no::text, ', ' ORDER BY source_row_no)
    INTO offending_rows
    FROM temp_cafe_vector_source
    WHERE cafe_vector_json IS NULL
       OR jsonb_typeof(cafe_vector_json) IS DISTINCT FROM 'array';

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each cafe_vector must be a JSON array. Offending rows: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(len=%s)', source_row_no, jsonb_array_length(cafe_vector_json)),
               ', '
               ORDER BY source_row_no
           )
    INTO offending_rows
    FROM temp_cafe_vector_source
    WHERE jsonb_typeof(cafe_vector_json) = 'array'
      AND jsonb_array_length(cafe_vector_json) <> 64;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each cafe_vector must contain exactly 64 elements. Offending rows: %',
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
        FROM temp_cafe_vector_source AS source
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE
                WHEN jsonb_typeof(source.cafe_vector_json) = 'array'
                    THEN source.cafe_vector_json
                ELSE '[]'::jsonb
            END
        ) WITH ORDINALITY AS element(value, ordinality)
        WHERE jsonb_typeof(element.value) IS DISTINCT FROM 'number'
        ORDER BY source.source_row_no, element.ordinality
        LIMIT 20
    ) AS invalid_elements;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Each cafe_vector element must be numeric. Sample offending elements: %',
            offending_rows;
    END IF;

    SELECT string_agg(
               format('%s(count=%s)', cafe_id_text, duplicate_count),
               ', '
               ORDER BY cafe_id_text
           )
    INTO offending_rows
    FROM (
        SELECT cafe_id_text, COUNT(*) AS duplicate_count
        FROM temp_cafe_vector_source
        GROUP BY cafe_id_text
        HAVING COUNT(*) > 1
    ) AS duplicates;

    IF offending_rows IS NOT NULL THEN
        RAISE EXCEPTION
            'Duplicate cafe_id values found in source JSON: %',
            offending_rows;
    END IF;
END
$$;

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_stage;
CREATE TEMP TABLE temp_cafe_vector_stage AS
SELECT
    source_row_no,
    cafe_id_text::uuid AS cafe_id,
    (
        '['
        || (
            SELECT string_agg(element.value, ',' ORDER BY element.ordinality)
            FROM jsonb_array_elements_text(cafe_vector_json) WITH ORDINALITY AS element(value, ordinality)
        )
        || ']'
    )::vector(64) AS cafe_vector
FROM temp_cafe_vector_source;

ALTER TABLE temp_cafe_vector_stage
    ADD PRIMARY KEY (cafe_id);

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_matched;
CREATE TEMP TABLE temp_cafe_vector_matched AS
SELECT stage.cafe_id
FROM temp_cafe_vector_stage AS stage
JOIN cafes
    ON cafes.cafe_id = stage.cafe_id;

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_missing;
CREATE TEMP TABLE temp_cafe_vector_missing AS
SELECT stage.cafe_id
FROM temp_cafe_vector_stage AS stage
LEFT JOIN cafes
    ON cafes.cafe_id = stage.cafe_id
WHERE cafes.cafe_id IS NULL;

DROP TABLE IF EXISTS pg_temp.temp_cafe_vector_updated;
CREATE TEMP TABLE temp_cafe_vector_updated AS
WITH updated_rows AS (
    UPDATE cafes
    SET cafe_vector = stage.cafe_vector
    FROM temp_cafe_vector_stage AS stage
    WHERE cafes.cafe_id = stage.cafe_id
      AND cafes.cafe_vector IS DISTINCT FROM stage.cafe_vector
    RETURNING cafes.cafe_id
)
SELECT cafe_id
FROM updated_rows;

\echo [load_cafes_cafe_vector] returning summary counts
SELECT
    (SELECT COUNT(*) FROM temp_cafe_vector_stage) AS source_count,
    (SELECT COUNT(*) FROM temp_cafe_vector_matched) AS matched_count,
    (SELECT COUNT(*) FROM temp_cafe_vector_updated) AS updated_count,
    (SELECT COUNT(*) FROM temp_cafe_vector_missing) AS missing_count;

\echo [load_cafes_cafe_vector] returning missing cafe_ids
SELECT cafe_id
FROM temp_cafe_vector_missing
ORDER BY cafe_id;

COMMIT;

\echo [load_cafes_cafe_vector] completed

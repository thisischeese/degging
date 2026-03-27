-- Add an ANN index for discovery queries that rank cafes by cosine distance.

CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE INDEX IF NOT EXISTS cafes_cafe_vector_hnsw_idx
    ON cafes
    USING hnsw (cafe_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    WHERE cafe_vector IS NOT NULL;

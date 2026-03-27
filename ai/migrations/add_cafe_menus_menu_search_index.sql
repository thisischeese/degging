-- Add menu search columns and indexes for BM25 + pgvector search.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_textsearch SCHEMA public;
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_search_text text;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_vector vector(64);

UPDATE cafe_menus
SET menu_search_text = trim(
    regexp_replace(
        concat_ws(' ', menu_name, COALESCE(menu_description, '')),
        '\s+',
        ' ',
        'g'
    )
)
WHERE menu_search_text IS DISTINCT FROM trim(
    regexp_replace(
        concat_ws(' ', menu_name, COALESCE(menu_description, '')),
        '\s+',
        ' ',
        'g'
    )
);

CREATE INDEX IF NOT EXISTS cafe_menus_menu_search_bm25_idx
    ON cafe_menus
    USING bm25 (menu_search_text)
    WITH (text_config = 'public.korean');

CREATE INDEX IF NOT EXISTS cafe_menus_menu_vector_hnsw_idx
    ON cafe_menus
    USING hnsw (menu_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMIT;

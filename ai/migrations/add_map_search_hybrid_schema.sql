BEGIN;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_search_text text;

ALTER TABLE cafe_menus
    ADD COLUMN IF NOT EXISTS menu_vector vector(64);

CREATE INDEX IF NOT EXISTS cafes_location_gist_idx
    ON cafes
    USING gist (location);

CREATE INDEX IF NOT EXISTS cafe_vibe_tags_tag_id_cafe_id_idx
    ON cafe_vibe_tags
    USING btree (tag_id, cafe_id);

CREATE INDEX IF NOT EXISTS cafe_menus_cafe_id_idx
    ON cafe_menus
    USING btree (cafe_id);

CREATE INDEX IF NOT EXISTS cafe_menus_menu_search_bm25_idx
    ON cafe_menus
    USING bm25 (menu_search_text)
    WITH (text_config = 'public.korean');

CREATE INDEX IF NOT EXISTS cafe_menus_menu_vector_hnsw_idx
    ON cafe_menus
    USING hnsw (menu_vector vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMIT;

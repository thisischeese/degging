# Map Search Hybrid Rollout

## 1. Verify remote PostgreSQL prerequisites

Run inside the remote postgres container:

```sql
SELECT extname
FROM pg_extension
WHERE extname IN ('postgis', 'vector', 'pg_textsearch')
ORDER BY extname;

SELECT proname, pg_get_function_identity_arguments(p.oid)
FROM pg_proc AS p
JOIN pg_namespace AS n
  ON n.oid = p.pronamespace
WHERE proname IN ('calculate_rrf', 'to_bm25query')
ORDER BY proname;
```

## 2. Apply schema changes on the remote server

Copy and run the schema SQL first:

```powershell
docker cp ./migrations/add_map_search_hybrid_schema.sql postgres:/tmp/add_map_search_hybrid_schema.sql
docker exec postgres psql -U sweetgirl -d degging -v ON_ERROR_STOP=1 -f /tmp/add_map_search_hybrid_schema.sql
```

Verify the new columns and indexes:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'cafe_menus'
  AND column_name IN ('menu_search_text', 'menu_vector')
ORDER BY column_name;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('cafes', 'cafe_vibe_tags', 'cafe_menus')
ORDER BY tablename, indexname;
```

## 3. Generate menu search artifacts locally with uv

Run from this repository:

```powershell
uv run python -m app.services.menu_search_artifacts
```

Expected outputs:

- `models/bm_k_kosimcse_roberta_multitask/`
- `models/menu_query_encoder.pkl`
- `models/menu_search_vectors.json`

## 4. Copy backfill artifacts to the remote postgres container

```powershell
docker cp ./models/menu_search_vectors.json postgres:/tmp/menu_search_vectors.json
docker cp ./migrations/load_cafe_menu_search_vectors.sql postgres:/tmp/load_cafe_menu_search_vectors.sql
docker exec postgres psql -U sweetgirl -d degging -v ON_ERROR_STOP=1 -f /tmp/load_cafe_menu_search_vectors.sql
```

## 5. Verify populated search data

```sql
SELECT
    COUNT(*) AS total_menus,
    COUNT(menu_search_text) AS menus_with_search_text,
    COUNT(menu_vector) AS menus_with_vector
FROM cafe_menus;

SELECT
    COUNT(*) AS cafes_with_vibe_tags
FROM (
    SELECT DISTINCT cafe_id
    FROM cafe_vibe_tags
) AS tagged_cafes;
```

## 6. Local application checks with uv

Run the targeted test suite locally:

```powershell
uv run python -m unittest tests.test_map_search_service tests.test_menu_query_encoder tests.test_query_preprocess_service tests.test_map_search_api
```

Optional full regression pass:

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

## Notes

- Apply DB changes before deploying the new application build.
- `menu_search_text` is generated from `menu_name + menu_description`.
- `menu_vector` is generated from `menu_name + menu_description + cafe vibe labels`.
- The rollout keeps DB mutation separate from app deployment so the remote server can be updated manually.

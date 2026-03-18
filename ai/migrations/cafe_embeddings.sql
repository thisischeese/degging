-- pgvector 확장 활성화 (최초 1회)
CREATE EXTENSION IF NOT EXISTS vector;

-- 카페 임베딩 테이블
-- Item Tower 가 생성한 768차원 벡터를 저장한다.
CREATE TABLE IF NOT EXISTS cafe_embeddings (
    cafe_id   uuid    NOT NULL REFERENCES cafes(cafe_id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (cafe_id)
);

-- HNSW 인덱스 (코사인 유사도 기준 ANN 검색)
-- m=16, ef_construction=64 는 속도/정확도 균형 기본값 (추후 튜닝)
CREATE INDEX IF NOT EXISTS cafe_embeddings_hnsw_idx
    ON cafe_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

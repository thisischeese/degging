-- [04-init-schema.sql] 스키마 초기화
--
-- 이 파일은 docker-entrypoint-initdb.d/ 에서 04번으로 실행된다.
-- 이미지 내장 init 순서:
--   01-init-extension.sql  → vector, pg_textsearch(BM25) 익스텐션 생성
--   02-init-functions.sql  → calculate_rrf() 함수 생성
--   03-init-mecab_ko.sql   → textsearch_ko(MeCab-KO) 파서/사전/설정 생성
--
-- vector, pg_textsearch는 01에서 이미 생성되므로 여기서는 중복 생성하지 않는다.
-- PostGIS는 이 이미지에 포함되지 않으며, cafes.location은 point 타입으로 대체한다.

-- Sequences
CREATE SEQUENCE IF NOT EXISTS cafe_menus_menu_id_seq;
CREATE SEQUENCE IF NOT EXISTS curation_items_curation_item_id_seq;
CREATE SEQUENCE IF NOT EXISTS vibe_synonym_dictionary_synonym_vibe_id_seq;

-- Tables
CREATE TABLE "cafe_menus" (
    "menu_id"    bigint        DEFAULT nextval('cafe_menus_menu_id_seq') NOT NULL,
    "menu_name"  varchar(100)  NOT NULL,
    "price"      integer       NULL,
    "cafe_id"    uuid          NOT NULL
);

CREATE TABLE "scrap_share_links" (
    "link_id"    bigserial       NOT NULL,
    "token"      varchar(255)    NOT NULL,
    "is_active"  boolean         NOT NULL,
    "created_at" timestamptz     NOT NULL,
    "scrap_id"   uuid            NOT NULL
);

-- 스키마 원본의 timestampz 오타 → timestamptz 수정
CREATE TABLE "menu_entities" (
    "menu_represent_id" bigint        NOT NULL,
    "menu_vector"       vector(768)   NULL,
    "created_at"        timestamptz   NOT NULL,
    "updated_at"        timestamptz   NULL
);

CREATE TABLE "user_preference" (
    "user_id"            uuid          NOT NULL,
    "preference_vector"  vector(768)   NULL,
    "preference_tags"    jsonb         NULL,
    "updated_at"         timestamptz   NOT NULL
);

CREATE TABLE "cafe_rating_stats" (
    "cafe_id"       uuid        NOT NULL,
    "review_count"  int         NOT NULL,
    "rating_sum"    int         NOT NULL,
    "updated_at"    timestamptz NOT NULL
);

CREATE TABLE "review_images" (
    "image_id"   bigserial      NOT NULL,
    "image_url"  varchar(255)   NOT NULL,
    "sort_order" int            NOT NULL,
    "created_at" timestamptz    NOT NULL,
    "review_id"  uuid           NOT NULL
);

CREATE TABLE "menu_synonym_dictionary" (
    "menu_represent_id" bigint      NOT NULL,
    "created_at"        timestamptz NOT NULL,
    "updated_at"        timestamptz NULL,
    "menu_id"           bigint      NOT NULL
);

CREATE TABLE "cafe_images" (
    "image_id"   bigserial      NOT NULL,
    "image_url"  varchar(255)   NOT NULL,
    "sort_order" int            NOT NULL,
    "created_at" timestamptz    NOT NULL,
    "cafe_id"    uuid           NOT NULL
);

CREATE TABLE "cafe_reviews" (
    "review_id"  uuid        NOT NULL,
    "cafe_id"    uuid        NOT NULL,
    "user_id"    uuid        NOT NULL,
    "rating"     smallint    NOT NULL,
    "content"    text        NOT NULL,
    "created_at" timestamptz NOT NULL,
    "updated_at" timestamptz NOT NULL
);

CREATE TABLE "curation_items" (
    "curation_item_id" bigint DEFAULT nextval('curation_items_curation_item_id_seq') NULL,
    "sort_order"       int         NULL,
    "created_at"       timestamptz NOT NULL,
    "updated_at"       timestamptz NULL,
    "cafe_id"          uuid        NOT NULL,
    "curation_id"      bigint      NOT NULL
);

CREATE TABLE "scrap_items" (
    "scrap_item_id" bigint      NOT NULL,
    "scrap_id"      uuid        NOT NULL,
    "cafe_id"       uuid        NOT NULL,
    "created_at"    timestamptz NOT NULL
);

CREATE TABLE "user_profiles" (
    "user_id"           uuid          NOT NULL,
    "nickname"          varchar(50)   NOT NULL,
    "gender"            varchar(10)   NULL,
    "birth"             date          NULL,
    "profile_image_url" varchar(255)  NULL,
    "is_onboarded"      boolean       NOT NULL,
    "updated_at"        timestamptz   NOT NULL
);

CREATE TABLE "users" (
    "user_id"    uuid          NOT NULL,
    "email"      varchar(100)  NOT NULL,
    "pw_hash"    varchar(255)  NOT NULL,
    "created_at" timestamptz   NOT NULL,
    "updated_at" timestamptz   NOT NULL
);

CREATE TABLE "vibe_entities" (
    "tag_id"     uuid          NOT NULL,
    "tag_name"   varchar(50)   NOT NULL,
    "tag_vector" vector(768)   NOT NULL,
    "updated_at" timestamptz   NOT NULL
);

CREATE TABLE "user_ab_tests" (
    "test_name"      varchar(20) NOT NULL,
    "user_id"        uuid        NOT NULL,
    "assigned_group" char(1)     NOT NULL,
    "created_at"     timestamptz NOT NULL
);

CREATE TABLE "scrap_members" (
    "scrap_member_id" bigint      NOT NULL,
    "category_id"     uuid        NOT NULL,
    "user_id"         uuid        NOT NULL,
    "role"            varchar(20) NOT NULL,
    "created_at"      timestamptz NOT NULL
);

COMMENT ON COLUMN "scrap_members"."role" IS 'OWNER/MEMBER';

CREATE TABLE "scrap_comments" (
    "comment_id" uuid        NOT NULL,
    "content"    text        NOT NULL,
    "created_at" timestamptz NOT NULL,
    "updated_at" timestamptz NOT NULL,
    "user_id"    uuid        NOT NULL,
    "scrap_id"   uuid        NOT NULL,
    "cafe_id"    uuid        NOT NULL
);

CREATE TABLE "curation" (
    "curation_id"   bigint        NOT NULL,
    "title"         varchar(100)  NOT NULL,
    "thumbnail_url" varchar(255)  NULL,
    "created_at"    timestamptz   NOT NULL,
    "updated_at"    timestamptz   NULL
);

CREATE TABLE "cafes" (
    "cafe_id"        uuid          NOT NULL,
    "kakao_place_id" bigint        NOT NULL,
    "name"           varchar(50)   NOT NULL,
    "address"        varchar(255)  NULL,
    "road_address"   varchar(255)  NULL,
    "phone"          varchar(50)   NULL,
    "kakao_map_url"  varchar(255)  NULL,
    "thumbnail_url"  varchar(255)  NULL,
    "status"         varchar(20)   DEFAULT 'OPEN' NOT NULL,
    "created_at"     timestamptz   NOT NULL,
    "updated_at"     timestamptz   NOT NULL,
    -- PostGIS 미포함 이미지 → point(longitude, latitude) 네이티브 타입으로 대체
    "location"       point         NOT NULL,
    "cafe_intro"     varchar(255)  NULL,
    "business_hours" jsonb         NULL
);

COMMENT ON COLUMN "cafes"."status" IS '영업/폐업 여부';

CREATE TABLE "scraps" (
    "scrap_id"      uuid          NOT NULL,
    "user_id"       uuid          NOT NULL,
    "name"          varchar(50)   NOT NULL,
    "thumbnail_url" varchar(255)  NULL,
    "created_at"    timestamptz   NOT NULL,
    "updated_at"    timestamptz   NOT NULL,
    "color"         varchar(20)   NOT NULL
);

CREATE TABLE "vibe_synonym_dictionary" (
    "tag_id"           VARCHAR(255) NOT NULL,
    "synonym_vibe_id"  bigint DEFAULT nextval('vibe_synonym_dictionary_synonym_vibe_id_seq') NULL,
    "vibe_keyword"     varchar(50)  NOT NULL,
    "updated_at"       timestamptz  NOT NULL
);

CREATE TABLE "cafe_vibe_tags" (
    "cafe_vibe_tag_id" bigint NOT NULL,
    "tag_id"           uuid   NOT NULL,
    "cafe_id"          uuid   NOT NULL
);

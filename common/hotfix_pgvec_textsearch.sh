#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"

DEFAULT_CONTAINER="auto"
DEFAULT_CONTAINER_CANDIDATES=("postgres-container" "postgres")
DEFAULT_PASSWORD_ENV="POSTGRES_PASSWORD"
DEFAULT_RESTART="yes"
DEFAULT_WORKDIR="/tmp/pgvec-textsearch-hotfix"
DEFAULT_CLEANUP="yes"

MECAB_KO_VERSION="mecab-0.996-ko-0.9.2"
MECAB_KO_DIC_VERSION="mecab-ko-dic-2.1.1-20180720"
TEXTSEARCH_KO_REPO="https://github.com/i0seph/textsearch_ko.git"
TEXTSEARCH_KO_REF="9ba24647ac35d7f490eae3d59f9bc75688af1056"
PG_TEXTSEARCH_REPO="https://github.com/timescale/pg_textsearch.git"
PG_TEXTSEARCH_REF="76ea737a5e9a3ae79f4ea8b2028163f8e80e9406"

EXIT_PREFLIGHT=10
EXIT_BUILD_NATIVE=20
EXIT_SQL_APPLY=30
EXIT_VERIFY=40

CONTAINER_NAME="$DEFAULT_CONTAINER"
CONTAINER_NAME_EXPLICIT="no"
DB_NAME=""
DB_USER=""
PASSWORD_ENV_NAME="$DEFAULT_PASSWORD_ENV"
RESTART_CONTAINER="$DEFAULT_RESTART"
VERIFY_ONLY="no"
RESUME_FROM="preflight"
WORKDIR_IN_CONTAINER="$DEFAULT_WORKDIR"
CLEANUP_WORKDIR="$DEFAULT_CLEANUP"
VERBOSE="no"

CURRENT_STEP="startup"
HOST_PSQL_PRESENT="no"
DB_PASSWORD=""
PG_MAJOR=""
CONTAINER_ARCH=""
CONFIGURE_BUILD_FLAG=""
PKGLIBDIR=""
SHAREDIR=""
VECTOR_AVAILABLE="no"
PG_TEXTSEARCH_AVAILABLE="no"
RRF_EXISTS="no"
KOREAN_CONFIG_EXISTS="no"
TS_MECABKO_PRESENT="no"
PG_TEXTSEARCH_CONTROL_PRESENT="no"

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME --db <name> --user <name> [options]

Options:
  --container <name>        Docker container name (default: auto-detect: postgres-container -> postgres)
  --db <name>               PostgreSQL database name
  --user <name>             PostgreSQL user name
  --password-env <ENV_NAME> Host env var that stores the DB password (default: $DEFAULT_PASSWORD_ENV)
  --restart yes|no          Restart the container after SQL apply (default: $DEFAULT_RESTART)
  --verify-only             Skip install/apply and run verification only
  --resume-from <step>      Resume from step: preflight|install_deps|build_native|apply_sql|restart|verify
  --workdir <path>          Build workdir inside the container (default: $DEFAULT_WORKDIR)
  --cleanup yes|no          Remove the container workdir after completion (default: $DEFAULT_CLEANUP)
  --verbose                 Enable shell tracing
  -h, --help                Show this help
EOF
}

log() {
    local level="$1"
    local step="$2"
    local message="$3"
    printf '[%s] step=%s message=%s\n' "$level" "$step" "$message"
}

info() {
    log "INFO" "$1" "$2"
}

warn() {
    log "WARN" "$1" "$2" >&2
}

error() {
    log "ERROR" "$1" "$2" >&2
}

die() {
    local code="$1"
    shift
    error "$CURRENT_STEP" "$*"
    exit "$code"
}

step_exit_code() {
    case "$1" in
        preflight|detect_platform)
            echo "$EXIT_PREFLIGHT"
            ;;
        install_deps|build_native)
            echo "$EXIT_BUILD_NATIVE"
            ;;
        apply_sql)
            echo "$EXIT_SQL_APPLY"
            ;;
        restart|verify)
            echo "$EXIT_VERIFY"
            ;;
        *)
            echo 1
            ;;
    esac
}

on_err() {
    local exit_code=$?
    local mapped_exit_code
    mapped_exit_code="$(step_exit_code "$CURRENT_STEP")"
    error "$CURRENT_STEP" "command failed at line ${BASH_LINENO[0]} with exit_code=${exit_code} mapped_exit_code=${mapped_exit_code}"
    exit "$mapped_exit_code"
}

trap on_err ERR

step_index() {
    case "$1" in
        preflight) echo 0 ;;
        install_deps) echo 1 ;;
        build_native) echo 2 ;;
        apply_sql) echo 3 ;;
        restart) echo 4 ;;
        verify) echo 5 ;;
        *)
            return 1
            ;;
    esac
}

should_run() {
    local target_step="$1"
    if [[ "$VERIFY_ONLY" == "yes" ]]; then
        [[ "$target_step" == "verify" ]]
        return
    fi

    local requested
    local target
    requested="$(step_index "$RESUME_FROM")" || die "$EXIT_PREFLIGHT" "invalid resume step: $RESUME_FROM"
    target="$(step_index "$target_step")" || die "$EXIT_PREFLIGHT" "invalid target step: $target_step"
    [[ "$target" -ge "$requested" ]]
}

require_command() {
    local command_name="$1"
    command -v "$command_name" >/dev/null 2>&1 || die "$EXIT_PREFLIGHT" "required command not found: $command_name"
}

container_exec() {
    docker exec "$CONTAINER_NAME" "$@"
}

container_exec_root() {
    docker exec -u 0 "$CONTAINER_NAME" "$@"
}

psql_cmd() {
    docker exec -e "PGPASSWORD=$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -P pager=off "$@"
}

psql_query_value() {
    local sql="$1"
    psql_cmd -Atqc "$sql"
}

resolve_container_name() {
    if [[ "$CONTAINER_NAME_EXPLICIT" == "yes" ]]; then
        return
    fi

    local candidate
    for candidate in "${DEFAULT_CONTAINER_CANDIDATES[@]}"; do
        if docker ps --format '{{.Names}}' | grep -Fx "$candidate" >/dev/null; then
            CONTAINER_NAME="$candidate"
            info "$CURRENT_STEP" "auto-detected container=$CONTAINER_NAME"
            return
        fi
    done

    die "$EXIT_PREFLIGHT" "no running postgres container found; tried: ${DEFAULT_CONTAINER_CANDIDATES[*]}"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --container)
                CONTAINER_NAME="$2"
                CONTAINER_NAME_EXPLICIT="yes"
                shift 2
                ;;
            --db)
                DB_NAME="$2"
                shift 2
                ;;
            --user)
                DB_USER="$2"
                shift 2
                ;;
            --password-env)
                PASSWORD_ENV_NAME="$2"
                shift 2
                ;;
            --restart)
                RESTART_CONTAINER="$2"
                shift 2
                ;;
            --verify-only)
                VERIFY_ONLY="yes"
                RESUME_FROM="verify"
                shift
                ;;
            --resume-from)
                RESUME_FROM="$2"
                shift 2
                ;;
            --workdir)
                WORKDIR_IN_CONTAINER="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP_WORKDIR="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE="yes"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                die "$EXIT_PREFLIGHT" "unknown argument: $1"
                ;;
        esac
    done

    [[ -n "$DB_NAME" ]] || die "$EXIT_PREFLIGHT" "--db is required"
    [[ -n "$DB_USER" ]] || die "$EXIT_PREFLIGHT" "--user is required"
    [[ "$RESTART_CONTAINER" == "yes" || "$RESTART_CONTAINER" == "no" ]] || die "$EXIT_PREFLIGHT" "--restart must be yes or no"
    [[ "$CLEANUP_WORKDIR" == "yes" || "$CLEANUP_WORKDIR" == "no" ]] || die "$EXIT_PREFLIGHT" "--cleanup must be yes or no"
    step_index "$RESUME_FROM" >/dev/null || die "$EXIT_PREFLIGHT" "--resume-from must be one of preflight|install_deps|build_native|apply_sql|restart|verify"
}

preflight() {
    CURRENT_STEP="preflight"

    require_command docker
    require_command git
    require_command bash
    if command -v psql >/dev/null 2>&1; then
        HOST_PSQL_PRESENT="yes"
    else
        HOST_PSQL_PRESENT="no"
        warn "$CURRENT_STEP" "host psql not found; container psql will be used"
    fi

    DB_PASSWORD="${!PASSWORD_ENV_NAME:-}"
    [[ -n "$DB_PASSWORD" ]] || die "$EXIT_PREFLIGHT" "host environment variable $PASSWORD_ENV_NAME is not set"

    resolve_container_name

    docker ps --format '{{.Names}}' | grep -Fx "$CONTAINER_NAME" >/dev/null \
        || die "$EXIT_PREFLIGHT" "container not running: $CONTAINER_NAME"

    container_exec bash -lc 'echo bash-ok' >/dev/null
    container_exec psql --version >/dev/null
    PKGLIBDIR="$(container_exec pg_config --pkglibdir | tr -d '\r')"
    SHAREDIR="$(container_exec pg_config --sharedir | tr -d '\r')"
    [[ -n "$PKGLIBDIR" ]] || die "$EXIT_PREFLIGHT" "failed to resolve pg_config --pkglibdir"
    [[ -n "$SHAREDIR" ]] || die "$EXIT_PREFLIGHT" "failed to resolve pg_config --sharedir"

    psql_query_value 'SELECT 1;' >/dev/null

    VECTOR_AVAILABLE="$(psql_query_value "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN 'yes' ELSE 'no' END;")"
    [[ "$VECTOR_AVAILABLE" == "yes" ]] || die "$EXIT_PREFLIGHT" "vector extension is not available in this container"

    PG_TEXTSEARCH_AVAILABLE="$(psql_query_value "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pg_textsearch') THEN 'yes' ELSE 'no' END;")"
    RRF_EXISTS="$(psql_query_value "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'calculate_rrf') THEN 'yes' ELSE 'no' END;")"
    KOREAN_CONFIG_EXISTS="$(psql_query_value "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_ts_config config JOIN pg_namespace namespace ON namespace.oid = config.cfgnamespace WHERE namespace.nspname = 'public' AND config.cfgname = 'korean') THEN 'yes' ELSE 'no' END;")"

    if container_exec_root bash -lc "test -f '$PKGLIBDIR/ts_mecab_ko.so'"; then
        TS_MECABKO_PRESENT="yes"
    else
        TS_MECABKO_PRESENT="no"
    fi

    if container_exec_root bash -lc "test -f '$SHAREDIR/extension/pg_textsearch.control'"; then
        PG_TEXTSEARCH_CONTROL_PRESENT="yes"
    else
        PG_TEXTSEARCH_CONTROL_PRESENT="no"
    fi

    info "$CURRENT_STEP" "container=$CONTAINER_NAME db=$DB_NAME user=$DB_USER host_psql=$HOST_PSQL_PRESENT vector_available=$VECTOR_AVAILABLE pg_textsearch_available=$PG_TEXTSEARCH_AVAILABLE rrf_exists=$RRF_EXISTS korean_config_exists=$KOREAN_CONFIG_EXISTS ts_mecabko_present=$TS_MECABKO_PRESENT"
}

detect_platform() {
    CURRENT_STEP="detect_platform"
    CONTAINER_ARCH="$(container_exec uname -m | tr -d '\r')"
    PG_MAJOR="$(container_exec bash -lc "psql --version | sed -E 's/.* ([0-9]+)(\\.[0-9]+)?$/\\1/'" | tr -d '\r')"
    [[ -n "$PG_MAJOR" ]] || die "$EXIT_PREFLIGHT" "failed to detect PostgreSQL major version"

    case "$CONTAINER_ARCH" in
        aarch64|arm64)
            CONFIGURE_BUILD_FLAG="--build=aarch64-unknown-linux-gnu"
            ;;
        *)
            CONFIGURE_BUILD_FLAG=""
            ;;
    esac

    info "$CURRENT_STEP" "arch=$CONTAINER_ARCH pg_major=$PG_MAJOR configure_flag=${CONFIGURE_BUILD_FLAG:-<none>}"
}

install_build_deps() {
    CURRENT_STEP="install_deps"
    detect_platform

    info "$CURRENT_STEP" "installing build dependencies inside $CONTAINER_NAME"
    docker exec -i -u 0 -e DEBIAN_FRONTEND=noninteractive "$CONTAINER_NAME" bash -s -- "$PG_MAJOR" <<'BASH'
set -Eeuo pipefail
pg_major="$1"
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    apt-utils \
    autoconf \
    automake \
    ca-certificates \
    cmake \
    curl \
    gcc \
    g++ \
    git \
    libtool \
    make \
    postgresql-server-dev-"$pg_major" \
    tzdata \
    zlib1g-dev
apt-get clean
rm -rf /var/lib/apt/lists/*
BASH
}

build_and_install_native_components() {
    CURRENT_STEP="build_native"
    detect_platform

    if [[ "$TS_MECABKO_PRESENT" == "yes" && "$PG_TEXTSEARCH_CONTROL_PRESENT" == "yes" ]]; then
        info "$CURRENT_STEP" "native components already present; skipping build"
        return
    fi

    info "$CURRENT_STEP" "building mecab-ko, dictionary, textsearch_ko, and pg_textsearch"
    docker exec -i -u 0 -e DEBIAN_FRONTEND=noninteractive "$CONTAINER_NAME" bash -s -- \
        "$WORKDIR_IN_CONTAINER" \
        "$CONFIGURE_BUILD_FLAG" \
        "$MECAB_KO_VERSION" \
        "$MECAB_KO_DIC_VERSION" \
        "$TEXTSEARCH_KO_REPO" \
        "$TEXTSEARCH_KO_REF" \
        "$PG_TEXTSEARCH_REPO" \
        "$PG_TEXTSEARCH_REF" <<'BASH'
set -Eeuo pipefail
workdir="$1"
configure_build_flag="$2"
mecab_ko_version="$3"
mecab_ko_dic_version="$4"
textsearch_ko_repo="$5"
textsearch_ko_ref="$6"
pg_textsearch_repo="$7"
pg_textsearch_ref="$8"

mkdir -p "$workdir"
cd "$workdir"

ensure_checkout() {
    local repo_url="$1"
    local ref="$2"
    local dir_name="$3"

    if [[ ! -d "$dir_name/.git" ]]; then
        rm -rf "$dir_name"
        git clone "$repo_url" "$dir_name"
    fi

    git -C "$dir_name" fetch --all --tags --prune
    git -C "$dir_name" checkout --detach "$ref"
}

build_mecab() {
    local tarball="${mecab_ko_version}.tar.gz"
    local src_dir="${workdir}/${mecab_ko_version}"
    if [[ ! -d "$src_dir" ]]; then
        curl -fsSL -o "$tarball" "https://bitbucket.org/eunjeon/mecab-ko/downloads/${tarball}"
        tar -xzf "$tarball"
        rm -f "$tarball"
    fi

    cd "$src_dir"
    if [[ -n "$configure_build_flag" ]]; then
        ./configure "$configure_build_flag"
    else
        ./configure
    fi
    make -j"$(nproc)"
    make install
}

build_mecab_dic() {
    local tarball="${mecab_ko_dic_version}.tar.gz"
    local src_dir="${workdir}/${mecab_ko_dic_version}"
    if [[ ! -d "$src_dir" ]]; then
        curl -fsSL -o "$tarball" "https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/${tarball}"
        tar -xzf "$tarball"
        rm -f "$tarball"
    fi

    cd "$src_dir"
    ./autogen.sh
    ./configure
    make -j"$(nproc)"
    make install
}

echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab-ko.conf
ldconfig

build_mecab
build_mecab_dic

ensure_checkout "$textsearch_ko_repo" "$textsearch_ko_ref" "textsearch_ko"
cd "$workdir/textsearch_ko"
make USE_PGXS=1
make USE_PGXS=1 install

ensure_checkout "$pg_textsearch_repo" "$pg_textsearch_ref" "pg_textsearch"
cd "$workdir/pg_textsearch"
make USE_PGXS=1
make USE_PGXS=1 install

ldconfig
BASH

    if container_exec_root bash -lc "test -f '$PKGLIBDIR/ts_mecab_ko.so'"; then
        TS_MECABKO_PRESENT="yes"
    else
        die "$EXIT_BUILD_NATIVE" "ts_mecab_ko.so was not installed into $PKGLIBDIR"
    fi

    if container_exec_root bash -lc "test -f '$SHAREDIR/extension/pg_textsearch.control'"; then
        PG_TEXTSEARCH_CONTROL_PRESENT="yes"
    else
        die "$EXIT_BUILD_NATIVE" "pg_textsearch.control was not installed into $SHAREDIR/extension"
    fi

    info "$CURRENT_STEP" "native components installed successfully"
}

apply_sql() {
    CURRENT_STEP="apply_sql"

    if [[ "$TS_MECABKO_PRESENT" != "yes" ]]; then
        die "$EXIT_SQL_APPLY" "ts_mecab_ko.so is missing; cannot apply mecab SQL"
    fi

    info "$CURRENT_STEP" "applying pg_textsearch/vector extension SQL"
    docker exec -i -e "PGPASSWORD=$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SET search_path = public;
CREATE EXTENSION IF NOT EXISTS pg_textsearch SCHEMA public;
CREATE EXTENSION IF NOT EXISTS vector;
COMMENT ON EXTENSION pg_textsearch IS 'BM25 scoring for full-text search';
SQL

    info "$CURRENT_STEP" "applying calculate_rrf SQL"
    docker exec -i -e "PGPASSWORD=$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SET search_path = public;
CREATE OR REPLACE FUNCTION calculate_rrf(rank1 int, rank2 int, k int DEFAULT 60)
RETURNS float8 AS $$
BEGIN
    RETURN (COALESCE(1.0 / (k + rank1), 0.0) + COALESCE(1.0 / (k + rank2), 0.0));
END;
$$ LANGUAGE plpgsql IMMUTABLE;
SQL

    info "$CURRENT_STEP" "applying mecab korean text search SQL"
    docker exec -i -e "PGPASSWORD=$DB_PASSWORD" "$CONTAINER_NAME" \
        psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
SET search_path = public;

CREATE OR REPLACE FUNCTION ts_mecabko_start(internal, int4) RETURNS internal AS '$libdir/ts_mecab_ko' LANGUAGE 'c' STRICT;
CREATE OR REPLACE FUNCTION ts_mecabko_gettoken(internal, internal, internal) RETURNS internal AS '$libdir/ts_mecab_ko' LANGUAGE 'c' STRICT;
CREATE OR REPLACE FUNCTION ts_mecabko_end(internal) RETURNS void AS '$libdir/ts_mecab_ko' LANGUAGE 'c' STRICT;
CREATE OR REPLACE FUNCTION ts_mecabko_lexize(internal, internal, internal, internal) RETURNS internal AS '$libdir/ts_mecab_ko' LANGUAGE 'c' STRICT;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_parser WHERE prsnamespace = 'public'::regnamespace AND prsname = 'korean') THEN
        CREATE TEXT SEARCH PARSER public.korean (
            START    = ts_mecabko_start,
            GETTOKEN = ts_mecabko_gettoken,
            END      = ts_mecabko_end,
            HEADLINE = pg_catalog.prsd_headline,
            LEXTYPES = pg_catalog.prsd_lextype
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_ts_template WHERE tmplnamespace = 'public'::regnamespace AND tmplname = 'mecabko') THEN
        CREATE TEXT SEARCH TEMPLATE public.mecabko (LEXIZE = ts_mecabko_lexize);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_ts_dict WHERE dictnamespace = 'public'::regnamespace AND dictname = 'korean_stem') THEN
        CREATE TEXT SEARCH DICTIONARY public.korean_stem (TEMPLATE = public.mecabko);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgnamespace = 'public'::regnamespace AND cfgname = 'korean') THEN
        CREATE TEXT SEARCH CONFIGURATION public.korean (PARSER = public.korean);

        ALTER TEXT SEARCH CONFIGURATION public.korean ADD MAPPING
            FOR email, url, url_path, host, file, version,
                sfloat, float, int, uint,
                numword, hword_numpart, numhword
            WITH simple;

        ALTER TEXT SEARCH CONFIGURATION public.korean ADD MAPPING
            FOR asciiword, hword_asciipart, asciihword
            WITH english_stem;

        ALTER TEXT SEARCH CONFIGURATION public.korean ADD MAPPING
            FOR word, hword_part, hword
            WITH public.korean_stem;
    END IF;
END $$;

CREATE OR REPLACE FUNCTION mecabko_analyze(text, OUT word text, OUT type text, OUT part1st text, OUT partlast text, OUT pronounce text, OUT conjtype text, OUT conjugation text, OUT basic text, OUT detail text, OUT lucene text) RETURNS SETOF record AS '$libdir/ts_mecab_ko' LANGUAGE 'c' IMMUTABLE STRICT;
CREATE OR REPLACE FUNCTION korean_normalize(text) RETURNS text AS '$libdir/ts_mecab_ko' LANGUAGE 'c' IMMUTABLE STRICT;
CREATE OR REPLACE FUNCTION hanja2hangul(text) RETURNS text AS '$libdir/ts_mecab_ko' LANGUAGE 'c' IMMUTABLE STRICT;
SQL

    PG_TEXTSEARCH_AVAILABLE="yes"
    RRF_EXISTS="yes"
    KOREAN_CONFIG_EXISTS="yes"
    info "$CURRENT_STEP" "SQL apply completed successfully"
}

restart_container_if_needed() {
    CURRENT_STEP="restart"

    if [[ "$RESTART_CONTAINER" != "yes" ]]; then
        info "$CURRENT_STEP" "restart disabled; skipping container restart"
        return
    fi

    info "$CURRENT_STEP" "restarting $CONTAINER_NAME"
    docker restart "$CONTAINER_NAME" >/dev/null

    local attempt
    for attempt in $(seq 1 30); do
        if psql_query_value 'SELECT 1;' >/dev/null 2>&1; then
            info "$CURRENT_STEP" "database became ready after restart on attempt=$attempt"
            return
        fi
        sleep 2
    done

    die "$EXIT_VERIFY" "database did not become ready after restart"
}

verify_installation() {
    CURRENT_STEP="verify"

    info "$CURRENT_STEP" "verifying pg_textsearch, calculate_rrf, and public.korean"
    psql_cmd -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pg_textsearch') ORDER BY extname;"
    psql_cmd -c "SELECT public.calculate_rrf(1, 2) AS rrf_score;"
    psql_cmd -c "SELECT namespace.nspname, config.cfgname FROM pg_ts_config AS config JOIN pg_namespace AS namespace ON namespace.oid = config.cfgnamespace WHERE namespace.nspname = 'public' AND config.cfgname = 'korean';"
    psql_cmd -c "SELECT to_tsvector('public.korean', '맛있는 케이크랑 커피 마시고 싶다') AS korean_vector;"
    psql_cmd -c "SELECT alias, token, lexemes FROM ts_debug('public.korean', '커피');"
    psql_cmd -c "SELECT * FROM mecabko_analyze('케이크');"
    info "$CURRENT_STEP" "verification completed successfully"
}

cleanup() {
    CURRENT_STEP="cleanup"
    if [[ "$CLEANUP_WORKDIR" != "yes" ]]; then
        info "$CURRENT_STEP" "cleanup disabled; leaving workdir at $WORKDIR_IN_CONTAINER"
        return
    fi

    container_exec_root bash -lc "rm -rf '$WORKDIR_IN_CONTAINER'" >/dev/null 2>&1 || true
    info "$CURRENT_STEP" "removed workdir $WORKDIR_IN_CONTAINER"
}

main() {
    parse_args "$@"

    if [[ "$VERBOSE" == "yes" ]]; then
        set -x
    fi

    preflight

    if should_run install_deps; then
        install_build_deps
    fi

    if should_run build_native; then
        build_and_install_native_components
    fi

    if should_run apply_sql; then
        apply_sql
    fi

    if should_run restart; then
        restart_container_if_needed
    fi

    if should_run verify; then
        verify_installation
    fi

    cleanup
    info "done" "hotfix workflow finished successfully"
}

main "$@"

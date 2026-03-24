from pathlib import Path
from typing import Annotated

from pydantic import Field, MongoDsn, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PortInt = Annotated[int, Field(gt=0, le=65535)]
RequiredStr = Annotated[str, Field(min_length=1)]


def find_env_file() -> str | None:
    current_dir = Path(__file__).resolve().parent

    for directory in (current_dir, *current_dir.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return str(candidate)

    return None


def find_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        str_strip_whitespace=True,
    )

    # PostgreSQL
    # docker-compose: POSTGRES_HOST=postgres-container, POSTGRES_PORT=5432
    # 로컬 개발:      POSTGRES_HOST=localhost, POSTGRES_PORT=(매핑 포트)
    postgres_host: str = "postgres-container"
    postgres_port: PortInt = 5432
    postgres_db: RequiredStr
    postgres_user: RequiredStr
    postgres_password: RequiredStr

    # MongoDB — docker-compose 변수명과 동일 (MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE)
    # docker-compose: MONGO_HOST=mongo-container, MONGO_PORT=27017
    # 로컬 개발:      MONGO_HOST=localhost, MONGO_PORT=27017
    mongo_host: str = "mongo-container"
    mongo_port: PortInt = 27017
    mongo_username: RequiredStr
    mongo_password: RequiredStr
    mongo_database: RequiredStr

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: PortInt = 8000

    s3_secret_key: RequiredStr
    s3_access_key: RequiredStr
    s3_bucket_name: RequiredStr
    s3_region: RequiredStr
    gms_api_key: RequiredStr

    # Discovery
    discovery_top_k: int = 100
    
    hf_token: RequiredStr

    @computed_field
    @property
    def postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )

    @computed_field
    @property
    def mongo_uri(self) -> MongoDsn:
        return MongoDsn.build(
            scheme="mongodb",
            username=self.mongo_username,
            password=self.mongo_password,
            host=self.mongo_host,
            port=self.mongo_port,
            path=self.mongo_database,
            query="authSource=admin",
        )


settings = Settings()

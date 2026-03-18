from typing import Annotated

from pydantic import Field, MongoDsn, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PortInt = Annotated[int, Field(gt=0, le=65535)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # PostgreSQL
    # docker-compose: POSTGRES_HOST=postgres-container, POSTGRES_PORT=5432
    # 로컬 개발:      POSTGRES_HOST=localhost, POSTGRES_PORT=(매핑 포트)
    postgres_host: str
    postgres_port: PortInt
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # MongoDB — docker-compose 변수명과 동일 (MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE)
    # docker-compose: MONGO_HOST=mongo-container, MONGO_PORT=27017
    # 로컬 개발:      MONGO_HOST=localhost, MONGO_PORT=27017
    mongo_host: str
    mongo_port: PortInt
    mongo_username: str
    mongo_password: str
    mongo_database: str

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: PortInt

    # Discovery
    discovery_top_k: int = 100

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
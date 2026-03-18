from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cafe_db"
    postgres_user: str = "postgres"
    postgres_password: str  # 기본값 없음 — .env 필수

    # MongoDB
    mongo_uri: str  # 인증 정보 포함 URI — 기본값 없음, .env 필수
    mongo_db: str = "cafe_ai"

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Discovery
    discovery_top_k: int = 100

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()

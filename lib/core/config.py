from functools import lru_cache
from os import getenv

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

env = getenv("ENV_FILE") or ".env.dev"


class Settings(BaseSettings):
    db_name: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    db_user: str | None = None
    db_password: str | None = None

    db_testing_url: str = "sqlite+aiosqlite:///:memory:"
    jwt_secret_key: str | None = None
    debug: bool = False
    project_name: str | None = None
    sendgrid_api_key: str | None = None
    sendgrid_from_email: EmailStr | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_bucket_name: str | None = None
    aws_region: str | None = None
    aws_endpoint_url: str | None = None
    get_stream_api_key: str = "3ptyb3jnvkmu"
    get_stream_api_secret: str = (
        "fyyuh6zhkqzx5accje9b7rx2j4qgpw6ngvh4932st8wpmwfy9jek7z4nyemjqny5"
    )

    model_config = SettingsConfigDict(env_file=env)

    @property
    def db_url(self):
        if self.db_name is None:
            return self.db_testing_url
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache()
def get_setting():
    return Settings()


settings: Settings = get_setting()

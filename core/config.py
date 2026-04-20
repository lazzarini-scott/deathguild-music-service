from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = ""
    spotify_refresh_token: str = ""

    deathguild_base_url: str = "http://www.deathguild.com"


settings = Settings()

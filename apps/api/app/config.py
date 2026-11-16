from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Local directory with the regions (development) or public R2 URL (production).
    assets_dir: str | None = None
    assets_url: str | None = None
    cors_origins: str = "http://localhost:3000"
    # https://api.nasa.gov key for DONKI. DEMO_KEY works for testing but runs out quickly.
    nasa_api_key: str = "DEMO_KEY"
    # false: /live only uses the saved copy (no internet, or in tests).
    live_data: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

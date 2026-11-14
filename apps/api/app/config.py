from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Directorio local con las regiones (desarrollo) o URL pública de R2 (producción).
    assets_dir: str | None = None
    assets_url: str | None = None
    cors_origins: str = "http://localhost:3000"
    # Llave de https://api.nasa.gov para DONKI. DEMO_KEY sirve para probar, pero se agota pronto.
    nasa_api_key: str = "DEMO_KEY"
    # false: /live usa solo la copia guardada (sin internet, o en las pruebas).
    live_data: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

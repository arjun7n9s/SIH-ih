from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_REPO_ENV), extra="ignore")

    use_mock: bool = True
    cors_origins: str = "http://localhost:5173"

    aimlapi_key: str = ""
    aimlapi_base_url: str = "https://api.aimlapi.com/v1"
    aimlapi_chat_model: str = "gpt-4o-mini"
    aimlapi_embed_model: str = "text-embedding-3-large"

    bright_data_api_token: str = ""
    brightdata_api_key: str = ""
    bright_data_unlocker_zone: str = ""
    bright_data_unlocker_token: str = ""

    speechmatics_api_key: str = ""
    speechmatics_jwt_ttl_seconds: int = 60

    @property
    def bd_token(self) -> str:
        return (
            self.bright_data_unlocker_token
            or self.bright_data_api_token
            or self.brightdata_api_key
        ).strip()

    @property
    def origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

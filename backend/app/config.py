from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ENV),
        extra="ignore",
        # Vercel often injects blank strings for unset keys; treat those as missing.
        env_ignore_empty=True,
    )

    use_mock: bool = False
    cors_origins: str = (
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:3000,"
        "https://suchna.vercel.app,https://suchna-tejesh-kunapareddy-s-projects.vercel.app"
    )

    aimlapi_key: str = ""
    aimlapi_base_url: str = "https://api.aimlapi.com/v1"
    # Gemini draft (open / general)
    aimlapi_chat_model: str = "gemini-2.5-flash"
    # RAG draft — stays on official passages
    aimlapi_grounded_model: str = "gpt-4o"
    # Third model: picks / merges the two drafts
    aimlapi_judge_model: str = "gpt-4o-mini"
    aimlapi_embed_model: str = "text-embedding-3-large"

    bright_data_api_token: str = ""
    brightdata_api_key: str = ""
    bright_data_unlocker_zone: str = ""
    bright_data_unlocker_token: str = ""

    speechmatics_api_key: str = ""
    speechmatics_jwt_ttl_seconds: int = 60
    # Melia-1 = multilingual batch (Hinglish / code-switch). Realtime Melia not shipped yet.
    speechmatics_batch_model: str = "melia-1"
    speechmatics_realtime_model: str = "enhanced"
    speechmatics_realtime_language: str = "en"
    speechmatics_language_hints: str = "en,hi"

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

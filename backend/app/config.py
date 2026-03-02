from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    transcription_model: str = "whisper-1"
    recipe_model: str = "gpt-4.1-mini"
    vision_model: str = "gpt-4.1-mini"
    database_url: str = "sqlite:///./app.db"
    storage_dir: str = "storage"
    max_upload_mb: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

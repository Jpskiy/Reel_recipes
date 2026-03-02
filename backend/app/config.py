from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    transcription_model_size: str = "small"
    transcription_device: str = "cpu"
    transcription_compute_type: str = "int8"
    ollama_host: str = "http://localhost:11434"
    recipe_model: str = "qwen2.5:7b-instruct"
    enable_vision: bool = False
    vision_model: str = "llava:7b"
    database_url: str = "sqlite:///./app.db"
    storage_dir: str = "storage"
    max_upload_mb: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

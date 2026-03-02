from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./app.db"
    STORAGE_DIR: str = "storage"
    MAX_UPLOAD_MB: int = 200
    OLLAMA_HOST: str = "http://localhost:11434"
    RECIPE_MODEL: str = "qwen2.5:7b-instruct"
    TRANSCRIPTION_MODEL_SIZE: str = "small"
    TRANSCRIPTION_DEVICE: str = "cpu"
    TRANSCRIPTION_COMPUTE_TYPE: str = "int8"
    ENABLE_VISION: bool = False


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    app_env: str = 'dev'
    project_id: str = ''
    firestore_database: str = '(default)'
    openai_api_key: str = ''
    openai_model: str = 'gpt-4o-mini'
    openai_timeout_seconds: float = 20.0
    llm_provider: str = 'gemini'
    llm_temperature: float = 0.4
    llm_timeout_seconds: float = 20.0
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    gemini_base_url: str = 'https://generativelanguage.googleapis.com/v1beta'
    openai_base_url: str | None = None
    allow_guest: bool = True

    points_correct: int = 10
    points_daily_login: int = 5
    points_topic_complete: int = 20


settings = Settings()

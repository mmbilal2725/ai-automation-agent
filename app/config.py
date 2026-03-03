from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Meta (Messenger + Instagram)
    meta_app_secret: str
    instagram_app_secret: str = ""
    meta_page_access_token: str
    meta_verify_token: str

    # SendGrid (Email)
    sendgrid_api_key: str
    sendgrid_from_email: str = "support@example.com"

    # Database
    database_url: str

    # App
    app_env: str = "development"
    escalation_confidence_threshold: float = 0.6
    brand_voice_prompt: str = (
        "You are a friendly, professional customer service agent. "
        "Be concise, helpful, and warm. Never make up information."
    )
    chroma_persist_dir: str = "./chroma_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses the asyncpg driver.
        Railway provides postgresql:// but asyncpg requires postgresql+asyncpg://
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_secret: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./wallet.db"
    payment_provider: str = "stub"
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    base_url: str = "http://localhost:8000"
    commission_percent: int = 7


settings = Settings()
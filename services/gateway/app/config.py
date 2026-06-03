from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "gateway"
    database_url: str
    jwt_secret: str = "change-me"
    jwt_expiry_minutes: int = 60

    order_service_url: str = "http://order:8000"
    inventory_service_url: str = "http://inventory:8000"
    shipping_service_url: str = "http://shipping:8000"


settings = Settings()

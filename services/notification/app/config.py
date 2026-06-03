from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "notification"
    database_url: str
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"


settings = Settings()

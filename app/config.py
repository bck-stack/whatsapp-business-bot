"""Configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Meta / WhatsApp Cloud API
    WHATSAPP_TOKEN: str          # Bearer token from Meta App Dashboard
    WHATSAPP_PHONE_ID: str       # Phone number ID (not the actual number)
    VERIFY_TOKEN: str            # Arbitrary string you set in Meta webhook config

    # Optional — used in order-notification example
    BUSINESS_NAME: str = "My Business"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

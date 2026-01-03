"""API settings configuration."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings."""

    # Add model config to allow extra fields
    model_config = ConfigDict(extra="ignore", env_prefix="UCKN_API_", env_file=".env")

    # Authentication settings
    api_key_header: str = "X-API-Key"
    require_auth: bool = True

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS settings
    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


_settings = None


def get_settings() -> APISettings:
    """Get API settings singleton."""
    global _settings
    if _settings is None:
        _settings = APISettings()
    return _settings

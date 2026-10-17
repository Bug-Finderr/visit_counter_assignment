from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis Configuration
    REDIS_NODES: str = ""  # Will be a comma-separated string of Redis nodes

    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Consistent Hashing Configuration
    # keep in sync with the .env the deployments were set up with
    VIRTUAL_NODES: int = 200

    # Batch Processing Configuration
    BATCH_INTERVAL_SECONDS: float = 5.0

    # Application Configuration
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()

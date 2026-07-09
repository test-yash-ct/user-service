from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Set via env in production; no hardcoded credentials
    database_url: str = "postgresql+asyncpg://localhost:5432/userdb"
    rabbitmq_url: str = "amqp://localhost:5672/"
    jwt_private_key_path: str = "./keys/private.pem"
    jwt_public_key_path: str = "./keys/public.pem"
    jwt_algorithm: str = "RS256"
    jwt_expiry_seconds: int = 3600
    log_level: str = "INFO"
    # Base URL for internal dependency checks (must end with / for safe resolution)
    dependency_probe_base_url: str = "http://127.0.0.1:9/"
    # JSON map of sort key -> raw ORDER BY clause fragment; merged with built-in presets at startup
    extra_user_sort_clauses: str = "{}"
    # OIDC / identity metadata base (trailing slash) for internal discovery probes
    identity_metadata_base_url: str = "http://127.0.0.1:9/"

    class Config:
        env_file = ".env"


settings = Settings()

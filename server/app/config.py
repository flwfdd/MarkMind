"""Configuration management using pydantic-settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI Configuration
    openai_api_key: str = "sk-xxx"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    # SurrealDB Configuration
    surrealdb_url: str = "ws://localhost:8000/rpc"
    surrealdb_namespace: str = "markmind"
    surrealdb_database: str = "knowledge"
    surrealdb_username: str = "root"
    surrealdb_password: str = "root"

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    upload_dir: str = "./uploads"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Vector dimension
    embedding_dimension: int = 1024


settings = Settings()

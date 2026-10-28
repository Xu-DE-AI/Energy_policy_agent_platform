"""Centralised configuration with conservative defaults for local and deployed environments."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_input_usd_per_1m: float = 0.40
    openai_output_usd_per_1m: float = 1.60
    database_url: str = "sqlite:///./data/agentops.db"
    policy_docs_dir: str = "./data/policy_docs"
    max_tool_calls: int = Field(default=6, ge=1, le=20)
    max_request_budget_usd: float = Field(default=0.10, gt=0)
    app_env: str = "local"

settings = Settings()

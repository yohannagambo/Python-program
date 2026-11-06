from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_DIR = Path(__file__).resolve().parent

class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=AGENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_url: str = "http://127.0.0.1:8000"
    enrollment_key: str = ""
    device_token: str = ""
    agent_version: str = "1.0.0"
    report_interval: int = 60

settings = AgentSettings()
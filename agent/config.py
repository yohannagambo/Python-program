import platform
import socket
import uuid
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


AGENT_DIR = Path(__file__).resolve().parent


class AgentSettings(BaseSettings):
    backend_url: str = "http://127.0.0.1:8000"
    enrollment_key: str = ""
    device_token: str = ""
    agent_version: str = "1.0.0"
    report_interval: int = 60

    model_config = SettingsConfigDict(
        env_file=AGENT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = AgentSettings()


def get_device_information() -> dict:
    """Collect basic device identity information for authorized enrollment."""

    device_uid = str(uuid.getnode())

    return {
        "device_uid": device_uid,
        "hostname": socket.gethostname(),
        "operating_system": f"{platform.system()} {platform.release()}",
        "agent_version": settings.agent_version,
    }
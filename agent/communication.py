import logging
import os
import tempfile
from pathlib import Path

import httpx

from agent.config import settings, get_device_information
from agent.collector import collect_system_metrics

logger = logging.getLogger(__name__)


def get_token_file() -> Path:
    """Return a per-user location for the device credential."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        return base / "WestwoodCapitalDevelopment" / "EndpointAgent" / "device-token"

    base = Path(
        os.environ.get(
            "XDG_STATE_HOME",
            Path.home() / ".local" / "state",
        )
    )
    return base / "westwood-endpoint" / "device-token"


def load_device_token() -> str:
    token_file = get_token_file()

    try:
        token = token_file.read_text(encoding="utf-8").strip()
        return token
    except FileNotFoundError:
        return ""
    except OSError:
        logger.exception("Could not read the saved device credential.")
        return ""


def save_device_token(token: str) -> None:
    """Save the credential atomically with restrictive file permissions."""
    if not token:
        raise ValueError("Cannot save an empty device token.")

    token_file = get_token_file()
    token_file.parent.mkdir(parents=True, exist_ok=True)

    if os.name != "nt":
        token_file.parent.chmod(0o700)

    fd, temporary_name = tempfile.mkstemp(
        prefix=".device-token-",
        dir=token_file.parent,
        text=True,
    )

    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(token)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_name, token_file)

        if os.name != "nt":
            token_file.chmod(0o600)

    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


class BackendClient:
    def __init__(self):
        self.base_url = settings.backend_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=20,
            verify=True,
        )

        # Prefer the securely persisted token over the optional env value.
        self.device_token = load_device_token() or settings.device_token

    def enroll(self):
        if not settings.enrollment_key:
            raise RuntimeError("ENROLLMENT_KEY is not configured.")

        information = get_device_information()

        response = self.client.post(
            "/api/v1/devices/enroll",
            json={
                **information,
                "enrollment_key": settings.enrollment_key,
            },
        )
        response.raise_for_status()

        data = response.json()
        token = data.get("device_token")

        if not token:
            raise RuntimeError("The server did not return a device token.")

        # Persist immediately: the token is only returned once.
        save_device_token(token)
        self.device_token = token

        logger.info(
            "Device enrolled successfully. Device ID: %s",
            data.get("device_id"),
        )

        return data

    def heartbeat(self):
        if not self.device_token:
            raise RuntimeError("Device is not enrolled.")

        response = self.client.post(
            "/api/v1/devices/heartbeat",
            headers={"X-Device-Token": self.device_token},
            json={"status": "online"},
        )
        response.raise_for_status()
        return response.json()

    def submit_monitoring_report(self):
        if not self.device_token:
            raise RuntimeError("Device is not enrolled.")

        metrics = collect_system_metrics()

        response = self.client.post(
            "/api/v1/monitoring/report",
            headers={"X-Device-Token": self.device_token},
            json=metrics,
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        self.client.close()

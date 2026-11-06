import logging
import os

import httpx

from agent.config import settings, get_device_information
from agent.collector import collect_system_metrics

logger = logging.getLogger(__name__)

class BackendClient:
    def __init__(self):
        self.base_url = settings.backend_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=20,
            verify=True,
        )
        self.device_token = settings.device_token

    def enroll(self):
        if not settings.enrollment_key:
            raise RuntimeError("DEVICE_ENROLLMENT_KEY is not configured")

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
        self.device_token = data["device_token"]

        logger.info("Device enrolled successfully: %s", data["device_uid"])

        return data

    def heartbeat(self):
        if not self.device_token:
            raise RuntimeError("Device is not enrolled")

        response = self.client.post(
            "/api/v1/devices/heartbeat",
            headers={"X-Device-Token": self.device_token},
            json={"status": "online"},
        )

        response.raise_for_status()
        return response.json()

    def submit_monitoring_report(self):
        if not self.device_token:
            raise RuntimeError("Device is not enrolled")

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

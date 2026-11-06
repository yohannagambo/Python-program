from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.security import require_admin
from backend.app.services.device_service import authenticate_device
from backend.app.services.monitoring_service import (
    get_latest_reports,
    save_report,
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


class MonitoringPayload(BaseModel):
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    network_sent_bytes: int = Field(default=0, ge=0)
    network_received_bytes: int = Field(default=0, ge=0)
    details: dict = Field(default_factory=dict)


@router.post("/report")
def submit_report(
    payload: MonitoringPayload,
    x_device_token: str = Header(...),
    db: Session = Depends(get_db),
):
    device = authenticate_device(db, x_device_token)

    report = save_report(
        db=db,
        device=device,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        disk_percent=payload.disk_percent,
        network_sent_bytes=payload.network_sent_bytes,
        network_received_bytes=payload.network_received_bytes,
        details=payload.details,
    )

    return {"message": "Monitoring report received", "report_id": report.id}


@router.get("/reports")
def reports(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    limit = max(1, min(limit, 500))
    return get_latest_reports(db, limit)

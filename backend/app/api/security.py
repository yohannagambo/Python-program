from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AuditLog, User
from backend.app.security import require_admin
from backend.app.services.audit_service import record_event
from backend.app.services.device_service import authenticate_device

router = APIRouter(prefix="/security", tags=["Security"])


class SecurityEventPayload(BaseModel):
    event_name: str = Field(min_length=2, max_length=100)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    details: str = Field(default="", max_length=3000)


@router.post("/events")
def report_security_event(
    payload: SecurityEventPayload,
    x_device_token: str = Header(...),
    db: Session = Depends(get_db),
):
    device = authenticate_device(db, x_device_token)

    event = record_event(
        db,
        actor=f"device:{device.device_uid}",
        action=payload.event_name,
        resource=f"device:{device.id}",
        outcome=payload.severity,
        details=payload.details,
    )

    return {"message": "Security event recorded", "event_id": event.id}


@router.get("/events")
def get_security_events(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    limit = max(1, min(limit, 500))

    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

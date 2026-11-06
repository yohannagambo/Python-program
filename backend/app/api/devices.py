import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import Device, User
from backend.app.security import require_admin
from backend.app.services.audit_service import record_event
from backend.app.services.device_service import (
    authenticate_device,
    enroll_device,
    list_devices,
    revoke_device,
)

router = APIRouter(prefix="/devices", tags=["Devices"])


class EnrollmentRequest(BaseModel):
    enrollment_key: str
    device_uid: str = Field(min_length=3, max_length=100)
    hostname: str = Field(min_length=1, max_length=255)
    operating_system: str = Field(min_length=1, max_length=255)
    agent_version: str = Field(default="1.0.0", max_length=50)


class HeartbeatRequest(BaseModel):
    status: str = "online"


@router.post("/enroll")
def enroll(payload: EnrollmentRequest, db: Session = Depends(get_db)):
    if not hmac.compare_digest(
        payload.enrollment_key, settings.device_enrollment_key
    ):
        raise HTTPException(status_code=403, detail="Invalid enrollment key")

    device, raw_token = enroll_device(
        db,
        payload.device_uid,
        payload.hostname,
        payload.operating_system,
        payload.agent_version,
    )

    record_event(
        db,
        actor=f"device:{device.device_uid}",
        action="device_enrolled",
        resource=str(device.id),
    )

    return {
        "device_id": device.id,
        "device_uid": device.device_uid,
        "device_token": raw_token,
        "message": "Store this device token securely. It will not be shown again.",
    }


@router.post("/heartbeat")
def heartbeat(
    payload: HeartbeatRequest,
    x_device_token: str = Header(...),
    db: Session = Depends(get_db),
):
    device = authenticate_device(db, x_device_token)

    return {
        "device_id": device.id,
        "status": "online",
        "message": "Heartbeat received",
    }


@router.get("")
def devices(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    return list_devices(db)


@router.post("/{device_id}/revoke")
def revoke(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    device = revoke_device(db, device_id)

    record_event(
        db,
        actor=user.email,
        action="device_revoked",
        resource=str(device.id),
    )

    return {"message": "Device access revoked", "device_id": device.id}

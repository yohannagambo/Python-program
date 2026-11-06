import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models import Device
from backend.app.security import hash_device_token


def enroll_device(
    db: Session,
    device_uid: str,
    hostname: str,
    operating_system: str,
    agent_version: str,
) -> tuple[Device, str]:
    existing = db.query(Device).filter(
        Device.device_uid == device_uid
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Device already enrolled")

    raw_token = secrets.token_urlsafe(48)

    device = Device(
        device_uid=device_uid,
        hostname=hostname,
        operating_system=operating_system,
        agent_version=agent_version,
        token_hash=hash_device_token(raw_token),
        is_active=True,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device, raw_token


def authenticate_device(db: Session, raw_token: str) -> Device:
    token_hash = hash_device_token(raw_token)

    device = db.query(Device).filter(
        Device.token_hash == token_hash,
        Device.is_active.is_(True),
    ).first()

    if not device:
        raise HTTPException(status_code=401, detail="Invalid device credential")

    device.last_seen = datetime.now(timezone.utc)
    db.commit()
    return device


def list_devices(db: Session) -> list[Device]:
    return db.query(Device).order_by(Device.created_at.desc()).all()


def revoke_device(db: Session, device_id: int) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.is_active = False
    db.commit()
    db.refresh(device)
    return device

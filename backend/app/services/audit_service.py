from sqlalchemy.orm import Session

from backend.app.models import AuditLog


def record_event(
    db: Session,
    actor: str,
    action: str,
    resource: str = "",
    outcome: str = "success",
    source_ip: str = "",
    details: str = "",
) -> AuditLog:
    event = AuditLog(
        actor=actor,
        action=action,
        resource=resource,
        outcome=outcome,
        source_ip=source_ip,
        details=details[:4000],
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event

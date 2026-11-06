from sqlalchemy.orm import Session

from backend.app.models import Device, MonitoringReport


def save_report(
    db: Session,
    device: Device,
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
    network_sent_bytes: int = 0,
    network_received_bytes: int = 0,
    details: dict | None = None,
) -> MonitoringReport:
    report = MonitoringReport(
        device_id=device.id,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        network_sent_bytes=network_sent_bytes,
        network_received_bytes=network_received_bytes,
        details=details or {},
    )

    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_latest_reports(db: Session, limit: int = 100):
    return (
        db.query(MonitoringReport)
        .order_by(MonitoringReport.recorded_at.desc())
        .limit(limit)
        .all()
    )

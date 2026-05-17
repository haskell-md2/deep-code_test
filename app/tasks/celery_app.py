import uuid
import statistics
from datetime import datetime
from typing import Optional

from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings

celery_app = Celery(
    "device_analytics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)


def _compute_stats(values: list[float]) -> dict:
    if not values:
        return {"min": None, "max": None, "count": 0, "sum": None, "median": None}
    return {
        "min": min(values),
        "max": max(values),
        "count": len(values),
        "sum": sum(values),
        "median": statistics.median(values),
    }


@celery_app.task(bind=True, name="tasks.compute_device_analytics")
def compute_device_analytics_task(
    self,
    device_id: str,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
) -> dict:

    from app.models.models import Measurement

    engine = create_engine(settings.DATABASE_URL_SYNC)

    with Session(engine) as db:
        query = select(Measurement).where(Measurement.device_id == uuid.UUID(device_id))

        if period_from:
            dt_from = datetime.fromisoformat(period_from)
            query = query.where(Measurement.timestamp >= dt_from)
        if period_to:
            dt_to = datetime.fromisoformat(period_to)
            query = query.where(Measurement.timestamp <= dt_to)

        result = db.execute(query)
        measurements = result.scalars().all()

    x_vals = [m.x for m in measurements]
    y_vals = [m.y for m in measurements]
    z_vals = [m.z for m in measurements]

    return {
        "device_id": device_id,
        "period_from": period_from,
        "period_to": period_to,
        "x": _compute_stats(x_vals),
        "y": _compute_stats(y_vals),
        "z": _compute_stats(z_vals),
    }


@celery_app.task(bind=True, name="tasks.compute_user_analytics")
def compute_user_analytics_task(
    self,
    user_id: str,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
) -> dict:

    from app.models.models import Measurement, Device

    engine = create_engine(settings.DATABASE_URL_SYNC)

    with Session(engine) as db:
        devices_result = db.execute(
            select(Device).where(Device.owner_id == uuid.UUID(user_id))
        )
        devices = devices_result.scalars().all()

        per_device = []
        all_x, all_y, all_z = [], [], []

        for device in devices:
            query = select(Measurement).where(Measurement.device_id == device.id)
            if period_from:
                query = query.where(Measurement.timestamp >= datetime.fromisoformat(period_from))
            if period_to:
                query = query.where(Measurement.timestamp <= datetime.fromisoformat(period_to))

            result = db.execute(query)
            measurements = result.scalars().all()

            x_vals = [m.x for m in measurements]
            y_vals = [m.y for m in measurements]
            z_vals = [m.z for m in measurements]

            all_x.extend(x_vals)
            all_y.extend(y_vals)
            all_z.extend(z_vals)

            per_device.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "analytics": {
                    "x": _compute_stats(x_vals),
                    "y": _compute_stats(y_vals),
                    "z": _compute_stats(z_vals),
                },
            })

    return {
        "user_id": user_id,
        "period_from": period_from,
        "period_to": period_to,
        "aggregated": {
            "x": _compute_stats(all_x),
            "y": _compute_stats(all_y),
            "z": _compute_stats(all_z),
        },
        "per_device": per_device,
    }

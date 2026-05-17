import uuid
import statistics
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Measurement, Device, User
from app.schemas.schemas import AxisStats, AnalyticsResponse, DeviceAnalytics, UserAnalyticsResponse


def _compute_stats(values: list[float]) -> AxisStats:
    if not values:
        return AxisStats(min=None, max=None, count=0, sum=None, median=None)
    return AxisStats(
        min=min(values),
        max=max(values),
        count=len(values),
        sum=sum(values),
        median=statistics.median(values),
    )


def _aggregate_stats(stats_list: list[AxisStats]) -> AxisStats:

    all_values_proxy: list[float] = []
    total_count = sum(s.count for s in stats_list)
    if total_count == 0:
        return AxisStats()

    mins = [s.min for s in stats_list if s.min is not None]
    maxs = [s.max for s in stats_list if s.max is not None]
    sums = [s.sum for s in stats_list if s.sum is not None]
    medians = [s.median for s in stats_list if s.median is not None]

    return AxisStats(
        min=min(mins) if mins else None,
        max=max(maxs) if maxs else None,
        count=total_count,
        sum=sum(sums) if sums else None,
        median=statistics.median(medians) if medians else None,
    )


async def get_measurements_for_device(
    db: AsyncSession,
    device_id: uuid.UUID,
    period_from: Optional[datetime] = None,
    period_to: Optional[datetime] = None,
) -> list[Measurement]:
    query = select(Measurement).where(Measurement.device_id == device_id)
    if period_from:
        query = query.where(Measurement.timestamp >= period_from)
    if period_to:
        query = query.where(Measurement.timestamp <= period_to)
    result = await db.execute(query)
    return result.scalars().all()


async def compute_device_analytics(
    db: AsyncSession,
    device_id: uuid.UUID,
    period_from: Optional[datetime] = None,
    period_to: Optional[datetime] = None,
) -> AnalyticsResponse:
    measurements = await get_measurements_for_device(db, device_id, period_from, period_to)

    x_vals = [m.x for m in measurements]
    y_vals = [m.y for m in measurements]
    z_vals = [m.z for m in measurements]

    return AnalyticsResponse(
        device_id=device_id,
        period_from=period_from,
        period_to=period_to,
        x=_compute_stats(x_vals),
        y=_compute_stats(y_vals),
        z=_compute_stats(z_vals),
    )


async def compute_user_analytics(
    db: AsyncSession,
    user_id: uuid.UUID,
    period_from: Optional[datetime] = None,
    period_to: Optional[datetime] = None,
) -> UserAnalyticsResponse:

    devices_result = await db.execute(
        select(Device).where(Device.owner_id == user_id)
    )
    devices = devices_result.scalars().all()

    per_device: list[DeviceAnalytics] = []
    all_x, all_y, all_z = [], [], []

    for device in devices:
        measurements = await get_measurements_for_device(
            db, device.id, period_from, period_to
        )
        x_vals = [m.x for m in measurements]
        y_vals = [m.y for m in measurements]
        z_vals = [m.z for m in measurements]

        all_x.extend(x_vals)
        all_y.extend(y_vals)
        all_z.extend(z_vals)

        device_analytics = AnalyticsResponse(
            device_id=device.id,
            period_from=period_from,
            period_to=period_to,
            x=_compute_stats(x_vals),
            y=_compute_stats(y_vals),
            z=_compute_stats(z_vals),
        )
        per_device.append(
            DeviceAnalytics(
                device_id=device.id,
                device_name=device.name,
                analytics=device_analytics,
            )
        )

    aggregated = AnalyticsResponse(
        period_from=period_from,
        period_to=period_to,
        x=_compute_stats(all_x),
        y=_compute_stats(all_y),
        z=_compute_stats(all_z),
    )

    return UserAnalyticsResponse(
        user_id=user_id,
        period_from=period_from,
        period_to=period_to,
        aggregated=aggregated,
        per_device=per_device,
    )

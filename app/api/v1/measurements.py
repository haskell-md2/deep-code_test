import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Measurement, Device
from app.schemas.schemas import MeasurementCreate, MeasurementResponse

router = APIRouter()


@router.post(
    "/{device_id}/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_measurement(
    device_id: uuid.UUID,
    payload: MeasurementCreate,
    db: AsyncSession = Depends(get_db),
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    measurement = Measurement(
        device_id=device_id,
        x=payload.x,
        y=payload.y,
        z=payload.z,
    )
    db.add(measurement)
    await db.flush()
    await db.refresh(measurement)
    return measurement


@router.get(
    "/{device_id}/measurements",
    response_model=list[MeasurementResponse],
)
async def list_measurements(
    device_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    result = await db.execute(
        select(Measurement)
        .where(Measurement.device_id == device_id)
        .order_by(Measurement.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

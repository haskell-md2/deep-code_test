import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Device, User
from app.schemas.schemas import DeviceCreate, DeviceResponse

router = APIRouter()


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    if payload.owner_id:
        owner = await db.get(User, payload.owner_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Owner user not found")

    device = Device(
        name=payload.name,
        description=payload.description,
        owner_id=payload.owner_id,
    )
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Device).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

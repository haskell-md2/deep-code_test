import uuid
from datetime import datetime
from typing import Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Device, User
from app.schemas.schemas import (
    AnalyticsResponse,
    AnalyticsTaskResponse,
    TaskResultResponse,
    UserAnalyticsResponse,
)
from app.services.analytics import compute_device_analytics, compute_user_analytics
from app.tasks.celery_app import (
    compute_device_analytics_task,
    compute_user_analytics_task,
)

router = APIRouter()


# Synchronous analytics

@router.get("/devices/{device_id}", response_model=AnalyticsResponse)
async def get_device_analytics(
    device_id: uuid.UUID,
    period_from: Optional[datetime] = Query(None),
    period_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return await compute_device_analytics(db, device_id, period_from, period_to)


@router.get("/users/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: uuid.UUID,
    period_from: Optional[datetime] = Query(None),
    period_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await compute_user_analytics(db, user_id, period_from, period_to)


# Asynchronous analytics

@router.post("/devices/{device_id}/async", response_model=AnalyticsTaskResponse)
async def get_device_analytics_async(
    device_id: uuid.UUID,
    period_from: Optional[datetime] = Query(None),
    period_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):

    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    task = compute_device_analytics_task.delay(
        device_id=str(device_id),
        period_from=period_from.isoformat() if period_from else None,
        period_to=period_to.isoformat() if period_to else None,
    )
    return AnalyticsTaskResponse(
        task_id=task.id,
        status="queued",
        message="Analytics task has been queued. Use /analytics/tasks/{task_id} to get result.",
    )


@router.post("/users/{user_id}/async", response_model=AnalyticsTaskResponse)
async def get_user_analytics_async(
    user_id: uuid.UUID,
    period_from: Optional[datetime] = Query(None),
    period_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    task = compute_user_analytics_task.delay(
        user_id=str(user_id),
        period_from=period_from.isoformat() if period_from else None,
        period_to=period_to.isoformat() if period_to else None,
    )
    return AnalyticsTaskResponse(
        task_id=task.id,
        status="queued",
        message="Analytics task has been queued. Use /analytics/tasks/{task_id} to get result.",
    )


@router.get("/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_result(task_id: str):

    result = AsyncResult(task_id)
    status = result.status

    if status == "PENDING":
        return TaskResultResponse(task_id=task_id, status="pending")
    elif status == "STARTED":
        return TaskResultResponse(task_id=task_id, status="running")
    elif status == "SUCCESS":
        raw = result.result

        analytics = _dict_to_analytics_response(raw)
        return TaskResultResponse(task_id=task_id, status="success", result=analytics)
    elif status == "FAILURE":
        return TaskResultResponse(
            task_id=task_id, status="failed", error=str(result.result)
        )
    return TaskResultResponse(task_id=task_id, status=status.lower())


def _dict_to_analytics_response(raw: dict) -> AnalyticsResponse:
    from app.schemas.schemas import AxisStats

    def to_axis(d: dict) -> AxisStats:
        return AxisStats(**d)

    return AnalyticsResponse(
        device_id=raw.get("device_id"),
        period_from=raw.get("period_from"),
        period_to=raw.get("period_to"),
        x=to_axis(raw["x"]),
        y=to_axis(raw["y"]),
        z=to_axis(raw["z"]),
    )

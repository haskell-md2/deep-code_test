import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Measurement

class MeasurementCreate(BaseModel):
    x: float
    y: float
    z: float


class MeasurementResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    x: float
    y: float
    z: float
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Analytics

class AxisStats(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    count: int = 0
    sum: Optional[float] = None
    median: Optional[float] = None


class AnalyticsResponse(BaseModel):
    device_id: Optional[uuid.UUID] = None
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None
    x: AxisStats
    y: AxisStats
    z: AxisStats


class AnalyticsTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[AnalyticsResponse] = None
    error: Optional[str] = None


# Device

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    owner_id: Optional[uuid.UUID] = None


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


# User

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithDevicesResponse(UserResponse):
    devices: list[DeviceResponse] = []


# User Analytics

class DeviceAnalytics(BaseModel):
    device_id: uuid.UUID
    device_name: str
    analytics: AnalyticsResponse


class UserAnalyticsResponse(BaseModel):
    user_id: uuid.UUID
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None
    aggregated: AnalyticsResponse
    per_device: list[DeviceAnalytics]

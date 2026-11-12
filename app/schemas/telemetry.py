from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TelemetryCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    temperature: float = Field(ge=-100, le=200)
    humidity: float = Field(ge=0, le=100)
    pressure: float = Field(ge=0, le=2000)


class TelemetryRead(TelemetryCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

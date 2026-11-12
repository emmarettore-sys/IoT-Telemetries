from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.telemetry import Telemetry
from app.schemas.telemetry import TelemetryCreate, TelemetryRead

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", response_model=TelemetryRead, status_code=status.HTTP_201_CREATED)
def create_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)) -> Telemetry:
    record = Telemetry(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[TelemetryRead])
def list_telemetry(
    device_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Telemetry]:
    statement = select(Telemetry).order_by(Telemetry.timestamp.desc()).limit(limit)
    if device_id:
        statement = statement.where(Telemetry.device_id == device_id)
    return list(db.scalars(statement))


@router.get("/latest", response_model=list[TelemetryRead])
def latest_telemetry(db: Session = Depends(get_db)) -> list[Telemetry]:
    statement = select(Telemetry).order_by(Telemetry.timestamp.desc()).limit(20)
    return list(db.scalars(statement))

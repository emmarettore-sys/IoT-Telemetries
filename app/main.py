from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.telemetry import router as telemetry_router
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="IoT Telemetry API", version="0.1.0", lifespan=lifespan)
app.include_router(telemetry_router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}

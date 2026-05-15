from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.api.v1 import api_router
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    yield

app = FastAPI(
    title="API Организационной структуры",
    description="REST API для управления организационной иерархией отделов и сотрудников.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)

@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
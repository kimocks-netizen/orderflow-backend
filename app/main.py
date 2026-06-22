from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.migrations import run_migrations
from app.errors.exceptions import AppError
from app.middleware.error_handler import app_error_handler
from app.routes import auth, orders, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations(get_settings().database_path)
    yield


app = FastAPI(
    title="OrderFlow API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(auth.router,      prefix="/api")
app.include_router(orders.router,    prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}

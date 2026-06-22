import sqlite3
from fastapi import APIRouter, Depends

from app.database.connection import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    return auth_service.authenticate(db, body.email, body.password)

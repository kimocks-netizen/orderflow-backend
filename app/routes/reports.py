import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database.connection import get_db
from app.core.security import get_current_user
from app.schemas.reports import ReportsSummary
from app.services import reports_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary", response_model=ReportsSummary)
def get_summary(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return reports_service.get_summary(db, date_from=date_from, date_to=date_to)

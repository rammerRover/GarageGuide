import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.database import check_database


router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def database_health(settings: Settings = Depends(get_settings)):
    try:
        ready = check_database(settings)
    except psycopg.Error:
        # Avoid logging driver messages, which can contain connection details.
        logger.warning("Database health check could not connect or query")
        raise HTTPException(503, "Database unavailable") from None
    if not ready:
        logger.warning("Database health check found an incomplete schema")
        raise HTTPException(503, "Database schema unavailable")
    return {"status": "ok", "database": "connected", "schema": "ready"}

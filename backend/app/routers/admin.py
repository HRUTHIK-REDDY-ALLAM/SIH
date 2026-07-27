from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import SessionLocal, get_db
from ..seed_data import reset_schema, seed

router = APIRouter(tags=["admin"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "tradebridge-api", "db": "connected"}


@router.post("/admin/reset")
def reset_demo():
    """Rebuild the schema and reseed the three demo scenarios.

    Demo convenience — deliberately unauthenticated for judge-friendly resets.
    In production this endpoint would not exist.
    """
    reset_schema()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    return {"ok": True, "detail": "Database reset and reseeded. All sessions were signed out."}

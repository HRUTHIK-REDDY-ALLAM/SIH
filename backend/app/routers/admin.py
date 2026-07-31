from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..cache import bump_auth_epoch, get_cache
from ..config import DATABASE_URL
from ..db import SessionLocal, get_db
from ..pipeline.retriever import get_retriever
from ..seed_data import reset_schema, seed

router = APIRouter(tags=["admin"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "vittsetu-api",
        "db": "postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite",
        "cache": get_cache().name,
        "regulatory_passages": len(getattr(get_retriever(), "passages", [])),
    }


@router.post("/admin/reset")
def reset_demo():
    """Rebuild the schema, reseed the three demo scenarios, and revoke every
    outstanding session (JWT auth-epoch bump).

    Demo convenience — deliberately unauthenticated for judge-friendly resets.
    In production this endpoint would not exist.
    """
    reset_schema()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    bump_auth_epoch()
    return {"ok": True, "detail": "Database reset and reseeded. All sessions were signed out."}

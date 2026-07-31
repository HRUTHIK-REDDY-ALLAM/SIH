from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .cache import get_cache
from .config import APP_NAME, APP_TAGLINE
from .db import Base, SessionLocal, engine
from .models import User
from .pipeline.retriever import get_retriever
from .routers import admin, auth_routes, consents, deals, financier, invoices
from .seed_data import seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.execute(select(User)).scalars().first() is None:
            seed(db)
            print("Seeded demo data (exporter: demo@saanvi.in / financier: fin@nexacapital.in — password demo1234)")
    finally:
        db.close()
    retriever = get_retriever()  # warm the BM25 index over the regulatory corpus
    print(f"{APP_NAME} up — cache: {get_cache().name} · "
          f"regulatory corpus: {len(retriever.passages)} passages indexed")
    yield


app = FastAPI(
    title=f"{APP_NAME} API",
    description=f"{APP_TAGLINE}. Decisioning API — FastAPI + LangGraph + SQLAlchemy "
                "(PostgreSQL via Docker Compose, SQLite for zero-setup local runs) with a Redis "
                "cache/session layer. External data sources are mock adapters over synthetic data; "
                "the lien registry, invoice fingerprinting, trade-graph cycle detection, consent "
                "enforcement, Shapley score attribution, RAG-grounded compliance and the audit log "
                "are real.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth_routes.router, invoices.router, consents.router,
               deals.router, financier.router, admin.router):
    app.include_router(router, prefix="/api")

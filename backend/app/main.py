from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import User
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
    yield


app = FastAPI(
    title="TradeBridge AI API",
    description="Underwriting decisioning API — FastAPI + LangGraph + SQLite. "
                "External data sources are mock adapters over synthetic data; "
                "the lien registry, consent enforcement, scoring and audit log are real.",
    version="1.0.0",
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

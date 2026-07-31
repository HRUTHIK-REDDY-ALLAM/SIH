import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import (create_access_token, get_current_user, hash_password,
                    verify_password)
from ..db import get_db
from ..models import Msme, User

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(Credentials):
    business_name: str = Field(default="New Exporter", max_length=255)
    gstin: str = Field(default="", max_length=15)


def _user_payload(user: User) -> dict:
    msme = user.msme
    return {
        "email": user.email,
        "role": user.role,
        "name": msme.short_name if msme else "Nexa Capital",
        "msme": None if msme is None else {
            "name": msme.name, "short": msme.short_name, "city": msme.city,
            "gstin": msme.gstin, "iec": msme.iec, "sector": msme.sector,
            "bank": msme.bank_account, "kyc": msme.kyc_status,
        },
    }


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not EMAIL_RE.match(body.email):
        raise HTTPException(status_code=422, detail="Invalid email address")
    if db.execute(select(User).where(User.email == body.email.lower())).scalars().first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    msme = Msme(name=body.business_name, short_name=body.business_name[:40],
                gstin=body.gstin or f"NEW{abs(hash(body.email)) % 10 ** 12}",
                kyc_status="pending", onboarding_status="onboarding")
    db.add(msme)
    db.flush()
    user = User(email=body.email.lower(), password_hash=hash_password(body.password),
                role="msme", msme_id=msme.id)
    db.add(user)
    db.commit()
    return {"token": create_access_token(user), "user": _user_payload(user)}


@router.post("/login")
def login(body: Credentials, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.lower())).scalars().first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": create_access_token(user), "user": _user_payload(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_payload(user)

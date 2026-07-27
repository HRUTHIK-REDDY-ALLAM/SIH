import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import Token, User


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(candidate, digest)


def issue_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(Token(token=token, user_id=user.id))
    db.commit()
    return token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    row = db.get(Token, header.removeprefix("Bearer ").strip())
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_msme(user: User = Depends(get_current_user)) -> User:
    if user.role != "msme" or user.msme_id is None:
        raise HTTPException(status_code=403, detail="Exporter account required")
    return user


def require_financier(user: User = Depends(get_current_user)) -> User:
    if user.role != "financier":
        raise HTTPException(status_code=403, detail="Financier account required")
    return user

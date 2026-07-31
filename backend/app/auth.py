"""OAuth2-style bearer auth with JWTs (HS256).

Tokens are stateless; revocation works through the cache-layer auth epoch —
every token carries the epoch it was issued under, and a demo reset bumps the
epoch, invalidating all outstanding sessions at once.
"""
import hashlib
import hmac
import secrets as py_secrets
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .cache import auth_epoch
from .db import get_db, now_utc
from .models import User
from .secrets import get_secrets_provider

JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 12

# PRODUCTION NOTE: set VS_JWT_SECRET from a real secrets manager; the dev
# default below exists so the prototype runs with zero configuration.
_DEV_SECRET = "vittsetu-dev-secret-do-not-use-in-production"


def _jwt_secret() -> str:
    return get_secrets_provider().get("VS_JWT_SECRET", _DEV_SECRET)


def hash_password(password: str) -> str:
    salt = py_secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(candidate, digest)


def create_access_token(user: User) -> str:
    now = now_utc()
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "epoch": auth_epoch(),
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = header.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if int(payload.get("epoch", -1)) != auth_epoch():
        raise HTTPException(status_code=401, detail="Session revoked — sign in again")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return user


def require_msme(user: User = Depends(get_current_user)) -> User:
    if user.role != "msme" or user.msme_id is None:
        raise HTTPException(status_code=403, detail="Exporter account required")
    return user


def require_financier(user: User = Depends(get_current_user)) -> User:
    if user.role != "financier":
        raise HTTPException(status_code=403, detail="Financier account required")
    return user

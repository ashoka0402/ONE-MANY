"""Argon2 password hashes and signed, short-lived access tokens."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher, exceptions
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from one_many_api.database import get_db
from one_many_api.models import User

_password_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)
_issuer = "one-many-api"


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def password_matches(hashed: str, candidate: str) -> bool:
    try:
        return _password_hasher.verify(hashed, candidate)
    except (exceptions.VerificationError, exceptions.InvalidHashError):
        return False


def _get_secret(request: Request) -> str:
    secret = request.app.state.settings.auth_secret
    if secret is None:
        raise HTTPException(503, "Authentication is not configured")
    return secret.get_secret_value()


def issue_token(user: User, request: Request) -> tuple[str, int]:
    minutes = request.app.state.settings.access_token_minutes
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "iss": _issuer,
        "aud": _issuer,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "type": "access",
    }
    return jwt.encode(payload, _get_secret(request), algorithm="HS256"), minutes * 60


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_secret(request),
            algorithms=["HS256"],
            audience=_issuer,
            issuer=_issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
        )
        if payload.get("type") != "access":
            raise ValueError("Unexpected token type")
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(
            401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
        ) from None
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return user

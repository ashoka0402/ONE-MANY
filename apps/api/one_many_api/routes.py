"""User-owned need APIs; paid checkout and matching deliberately deferred."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from one_many_api.auth import get_current_user, hash_password, issue_token, password_matches
from one_many_api.database import get_db
from one_many_api.models import Need, User
from one_many_api.schemas import (
    AuthOut,
    LoginIn,
    NeedCreate,
    NeedOut,
    NeedsPage,
    NeedUpdate,
    RegisterIn,
    UserOut,
)

router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if request.app.state.settings.auth_secret is None:
        raise HTTPException(503, "Authentication is not configured")
    user = User(
        email=str(payload.email).lower(),
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists") from None
    db.refresh(user)
    token, seconds = issue_token(user, request)
    return AuthOut(access_token=token, expires_in=seconds, user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=AuthOut, tags=["auth"])
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    if request.app.state.settings.auth_secret is None:
        raise HTTPException(503, "Authentication is not configured")
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not password_matches(user.password_hash, payload.password):
        raise HTTPException(401, "Invalid email or password")
    token, seconds = issue_token(user, request)
    return AuthOut(access_token=token, expires_in=seconds, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/needs", response_model=NeedOut, status_code=status.HTTP_201_CREATED, tags=["needs"])
def create_need(
    payload: NeedCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = Need(owner_id=user.id, **payload.model_dump())
    db.add(need)
    db.commit()
    db.refresh(need)
    return need


@router.get("/needs", response_model=NeedsPage, tags=["needs"])
def list_needs(
    status_filter: str | None = Query(default=None, alias="status", pattern="^(open|archived)$"),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conditions = [Need.owner_id == user.id]
    if status_filter is not None:
        conditions.append(Need.status == status_filter)
    total = db.scalar(select(func.count(Need.id)).where(*conditions)) or 0
    items = db.scalars(
        select(Need)
        .where(*conditions)
        .order_by(Need.created_at.desc(), Need.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return NeedsPage(
        items=[NeedOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def _owned_need(db: Session, user: User, need_id: UUID) -> Need:
    need = db.scalar(select(Need).where(Need.id == need_id, Need.owner_id == user.id))
    if need is None:
        raise HTTPException(404, "Need not found")
    return need


@router.get("/needs/{need_id}", response_model=NeedOut, tags=["needs"])
def read_need(
    need_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _owned_need(db, user, need_id)


@router.patch("/needs/{need_id}", response_model=NeedOut, tags=["needs"])
def update_need(
    need_id: UUID,
    payload: NeedUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = _owned_need(db, user, need_id)
    updates = payload.model_dump(exclude_unset=True)
    proposed_from = updates.get("needed_from", need.needed_from)
    proposed_until = updates.get("needed_until", need.needed_until)
    if proposed_from and proposed_until and proposed_until < proposed_from:
        raise HTTPException(422, "needed_until cannot be before needed_from")
    for field, value in updates.items():
        setattr(need, field, value)
    db.commit()
    db.refresh(need)
    return need


@router.delete("/needs/{need_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["needs"])
def archive_need(
    need_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    need = _owned_need(db, user, need_id)
    need.status = "archived"
    db.commit()

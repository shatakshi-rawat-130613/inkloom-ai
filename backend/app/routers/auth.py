"""Authentication, session management and organisation membership endpoints."""

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.auth.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.enums import UserRole
from app.models import Organisation, User
from app.schemas import AuthResponse, MemberCreateRequest, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_to_response(user: User, org_name: str | None = None) -> UserResponse:
    return UserResponse(
        id=user.id,
        organisation_id=user.organisation_id,
        organisation_name=org_name or (user.organisation.name if user.organisation else ""),
        display_name=user.display_name,
        email=user.email or "",
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return cleaned[:50] or "org"


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    """Register a new organisation and its initial Brand Manager (Admin)."""
    email_clean = payload.email.lower().strip()
    existing_user = db.scalar(select(User).where(User.email == email_clean))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    base_slug = _slugify(payload.organisation_name)
    slug = base_slug
    suffix = 1
    while db.scalar(select(Organisation).where(Organisation.slug == slug)) is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    org = Organisation(name=payload.organisation_name.strip(), slug=slug)
    db.add(org)
    db.flush()

    user = User(
        organisation_id=org.id,
        display_name=payload.display_name.strip(),
        email=email_clean,
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,  # Initial registrant is always Brand Manager
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    token = create_access_token(
        {
            "sub": str(user.id),
            "org_id": str(org.id),
            "role": user.role.value,
            "email": user.email,
        }
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_user_to_response(user, org.name),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
    """Authenticate with email and password and return a JWT access token."""
    email_clean = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email_clean))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "org_id": str(user.organisation_id),
            "role": user.role.value,
            "email": user.email,
        }
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_user_to_response(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the profile and permissions of the currently authenticated user."""
    return _user_to_response(current_user)


@router.get("/members", response_model=list[UserResponse])
def list_members(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    """List all team members belonging to the caller's organisation."""
    users = db.scalars(
        select(User)
        .where(User.organisation_id == current_user.organisation_id)
        .order_by(User.created_at)
    ).all()
    org_name = current_user.organisation.name if current_user.organisation else ""
    return [_user_to_response(u, org_name) for u in users]


@router.post("/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_member(
    payload: MemberCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Invite/create a team member in the caller's organisation. Requires Brand Manager (ADMIN)."""
    email_clean = payload.email.lower().strip()
    existing_user = db.scalar(select(User).where(User.email == email_clean))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        organisation_id=current_user.organisation_id,
        display_name=payload.display_name.strip(),
        email=email_clean,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    org_name = current_user.organisation.name if current_user.organisation else ""
    return _user_to_response(user, org_name)

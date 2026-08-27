"""
PYRO-SENTRY Auth Router.

Endpoints: POST /auth/register, POST /auth/login, POST /auth/refresh, GET /auth/me, POST /auth/logout
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import User, RefreshToken, AuditLog, UserRole
from app.auth.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenRefreshRequest,
    LogoutRequest, TokenResponse, UserResponse, MessageResponse,
)
from app.auth.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, hash_token,
    get_current_user,
)
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _write_audit_log(
    db: AsyncSession, action: str, user_id: str = None,
    ip_address: str = None, details: str = None,
) -> None:
    """Write an entry to the audit_logs table."""
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        details=details,
    )
    db.add(log)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register New User")
async def register(body: UserRegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    # Validate role
    role_str = (body.role or "VIEWER").upper()
    try:
        role = UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{body.role}'. Must be one of: {[r.value for r in UserRole]}",
        )

    # Check for duplicates
    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' is already registered",
        )

    existing_user = await db.execute(select(User).where(User.username == body.username))
    if existing_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    await _write_audit_log(db, "REGISTER", user.id, _get_client_ip(request), f"New user: {body.username}")
    await db.commit()
    await db.refresh(user)
    return UserResponse(
        id=user.id, email=user.email, username=user.username,
        role=user.role.value, is_active=user.is_active, created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(body: UserLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive JWT access + refresh tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalars().first()

    if not user or not verify_password(body.password, user.hashed_password):
        await _write_audit_log(
            db, "LOGIN_FAILED", None, _get_client_ip(request),
            f"Failed login attempt for email: {body.email}",
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Generate tokens
    access_token = create_access_token({"sub": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.id})

    # Store hashed refresh token
    decoded_refresh = decode_token(refresh_token)
    rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.fromtimestamp(decoded_refresh["exp"], tz=timezone.utc),
        revoked=False,
    )
    db.add(rt)

    await _write_audit_log(db, "LOGIN_SUCCESS", user.id, _get_client_ip(request))
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh(body: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired")

    # Check if token is revoked
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored_token = result.scalars().first()
    if not stored_token or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or unknown")

    # Revoke old token
    stored_token.revoked = True

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Issue new pair
    new_access = create_access_token({"sub": user.id, "role": user.role.value})
    new_refresh = create_refresh_token({"sub": user.id})

    decoded_new = decode_token(new_refresh)
    new_rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        expires_at=datetime.fromtimestamp(decoded_new["exp"], tz=timezone.utc),
        revoked=False,
    )
    db.add(new_rt)
    await db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse, summary="Get Current User Profile")
async def me(current_user: User = Depends(get_current_user)):
    """Retrieve the authenticated user's profile."""
    return UserResponse(
        id=current_user.id, email=current_user.email, username=current_user.username,
        role=current_user.role.value, is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/logout", response_model=MessageResponse, summary="Logout / Revoke Refresh Token")
async def logout(
    body: LogoutRequest, request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the given refresh token (logout)."""
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored_token = result.scalars().first()
    if stored_token:
        stored_token.revoked = True

    await _write_audit_log(db, "LOGOUT", current_user.id, _get_client_ip(request))
    await db.commit()

    return MessageResponse(message="Successfully logged out")

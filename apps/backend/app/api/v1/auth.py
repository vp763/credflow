# CredFlow Backend - Auth Endpoints

from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db, get_tenant_db
from app.core.security import (
    create_token_pair,
    decode_token,
    verify_password,
    get_password_hash,
    keycloak_client,
)
from app.core.tenant import get_current_tenant_id, get_current_user_id, get_current_permissions
from app.models import User, RefreshToken, Invitation, Tenant
from app.models.base import TenantMixin

router = APIRouter()


# Request/Response Models
class RegisterRequest(BaseModel):
    tenant_name: str
    subdomain: str
    admin_email: EmailStr
    admin_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    permissions: list[str]
    tenant: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class InviteAcceptRequest(BaseModel):
    password: str
    name: str


class OIDCCallbackRequest(BaseModel):
    code: str
    state: str


# Helper: Get permissions for role
ROLE_PERMISSIONS = {
    "super_admin": ["*"],
    "tenant_admin": [
        "invoices:read", "invoices:write", "invoices:delete",
        "customers:read", "customers:write",
        "payments:read", "payments:write",
        "templates:read", "templates:write",
        "reminders:send",
        "tasks:read", "tasks:write",
        "disputes:read", "disputes:write",
        "dashboard:read", "reports:read",
        "settings:read", "settings:write",
        "users:invite", "users:read", "users:update_role", "users:remove",
        "agents:register", "agents:read", "agents:delete",
    ],
    "analyst": [
        "invoices:read", "invoices:write",
        "customers:read", "customers:write",
        "payments:read", "payments:write",
        "templates:read", "templates:write",
        "reminders:send",
        "tasks:read", "tasks:write",
        "disputes:read", "disputes:write",
        "dashboard:read", "reports:read",
        "settings:read",
        "agents:read",
    ],
    "viewer": [
        "invoices:read",
        "customers:read",
        "payments:read",
        "templates:read",
        "dashboard:read",
        "reports:read",
        "settings:read",
    ],
}


def get_permissions_for_role(role: str) -> list:
    return ROLE_PERMISSIONS.get(role, [])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new tenant and admin user."""
    # Check if subdomain exists
    existing = await db.execute(select(Tenant).where(Tenant.subdomain == request.subdomain))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "SUBDOMAIN_EXISTS",
                    "message": f"Subdomain '{request.subdomain}' already taken",
                },
            },
        )

    # Create tenant
    tenant = Tenant(
        name=request.tenant_name,
        subdomain=request.subdomain,
        status="active",  # Skip trial for MVP
    )
    db.add(tenant)
    await db.flush()

    # Create admin user
    from app.core.security import get_password_hash
    user = User(
        tenant_id=tenant.id,
        email=request.admin_email,
        name=request.admin_name,
        hashed_password=get_password_hash(request.password),
        role="tenant_admin",
        status="active",
    )
    db.add(user)
    await db.flush()

    # Create token pair
    permissions = get_permissions_for_role("tenant_admin")
    tokens = create_token_pair(
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )

    # Store refresh token hash
    from app.core.security import verify_password
    import hashlib
    from datetime import datetime, timezone, timedelta
    refresh_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    refresh_token = RefreshToken(
        user_id=user.id,
        tenant_id=tenant.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)

    await db.commit()

    # Set refresh token as HttpOnly cookie
    response_data = TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )

    return response_data


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email/password."""
    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email).where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                },
            },
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Account is not active",
                },
            },
        )

    # Check tenant status
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant or tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "TENANT_SUSPENDED",
                    "message": "Tenant is suspended",
                },
            },
        )

    # Create token pair
    permissions = get_permissions_for_role(user.role)
    tokens = create_token_pair(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )

    # Store refresh token hash
    import hashlib
    from datetime import datetime, timezone, timedelta
    refresh_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    refresh_token = RefreshToken(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)

    # Update last login
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)

    await db.commit()

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/callback", response_model=TokenResponse)
async def oidc_callback(
    request: OIDCCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """OIDC callback from Keycloak/Azure Entra ID."""
    # Exchange code for tokens
    token_data = await keycloak_client.exchange_code_for_tokens(
        code=request.code,
        redirect_uri=f"{settings.cors_origins_list[0]}/auth/callback",
    )

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")

    # Get user info
    user_info = await keycloak_client.get_user_info(access_token)

    # Find or create user
    email = user_info.get("email")
    result = await db.execute(
        select(User).where(User.email == email).where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create user (would need tenant_id from claims)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not registered. Contact admin.",
                },
            },
        )

    # Create token pair
    permissions = get_permissions_for_role(user.role)
    tokens = create_token_pair(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )

    # Store refresh token hash
    import hashlib
    from datetime import datetime, timezone, timedelta
    refresh_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    rt = RefreshToken(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    import hashlib

    # Validate refresh token
    token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()

    if not rt or rt.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "TOKEN_REVOKED",
                    "message": "Refresh token revoked or invalid",
                },
            },
        )

    # Get user
    result = await db.execute(
        select(User).where(User.id == rt.user_id).where(User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "USER_INACTIVE",
                    "message": "User not found or inactive",
                },
            },
        )

    # Revoke old refresh token
    rt.revoked_at = datetime.now(timezone.utc)

    # Create new token pair
    permissions = get_permissions_for_role(user.role)
    tokens = create_token_pair(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )

    # Store new refresh token hash
    from datetime import datetime, timezone, timedelta
    new_refresh_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    new_rt = RefreshToken(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=new_refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)

    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/logout")
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke refresh token."""
    import hashlib

    token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()

    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        await db.commit()

    return {
        "success": True,
        "data": {"message": "Logged out successfully"},
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    permissions: list = Depends(get_current_permissions),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get current user profile."""
    result = await db.execute(
        select(User, Tenant)
        .join(Tenant, User.tenant_id == Tenant.id)
        .where(User.id == user_id)
        .where(User.tenant_id == tenant_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    user, tenant = row

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        permissions=permissions,
        tenant={
            "id": str(tenant.id),
            "name": tenant.name,
            "subdomain": tenant.subdomain,
        },
    )


@router.post("/invite/{token}", response_model=TokenResponse)
async def accept_invitation(
    token: str,
    request: InviteAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept invitation and set password."""
    # Find invitation
    result = await db.execute(
        select(Invitation).where(Invitation.token == token).where(Invitation.accepted_at.is_(None))
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "INVITATION_NOT_FOUND",
                    "message": "Invalid or expired invitation",
                },
            },
        )

    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVITATION_EXPIRED",
                    "message": "Invitation has expired",
                },
            },
        )

    # Create user
    user = User(
        tenant_id=invitation.tenant_id,
        email=invitation.email,
        name=request.name,
        role=invitation.role,
        status="active",
    )
    db.add(user)
    await db.flush()

    # Mark invitation as accepted
    invitation.accepted_at = datetime.now(timezone.utc)

    # Create token pair
    permissions = get_permissions_for_role(invitation.role)
    tokens = create_token_pair(
        user_id=user.id,
        tenant_id=invitation.tenant_id,
        email=user.email,
        role=user.role,
        permissions=permissions,
    )

    # Store refresh token hash
    import hashlib
    refresh_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
    rt = RefreshToken(user_id=user.id, token_hash=refresh_hash)
    db.add(rt)

    await db.commit()

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
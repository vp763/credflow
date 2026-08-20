# CredFlow Backend - Security Utilities

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import jwt
from jwt import PyJWKClient
from passlib.context import CryptContext
from pydantic import BaseModel
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Password hashing - use argon2 to avoid bcrypt 72-byte limit bug
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # user_id
    tenant_id: str
    email: str
    role: str
    permissions: List[str] = []
    exp: int
    iat: int
    jti: str
    type: str = "access"  # access, refresh


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    role: str,
    permissions: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "role": role,
        "permissions": permissions,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": uuid4().hex,
        "type": "access",
    }

    # Use HS256 for development (shared secret), RS256 requires RSA keys
    algorithm = "HS256" if settings.APP_ENV == "development" else settings.JWT_ALGORITHM
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=algorithm)


def create_refresh_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": uuid4().hex,
        "type": "refresh",
    }

    # Use HS256 for development (shared secret), RS256 requires RSA keys
    algorithm = "HS256" if settings.APP_ENV == "development" else settings.JWT_ALGORITHM
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=algorithm)


def create_token_pair(
    *,
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    role: str,
    permissions: List[str],
) -> TokenPair:
    """Create access and refresh token pair."""
    access_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
        role=role,
        permissions=permissions,
    )
    refresh_token = create_refresh_token(
        user_id=user_id,
        tenant_id=tenant_id,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token."""
    try:
        # Use HS256 for development (shared secret), RS256 requires RSA keys
        algorithm = "HS256" if settings.APP_ENV == "development" else settings.JWT_ALGORITHM
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[algorithm],
            options={"verify_aud": False},
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        raise ValueError("Invalid token")


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without validation (for debugging)."""
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
    except Exception:
        return None


# Keycloak / OIDC Integration
class KeycloakClient:
    """Keycloak/OIDC client for token validation and user info."""

    def __init__(self):
        self.jwks_client: Optional[PyJWKClient] = None
        self._jwks_url: str = ""

    @property
    def jwks_url(self) -> str:
        if not self._jwks_url:
            self._jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        return self._jwks_url

    def _get_jwks_client(self) -> PyJWKClient:
        if self.jwks_client is None:
            self.jwks_client = PyJWKClient(self.jwks_url)
        return self.jwks_client

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Keycloak-issued JWT token."""
        try:
            signing_key = self._get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.KEYCLOAK_CLIENT_ID,
                issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}",
                options={"verify_aud": True},
            )
            return payload
        except Exception as e:
            logger.warning("Keycloak token validation failed", error=str(e))
            raise ValueError("Invalid Keycloak token")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from Keycloak."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.KEYCLOAK_CLIENT_ID,
                    "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.KEYCLOAK_CLIENT_ID,
                    "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()


# Singleton instance
keycloak_client = KeycloakClient()


# Agent API Key Authentication
def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash.
    Returns: (plain_key, hashed_key)
    """
    import secrets
    import hashlib

    # Generate 256-bit key
    plain_key = f"cf_{secrets.token_urlsafe(32)}"
    # Hash for storage
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, hashed_key


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against stored hash."""
    import hashlib
    computed_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, hashed_key)


# Import secrets for constant-time comparison
import secrets
# CredFlow Backend - Tenant Middleware

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import decode_token, keycloak_client
from app.core.config import settings


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant context from JWT and set for RLS."""

    # Paths that don't require tenant context
    EXCLUDED_PATHS = {
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/callback",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/invite",
        "/api/v1/payments/webhook/razorpay",
        "/pay",
    }

    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Check if path starts with excluded prefix
        for excluded in self.EXCLUDED_PATHS:
            if request.url.path.startswith(excluded.rstrip("/")):
                return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing or invalid Authorization header",
                    },
                },
            )

        token = auth_header.split(" ")[1]

        try:
            # Validate token based on auth provider
            if settings.AUTH_PROVIDER == "keycloak":
                payload = keycloak_client.validate_token(token)
                tenant_id = payload.get("tenant_id") or payload.get("custom:tenant_id")
                if not tenant_id:
                    # Try to get from realm roles or custom claims
                    tenant_id = payload.get("tenant_id")
            else:
                # Local JWT validation
                payload = decode_token(token)
                tenant_id = payload.tenant_id

            if not tenant_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "error": {
                            "code": "INVALID_TOKEN",
                            "message": "Token missing tenant_id claim",
                        },
                    },
                )

            # Set tenant context on request state
            request.state.tenant_id = tenant_id
            # Handle both dict (Keycloak) and TokenPayload (local JWT)
            if hasattr(payload, "model_dump"):
                payload_dict = payload.model_dump()
            elif hasattr(payload, "dict"):
                payload_dict = payload.dict()
            else:
                payload_dict = payload

            request.state.user_id = payload_dict.get("sub")
            request.state.role = payload_dict.get("role", "viewer")
            request.state.permissions = payload_dict.get("permissions", [])
            request.state.email = payload_dict.get("email")

        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": str(e),
                    },
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "AUTH_ERROR",
                        "message": "Authentication error",
                    },
                },
            )

        return await call_next(request)


def get_current_tenant_id(request: Request) -> str:
    """FastAPI dependency to get current tenant_id from request state."""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not set",
        )
    return request.state.tenant_id


def get_current_user_id(request: Request) -> str:
    """FastAPI dependency to get current user_id from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User context not set",
        )
    return request.state.user_id


def get_current_role(request: Request) -> str:
    """FastAPI dependency to get current user role."""
    return getattr(request.state, "role", "viewer")


def get_current_permissions(request: Request) -> list:
    """FastAPI dependency to get current user permissions."""
    return getattr(request.state, "permissions", [])


def require_permission(permission: str):
    """FastAPI dependency factory for permission checks."""
    def checker(request: Request):
        permissions = get_current_permissions(request)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Missing permission: {permission}",
                    },
                },
            )
        return True
    return checker


def require_role(*allowed_roles: str):
    """FastAPI dependency factory for role checks."""
    def checker(request: Request):
        role = get_current_role(request)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Requires one of roles: {', '.join(allowed_roles)}",
                    },
                },
            )
        return True
    return checker
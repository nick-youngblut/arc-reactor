from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, status
from google.auth import jwt
from google.auth.transport import requests
from google.oauth2 import id_token

from backend.config import settings


class AuthType(Enum):
    IAP = "iap"
    OIDC = "oidc"


@dataclass(frozen=True)
class UserContext:
    email: str
    name: str
    is_admin: bool = False


@dataclass(frozen=True)
class ServiceContext:
    """Context for service account authentication (Pub/Sub, Cloud Scheduler)."""

    email: str
    auth_type: AuthType = AuthType.OIDC


ALLOWED_SERVICE_ACCOUNTS = {
    "arc-reactor-pubsub@{project}.iam.gserviceaccount.com",
    "arc-reactor-scheduler@{project}.iam.gserviceaccount.com",
}


def _audience() -> str | None:
    project_number = os.getenv("IAP_PROJECT_NUMBER") or getattr(settings, "iap_project_number", None)
    project_id = os.getenv("IAP_PROJECT_ID") or getattr(settings, "iap_project_id", None)
    if not project_number or not project_id:
        return None
    return f"/projects/{project_number}/apps/{project_id}"


def _admin_emails() -> set[str]:
    raw = os.getenv("ARC_REACTOR_ADMIN_EMAILS") or getattr(settings, "admin_emails", "")
    return {email.strip().lower() for email in str(raw).split(",") if email.strip()}


def _allowed_domain() -> str | None:
    return os.getenv("IAP_ALLOWED_DOMAIN") or getattr(settings, "iap_allowed_domain", None)


def verify_iap_jwt(token: str) -> dict:
    request = requests.Request()
    audience = _audience()
    if not audience:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IAP audience is not configured",
        )

    claims = jwt.decode(token, request=request, audience=audience)
    allowed_domain = _allowed_domain()
    if allowed_domain:
        hosted_domain = claims.get("hd")
        if hosted_domain != allowed_domain:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hosted domain not authorized",
            )

    return claims


def verify_oidc_token(token: str, audience: str) -> dict:
    """Verify OIDC token from service account."""
    try:
        claims = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=audience,
        )

        email = claims.get("email", "")
        project = settings.get("gcp_project")
        allowed = {sa.format(project=project) for sa in ALLOWED_SERVICE_ACCOUNTS}

        if email not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Service account not authorized: {email}",
            )

        return claims
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OIDC token: {e}",
        )


async def get_current_user(request: Request) -> UserContext:
    jwt_token = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if not jwt_token:
        if settings.get("debug", False):
            return UserContext(email="dev@example.com", name="Developer")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    claims = verify_iap_jwt(jwt_token)
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    name = claims.get("name", email)
    is_admin = email.lower() in _admin_emails()
    return UserContext(email=email, name=name, is_admin=is_admin)


async def get_service_context(request: Request) -> ServiceContext:
    """Extract service account from OIDC token."""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    token = auth_header[7:]
    audience = str(request.url).split("?")[0]
    claims = verify_oidc_token(token, audience)

    return ServiceContext(email=claims.get("email", "unknown"))

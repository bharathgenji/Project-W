"""Firebase Auth middleware — verifies ID tokens from the frontend.

In demo/dev mode (ENVIRONMENT=development), auth is optional:
- Requests without Authorization header are treated as anonymous demo user
- Requests with a valid token get full user context

In production, all non-public endpoints require a valid token.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.config import get_settings

logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=False)

# ── Firebase Admin SDK init ──────────────────────────────────────────────────

@lru_cache
def _get_firebase_app():
    settings = get_settings()
    if not settings.firebase_project_id:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
        cred_path = settings.google_application_credentials
        if cred_path:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred, name="buildscope")
        else:
            app = firebase_admin.initialize_app(name="buildscope")
        logger.info("firebase_auth_initialized", project=settings.firebase_project_id)
        return app
    except Exception as exc:
        logger.warning("firebase_auth_init_failed", error=str(exc))
        return None


# ── Token verification ────────────────────────────────────────────────────────

def verify_token(token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and return the decoded claims."""
    app = _get_firebase_app()
    if app is None:
        raise HTTPException(status_code=503, detail="Auth service not configured")
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token, app=app)
        return decoded
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc


# ── FastAPI dependencies ──────────────────────────────────────────────────────

DEMO_USER = {
    "uid": "demo-user-001",
    "email": "demo@buildscope.app",
    "name": "Demo User",
    "tier": "pro",
    "is_demo": True,
}


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict[str, Any]:
    """
    Returns the current user.
    - In dev/demo mode: returns DEMO_USER if no token provided
    - In production: requires valid Firebase ID token
    """
    settings = get_settings()

    if credentials and credentials.credentials:
        return verify_token(credentials.credentials)

    # Dev/demo mode — allow unauthenticated access
    if settings.environment == "development":
        # Check if a pipeline_email cookie/header is set for personalization
        email = request.headers.get("X-User-Email", "")
        if email:
            return {**DEMO_USER, "email": email, "uid": f"demo-{email}"}
        return DEMO_USER

    raise HTTPException(status_code=401, detail="Authentication required")


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict[str, Any] | None:
    """Like get_current_user but returns None instead of raising for unauthenticated."""
    try:
        return get_current_user(request, credentials)
    except HTTPException:
        return None

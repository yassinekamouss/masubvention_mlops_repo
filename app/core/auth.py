"""
Authentication and internal token validation dependencies for MLOps endpoints.
Provides constant-time verification for inter-service communication.
"""
import logging
import re
import secrets
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_internal_token(
    x_internal_secret: Optional[str] = Header(None, alias="X-Internal-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Validates that incoming requests contain a valid internal shared secret.
    Accepts either:
      - Header 'X-Internal-Secret: <token>'
      - Header 'Authorization: Bearer <token>'
    Uses secrets.compare_digest for constant-time comparison to prevent timing attacks.
    """
    configured_secret = (
        getattr(settings, "INTERNAL_API_SECRET", None)
        or getattr(settings, "INTERNAL_WEBHOOK_SECRET", None)
        or ""
    )

    if not configured_secret:
        logger.error("[SECURITY ERROR] INTERNAL_WEBHOOK_SECRET is not configured on MLOps microservice!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security configuration error: internal secret is not configured."
        )

    incoming_secret: Optional[str] = None
    if x_internal_secret:
        incoming_secret = x_internal_secret.strip()
    elif authorization:
        cleaned_auth = authorization.strip()
        # Handle Bearer prefix with variable whitespace safely
        incoming_secret = re.sub(r"^Bearer\s*", "", cleaned_auth, flags=re.IGNORECASE).strip()

    if not incoming_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès refusé : jeton d'authentification interne manquant (en-tête X-Internal-Secret ou Authorization requis).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not secrets.compare_digest(incoming_secret, configured_secret):
        logger.warning("[SECURITY WARNING] Tentative d'accès non autorisée au microservice MLOps (jeton invalide).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : jeton d'authentification interne invalide."
        )

    return incoming_secret


# Backward-compatible alias
verify_internal_secret = verify_internal_token

__all__ = ["verify_internal_token", "verify_internal_secret"]

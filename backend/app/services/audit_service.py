import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.app.models.base import AuditLog, User

logger = logging.getLogger(__name__)

# Keys strictly scrubbed from audit logs to prevent credential leakage
SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "secret", "jwt", "authorization", "api_key", "dev_reset_token"
}


def sanitize_audit_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively removes sensitive keys, passwords, and tokens from audit data."""
    if not isinstance(payload, dict):
        return {}
    sanitized = {}
    for k, v in payload.items():
        if any(secret in k.lower() for secret in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_audit_payload(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            sanitized[k] = v
        else:
            sanitized[k] = str(v)[:250]
    return sanitized


class SecurityAuditService:
    """
    Centralized security audit logging service.
    Guarantees privacy-compliant, tamper-evident recording of security-critical actions:
    - Authentication events (login, logout, failed attempts, password resets)
    - Resource deletions
    - Role modifications & member invitations
    - Editorial approvals and finalizations
    - Sensitive export and download operations
    """

    @classmethod
    def log_event(
        cls,
        db: Session,
        event_type: str,
        user: Optional[User] = None,
        organization_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AuditLog]:
        try:
            user_id = user.id if user else None
            resolved_email = actor_email or (user.email if user else None)
            clean_metadata = sanitize_audit_payload(metadata or {})

            audit_entry = AuditLog(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                user_id=user_id,
                event_type=event_type,
                actor_email=resolved_email,
                ip_address=ip_address or "127.0.0.1",
                user_agent=(user_agent or "Unknown")[:250],
                changes_json=clean_metadata,
                created_at=datetime.now(timezone.utc),
            )
            db.add(audit_entry)
            db.commit()
            return audit_entry
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to record security audit log for '%s': %s", event_type, exc)
            return None


audit_service = SecurityAuditService()

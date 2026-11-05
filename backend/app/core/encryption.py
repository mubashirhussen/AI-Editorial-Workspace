import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, MultiFernet
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def _derive_fernet_key(passphrase: str) -> Fernet:
    """Derives a deterministic 32-byte url-safe base64 Fernet key from a string."""
    derived_hash = hashlib.sha256(passphrase.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(derived_hash)
    return Fernet(b64_key)

def _get_fernet_instance() -> MultiFernet:
    """
    Returns a MultiFernet instance supporting independent ENCRYPTION_KEY with
    seamless fallback to SECRET_KEY for existing database credentials.
    """
    fernet_keys = []
    
    # 1. Primary encryption key (dedicated for data-at-rest)
    if getattr(settings, "ENCRYPTION_KEY", None):
        fernet_keys.append(_derive_fernet_key(settings.ENCRYPTION_KEY))
    
    # 2. Legacy / Compatibility key (derived from SECRET_KEY / JWT_SECRET)
    raw_secret = getattr(settings, "SECRET_KEY", "editorial-workspace-encryption-key-production-seed-32bytes")
    fernet_keys.append(_derive_fernet_key(raw_secret))
    
    # 3. Baseline fallback default key to guarantee decryption of legacy dev seed fixtures
    baseline_default = "editorial-workspace-encryption-key-production-seed-32bytes"
    if raw_secret != baseline_default:
        fernet_keys.append(_derive_fernet_key(baseline_default))

    return MultiFernet(fernet_keys)

def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    """Encrypts sensitive credentials or API keys before storing in database."""
    if not plaintext:
        return None
    f = _get_fernet_instance()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypts database-persisted credentials.
    Supports key rotation: tries primary key, then fallback keys in sequence.
    """
    if not ciphertext:
        return None
    try:
        f = _get_fernet_instance()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        logger.warning("Decryption failed for ciphertext token: %s", exc)
        return None

def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """Safely masks credentials (e.g. sk-...9a2f) for API responses and client UI."""
    if not secret:
        return "Not configured"
    clean = secret.strip()
    if len(clean) <= visible_chars * 2:
        return "****"
    return f"{clean[:visible_chars]}...{clean[-visible_chars:]}"

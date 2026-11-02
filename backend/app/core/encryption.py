import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from backend.app.core.config import settings

def _get_fernet_instance() -> Fernet:
    """Derives a deterministic 32-byte url-safe base64 key from settings.SECRET_KEY."""
    raw_key = getattr(settings, "SECRET_KEY", "editorial-workspace-encryption-key-production-seed-32bytes")
    derived_hash = hashlib.sha256(raw_key.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(derived_hash)
    return Fernet(b64_key)

def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    """Encrypts sensitive credentials or API keys before storing in database."""
    if not plaintext:
        return None
    f = _get_fernet_instance()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypts database-persisted credentials for backend service use."""
    if not ciphertext:
        return None
    try:
        f = _get_fernet_instance()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        # Return None or error if corrupted
        return None

def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """Safely masks credentials (e.g. sk-...9a2f) for API responses and client UI."""
    if not secret:
        return "Not configured"
    clean = secret.strip()
    if len(clean) <= visible_chars * 2:
        return "****"
    return f"{clean[:visible_chars]}...{clean[-visible_chars:]}"


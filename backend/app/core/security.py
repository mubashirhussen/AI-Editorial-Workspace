import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from backend.app.core.config import settings

# In-memory revoked tokens store (blacklist) for instant logout / invalidation
_revoked_tokens: Set[str] = set()

def hash_password(plain_password: str) -> str:
    """Securely hash a password using bcrypt with automatic salt generation."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed HS256 JWT access token with expiration."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token, checking blacklist and expiration."""
    if token in _revoked_tokens:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def revoke_token(token: str) -> None:
    """Add a token to the revoked tokens store."""
    _revoked_tokens.add(token)

def is_token_revoked(token: str) -> bool:
    """Check if a token has been revoked."""
    return token in _revoked_tokens


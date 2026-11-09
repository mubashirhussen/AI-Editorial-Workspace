import re
import secrets
import hashlib
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Set, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from backend.app.core.config import settings

# Initialize Argon2id password hasher (RFC 9106 recommended parameters)
_argon2_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

# In-memory revoked tokens store (blacklist) for instant logout / invalidation
_revoked_tokens: Set[str] = set()

# Denylist of common compromised passwords and dictionary patterns
COMMON_PASSWORDS_DENYLIST = {
    "password12345", "password123456", "admin12345678", "welcome123456",
    "qwerty123456", "letmein123456", "iloveyou12345", "monkey123456",
    "dragon123456", "master123456", "sunshine12345", "princess12345",
    "football12345", "superman12345", "charlie12345", "trustno112345",
    "admin123456!", "welcome1234!", "qwerty12345!",
    "administrator!", "editorial123!", "editorialworkspace!", "changeme123!"
}


def hash_password(plain_password: str) -> str:
    """
    Securely hash a password using Argon2id with unique cryptographic salt.
    Fallback to bcrypt if Argon2 is unavailable.
    """
    try:
        return _argon2_hasher.hash(plain_password)
    except Exception:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against an Argon2id or legacy bcrypt hash.
    Safely handles invalid formats and constant-time comparison.
    """
    if not plain_password or not hashed_password:
        return False

    # Check for Argon2id hash format
    if hashed_password.startswith("$argon2"):
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, InvalidHashError):
            return False
        except Exception:
            return False

    # Check for legacy bcrypt hash format ($2a$, $2b$, $2y$)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    return False


def hash_token(token: str) -> str:
    """Compute SHA-256 cryptographic digest of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate an unguessable URL-safe cryptographic token."""
    return secrets.token_urlsafe(nbytes)


def validate_password_strength(
    password: str,
    email: str = "",
    full_name: str = ""
) -> Tuple[bool, str, int]:
    """
    Enforces production password policy:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    - Not matching common compromised denylist
    - Not containing user's email prefix or full name
    
    Returns: (is_valid: bool, error_message: str, strength_score: int [0-4])
    """
    if not password:
        return False, "Password cannot be empty.", 0

    score = 0
    checks = {
        "length": len(password) >= 12,
        "uppercase": bool(re.search(r'[A-Z]', password)),
        "lowercase": bool(re.search(r'[a-z]', password)),
        "digit": bool(re.search(r'\d', password)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]', password))
    }

    if checks["length"]:
        score += 1
    if checks["uppercase"] and checks["lowercase"]:
        score += 1
    if checks["digit"]:
        score += 1
    if checks["special"]:
        score += 1

    # Length requirement
    if len(password) < 12:
        return False, "Password must be at least 12 characters long.", min(score, 1)

    # Complexity requirements
    if not checks["uppercase"]:
        return False, "Password must include at least one uppercase letter (A-Z).", score
    if not checks["lowercase"]:
        return False, "Password must include at least one lowercase letter (a-z).", score
    if not checks["digit"]:
        return False, "Password must include at least one numeric digit (0-9).", score
    if not checks["special"]:
        return False, "Password must include at least one special character (!@#$%^&* etc.).", score

    # Check common compromised denylist
    clean_pwd = password.strip().lower()
    if clean_pwd in COMMON_PASSWORDS_DENYLIST:
        return False, "This password is too common or easily compromised. Please choose a unique passphrase.", 1

    # Check for personal information in password (email prefix or entire full name)
    if email:
        email_prefix = email.split('@')[0].strip().lower()
        if len(email_prefix) >= 5 and email_prefix in clean_pwd:
            return False, "Password must not contain your email address.", 1

    if full_name:
        clean_name = full_name.strip().lower()
        no_spaces_name = clean_name.replace(" ", "")
        if (len(clean_name) >= 5 and clean_name in clean_pwd) or (len(no_spaces_name) >= 5 and no_spaces_name in clean_pwd):
            return False, "Password must not contain your full name.", 1

    return True, "", 4


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed HS256 JWT access token with expiration and session payload."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": secrets.token_hex(16)
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

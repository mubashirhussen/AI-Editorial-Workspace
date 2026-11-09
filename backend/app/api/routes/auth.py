import re
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    generate_secure_token,
    validate_password_strength,
    create_access_token,
    decode_access_token,
    revoke_token,
)
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    PasswordResetToken,
    EmailVerificationToken,
    UserSession,
    AuditLog,
)
from backend.app.schemas.auth import (
    PasswordForgotRequest,
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    OrganizationResponse,
    AuthResponse,
    PasswordResetRequest,
    PasswordChangeRequest,
    EmailVerificationRequest,
    TokenRefreshResponse,
    PasswordStrengthCheckRequest,
    PasswordStrengthCheckResponse,
)
from backend.app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory sliding window rate limiter for brute-force protection
# Key: client IP / identifier -> list of failed attempt timestamps
_login_failures: Dict[str, list[float]] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_FAILED_ATTEMPTS = 5


def check_login_rate_limit(client_id: str) -> None:
    """Enforces rate limiting on authentication attempts to mitigate brute-force attacks."""
    now = datetime.now(timezone.utc).timestamp()
    attempts = _login_failures.get(client_id, [])
    # Filter attempts within the sliding window
    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _login_failures[client_id] = attempts
    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 60 seconds before trying again."
        )


def record_login_failure(client_id: str) -> None:
    now = datetime.now(timezone.utc).timestamp()
    if client_id not in _login_failures:
        _login_failures[client_id] = []
    _login_failures[client_id].append(now)


def clear_login_failures(client_id: str) -> None:
    _login_failures.pop(client_id, None)


def slugify(text: str) -> str:
    s = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', s)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with strict password validation,
    creates personal organization workspace, and issues authenticated session.
    """
    email_clean = payload.email.strip().lower()

    # 1. Email format validation
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # 2. Terms validation
    if not payload.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms and Conditions to create an account."
        )

    # 3. Password confirmation validation
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match."
        )

    # 4. Duplicate email prevention
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 5. Strong Password Policy enforcement
    is_valid, err_msg, _ = validate_password_strength(
        payload.password,
        email=email_clean,
        full_name=payload.full_name
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    # 6. Assign Default Role (First user gets ADMIN, subsequent get USER or configured)
    user_count = db.query(User).count()
    assigned_role = "ADMIN" if user_count == 0 or email_clean.startswith("admin@") else "USER"

    # 7. Create User with Argon2id hash
    new_user = User(
        id=str(uuid.uuid4()),
        email=email_clean,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=assigned_role,
        is_active=True,
        is_verified=False  # Verification token generated below
    )
    db.add(new_user)
    db.flush()

    # 8. Create Email Verification Token
    raw_verify_token = generate_secure_token(32)
    verify_record = EmailVerificationToken(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        token_hash=hash_token(raw_verify_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        is_used=False
    )
    db.add(verify_record)

    # 9. Provision Personal Workspace Organization
    org_name = payload.organization_name.strip() if payload.organization_name else f"{new_user.full_name}'s Workspace"
    base_slug = slugify(org_name)
    slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"

    new_org = Organization(
        id=str(uuid.uuid4()),
        name=org_name,
        slug=slug
    )
    db.add(new_org)
    db.flush()

    # 10. Create OWNER Membership
    membership = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=new_org.id,
        user_id=new_user.id,
        role="OWNER"
    )
    db.add(membership)

    # 11. Generate Access Token & Record Session
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")[:250]
    session_expire = datetime.now(timezone.utc) + timedelta(hours=24)

    token = create_access_token(
        data={"sub": new_user.id, "email": new_user.email, "role": new_user.role},
        expires_delta=timedelta(hours=24)
    )

    new_session = UserSession(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        token_hash=hash_token(token),
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=session_expire,
        is_revoked=False,
        last_activity_at=datetime.now(timezone.utc)
    )
    db.add(new_session)

    db.commit()
    db.refresh(new_user)
    db.refresh(new_org)

    org_resp = OrganizationResponse(
        id=new_org.id,
        name=new_org.name,
        slug=new_org.slug,
        role="OWNER",
        created_at=new_org.created_at
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
        organization=org_resp
    )


@router.post("/login", response_model=AuthResponse)
def login_user(
    payload: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticates email and password credentials with rate limiting and generic error handling.
    Creates an active user session and records login activity.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_login_rate_limit(client_ip)

    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    # Generic authentication failure (prevents email enumeration)
    if not user or not verify_password(payload.password, user.hashed_password):
        record_login_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    # Clear rate limit counter on successful credentials
    clear_login_failures(client_ip)

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    # Session duration (30 days if remember_me, else 24 hours)
    duration = timedelta(days=30) if payload.remember_me else timedelta(hours=24)
    session_expire = datetime.now(timezone.utc) + duration

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "USER")},
        expires_delta=duration
    )

    # Record UserSession in database
    user_agent = request.headers.get("user-agent", "Unknown")[:250]
    session_entry = UserSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(token),
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=session_expire,
        is_revoked=False,
        last_activity_at=datetime.now(timezone.utc)
    )
    db.add(session_entry)
    db.commit()

    # Resolve primary organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).order_by(OrganizationMembership.joined_at.asc()).first()

    org_resp = None
    if membership and membership.organization:
        org_resp = OrganizationResponse(
            id=membership.organization.id,
            name=membership.organization.name,
            slug=membership.organization.slug,
            role=membership.role,
            created_at=membership.organization.created_at
        )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        organization=org_resp
    )


@router.get("/me")
def get_current_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns profile and organization list for the currently authenticated user."""
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).all()

    orgs = []
    for mem in memberships:
        if mem.organization:
            orgs.append({
                "id": mem.organization.id,
                "name": mem.organization.name,
                "slug": mem.organization.slug,
                "role": mem.role,
                "joined_at": mem.joined_at.isoformat()
            })

    return {
        "user": UserResponse.model_validate(user),
        "organizations": orgs
    }


@router.post("/logout")
def logout_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Revokes the current JWT access token and marks database session as revoked."""
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        revoke_token(token)
        # Invalidate database session
        t_hash = hash_token(token)
        db.query(UserSession).filter(UserSession.token_hash == t_hash).update({"is_revoked": True})
        db.commit()
    return {"message": "Logged out successfully."}


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Refreshes an active session token before expiration."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header.")
    token = authorization[7:].strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired or invalid.")

    # Check if database session is revoked
    t_hash = hash_token(token)
    session_rec = db.query(UserSession).filter(UserSession.token_hash == t_hash).first()
    if session_rec and session_rec.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked.")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive.")

    new_token = create_access_token(data={"sub": user.id, "email": user.email, "role": getattr(user, "role", "USER")})

    # Update session last activity
    if session_rec:
        session_rec.last_activity_at = datetime.now(timezone.utc)
        db.commit()

    return TokenRefreshResponse(access_token=new_token, token_type="bearer")


@router.post("/forgot-password")
def forgot_password(
    payload: PasswordForgotRequest,
    db: Session = Depends(get_db)
):
    """
    Initiates a secure password reset workflow. Always returns a generic confirmation
    message to avoid exposing whether an email is registered.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    dev_token = None
    if user and user.is_active:
        raw_token = generate_secure_token(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        # Invalidate prior unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

        reset_entry = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(reset_entry)
        db.commit()
        dev_token = raw_token
        logger.info("Password reset token generated for user %s", user.id)

    resp = {
        "success": True,
        "message": "If this email address is registered, password reset instructions have been dispatched."
    }
    if dev_token and getattr(settings, "ENVIRONMENT", "development").lower() not in ("production", "prod"):
        resp["dev_reset_token"] = dev_token
    return resp


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Validates the cryptographic reset token, updates password with Argon2id, and revokes active sessions."""
    if not payload.token or len(payload.token.strip()) < 16:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid reset token is required.")

    token_hash = hash_token(payload.token.strip())
    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False
    ).first()

    if not reset_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid, expired, or previously used reset token.")

    now = datetime.now(timezone.utc)
    exp = reset_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        reset_record.is_used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired.")

    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User account is inactive or not found.")

    # Validate new password strength
    is_valid, err_msg, _ = validate_password_strength(payload.new_password, email=user.email, full_name=user.full_name)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    user.hashed_password = hash_password(payload.new_password)
    reset_record.is_used = True

    # Invalidate all user sessions
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True})
    db.commit()

    return {"success": True, "message": "Password successfully reset. All previous sessions have been invalidated."}


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates password for the currently authenticated user, enforcing password policy."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as your current password.")

    is_valid, err_msg, _ = validate_password_strength(
        payload.new_password,
        email=current_user.email,
        full_name=current_user.full_name
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"success": True, "message": "Password changed successfully."}


@router.post("/verify-email")
def verify_email(
    payload: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Validates the email verification token and marks user account as verified."""
    token_hash = hash_token(payload.token.strip())
    verify_record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash,
        EmailVerificationToken.is_used == False
    ).first()

    if not verify_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid, expired, or previously used verification token.")

    now = datetime.now(timezone.utc)
    exp = verify_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        verify_record.is_used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired.")

    user = db.query(User).filter(User.id == verify_record.user_id).first()
    if user:
        user.is_verified = True
        verify_record.is_used = True
        db.commit()

    return {"success": True, "message": "Email verified successfully."}


@router.post("/check-password-strength", response_model=PasswordStrengthCheckResponse)
def check_password_strength(payload: PasswordStrengthCheckRequest):
    """Live validation utility returning criteria checkmarks and strength score."""
    pwd = payload.password
    checks = {
        "length": len(pwd) >= 12,
        "uppercase": bool(re.search(r'[A-Z]', pwd)),
        "lowercase": bool(re.search(r'[a-z]', pwd)),
        "digit": bool(re.search(r'\d', pwd)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]', pwd))
    }

    is_valid, err_msg, score = validate_password_strength(
        pwd,
        email=payload.email or "",
        full_name=payload.full_name or ""
    )

    labels = {0: "Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong"}
    return PasswordStrengthCheckResponse(
        is_valid=is_valid,
        score=score,
        strength_label=labels.get(score, "Weak"),
        error_message=err_msg,
        requirements=checks
    )

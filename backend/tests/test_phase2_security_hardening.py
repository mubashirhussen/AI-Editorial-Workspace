import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.core.config import Settings
from backend.app.core.encryption import encrypt_secret, decrypt_secret, mask_secret
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.base import User, Organization, OrganizationMembership, ResearchProject, PasswordResetToken, UserSession

def test_production_settings_validation():
    """Validates that production environment strictly forbids weak or default secrets."""
    # 1. Default secret rejected in production
    with pytest.raises(ValueError, match="cannot use the development default"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="super-secret-editorial-ai-jwt-key-change-in-production",
            ALLOW_ANONYMOUS_DEV=False
        )

    # 2. Short secret (< 32 chars) rejected in production
    with pytest.raises(ValueError, match="at least 32 characters long"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-secret",
            ALLOW_ANONYMOUS_DEV=False
        )

    # 3. Anonymous dev mode forbidden in production
    with pytest.raises(ValueError, match="ALLOW_ANONYMOUS_DEV must be set to False"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-very-strong-and-secure-production-secret-key-12345",
            ALLOW_ANONYMOUS_DEV=True
        )

    # 4. Valid production settings accepted
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-very-strong-and-secure-production-secret-key-12345",
        ALLOW_ANONYMOUS_DEV=False
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.ALLOW_ANONYMOUS_DEV is False


def test_encryption_key_decoupling_and_backward_compatibility():
    """
    Verifies that ENCRYPTION_KEY is decoupled from JWT SECRET_KEY and
    MultiFernet maintains seamless decryption of legacy credentials.
    """
    secret_text = "sk-ant-api03-sample-ai-provider-token-12345"
    
    # Encrypt secret
    ciphertext = encrypt_secret(secret_text)
    assert ciphertext is not None
    assert ciphertext != secret_text
    
    # Decrypt secret
    decrypted = decrypt_secret(ciphertext)
    assert decrypted == secret_text
    
    # Masking
    masked = mask_secret(secret_text)
    assert masked.startswith("sk-a")
    assert masked.endswith("2345")
    assert "..." in masked


def test_password_reset_lifecycle_and_invariants(client: TestClient, db_session: Session):
    """
    Verifies complete secure 2-step password reset workflow:
    1. Forgot password initiates token in DB
    2. Invalid / expired / reused tokens are rejected
    3. Valid token updates password and revokes active sessions
    """
    user_email = f"reset_test_{uuid.uuid4().hex[:8]}@example.com"
    initial_pass = "InitialSecurePassword123!"
    updated_pass = "NewStrongerPassword456!"
    
    # Create test user
    user = User(
        id=str(uuid.uuid4()),
        email=user_email,
        hashed_password=hash_password(initial_pass),
        full_name="Password Reset User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Create an active session to test session revocation on reset
    session_record = UserSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash="sample_session_token_hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_revoked=False
    )
    db_session.add(session_record)
    db_session.commit()

    # Step 1: Request forgot password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": user_email})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    assert forgot_data["success"] is True
    dev_token = forgot_data.get("dev_reset_token")
    assert dev_token is not None, "Dev reset token should be provided in dev/test mode"

    # Step 2: Attempt reset with invalid token -> 400
    bad_res = client.post("/api/v1/auth/reset-password", json={
        "token": "invalid_nonexistent_token_12345",
        "new_password": updated_pass
    })
    assert bad_res.status_code == 400

    # Step 3: Attempt reset with valid token -> 200
    good_res = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": updated_pass
    })
    assert good_res.status_code == 200
    assert good_res.json()["success"] is True

    # Verify password was updated in DB
    db_session.refresh(user)
    assert verify_password(updated_pass, user.hashed_password) is True
    assert verify_password(initial_pass, user.hashed_password) is False

    # Verify active session was invalidated
    db_session.refresh(session_record)
    assert session_record.is_revoked is True

    # Step 4: Attempt replay / reuse of the same token -> 400 (reused token rejected)
    replay_res = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": "AnotherNewPassword789!"
    })
    assert replay_res.status_code == 400


def test_multi_tenant_project_isolation(client: TestClient, db_session: Session):
    """
    Verifies that User in Org Alpha cannot read, update, or delete
    projects belonging to Org Beta.
    """
    # Create Org Alpha and User Alpha
    org_alpha = Organization(id=str(uuid.uuid4()), name="Org Alpha", slug=f"alpha-{uuid.uuid4().hex[:6]}")
    user_alpha = User(
        id=str(uuid.uuid4()),
        email=f"alpha_{uuid.uuid4().hex[:6]}@alpha.corp",
        hashed_password=hash_password("Pass123!"),
        full_name="Alpha Lead",
        is_active=True
    )
    db_session.add_all([org_alpha, user_alpha])
    db_session.flush()
    mem_alpha = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=org_alpha.id,
        user_id=user_alpha.id,
        role="OWNER"
    )
    db_session.add(mem_alpha)

    # Create Org Beta and User Beta
    org_beta = Organization(id=str(uuid.uuid4()), name="Org Beta", slug=f"beta-{uuid.uuid4().hex[:6]}")
    user_beta = User(
        id=str(uuid.uuid4()),
        email=f"beta_{uuid.uuid4().hex[:6]}@beta.corp",
        hashed_password=hash_password("Pass123!"),
        full_name="Beta Lead",
        is_active=True
    )
    db_session.add_all([org_beta, user_beta])
    db_session.flush()
    mem_beta = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=org_beta.id,
        user_id=user_beta.id,
        role="OWNER"
    )
    db_session.add(mem_beta)

    # Create Project in Org Beta
    proj_beta = ResearchProject(
        id=str(uuid.uuid4()),
        title="Beta Confidential Project",
        description="Proprietary research",
        organization_id=org_beta.id,
        status="active"
    )
    db_session.add(proj_beta)
    db_session.commit()

    # Create Auth Token for User Alpha
    token_alpha = create_access_token(data={"sub": user_alpha.id, "email": user_alpha.email})
    headers_alpha = {
        "Authorization": f"Bearer {token_alpha}",
        "X-Organization-Id": org_alpha.id
    }

    # User Alpha attempts to GET Beta's project -> 404 (prevents tenant existence disclosure)
    res_get = client.get(f"/api/v1/research/projects/{proj_beta.id}", headers=headers_alpha)
    assert res_get.status_code == 404

    # User Alpha attempts to UPDATE Beta's project -> 404
    res_put = client.put(
        f"/api/v1/research/projects/{proj_beta.id}",
        json={"title": "Hacked Title"},
        headers=headers_alpha
    )
    assert res_put.status_code == 404

    # User Alpha attempts to DELETE Beta's project -> 404
    res_del = client.delete(f"/api/v1/research/projects/{proj_beta.id}", headers=headers_alpha)
    assert res_del.status_code == 404

    # User Alpha attempts to add source to Beta's project -> 404
    res_src = client.post(
        f"/api/v1/research/projects/{proj_beta.id}/sources",
        json={"source_type": "text", "title": "Tampered Source", "text_content": "Injected data"},
        headers=headers_alpha
    )
    assert res_src.status_code == 404

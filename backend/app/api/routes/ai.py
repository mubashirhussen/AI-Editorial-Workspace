import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.encryption import encrypt_secret, decrypt_secret, mask_secret
from backend.app.models.base import User, IntegrationConnection, AiProviderConfig, ProviderUsageRecord
from backend.app.api.deps import get_current_user
from backend.app.schemas.ai import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionRotate,
    ConnectionResponse,
    AIHealthResponse,
    UsageSummaryResponse
)
from backend.app.services.ai.models import get_all_providers, get_all_models, get_default_model
from backend.app.services.ai.router import ai_router
from backend.app.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/ai", tags=["AI Integration Engine"])

@router.get("/providers")
def list_supported_providers():
    """Returns catalog of supported AI providers, capabilities, and configurations."""
    return get_all_providers()

@router.get("/models")
def list_supported_models(provider: Optional[str] = Query(None)):
    """Returns available models filtered by provider with context limits and capabilities."""
    return get_all_models(provider)

@router.get("/connections", response_model=List[ConnectionResponse])
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists configured provider connections with masked credentials."""
    conns = db.query(IntegrationConnection).order_by(IntegrationConnection.created_at.desc()).all()
    
    # If no database connections exist yet, but environment keys exist, create default connection
    if not conns:
        if settings.GROQ_API_KEY:
            default_conn = IntegrationConnection(
                id=f"conn-groq-{uuid.uuid4().hex[:8]}",
                provider="groq",
                name="System Groq LPU Connection",
                status="connected",
                masked_key=mask_secret(settings.GROQ_API_KEY),
                encrypted_secret=encrypt_secret(settings.GROQ_API_KEY),
                is_active=True,
                is_default=True,
                last_synced_at=datetime.now(timezone.utc)
            )
            db.add(default_conn)
            db.commit()
            db.refresh(default_conn)
            conns = [default_conn]

    result = []
    for c in conns:
        result.append(ConnectionResponse(
            id=c.id,
            provider=c.provider,
            name=c.name,
            status=c.status,
            model=settings.DEFAULT_AI_MODEL if c.provider == "groq" else (settings.AI_MODEL if c.provider == "openai" else "default"),
            masked_key=c.masked_key or mask_secret(decrypt_secret(c.encrypted_secret)),
            is_active=c.is_active,
            is_default=c.is_default,
            last_synced_at=c.last_synced_at,
            created_at=c.created_at
        ))
    return result

@router.post("/connections", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registers and encrypts a new provider credential connection."""
    prov = data.provider.lower().strip()
    enc_secret = encrypt_secret(data.api_key)
    masked = mask_secret(data.api_key)
    chosen_model = data.model or get_default_model(prov) or "default"

    # Reset default if this new connection is set as default
    if data.is_default:
        db.query(IntegrationConnection).filter(IntegrationConnection.provider == prov).update({"is_default": False})

    conn = IntegrationConnection(
        id=f"conn-{uuid.uuid4().hex[:8]}",
        provider=prov,
        name=data.name,
        status="configured",
        masked_key=masked,
        encrypted_secret=enc_secret,
        is_active=True,
        is_default=data.is_default,
        last_synced_at=datetime.now(timezone.utc)
    )
    db.add(conn)

    # Sync into ai_provider_configs
    p_config = db.query(AiProviderConfig).filter(AiProviderConfig.provider == prov).first()
    if p_config:
        p_config.encrypted_api_key = enc_secret
        p_config.model_name = chosen_model
        p_config.is_active = True
        p_config.is_default = data.is_default
    else:
        p_config = AiProviderConfig(
            id=f"cfg-{uuid.uuid4().hex[:8]}",
            provider=prov,
            model_name=chosen_model,
            encrypted_api_key=enc_secret,
            is_active=True,
            is_default=data.is_default,
            config_json={"source": "api_registration"}
        )
        db.add(p_config)

    db.commit()
    db.refresh(conn)

    return ConnectionResponse(
        id=conn.id,
        provider=conn.provider,
        name=conn.name,
        status=conn.status,
        model=chosen_model,
        masked_key=conn.masked_key,
        is_active=conn.is_active,
        is_default=conn.is_default,
        last_synced_at=conn.last_synced_at,
        created_at=conn.created_at
    )

@router.post("/connections/{connection_id}/validate")
async def validate_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes live handshake verification against provider endpoint using stored encrypted secret."""
    conn = db.query(IntegrationConnection).filter(IntegrationConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    plaintext_key = decrypt_secret(conn.encrypted_secret) if conn.encrypted_secret else None
    if not plaintext_key and conn.provider == "groq" and settings.GROQ_API_KEY:
        plaintext_key = settings.GROQ_API_KEY

    adapter = ai_router.get_adapter(provider=conn.provider, db=db)
    if plaintext_key:
        adapter.api_key = plaintext_key

    health = await adapter.check_health()
    conn.last_synced_at = datetime.now(timezone.utc)
    if health.get("status") in ("connected", "healthy"):
        conn.status = "connected"
    else:
        conn.status = "error"
    db.commit()

    return {
        "connection_id": connection_id,
        "provider": conn.provider,
        "status": conn.status,
        "details": health,
        "last_validated": conn.last_synced_at.isoformat()
    }

@router.patch("/connections/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: str,
    data: ConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates provider configuration details or toggles active status."""
    conn = db.query(IntegrationConnection).filter(IntegrationConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    if data.name:
        conn.name = data.name
    if data.is_active is not None:
        conn.is_active = data.is_active
    if data.is_default is not None:
        if data.is_default:
            db.query(IntegrationConnection).filter(IntegrationConnection.provider == conn.provider).update({"is_default": False})
        conn.is_default = data.is_default
    if data.api_key:
        conn.encrypted_secret = encrypt_secret(data.api_key)
        conn.masked_key = mask_secret(data.api_key)
        conn.status = "configured"

    db.commit()
    db.refresh(conn)

    return ConnectionResponse(
        id=conn.id,
        provider=conn.provider,
        name=conn.name,
        status=conn.status,
        model=data.model or "default",
        masked_key=conn.masked_key,
        is_active=conn.is_active,
        is_default=conn.is_default,
        last_synced_at=conn.last_synced_at,
        created_at=conn.created_at
    )

@router.post("/connections/{connection_id}/rotate", response_model=ConnectionResponse)
async def rotate_connection_secret(
    connection_id: str,
    data: ConnectionRotate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rotates provider credential with a new secret and immediately executes live validation."""
    conn = db.query(IntegrationConnection).filter(IntegrationConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    conn.encrypted_secret = encrypt_secret(data.new_api_key)
    conn.masked_key = mask_secret(data.new_api_key)
    conn.status = "validating"
    conn.last_synced_at = datetime.now(timezone.utc)
    db.commit()

    # Immediate live verification
    adapter = ai_router.get_adapter(provider=conn.provider)
    adapter.api_key = data.new_api_key
    health = await adapter.check_health()
    conn.status = "connected" if health.get("status") in ("connected", "healthy") else "invalid_credentials"
    db.commit()
    db.refresh(conn)

    return ConnectionResponse(
        id=conn.id,
        provider=conn.provider,
        name=conn.name,
        status=conn.status,
        model=get_default_model(conn.provider) or "default",
        masked_key=conn.masked_key,
        is_active=conn.is_active,
        is_default=conn.is_default,
        last_synced_at=conn.last_synced_at,
        created_at=conn.created_at
    )

@router.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a configured provider connection."""
    conn = db.query(IntegrationConnection).filter(IntegrationConnection.id == connection_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")
    db.delete(conn)
    db.commit()
    return {"success": True, "message": f"Connection '{connection_id}' removed."}

@router.get("/health", response_model=AIHealthResponse)
async def get_ai_engine_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Summarizes overall multi-provider operational health, fallback state, and token telemetry."""
    conns = db.query(IntegrationConnection).filter(IntegrationConnection.is_active == True).all()
    providers_status = []
    
    active_prov = settings.DEFAULT_AI_PROVIDER
    active_m = settings.DEFAULT_AI_MODEL
    has_live = False

    # Check primary adapter
    primary = ai_router.get_adapter()
    primary_health = await primary.check_health()
    providers_status.append(primary_health)
    if primary_health.get("status") in ("connected", "healthy"):
        has_live = True
        active_prov = primary.provider_name
        active_m = primary.model

    telemetry = monitoring_service.get_telemetry_summary()

    return AIHealthResponse(
        status="operational" if has_live else "deterministic_fallback",
        active_provider=active_prov,
        active_model=active_m,
        total_configured_connections=len(conns),
        providers=providers_status,
        telemetry_summary=telemetry
    )

@router.get("/usage")
def list_usage_records(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns fine-grained provider usage records."""
    records = db.query(ProviderUsageRecord).order_by(ProviderUsageRecord.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "provider": r.provider,
            "model": r.model,
            "operation": r.operation,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens,
            "duration_ms": r.duration_ms,
            "status": r.status,
            "timestamp": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]

@router.get("/usage/summary", response_model=UsageSummaryResponse)
def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates aggregated token and operational metrics grouped by provider and operation."""
    records = db.query(ProviderUsageRecord).all()
    
    total_calls = len(records)
    total_tokens = sum(r.total_tokens for r in records)
    total_prompt = sum(r.prompt_tokens for r in records)
    total_completion = sum(r.completion_tokens for r in records)

    by_provider: Dict[str, Dict[str, Any]] = {}
    by_operation: Dict[str, int] = {}

    for r in records:
        if r.provider not in by_provider:
            by_provider[r.provider] = {"calls": 0, "tokens": 0, "success_count": 0}
        by_provider[r.provider]["calls"] += 1
        by_provider[r.provider]["tokens"] += r.total_tokens
        if r.status == "success":
            by_provider[r.provider]["success_count"] += 1

        by_operation[r.operation] = by_operation.get(r.operation, 0) + 1

    active_conns = db.query(IntegrationConnection).filter(IntegrationConnection.is_active == True).count()

    return UsageSummaryResponse(
        total_calls=total_calls,
        total_tokens=total_tokens,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        active_connections_count=active_conns,
        by_provider=by_provider,
        by_operation=by_operation
    )

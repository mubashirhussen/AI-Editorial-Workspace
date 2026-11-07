import time
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db, check_db_health
from backend.app.services.ai_service import ai_service
from backend.app.services.monitoring_service import monitoring_service

router = APIRouter(tags=["Health"])

@router.get("/health/live")
def liveness_check():
    """
    Kubernetes / Platform Liveness probe:
    Returns 200 OK if the FastAPI process is running and able to handle requests.
    """
    return {
        "status": "alive",
        "application": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@router.get("/health/startup")
def startup_check(response: Response, db: Session = Depends(get_db)):
    """
    Kubernetes / Platform Startup probe:
    Returns 200 OK once the application has fully initialized its database engine and configuration.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "started",
            "database_initialized": True,
            "application": settings.PROJECT_NAME
        }
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "starting",
            "database_initialized": False,
            "error": str(e)
        }

@router.get("/health/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Kubernetes / Platform Readiness probe:
    Returns 200 OK if critical backend dependencies (database, Redis if configured) are accessible.
    Returns 503 Service Unavailable if any required dependency is unreachable.
    Does NOT fail if external AI provider is offline (deterministic fallback engine is available).
    """
    # Probe database using injected session dependency
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "detail": f"Database disconnected: {e}",
            "error": str(e),
            "dependencies": {
                "database": {"status": "unhealthy", "error": str(e)},
                "ai_engine": "fallback_ready"
            }
        }

    db_health = check_db_health()
    if db_health.get("status") != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "dependencies": {
                "database": db_health,
                "ai_engine": "fallback_ready"
            }
        }

    # Optional Redis probe if configured
    redis_status = "not_configured"
    if settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            r.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"unreachable: {e}"

    return {
        "status": "ready",
        "database": "connected",
        "db_latency_ms": db_health.get("latency_ms", 0.0),
        "dependencies": {
            "database": db_health,
            "redis": redis_status,
            "ai_engine": "live" if ai_service.is_available else "fallback_ready"
        }
    }

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Detailed operational diagnostics endpoint with telemetry and dependency latencies.
    """
    db_health = check_db_health()
    telemetry = monitoring_service.get_telemetry_summary()

    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_health.get("status") == "healthy" else "disconnected",
        "database_diagnostics": db_health,
        "application": settings.PROJECT_NAME,
        "version": "1.0.0",
        "ai_engine": {
            "configured": bool(settings.AI_API_KEY or settings.GROQ_API_KEY),
            "available": ai_service.is_available,
            "default_provider": settings.DEFAULT_AI_PROVIDER,
            "model": settings.AI_MODEL,
            "mode": "Live AI API" if ai_service.is_available else "Deterministic Fallback Engine"
        },
        "telemetry": telemetry
    }

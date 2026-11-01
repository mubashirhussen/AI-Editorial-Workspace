from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
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
        "version": "1.0.0"
    }

@router.get("/health/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Kubernetes / Platform Readiness probe:
    Returns 200 OK if critical backend dependencies (database) are accessible.
    Returns 503 Service Unavailable if the database is disconnected.
    Does NOT fail if external AI is unconfigured (offline fallback mode is supported).
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "dependencies": {
                "database": "ready",
                "ai_engine": "live" if ai_service.is_available else "fallback_ready"
            }
        }
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": "Database dependency unreachable.",
            "detail": str(e)
        }

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        
    telemetry = monitoring_service.get_telemetry_summary()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "application": settings.PROJECT_NAME,
        "version": "1.0.0",
        "ai_engine": {
            "configured": bool(settings.AI_API_KEY),
            "available": ai_service.is_available,
            "model": settings.AI_MODEL,
            "mode": "Live OpenAI API" if ai_service.is_available else "Deterministic Fallback Engine"
        },
        "telemetry": telemetry
    }

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque

class MonitoringService:
    """
    Lightweight, in-memory operational telemetry and AI monitoring service.
    Tracks execution metrics, AI provider status, error categories, and token usage
    without external dependencies (suitable for single-instance & containerized deployments).
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.start_time = datetime.now(timezone.utc)
        self.total_requests = 0
        self.total_errors = 0
        self.last_successful_operation: Optional[str] = None
        
        # AI Specific Telemetry
        self.ai_operations_total = 0
        self.ai_operations_success = 0
        self.ai_operations_fallback = 0
        self.ai_operations_failed = 0
        
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        
        # Recent activity ring buffer (thread-safe deque)
        self.recent_events: deque = deque(maxlen=max_history)

    def record_ai_operation(
        self,
        operation_type: str,
        duration_ms: float,
        status: str,  # "success", "fallback", "failed"
        provider_error: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        self.ai_operations_total += 1
        now_iso = datetime.now(timezone.utc).isoformat()

        if status == "success":
            self.ai_operations_success += 1
            self.last_successful_operation = now_iso
        elif status == "fallback":
            self.ai_operations_fallback += 1
            self.last_successful_operation = now_iso
        else:
            self.ai_operations_failed += 1

        if prompt_tokens:
            self.total_prompt_tokens += prompt_tokens
        if completion_tokens:
            self.total_completion_tokens += completion_tokens

        event = {
            "timestamp": now_iso,
            "operation": operation_type,
            "duration_ms": round(duration_ms, 2),
            "status": status,
            "error_category": provider_error,
            "tokens": {
                "prompt": prompt_tokens or 0,
                "completion": completion_tokens or 0,
                "total": (prompt_tokens or 0) + (completion_tokens or 0)
            } if (prompt_tokens or completion_tokens) else None
        }
        self.recent_events.appendleft(event)
        return event

    def record_request_error(self, path: str, error_category: str, status_code: int):
        self.total_errors += 1
        self.recent_events.appendleft({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": f"HTTP {status_code} {path}",
            "duration_ms": 0.0,
            "status": "error",
            "error_category": error_category,
            "tokens": None
        })

    def get_telemetry_summary(self) -> Dict[str, Any]:
        uptime_seconds = round((datetime.now(timezone.utc) - self.start_time).total_seconds(), 1)
        
        return {
            "uptime_seconds": uptime_seconds,
            "last_successful_operation": self.last_successful_operation,
            "ai_telemetry": {
                "total_operations": self.ai_operations_total,
                "successful_operations": self.ai_operations_success,
                "fallback_operations": self.ai_operations_fallback,
                "failed_operations": self.ai_operations_failed,
                "cumulative_tokens": {
                    "prompt_tokens": self.total_prompt_tokens,
                    "completion_tokens": self.total_completion_tokens,
                    "total_tokens": self.total_prompt_tokens + self.total_completion_tokens
                }
            },
            "recent_events": list(self.recent_events)[:10]
        }

monitoring_service = MonitoringService()


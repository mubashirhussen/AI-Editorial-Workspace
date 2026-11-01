from backend.app.services.research.extraction_service import extraction_service, ResearchExtractionService

# Legacy alias
ExtractionService = ResearchExtractionService

__all__ = ["extraction_service", "ExtractionService", "ResearchExtractionService"]

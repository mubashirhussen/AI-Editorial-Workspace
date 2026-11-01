# Import all the models, so that Base has them before being
# imported by Alembic or database initialization
from backend.app.core.database import Base
from backend.app.models.base import (
    ResearchProject,
    Source,
    SourceAnalysis,
    ResearchBrief,
    WritingDraft,
    WritingSuggestion,
    EditorialOutput
)

__all__ = [
    "Base",
    "ResearchProject",
    "Source",
    "SourceAnalysis",
    "ResearchBrief",
    "WritingDraft",
    "WritingSuggestion",
    "EditorialOutput"
]


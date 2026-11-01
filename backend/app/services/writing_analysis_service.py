from backend.app.services.writing.writing_analyzer import writing_analyzer, DeterministicWritingAnalyzer

# Legacy alias
writing_analysis_service = writing_analyzer
WritingAnalysisService = DeterministicWritingAnalyzer

__all__ = ["writing_analysis_service", "WritingAnalysisService", "writing_analyzer", "DeterministicWritingAnalyzer"]

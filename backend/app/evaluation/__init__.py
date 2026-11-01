"""
Evaluation and Quality Benchmarking Framework for AI Editorial Workspace.
Provides offline and online evaluation suites across Research, Writing,
Editorial, and Hallucination detection.
"""

import sys
import os

# Ensure the parent of backend is in sys.path so 'backend.app' can always be resolved
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
workspace_root = os.path.dirname(backend_dir)
for p in [workspace_root, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from .runners.runner import EvaluationRunner

__all__ = ["EvaluationRunner"]

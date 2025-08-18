"""
Purpose: Public API surface for the scoring module.
Description: Exposes the main scoring functions for external use.
Key Functions/Classes: `score_domain`, `score_labeled_domain`, `score_labeled_file`.
"""

from .api import score_domain, score_labeled_domain, score_labeled_file

__all__ = [
    "score_domain",
    "score_labeled_domain", 
    "score_labeled_file",
]
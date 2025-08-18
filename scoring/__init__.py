"""
Purpose: Public API surface for the lightweight LLM scoring pipeline.
Description: Exposes Python-callable helpers to score a single domain or a file
of aggregated contexts. Thin wrapper that delegates to `api` module.
Key Functions/Classes: `score_domain`, `score_file`, `score_labeled_domain`, `score_labeled_file`.
"""

# AIDEV-NOTE: Keep __all__ minimal and stable for import ergonomics.

from .api import score_domain, score_file, score_labeled_domain, score_labeled_file

__all__ = [
    "score_domain",
    "score_file",
    "score_labeled_domain", 
    "score_labeled_file",
]
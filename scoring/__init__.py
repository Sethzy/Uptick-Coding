"""
Purpose: Uptick scoring module for domain classification using LLM.
Description: Provides domain scoring, classification, and numerical scoring capabilities.
Key Functions/Classes: `score_domain`, `score_raw_crawler_file`.
Note: Now uses unified scoring that automatically handles both raw and enriched data.
"""

from .api import score_domain, score_raw_crawler_file

__all__ = [
    "score_domain",
    "score_raw_crawler_file",
]
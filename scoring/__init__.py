"""
Purpose: Package initializer for the scoring module.
Description: Exposes configuration helpers and constants for external consumers.
Key Functions/Classes: ScoringConfig dataclass, load_config; DEFAULT_PROMPT_VERSION.
"""

# AIDEV-NOTE: Keep exports minimal; expand as submodules are implemented.

from .config import ScoringConfig, load_config
from .constants import DEFAULT_PROMPT_VERSION

__all__ = [
    "ScoringConfig",
    "load_config",
    "DEFAULT_PROMPT_VERSION",
]



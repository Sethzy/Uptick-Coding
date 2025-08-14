"""
Purpose: Configuration management for the scoring pipeline.
Description: Defines a typed configuration dataclass and helpers to load from YAML/JSON and env overrides.
Key Functions/Classes: ScoringConfig, load_config, load_config_from_path.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotenv import load_dotenv

# AIDEV-NOTE: Keep config minimal per PRD; extend only when required by scope.


@dataclass
class RetryPolicy:
    max_attempts: int = 2
    base_delay_ms: int = 250
    max_delay_ms: int = 3_000


@dataclass
class Thresholds:
    tier_a: int = 75
    tier_b: int = 50


@dataclass
class ScoringConfig:
    model: str = "qwen3-30b-a3b"
    temperature: float = 0.0
    thresholds: Thresholds = field(default_factory=Thresholds)
    max_evidence: int = 3
    timeout_s: int = 90
    max_tokens: int = 1024
    worker_count: int = 3
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    endpoint_base_url: str = "https://openrouter.ai/api/v1"


def _load_json_or_yaml(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Naive detection; YAML optional to keep deps minimal in v1
    if path.endswith(".json") or text.strip().startswith("{"):
        return json.loads(text)
    # Minimal YAML support: key: value pairs, no lists or nesting beyond one level
    data: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _apply_env_overrides(cfg: ScoringConfig) -> ScoringConfig:
    # Load common env keys if present
    model = os.getenv("SCORING_MODEL") or os.getenv("CUSTOM_MODEL")
    if model:
        cfg.model = model
    temperature = os.getenv("SCORING_TEMPERATURE")
    if temperature is not None:
        try:
            cfg.temperature = float(temperature)
        except ValueError:
            pass
    timeout = os.getenv("SCORING_TIMEOUT_S")
    if timeout is not None:
        try:
            cfg.timeout_s = int(timeout)
        except ValueError:
            pass
    workers = os.getenv("SCORING_WORKER_COUNT")
    if workers is not None:
        try:
            cfg.worker_count = int(workers)
        except ValueError:
            pass
    max_tokens = os.getenv("SCORING_MAX_TOKENS") or os.getenv("CONTEXT_SIZE")
    if max_tokens is not None:
        try:
            cfg.max_tokens = int(max_tokens)
        except ValueError:
            pass
    endpoint = os.getenv("OPENROUTER_ENDPOINT") or os.getenv("OPENAI_ENDPOINT")
    if endpoint:
        cfg.endpoint_base_url = endpoint.rstrip("/")
    return cfg


def load_config_from_dict(data: Dict) -> ScoringConfig:
    cfg = ScoringConfig()
    if "model" in data:
        cfg.model = str(data["model"]) 
    if "temperature" in data:
        try:
            cfg.temperature = float(data["temperature"]) 
        except Exception:
            pass
    if "thresholds" in data and isinstance(data["thresholds"], dict):
        t = data["thresholds"]
        cfg.thresholds = Thresholds(
            tier_a=int(t.get("A", t.get("tier_a", cfg.thresholds.tier_a))),
            tier_b=int(t.get("B", t.get("tier_b", cfg.thresholds.tier_b))),
        )
    if "max_evidence" in data:
        cfg.max_evidence = int(data["max_evidence"]) 
    if "timeout_s" in data:
        cfg.timeout_s = int(data["timeout_s"]) 
    if "max_tokens" in data:
        cfg.max_tokens = int(data["max_tokens"]) 
    if "worker_count" in data:
        cfg.worker_count = int(data["worker_count"]) 
    if "retry" in data and isinstance(data["retry"], dict):
        r = data["retry"]
        cfg.retry = RetryPolicy(
            max_attempts=int(r.get("max_attempts", cfg.retry.max_attempts)),
            base_delay_ms=int(r.get("base_delay_ms", cfg.retry.base_delay_ms)),
            max_delay_ms=int(r.get("max_delay_ms", cfg.retry.max_delay_ms)),
        )
    return _apply_env_overrides(cfg)


def load_config_from_path(path: str) -> ScoringConfig:
    data = _load_json_or_yaml(path)
    return load_config_from_dict(data)


def load_config(path: Optional[str] = None, overrides: Optional[Dict] = None) -> ScoringConfig:
    # Load .env at the start so subsequent env lookups are populated
    load_dotenv(override=False)
    if path:
        cfg = load_config_from_path(path)
    else:
        cfg = ScoringConfig()
    if overrides:
        # Shallow override; intended for CLI flags
        merged = {**cfg.__dict__, **overrides}
        cfg = load_config_from_dict(merged)
    return _apply_env_overrides(cfg)



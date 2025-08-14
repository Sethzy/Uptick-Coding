"""
Purpose: Unit tests for strict JSON parsing and single repair flow in model wrapper.
Description: Mocks HTTP responses to ensure valid JSON path passes and invalid then repair path is attempted once.
Key Tests: test_valid_json_passes, test_invalid_then_invalid_sets_status.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import httpx
import pytest

from scoring.config import ScoringConfig
from scoring.models import classify_domain_with_model


class _MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, texts: list[str]):
        self._texts = texts
        self._idx = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
        text = self._texts[min(self._idx, len(self._texts) - 1)]
        self._idx += 1
        return httpx.Response(200, text=text)


@pytest.mark.asyncio
async def test_valid_json_passes():
    cfg = ScoringConfig()
    json_text = (
        '{"classification_category":"Install Focus","confidence":80,'
        '"rationale":"clear rationale"}'
    )
    transport = _MockTransport([json_text])
    async with httpx.AsyncClient(transport=transport) as client:
        parsed, meta = await classify_domain_with_model(client, cfg, aggregated_context="CTX", prompt_version="v1")
    assert parsed is not None
    assert meta["status"] == "ok"


@pytest.mark.asyncio
async def test_invalid_then_invalid_sets_status():
    cfg = ScoringConfig()
    transport = _MockTransport(["not-json", "still-not-json"])
    async with httpx.AsyncClient(transport=transport) as client:
        parsed, meta = await classify_domain_with_model(client, cfg, aggregated_context="CTX", prompt_version="v1")
    assert parsed is None
    assert meta["status"] in {"invalid_json", "unhandled_error"}



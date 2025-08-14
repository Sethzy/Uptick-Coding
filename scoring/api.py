"""
Purpose: Public Python API for scoring.
Description: Synchronous wrappers for classifying a single domain or a JSONL file of inputs.
Key Functions/Classes: score_domain, score_file.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set
from uuid import uuid4

import httpx

from .config import ScoringConfig, load_config
from .constants import DEFAULT_PROMPT_VERSION
from .evidence import validate_and_normalize_evidence
from .io_csv import append_row as append_csv_row
from .io_jsonl import append_jsonl, append_raw_jsonl
from .models import classify_domain_with_model
from .logging import get_logger
from .run import build_http_client


def _iter_jsonl(path: str | Path) -> Iterable[Dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _flatten_for_csv(domain: str, result: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "domain": domain,
        "classification_category": result.get("classification_category", ""),
        "confidence": result.get("confidence", ""),
        "rationale": result.get("rationale", ""),
        "other_sublabel": result.get("other_sublabel", ""),
        "other_sublabel_definition": result.get("other_sublabel_definition", ""),
        "model_name": result.get("model_name", ""),
        "prompt_version": result.get("prompt_version", ""),
        "run_id": result.get("run_id", ""),
        "evidence_url_1": "",
        "evidence_snippet_1": "",
        "evidence_url_2": "",
        "evidence_snippet_2": "",
        "evidence_url_3": "",
        "evidence_snippet_3": "",
    }
    ev = result.get("evidence") or []
    for idx in range(min(3, len(ev))):
        row[f"evidence_url_{idx+1}"] = ev[idx].get("url", "")
        row[f"evidence_snippet_{idx+1}"] = ev[idx].get("snippet", "")
    return row


async def _classify_one_async(
    client: httpx.AsyncClient,
    cfg: ScoringConfig,
    domain: str,
    aggregated_context: str,
    prompt_version: str,
    run_id: str,
    raw_jsonl_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    parsed, meta = await classify_domain_with_model(client, cfg, aggregated_context, prompt_version)
    if meta.get("raw") and raw_jsonl_path:
        append_raw_jsonl(raw_jsonl_path, meta["raw"])  # persist raw model text

    base: Dict[str, Any] = {
        "domain": domain,
        "model_name": meta.get("model_name"),
        "prompt_version": meta.get("prompt_version"),
        "run_id": run_id,
        "token_counts": meta.get("token_counts"),
    }

    if parsed is None:
        base.update({"status": meta.get("status", "error"), "error": meta.get("error")})
        return base

    # Evidence validation
    valid_evidence, errors = validate_and_normalize_evidence(
        aggregated_context, [e.model_dump() for e in parsed.evidence]  # type: ignore[arg-type]
    )
    if not valid_evidence:
        base.update({
            "status": "invalid_evidence",
            "error": "; ".join(errors) if errors else "no_valid_evidence",
            "classification_category": parsed.classification_category,
            "confidence": parsed.confidence,
            "rationale": parsed.rationale,
            "evidence": [],
        })
        if parsed.classification_category == "Other":
            # Include sublabel details for transparency even when evidence invalid
            base.update({
                "other_sublabel": getattr(parsed, "other_sublabel", None),
                "other_sublabel_definition": getattr(parsed, "other_sublabel_definition", None),
            })
        return base

    base.update({
        "status": "ok",
        "classification_category": parsed.classification_category,
        "confidence": parsed.confidence,
        "rationale": parsed.rationale,
        "evidence": valid_evidence,
    })
    if parsed.classification_category == "Other":
        base.update({
            "other_sublabel": getattr(parsed, "other_sublabel", None),
            "other_sublabel_definition": getattr(parsed, "other_sublabel_definition", None),
        })
    return base


def score_domain(
    *,
    domain: str,
    aggregated_context: str,
    cfg: Optional[ScoringConfig] = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> Dict[str, Any]:
    cfg = cfg or load_config()
    run_id = str(uuid4())
    async def _inner() -> Dict[str, Any]:
        async with build_http_client(cfg) as client:
            return await _classify_one_async(client, cfg, domain, aggregated_context, prompt_version, run_id)
    return asyncio.run(_inner())


def score_file(
    *,
    input_jsonl: str | Path,
    output_jsonl: Optional[str | Path] = None,
    output_csv: Optional[str | Path] = None,
    cfg: Optional[ScoringConfig] = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    raw_jsonl: Optional[str | Path] = None,
    checkpoint: Optional[str | Path] = None,
    workers: Optional[int] = None,
) -> None:
    cfg = cfg or load_config()
    run_id = str(uuid4())
    logger = get_logger()
    worker_count = workers or cfg.worker_count

    # Derive default output paths (more descriptive) if not supplied
    input_path = Path(input_jsonl)
    out_dir = input_path.parent
    if output_jsonl is None:
        output_jsonl = str(out_dir / "classifications.jsonl")
    if output_csv is None:
        output_csv = str(out_dir / "classifications-review.csv")
    if raw_jsonl is None:
        raw_jsonl = str(out_dir / "raw-model-responses.jsonl")

    def _load_checkpoint(path: Path) -> Set[str]:
        if not path.exists():
            return set()
        return set([line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])

    def _append_checkpoint(path: Path, domain: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(domain + "\n")

    async def _inner() -> None:
        async with build_http_client(cfg) as client:
            # Prepare tasks and checkpoint
            ckpt_path: Optional[Path]
            if checkpoint:
                ckpt_path = Path(checkpoint)
            else:
                # Default checkpoint alongside outputs with a descriptive name
                ckpt_path = Path(output_jsonl).with_name("processed-domains.ckpt") if output_jsonl else None
            processed: Set[str] = _load_checkpoint(ckpt_path) if ckpt_path else set()
            items: List[Tuple[str, str, str]] = []
            for obj in _iter_jsonl(input_jsonl):
                d = obj.get("domain", "")
                if ckpt_path and d in processed:
                    continue
                rid = str(obj.get("record_id", "")) if obj.get("record_id") is not None else ""
                items.append((d, obj.get("aggregated_context", ""), rid))

            sem = asyncio.Semaphore(max(1, int(worker_count)))
            write_lock = asyncio.Lock()

            async def _run_one(d: str, ctx: str, rid: str) -> None:
                async with sem:
                    logger.log("classify.start", domain=d, run_id=run_id, model=cfg.model, prompt_version=prompt_version)
                    result = await _classify_one_async(
                        client, cfg, domain=d, aggregated_context=ctx, prompt_version=prompt_version, run_id=run_id, raw_jsonl_path=raw_jsonl
                    )
                    logger.log("classify.end", domain=d, run_id=run_id, status=result.get("status"), error=result.get("error"))
                    async with write_lock:
                        if output_jsonl:
                            # Carry through record_id if present on input aggregated JSONL
                            result_with_id = dict(result)
                            if rid:
                                result_with_id["record_id"] = rid
                            append_jsonl(output_jsonl, result_with_id)
                        if output_csv:
                            row = _flatten_for_csv(d, result)
                            if rid:
                                row["record_id"] = rid
                            append_csv_row(output_csv, row)
                        if ckpt_path:
                            _append_checkpoint(ckpt_path, d)

            await asyncio.gather(*[ _run_one(d, c, r) for d, c, r in items ])

    asyncio.run(_inner())



# PRD: LM Studio Local LLM Integration for Scoring (Qwen 30B 4-bit)

## Introduction / Overview

This feature integrates a locally hosted Large Language Model (LLM) via LM Studio into this project to support the existing workflows that score and rank scraped website data. The primary local model will be a 4-bit quantized Qwen model (`qwen/qwen3-30b-a3b-2507`) accessed through LM Studio’s OpenAI-compatible REST API (`/v1/chat/completions`).

The solution provides a minimal, reliable local-first integration with a configurable fallback to cloud providers (e.g., OpenAI-compatible endpoints such as OpenRouter or a Modal-hosted endpoint) via environment variables. The integration will expose shared client wrappers in both TypeScript and Python to be reused across scripts and services in the repo.

## Goals

- Local-first inference: default to LM Studio on the developer’s machine for low-latency iteration and no external data egress.
- Cloud fallback: optional, controlled by environment variables, to a single cloud provider (OpenAI-compatible) when local is not available.
- Reusable wrappers: provide a simple, unified client in both TypeScript and Python to call chat completions for scoring and ranking tasks.
- Default scoring system prompt: include a clear, reusable prompt template tailored to evaluating and ranking scraped website content.
- Minimal configuration: require only a few environment variables to switch between providers and models.
- Non-streaming responses by default for simpler pipeline integration (optional streaming flag for future use).

## User Stories

1. As a developer, I can run a scoring pipeline that calls the local LM Studio model without changing code, relying only on `.env` settings.
2. As a developer, I can enable cloud fallback via an environment flag so that if LM Studio is not running, the pipeline automatically uses a cloud provider.
3. As a developer, I can use a single function (`chat`) from the shared client wrapper in TS or Python to get a completion for a given list of messages.
4. As a developer, I can customize the model name via environment variables without changing code.
5. As a developer, I can use an out-of-the-box system prompt that scores and ranks scraped content consistently.

## Functional Requirements

1. OpenAI-compatible API

   - The local provider must communicate with LM Studio using OpenAI-compatible REST endpoints.
   - Default base URL: `http://localhost:1234/v1`.
   - Endpoint: `/v1/chat/completions`.
   - Default model: `qwen/qwen3-30b-a3b-2507` (configurable).

2. Shared Client Wrappers

   - Provide a TypeScript client and a Python client that expose a unified interface for chat completions.
   - Recommended locations:
     - TypeScript: `Uptick-Coding/CRAWL4AI test 1/reference-perplexity-deep-research-backend/llm/client.ts`
     - Python: `Uptick-Coding/CRAWL4AI test 1/scripts/llm_client.py`
   - Core API (both languages):
     - `chat({ messages, temperature?, maxTokens?, stream? }): Promise<string | AsyncIterable<string>>`
     - Non-streaming is the default; `stream` is optional and may be implemented later.

3. Configuration and Fallback

   - Environment variables control provider selection and credentials:
     - `LLM_PROVIDER` (default: `local`) — options: `local`, `openai`, `openrouter`, `modal`.
     - `LLM_FALLBACK_ENABLED` (default: `true`) — when true, attempt cloud provider if local fails.
     - Local settings:
       - `LMSTUDIO_API_BASE` (default: `http://localhost:1234/v1`)
       - `LMSTUDIO_MODEL` (default: `qwen/qwen3-30b-a3b-2507`)
     - Cloud settings (OpenAI-compatible):
       - `CLOUD_API_BASE` (e.g., `https://api.openai.com/v1` or OpenRouter base)
       - `CLOUD_API_KEY` (string)
       - `CLOUD_MODEL` (string)
   - Fallback behavior:
     - Try `local` first. If connection fails or returns a transport error, and `LLM_FALLBACK_ENABLED=true`, route to `LLM_PROVIDER` if it is not `local`.
     - If `LLM_PROVIDER=local` and fallback is enabled, attempt `openrouter` then `openai` (or another ordered preference via `LLM_PROVIDER_PREFERENCE`, if provided).

4. Security and Privacy

   - No logging of prompt or completion content to disk by default.
   - Allow optional debug logging of metadata (status codes, provider used) when `LLM_DEBUG=true`.

5. Timeouts and Retries

   - Default request timeout: 60 seconds.
   - Retries: up to 2 retries with exponential backoff on transient errors (connection refused, 429/5xx).

6. Scoring Prompt Template

   - Provide a default system prompt template aimed at scoring and ranking scraped website data for relevance and quality.
   - Example template (to be included in code as a constant):
     - Name: `DEFAULT_SCORING_SYSTEM_PROMPT`
     - Behavior: Given website content and target criteria, return a JSON object with fields: `relevance_score` (0-100), `confidence` (0-1), `key_rationales` (array of strings), `category` (string label), and `notes` (string). Keep output strictly valid JSON.

7. Integration Points

   - The wrappers must be callable from:
     - TypeScript workflows under `reference-perplexity-deep-research-backend/` (e.g., `deep-research-crawl4ai.ts`).
     - Python scripts under `CRAWL4AI test 1/scripts/` (e.g., `crawl_homepages.py`, scoring helpers).
   - The scoring logic that consumes the wrapper should be able to accept raw page content and return a structured score object.

8. Non-Streaming Default
   - Use non-streaming mode by default to simplify scoring pipelines and CSV workflows. Streaming can be added later behind a flag.

## Non-Goals (Out of Scope)

- UI changes or visualization dashboards.
- Remote deployment or multi-machine orchestration.
- Embeddings or vector databases (unless trivially available via the chosen provider; not required).
- Fine-tuning or model training.

## Design Considerations (Optional)

- The Qwen 30B 4-bit model may have higher first-token latency compared to smaller models; consider small `maxTokens` defaults for scoring.
- Keep messages and page excerpts concise to stay within context windows.
- Consistent JSON output from the model simplifies downstream parsing for ranking and CSV updates.
- Provide a simple TypeScript and Python helper to coerce/validate the JSON response and handle invalid outputs gracefully.

## Technical Considerations (Optional)

- Model endpoint parity: both local and cloud providers must accept OpenAI-compatible payloads (messages array, model name, temperature, max_tokens).
- For OpenRouter and Modal, use their OpenAI-compatible surface when possible; otherwise, a thin adapter may be needed.
- Include user agent or `X-Client` header for analytics if desired; optional and disabled by default.
- Concurrency target: single-user dev (≤ 2 concurrent requests) — no queueing or pooling needed initially.

## Success Metrics

- Developer can run a smoke test script that calls the local LM Studio model and receives a valid JSON scoring response in under 60 seconds.
- When LM Studio is stopped, setting `LLM_FALLBACK_ENABLED=true` and valid cloud credentials results in a successful scoring response without code changes.
- The shared wrappers are used by at least one TS and one Python script in the repo without modification.

## Open Questions

- Exact call sites to replace in the existing pipelines (TS and Python) and the precise scoring rubric for each use-case.
- Preferred cloud provider for fallback (OpenRouter vs. OpenAI vs. Modal-managed endpoint) and the order of preference.
- Limits for input size (tokenization strategy or chunking) per pipeline.

## Acceptance Criteria

1. Environment toggle

   - `.env` supports selecting `LLM_PROVIDER` and enabling `LLM_FALLBACK_ENABLED`.
   - Example `.env.example` is provided with the required variables.

2. Working local integration

   - A simple TS and Python test script demonstrates a non-streaming call to LM Studio with `qwen/qwen3-30b-a3b-2507` returning valid JSON per the template.

3. Optional fallback

   - When local is unavailable and `LLM_FALLBACK_ENABLED=true` with valid `CLOUD_API_*` set, the same test scripts succeed via the fallback provider without code changes.

4. Documentation

   - README section documents LM Studio setup (model load, server start), environment variables, and how to run the test scripts.

5. Quality and reliability
   - Default timeout and retries implemented; no prompt/output content is logged by default.

## Appendix: Environment Variables

Required (with defaults where noted):

- `LLM_PROVIDER=local` — one of `local`, `openai`, `openrouter`, `modal`.
- `LLM_FALLBACK_ENABLED=true`
- `LMSTUDIO_API_BASE=http://localhost:1234/v1`
- `LMSTUDIO_MODEL=qwen/qwen3-30b-a3b-2507`
- `CLOUD_API_BASE` — e.g., `https://api.openai.com/v1` or OpenRouter base (optional unless fallback is used)
- `CLOUD_API_KEY` — string (optional unless fallback is used)
- `CLOUD_MODEL` — string (optional unless fallback is used)
- `LLM_DEBUG` — optional, when `true` logs metadata only

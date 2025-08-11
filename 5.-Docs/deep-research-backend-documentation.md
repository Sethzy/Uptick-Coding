### Feature Overview

The Deep Research Backend provides an AI-powered research API designed to iteratively explore a topic, extract structured learnings from the web, and produce final answers or detailed reports. It replaces Firecrawl with a fully compatible Crawl4AI-based adapter and adds optional Supabase-backed persistence and auth-protected endpoints for specialized stock research.

- **Business value**: Automates comprehensive research and reporting; enables specialized investment workflows; exposes HTTP endpoints that the frontend can call.
- **Problem it solves**: Searching, filtering, and synthesizing information across many sources with repeatable, parameterized depth/breadth control.
- **Target users/use cases**: Internal product features that need research-as-a-service, investment analysis (ticker-specific workflows), and long-form report generation.

```mermaid
flowchart LR
  Client[Frontend/Client] -->|HTTP| API[Express API (Node, :3051)]
  API -->|/api/*| Deep[deepResearch()]
  Deep --> Prov[AI Providers (OpenAI/Fireworks)]
  Deep --> C4A[Crawl4AI Adapter]
  C4A -->|HTTP :8001 (or :8000 via Docker)| PyAPI[Crawl4AI FastAPI Service]
  Deep -->|learnings/urls| Synthesize[writeFinalAnswer / writeFinalReport]
  API --> Supa[(Supabase DB)]
  API -->|JSON| Client
```

### Application Structure

- Backend root: `backend/`
- Runtime: Node.js (TypeScript, ESM), Express server
- Research engine: Crawl4AI service (Python, FastAPI) called via a Firecrawl-compatible adapter
- Optional persistence and auth: Supabase

Key files and directories:

- `src/api.ts`: Express server and HTTP routes
- `src/deep-research-crawl4ai.ts`: Core iterative research loop, SERP query generation, content processing, final synthesis
- `src/crawl4ai-adapter.ts`: FirecrawlApp-compatible interface that calls the Python Crawl4AI service
- `src/ai/providers.ts`: LLM provider/model selection and prompt trimming utilities
- `src/prompt.ts`: System prompt used across LLM calls
- `src/feedback.ts`: Generates follow-up questions for better research plans
- `src/middleware/auth.ts`: Supabase JWT verification middleware
- `src/db/research.ts`: Supabase DB helpers (save, delete, fetch)
- `src/supabase.ts`: Supabase anon client
- `src/supabase-service.ts`: Supabase service-role client (bypasses RLS for backend ops)
- `run.ts`: CLI runner for manual research sessions
- `crawl4ai_deep_research.py`: Python FastAPI app powering concurrent crawling and DDGS-backed search
- `docker-compose.yml`, `Dockerfile`, `Dockerfile.python`: Local container orchestration

### Functionalities Overview

- **Run research** (`POST /api/research`):

  - Body: `{ query: string, breadth?: number=3, depth?: number=3 }`
  - Flow: deepResearch → Crawl4AI → learnings/urls → writeFinalAnswer → JSON response
  - Files: `src/api.ts`, `src/deep-research-crawl4ai.ts`, `src/crawl4ai-adapter.ts`

- **Generate long report** (`POST /api/generate-report`):

  - Body: `{ query: string, breadth?: number=3, depth?: number=3 }`
  - Flow: deepResearch → writeFinalReport (appends Sources) → JSON response
  - Files: same as above

- **Specialized stock research (sequential 5-chapter reports)** (`POST /api/stocks/:ticker/specialized-research`):

  - Auth required (Supabase JWT in `Authorization: Bearer <token>`)
  - Executes five themed research runs; persists results to Supabase
  - Files: `src/api.ts`, `src/middleware/auth.ts`, `src/db/research.ts`

- **Delete research record** (`DELETE /api/research/:id`):

  - Auth required; only owner can delete
  - Files: `src/api.ts`, `src/db/research.ts`

- **Progress polling** (`GET /api/progress/:query`):

  - Returns last-known progress for a query
  - Files: `src/api.ts`

- **Health** (`GET /api/health`) and Root (`GET /`) endpoints

Data flow (deep research):

1. Generate SERP queries via LLM (`generateObject`) → 2) Crawl4AI Adapter calls Python FastAPI `POST /api/multi-search` → 3) Extract learnings and follow-ups via LLM → 4) Recurse with reduced depth/breadth → 5) Synthesize final answer/report (LLM) → 6) Return JSON and optionally persist to Supabase.

### Technical Implementation

- **Stack**:

  - Node.js + TypeScript (ESM), Express, Zod, `ai` SDK, Supabase JS
  - Python 3 + FastAPI, Crawl4AI, DDGS (DuckDuckGo Search)
  - Logging via console; optional Winston deps present

- **Models/Providers** (`src/ai/providers.ts`):

  - OpenAI via `OPENROUTER_KEY` (or `OPENAI_ENDPOINT`) and Fireworks `FIREWORKS_KEY`
  - Prefers `CUSTOM_MODEL` if set; else DeepSeek R1 via Fireworks; else `o3-mini`
  - Prompt trimming with js-tiktoken + recursive splitter

- **Crawl4AI Adapter** (`src/crawl4ai-adapter.ts`):

  - Firecrawl-compatible API: `search(query, { timeout, limit, scrapeOptions })`
  - Calls Python `POST /api/multi-search` at `CRAWL4AI_API_URL` (default `http://localhost:8001`)
  - Returns `{ data: [{ markdown, url }] }` matching Firecrawl shape
  - Graceful timeouts → return empty set for resilience

- **Python service** (`crawl4ai_deep_research.py`):

  - Endpoints: `/health`, `POST /api/multi-search`, `POST /api/streaming-search`, `GET /api/test-concurrent`
  - DDGS-backed URL discovery when adapter sends `urls: []`
  - Concurrent crawling (10–20+), pruning content filter (~0.25), structured markdown output
  - Environment-tunable thresholds and concurrency

- **Database** (`src/db/research.ts`):

  - Table: `research_results` (JSONB `content` and `metadata` fields assumed)
  - Uses service-role client by default; falls back to anon client when needed
  - Helpers: save success/failed, history, fetch by id, delete with ownership check

- **Environment variables**

  - Node/Express:
    - `PORT` (default 3051)
    - `CRAWL4AI_API_URL` (default `http://localhost:8001`; set to `http://localhost:8000` when using docker-compose as configured)
    - `OPENROUTER_KEY`, `OPENAI_ENDPOINT`, `CUSTOM_MODEL`
    - `FIREWORKS_KEY` (DeepSeek R1 support)
    - `CONTEXT_SIZE` (default 128000)
    - `SUPABASE_URL`, `SUPABASE_ANON_KEY` (required)
    - `SUPABASE_SERVICE_ROLE_KEY` (for backend writes, optional but recommended)
  - Python/Crawl4AI:
    - `DDGS_BACKENDS` (e.g., `google,yahoo,brave,duckduckgo,bing`)
    - `DDGS_MAX_RESULTS`, `DDGS_REGION`, `DDGS_SAFESEARCH`
    - `CRAWL4AI_MAX_CONCURRENT`, `CRAWL4AI_FILTER_THRESHOLD`, `CRAWL4AI_MEMORY_THRESHOLD`, `CRAWL4AI_TIMEOUT`

- **Docker** (`docker-compose.yml`):
  - Node service depends on the Python service
  - Python service publishes on `8000` (compose) but TS adapter defaults to `8001` → set `CRAWL4AI_API_URL=http://localhost:8000` when using compose

### Integration Points

- **Frontend**:

  - CORS enabled; call `POST /api/research` and `POST /api/generate-report`
  - For specialized stock research and delete: include `Authorization: Bearer <supabase_jwt>`

- **Supabase**:

  - Auth: `authenticateUser` verifies JWT via `supabase.auth.getUser(token)`
  - Persistence: writes to `research_results` via service role, with anon fallback
  - Ensure RLS policies align with access patterns if not using service role

- **Python service**:
  - Ensure it is reachable at `CRAWL4AI_API_URL`
  - If using docker-compose, adapter URL should be `http://localhost:8000`

### Development Status

- Core endpoints functional and covered by modular files
- Known integration notes:
  - Port mismatch risk: adapter default (8001) vs docker-compose (8000). Set `CRAWL4AI_API_URL` accordingly.
  - docker-compose command references `crawl4ai_api:app`; repo provides `crawl4ai_deep_research.py` with `app`. Ensure entrypoint/name alignment.

Planned improvements:

- Optional SSE for real-time progress streaming from Node (current progress map is polling-only)
- More granular error codes and rate-limit handling
- Add tests for DB layer and adapter resiliency

### Usage Examples

- Run server locally:

```bash
cd backend
pnpm install
pnpm dev
# Ensure Python service is running and CRAWL4AI_API_URL is set appropriately
```

- Research (concise answer):

```bash
curl -X POST http://localhost:3051/api/research \
  -H 'Content-Type: application/json' \
  -d '{"query":"Explain diffusion models for images","breadth":3,"depth":2}'
```

- Long report:

```bash
curl -X POST http://localhost:3051/api/generate-report \
  -H 'Content-Type: application/json' \
  -d '{"query":"State of vector databases in 2025","breadth":3,"depth":2}'
```

- Specialized stock research (auth required):

```bash
curl -X POST http://localhost:3051/api/stocks/NVDA/specialized-research \
  -H 'Authorization: Bearer <SUPABASE_JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"breadth":3,"depth":2}'
```

- Delete a research record (auth required):

```bash
curl -X DELETE http://localhost:3051/api/research/<ID> \
  -H 'Authorization: Bearer <SUPABASE_JWT>'
```

### Troubleshooting Guide

- **401 Invalid token / Authentication required**: Ensure `Authorization: Bearer <JWT>` from Supabase; token not expired; `SUPABASE_URL`/`SUPABASE_ANON_KEY` set.
- **500 Crawl4AI service unavailable**: Start Python FastAPI service; set `CRAWL4AI_API_URL` to correct host/port; check docker-compose mapping (8000).
- **Timeouts / empty results**: Increase adapter timeout; ensure internet connectivity; reduce `breadth`/`depth`; check DDGS throttling.
- **Database write failures**: Provide `SUPABASE_SERVICE_ROLE_KEY`; verify `research_results` table exists and RLS policies; inspect error payloads in logs.
- **Port mismatch**: If using docker-compose, adapter must target `http://localhost:8000`; or update compose/command to 8001 to match defaults.
- **Module/entrypoint mismatch**: docker-compose references `crawl4ai_api:app`; if using `crawl4ai_deep_research.py`, update command to `python3 -m uvicorn crawl4ai_deep_research:app --host 0.0.0.0 --port 8000 --reload`.

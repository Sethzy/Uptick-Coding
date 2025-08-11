## Crawl4AI Testing Folder

This folder contains scripts and outputs for a small-scale Crawl4AI test. We take the first N sites from `uptick-csvs/testing-crawl4AI.csv` and crawl their homepages to Markdown.

- **Scripts**: `scripts/`
- **Outputs**: `outputs/`

### Prerequisites

- Python virtualenv already set up at `venv/`.
- Crawl4AI installed and initialized (we ran `crawl4ai-setup` and `crawl4ai-doctor`).

### Commands

Run the homepage crawl for first 10 sites:

```bash
/Users/sethlim/Documents/Uptick-Coding/venv/bin/python "CRAWL4AI testing/scripts/crawl_homepages.py" \
  --csv uptick-csvs/testing-crawl4AI.csv \
  --limit 10 \
  --out "CRAWL4AI testing/outputs"
```

Optional smoke test (single URL):

```bash
/Users/sethlim/Documents/Uptick-Coding/venv/bin/python "CRAWL4AI testing/scripts/crawl_smoke_test.py"
```

### Installation and validation (performed)

- Installed Crawl4AI into the project venv:
  - `pip install -U crawl4ai`
  - `crawl4ai-setup` (installed Playwright + Patchright browsers, initialized DB)
  - `crawl4ai-doctor` (verified crawl works)
- Versions observed:
  - Crawl4AI: 0.7.3
  - Playwright Chromium build: 1169 (Chromium 136.0.7103.25)
  - Patchright Chromium headless shell installed

### Effective configuration used in scripts

- Entry script: `scripts/crawl_homepages.py`
- Crawler client: `AsyncWebCrawler()` with default browser settings
- Run configuration (`CrawlerRunConfig`):
  - `check_robots_txt=True` (respect robots.txt)
  - `cache_mode=CacheMode.ENABLED` (read/write cache)
  - `verbose=False`
  - Default user agent (no explicit override)
- Concurrency and pacing:
  - Sequential crawl (no dispatcher or rate limiter configured)
  - No artificial delays added
- Anti-detection and interaction:
  - No `magic`, `simulate_user`, or `override_navigator` enabled
  - No JS injection, iframe processing, or scrolling configured

### CSV handling and normalization

- Input: `uptick-csvs/testing-crawl4AI.csv`
- Uses `scripts/csv_utils.py` to:
  - Read `website` column, skip blanks
  - Normalize by adding `https://` if no scheme present
  - Lowercase host, validate presence of netloc
  - Preserve original order and deduplicate
  - Limit first N (default 10 via `--limit`)

### Output structure

- Output root: `CRAWL4AI testing/outputs/`
- Per-domain folder: `<domain>/index.md`
- Markdown extraction strategy: default (print/save raw markdown if available)

### Error handling

- Per-URL try/continue; failures do not stop the run
- When blocked by robots.txt:
  - `result.success=False`, `status_code=403`, `error_message="Access denied by robots.txt"`
  - The URL is logged as failed and skipped

### Adjusting robots.txt behavior (use cautiously)

- Current behavior: robots.txt compliance ON (recommended)
- To bypass (only with permission): set `check_robots_txt=False` in `CrawlerRunConfig`
- Optionally set a clear `user_agent`, add polite delays, and use concurrency limits if scaling

### Reproducibility notes

- Python venv path: `/Users/sethlim/Documents/Uptick-Coding/venv/`
- Commands above assume macOS and the existing venv
- Folder name contains a space; scripts support direct invocation (import fallback is built in)

### References

- Crawl4AI Documentation: https://docs.crawl4ai.com/
- Robots handling (403 on block): https://github.com/unclecode/crawl4ai/blob/main/deploy/docker/c4ai-code-context.md#_snippet_47
- Configuring `check_robots_txt`: https://github.com/unclecode/crawl4ai/blob/main/docs/md_v2/api/arun.md#_snippet_1

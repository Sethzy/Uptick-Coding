/**
 * Purpose: Shared helpers for JSON/JSONL previewers (drag/drop, parsing, mapping, persistence).
 * Description: Provides utilities to read files, parse JSON/JSONL, detect likely schema fields,
 * and persist user mapping overrides in localStorage. Used by both aggregate and raw previewers.
 * Key Functions: parseJsonOrJsonl, readFileAsText, detectAggregateMappings, detectPagesMappings,
 * saveMapping, loadMapping, wireGlobalDropZone.
 */

// AIDEV-NOTE: Keep dependencies minimal; no external libs

export function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => resolve(String(reader.result || ""));
    reader.readAsText(file);
  });
}

export function parseJsonOrJsonl(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) return [];
  const first = trimmed[0];
  if (first === "{" || first === "[") {
    try {
      const parsed = JSON.parse(trimmed);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      // fallthrough to JSONL attempt
    }
  }
  return trimmed
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch (e) {
        // AIDEV-NOTE: Skip malformed lines; keep UX resilient
        return null;
      }
    })
    .filter((x) => x && typeof x === "object");
}

export function unionObjectKeys(records, limit = 200) {
  const keys = new Set();
  for (let i = 0; i < Math.min(records.length, limit); i++) {
    const r = records[i];
    if (r && typeof r === "object") Object.keys(r).forEach((k) => keys.add(k));
  }
  return Array.from(keys);
}

export function detectKey(candidates, obj) {
  if (!obj || typeof obj !== "object") return null;
  const lowerToKey = Object.keys(obj).reduce((acc, k) => {
    acc[k.toLowerCase()] = k;
    return acc;
  }, {});
  for (const cand of candidates) {
    const found = lowerToKey[cand.toLowerCase()];
    if (found) return found;
  }
  return null;
}

export function detectAggregateMappings(record) {
  const labelKey =
    detectKey(["domain", "label", "name", "company", "title"], record) ||
    null;
  const markdownKey =
    detectKey(
      ["aggregated_context", "markdown", "content", "body", "text"],
      record
    ) || "aggregated_context";
  const urlsKey = detectKey(["included_urls", "urls", "links"], record);
  return { labelKey, markdownKey, urlsKey };
}

export function detectPagesMappings(record) {
  const pagesKey =
    detectKey(["pages", "items", "docs", "documents", "entries"], record) ||
    "pages";
  const sample = Array.isArray(record?.[pagesKey]) ? record[pagesKey][0] : null;
  const fitKey = detectKey(["markdown_fit", "fit", "md_fit"], sample);
  const scopedKey = detectKey(["markdown_scoped", "scoped", "md_scoped"], sample);
  const rawKey =
    detectKey(["markdown_raw", "raw", "md_raw", "markdown"], sample) || rawFallback(sample);
  const titleKey = detectKey(["title", "name"], sample) || "title";
  const urlKey = detectKey(["url", "link", "href"], sample) || "url";
  return { pagesKey, fitKey, scopedKey, rawKey, titleKey, urlKey };
}

function rawFallback(sample) {
  if (!sample || typeof sample !== "object") return undefined;
  if (typeof sample.markdown === "string") return "markdown";
  return undefined;
}

export function saveMapping(kind, sourceKey, mapping) {
  try {
    localStorage.setItem(
      `previewer:mapping:${kind}:${sourceKey}`,
      JSON.stringify(mapping)
    );
  } catch {}
}

export function loadMapping(kind, sourceKey) {
  try {
    const raw = localStorage.getItem(`previewer:mapping:${kind}:${sourceKey}`);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function wireGlobalDropZone(onFileText) {
  const prevent = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };
  window.addEventListener("dragover", prevent);
  window.addEventListener("dragenter", prevent);
  window.addEventListener("drop", async (e) => {
    prevent(e);
    const file = e.dataTransfer?.files?.[0];
    if (!file) return;
    try {
      const text = await readFileAsText(file);
      onFileText(text, file.name || "dropped.jsonl");
    } catch (err) {
      console.error(err);
    }
  });
}

// AIDEV-TODO: Consider adding URL query param loader in a later iteration



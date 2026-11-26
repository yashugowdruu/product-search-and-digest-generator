import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from urllib.request import Request, urlopen

STOPWORDS = {
    "best", "top", "cheap", "cheapest", "good", "for", "a", "an",
    "the", "with", "buy", "find", "me", "show", "in", "of"
}


def validate_query(query: str) -> Tuple[bool, str, Dict]:
    """FR1: Validate user search query, strip filler words, and extract optional price limit."""
    cleaned = (query or "").strip()
    if not cleaned:
        return False, "Search query cannot be empty.", {}
    if len(cleaned) > 120:
        return False, "Search query exceeds 120 characters.", {}
    if not re.search(r"[A-Za-z0-9]", cleaned):
        return False, "Search query must contain alphanumeric characters.", {}

    max_price = None
    match = re.search(r"under\s+(\d+)", cleaned, re.IGNORECASE)
    if match:
        max_price = float(match.group(1))
        keywords_text = re.sub(r"under\s+\d+", "", cleaned, flags=re.IGNORECASE).strip()
    else:
        keywords_text = cleaned

    raw_tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9]+", keywords_text)]
    tokens = [t for t in raw_tokens if t not in STOPWORDS]
    return True, "Valid query", {"raw": cleaned, "tokens": tokens, "max_price": max_price}


def load_sources(config_path: str = "sources.json") -> List[Dict]:
    """NFR-5: Load monitored websites from external configuration file."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])


def discover_websites(query_params: Dict, config_path: str = "sources.json") -> List[Dict]:
    """FR2: Automatically identify and list websites relevant to the user's query."""
    sources = load_sources(config_path)
    tokens = set(query_params.get("tokens", []))
    matched = []
    for src in sources:
        src_keywords = set(k.lower() for k in src.get("keywords", []))
        if not tokens or not src_keywords or tokens.intersection(src_keywords):
            matched.append(src)
    return matched


def _fetch_single(source: Dict, timeout: float = 3.0) -> Dict:
    """Fetch a single URL with fault isolation so one failure never crashes the system (NFR-4)."""
    url = source["url"]
    name = source["name"]
    try:
        if url.startswith("file://"):
            local_path = url.replace("file://", "", 1)
            with open(local_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"name": name, "url": url, "status": "ok", "html": content, "error": None}
        req = Request(url, headers={"User-Agent": "ProductDigestBot/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        return {"name": name, "url": url, "status": "ok", "html": content, "error": None}
    except Exception as exc:
        return {"name": name, "url": url, "status": "failed", "html": "", "error": str(exc)}


def scrape_websites_concurrently(sources: List[Dict], max_workers: int = 6, timeout: float = 2.0) -> Tuple[List[Dict], List[Dict]]:
    """NFR-1 & NFR-2: Scrape multiple pages concurrently with bounded worker threads."""
    successes, failures = [], []
    if not sources:
        return successes, failures
    worker_count = min(max_workers, len(sources))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(_fetch_single, src, timeout): src for src in sources}
        for future in as_completed(future_map):
            res = future.result()
            if res["status"] == "ok":
                successes.append(res)
            else:
                failures.append(res)
    return successes, failures

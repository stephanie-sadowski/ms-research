"""Polite HTTP access to public APIs: rate limits, retries and an on-disk cache."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

import requests

from . import __version__
from .paths import raw_dir

# Generic client name; no personal or project details are sent to APIs.
USER_AGENT = f"python-msr/{__version__}"

# Minimum seconds between requests to the same host.
# NCBI allows 3 requests/second without an API key.
MIN_INTERVAL = {
    "eutils.ncbi.nlm.nih.gov": 0.34,
    "www.ncbi.nlm.nih.gov": 0.34,
    "www.ebi.ac.uk": 0.2,
    "clinicaltrials.gov": 0.2,
}
DEFAULT_INTERVAL = 0.5
RETRY_STATUSES = {429, 500, 502, 503, 504}

_last_request: dict[str, float] = {}
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = USER_AGENT
    return _session


def _wait_for(host: str) -> None:
    interval = MIN_INTERVAL.get(host, DEFAULT_INTERVAL)
    elapsed = time.monotonic() - _last_request.get(host, 0.0)
    if elapsed < interval:
        time.sleep(interval - elapsed)
    _last_request[host] = time.monotonic()


def cache_key(url: str, params: dict[str, Any] | None) -> str:
    """Stable key for a request, independent of parameter order."""
    query = urlencode(sorted((params or {}).items()), doseq=True)
    return hashlib.sha256(f"{url}?{query}".encode()).hexdigest()[:32]


def _cache_file(url: str, params: dict[str, Any] | None) -> Path:
    return raw_dir("_cache") / f"{cache_key(url, params)}.txt"


def get_text(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    use_cache: bool = True,
    retries: int = 4,
    timeout: float = 60,
) -> str:
    """GET a URL and return the body, using the cache when allowed."""
    cached = _cache_file(url, params)
    if use_cache and cached.exists():
        return cached.read_text()

    host = urlparse(url).netloc
    session = _get_session()
    for attempt in range(retries + 1):
        _wait_for(host)
        response = session.get(url, params=params, timeout=timeout)
        if response.status_code in RETRY_STATUSES and attempt < retries:
            time.sleep(2**attempt)
            continue
        response.raise_for_status()
        break

    body = response.text
    if use_cache:
        cached.write_text(body)
    return body


def get_json(url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
    return json.loads(get_text(url, params, **kwargs))


def post_json(url: str, payload: dict[str, Any], *, use_cache: bool = True, timeout: float = 120) -> Any:
    """POST a JSON body (for GraphQL APIs) and return the parsed response, with caching."""
    body_key = json.dumps(payload, sort_keys=True)
    cached = _cache_file(url, {"post": body_key})
    if use_cache and cached.exists():
        return json.loads(cached.read_text())
    host = urlparse(url).netloc
    for attempt in range(5):
        _wait_for(host)
        response = _get_session().post(url, json=payload, timeout=timeout)
        if response.status_code in RETRY_STATUSES and attempt < 4:
            time.sleep(2**attempt)
            continue
        response.raise_for_status()
        break
    data = response.json()
    if use_cache:
        cached.write_text(json.dumps(data))
    return data


def download(url: str, dest: Path, *, refresh: bool = False, timeout: float = 600) -> Path:
    """Download a (possibly large) file to dest, unless it is already there."""
    if dest.exists() and not refresh:
        return dest
    _wait_for(urlparse(url).netloc)
    tmp = dest.with_name(dest.name + ".part")
    with _get_session().get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(dest)
    return dest

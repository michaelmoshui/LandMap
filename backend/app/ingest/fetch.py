"""Minimal stdlib HTTP helpers for ingestion scripts.

Ingestion is a one-shot offline task, so we deliberately use ``urllib`` from
the standard library instead of adding a runtime HTTP dependency.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = "LandMap-ingest/1.0 (self-hosted land map; github.com/aexzhou/landmap)"

_RETRIES = 2
_BACKOFF_SECONDS = 4.0


def _request_json(url: str, body: bytes | None, timeout: float) -> Any:
    request = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def get_bytes(url: str, *, timeout: float = 300.0) -> bytes:
    """GET a binary document (e.g. a GTFS zip), retrying transient failures."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                return response.read()
        except Exception as exc:  # noqa: BLE001 - retry any transport error
            last_error = exc
            if attempt < _RETRIES:
                time.sleep(_BACKOFF_SECONDS * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {_RETRIES + 1} attempts: {last_error}")


def get_json(url: str, params: dict[str, str] | None = None, *, timeout: float = 90.0) -> Any:
    """GET a JSON document, retrying transient failures with backoff."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(_RETRIES + 1):
        try:
            return _request_json(url, None, timeout)
        except Exception as exc:  # noqa: BLE001 - retry any transport/parse error
            last_error = exc
            if attempt < _RETRIES:
                time.sleep(_BACKOFF_SECONDS * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {_RETRIES + 1} attempts: {last_error}")


def post_form_json(url: str, form: dict[str, str], *, timeout: float = 120.0) -> Any:
    """POST an urlencoded form and parse the JSON response (Overpass API style)."""
    body = urllib.parse.urlencode(form).encode()
    last_error: Exception | None = None
    for attempt in range(_RETRIES + 1):
        try:
            return _request_json(url, body, timeout)
        except Exception as exc:  # noqa: BLE001 - retry any transport/parse error
            last_error = exc
            if attempt < _RETRIES:
                time.sleep(_BACKOFF_SECONDS * (attempt + 1))
    raise RuntimeError(f"POST {url} failed after {_RETRIES + 1} attempts: {last_error}")

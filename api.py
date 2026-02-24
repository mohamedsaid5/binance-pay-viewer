"""Binance API integration and background worker.

The Pay endpoint ``/sapi/v1/pay/transactions`` limits each request to a
**90-day window**.  For larger ranges the helper ``fetch_all`` automatically
splits the request into consecutive 90-day chunks and merges the results.
"""

import time
import hmac
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from config import BASE_URL, PAGE_LIMIT, RECV_WINDOW

log = logging.getLogger(__name__)

_MAX_RANGE_DAYS = 89          # Binance Pay hard limit (< 90 full days)
_MAX_RANGE_MS = _MAX_RANGE_DAYS * 86_400_000


# ── REST helpers ───────────────────────────────────────────────────────────

def _sign(secret: str, query: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


def fetch_page(
    api_key: str,
    api_secret: str,
    start_ms: int,
    end_ms: int,
    limit: int = PAGE_LIMIT,
    page: int = 1,
) -> dict:
    """Fetch one page of Binance Pay transactions."""
    ts = int(time.time() * 1000)
    params = {
        "startTime": start_ms,
        "endTime": end_ms,
        "timestamp": ts,
        "recvWindow": RECV_WINDOW,
        "limit": limit,
        "page": page,
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    qs += f"&signature={_sign(api_secret, qs)}"

    try:
        r = requests.get(
            f"{BASE_URL}/sapi/v1/pay/transactions?{qs}",
            headers={"X-MBX-APIKEY": api_key},
            timeout=30,
        )
        r.raise_for_status()
        records = sorted(
            r.json().get("data", []),
            key=lambda x: x.get("transactionTime", 0),
        )
        return {"data": records, "more": len(records) == limit}
    except requests.RequestException as exc:
        log.error("API request failed: %s", exc)
        return {"data": [], "more": False}


def _fetch_range(
    api_key: str, api_secret: str, start_ms: int, end_ms: int
) -> list[dict]:
    """Paginate through all transactions for a **single ≤ 90-day** window."""
    results: list[dict] = []
    page = 1
    while True:
        resp = fetch_page(api_key, api_secret, start_ms, end_ms, page=page)
        results.extend(resp["data"])
        if not resp["more"] or not resp["data"]:
            break
        page += 1
    return results


def fetch_all(
    api_key: str, api_secret: str, start_ms: int, end_ms: int
) -> list[dict]:
    """Fetch **all** transactions for an arbitrary date range.

    Automatically splits the request into ≤ 90-day windows to satisfy the
    Binance Pay API limit, then merges and de-duplicates the results.
    """
    results: list[dict] = []
    chunk_start = start_ms

    while chunk_start < end_ms:
        chunk_end = min(chunk_start + _MAX_RANGE_MS, end_ms)
        log.info(
            "Fetching chunk %s → %s",
            datetime.fromtimestamp(chunk_start / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            datetime.fromtimestamp(chunk_end / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        )
        chunk = _fetch_range(api_key, api_secret, chunk_start, chunk_end)
        results.extend(chunk)
        chunk_start = chunk_end + 1      # next ms to avoid overlap

    # De-duplicate by orderId (overlapping boundaries)
    seen: set[str] = set()
    unique: list[dict] = []
    for tx in results:
        oid = tx.get("orderId", "")
        if oid and oid not in seen:
            seen.add(oid)
            unique.append(tx)

    unique.sort(key=lambda x: x.get("transactionTime", 0))
    return unique


def fetch_ticker(symbol: str) -> float | None:
    """Fetch a live ticker price (e.g. ``BNBUSDT``). Returns *None* on failure."""
    try:
        r = requests.get(
            f"{BASE_URL}/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=10,
        )
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception as exc:
        log.warning("Price fetch failed for %s: %s", symbol, exc)
        return None


# ── Worker thread ──────────────────────────────────────────────────────────

class FetchWorker(QObject):
    """Runs ``fetch_all`` in a background QThread."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(list)

    def __init__(
        self, api_key: str, api_secret: str, start_ms: int, end_ms: int
    ):
        super().__init__()
        self._key = api_key
        self._secret = api_secret
        self._start = start_ms
        self._end = end_ms

    @pyqtSlot()
    def run(self) -> None:
        try:
            data = fetch_all(self._key, self._secret, self._start, self._end)
            self.result.emit(data)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

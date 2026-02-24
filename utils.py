"""Utility functions — time conversion, parsing, currency rates."""

from datetime import datetime, timedelta, timezone

# ── Constants ──────────────────────────────────────────────────────────────
EGYPT_TZ = timezone(timedelta(hours=2))

_FALLBACK_USD: dict[str, float] = {
    "USDT": 1.0,
    "BNB": 600.0,
    "BTC": 95_000.0,
}

_price_cache: dict[str, float] = {}


# ── Time ───────────────────────────────────────────────────────────────────
def to_egypt_time(timestamp_ms: int) -> str:
    """Convert a Unix timestamp (ms) to Egypt local time string (UTC+2)."""
    if not timestamp_ms:
        return "N/A"
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
    return dt.astimezone(EGYPT_TZ).strftime("%Y-%m-%d %H:%M:%S")


# ── Parsing ────────────────────────────────────────────────────────────────
def parse_order_ids(text: str) -> list[str]:
    """Parse comma-separated order IDs; each must be exactly 18 digits."""
    if not text.strip():
        return []
    ids = [x.strip() for x in text.split(",") if x.strip()]
    for oid in ids:
        if not (len(oid) == 18 and oid.isdigit()):
            raise ValueError(f"Invalid Order ID: '{oid}' — must be 18 digits.")
    return ids


# ── Period helpers ─────────────────────────────────────────────────────────
def get_period_dates(option: str) -> tuple[datetime | None, datetime | None]:
    """Return (start, end) datetime for a quick-select period."""
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)

    if option == "This Month":
        first = datetime(now.year, now.month, 1)
        return (first, today)
    if option == "Last Month":
        # First day of last month → last day of last month
        first_this = datetime(now.year, now.month, 1)
        last_day = first_this - timedelta(days=1)  # last day of prev month
        first_prev = datetime(last_day.year, last_day.month, 1)
        return (first_prev, last_day)

    periods = {
        "Today":        (today, today),
        "Yesterday":    (today - timedelta(1), today - timedelta(1)),
        "Last 7 Days":  (today - timedelta(6), today),
        "Last 14 Days": (today - timedelta(13), today),
        "Last 30 Days": (today - timedelta(29), today),
        "Last 90 Days": (today - timedelta(89), today),
    }
    return periods.get(option, (None, None))


# ── Currency conversion ───────────────────────────────────────────────────
def conversion_rate(symbol: str, target: str, egp_rate: float) -> float:
    """Get conversion rate from a crypto symbol to USD or EGP."""
    usd = _price_cache.get(
        symbol.upper(),
        _FALLBACK_USD.get(symbol.upper(), 1.0),
    )
    if target.upper() == "EGP":
        return usd * egp_rate
    return usd  # USD


def update_prices(prices: dict[str, float]) -> None:
    """Update the live-price cache."""
    _price_cache.update(prices)

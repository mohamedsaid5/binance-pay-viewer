"""Application configuration and constants."""

import os
import logging

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Environment ────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY: str = os.environ.get("API_KEY", "")
API_SECRET: str = os.environ.get("API_SECRET", "")

# ── API ────────────────────────────────────────────────────────────────────
BASE_URL: str = "https://api.binance.com"
PAGE_LIMIT: int = 100
RECV_WINDOW: int = 60_000

# ── App ────────────────────────────────────────────────────────────────────
USDT_EGP_RATE: float = 47.0  # Approximate — update as needed

PERIOD_OPTIONS: list[str] = [
    "Custom",
    "Today",
    "Yesterday",
    "Last 7 Days",
    "Last 14 Days",
    "Last 30 Days",
    "Last 90 Days",
    "This Month",
    "Last Month",
]

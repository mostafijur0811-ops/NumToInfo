"""Configuration module for Number To Country Info Bot.

Loads environment variables and sets up global logging configuration.
No personal or subscriber data is ever handled by this bot — only public,
country-level information derived from a phone number's dialing code.
"""

from __future__ import annotations

import logging
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; env vars can be set directly on the host
    # (e.g. Koyeb / Railway / Render environment variable settings).
    pass

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is not set.", file=sys.stderr)
    print(
        "Create a .env file (see .env.example) or export BOT_TOKEN before running.",
        file=sys.stderr,
    )
    sys.exit(1)

# Minimum seconds a user must wait between two number lookups.
RATE_LIMIT_SECONDS: float = float(os.getenv("RATE_LIMIT_SECONDS", "1.5"))

# REST Countries API base URL (free, no API key required).
REST_COUNTRIES_BASE_URL: str = os.getenv(
    "REST_COUNTRIES_BASE_URL", "https://restcountries.com/v3.1"
)

# HTTP request timeout (seconds) for outbound API calls.
HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "10"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=LOG_LEVEL,
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Quiet down noisy third-party loggers.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("number2country")

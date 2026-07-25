"""Utility helpers: rate limiting, input sanitizing, and message formatting."""

from __future__ import annotations

import time
from html import escape

import phonenumbers

from config import RATE_LIMIT_SECONDS
from country import CountryInfo


class RateLimiter:
    """Simple in-memory per-user cooldown rate limiter.

    Not distributed or persistent — sufficient for a single-process bot with
    no database requirement, as specified in the project constraints.
    """

    def __init__(self, cooldown_seconds: float = RATE_LIMIT_SECONDS) -> None:
        self._cooldown = cooldown_seconds
        self._last_request: dict[int, float] = {}

    def check(self, user_id: int) -> tuple[bool, float]:
        """Check whether a user may make another request right now.

        Returns a tuple of (allowed, seconds_remaining_if_blocked).
        """
        now = time.monotonic()
        last = self._last_request.get(user_id, 0.0)
        elapsed = now - last
        if elapsed < self._cooldown:
            return False, round(self._cooldown - elapsed, 1)
        self._last_request[user_id] = now
        return True, 0.0


def extract_number_candidate(text: str) -> str:
    """Strip whitespace/formatting noise from a user message to isolate a number."""
    return "".join(ch for ch in text.strip() if ch.isdigit() or ch == "+")


def format_country_message(
    parsed: phonenumbers.PhoneNumber, info: CountryInfo
) -> str:
    """Build the final HTML-formatted Telegram message shown to the user."""
    e164_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    lines = [
        f"📱 <b>Number:</b> <code>{escape(e164_number)}</code>",
        "",
        f"🌍 <b>Country:</b> {escape(info.name)} {info.flag_emoji}",
        f"📞 <b>Calling Code:</b> {escape(info.calling_code)}",
        f"🏛 <b>Capital:</b> {escape(info.capital)}",
        f"🌎 <b>Continent:</b> {escape(info.continent)}",
        f"📍 <b>Region:</b> {escape(info.region)}",
        f"🗣 <b>Official Language(s):</b> {escape(info.languages)}",
        f"💰 <b>Currency:</b> {escape(info.currency)}",
        f"🕒 <b>Time Zone:</b> {escape(info.timezone)}",
        f"⏰ <b>Current Local Time:</b> {escape(info.local_time)}",
        f"🌐 <b>Internet Domain:</b> {escape(info.tld)}",
        f"📌 <b>ISO Code:</b> {escape(info.iso_code)}",
        f"🚗 <b>Driving Side:</b> {escape(info.driving_side)}",
        f"👥 <b>Population:</b> {escape(info.population)}",
        f"📱 <b>Typical Mobile Number Length:</b> {escape(info.mobile_length)}",
        f"🚨 <b>Emergency Number:</b> {escape(info.emergency_number)}",
    ]

    if info.maps_url:
        lines.append(
            f'🗺 <b>Google Maps:</b> <a href="{escape(info.maps_url)}">Open Map</a>'
        )

    return "\n".join(lines)

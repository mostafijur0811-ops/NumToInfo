"""Country lookup and phone-number parsing logic.

This module ONLY derives publicly available *country* information from a
phone number's international calling code / region. It never attempts to
identify the owner, carrier, SIM holder, location, or any other
personal/private data — that information is neither available from, nor
requested through, the dialing code alone.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import phonenumbers
import pycountry
import pytz
import requests
from phonenumbers import PhoneNumberFormat, PhoneNumberType

from config import HTTP_TIMEOUT, REST_COUNTRIES_BASE_URL, logger

# Small fallback map of general emergency numbers for countries where the
# public REST Countries API does not expose this field. Not exhaustive —
# purely public, widely published information (not subscriber-specific).
_EMERGENCY_FALLBACK: dict[str, str] = {
    "US": "911", "CA": "911", "GB": "999", "IN": "112", "BD": "999",
    "PK": "15", "AU": "000", "NZ": "111", "DE": "112", "FR": "112",
    "IT": "112", "ES": "112", "RU": "112", "CN": "110", "JP": "110",
    "BR": "190", "ZA": "10111", "NG": "112", "AE": "999", "SA": "911",
    "SG": "999", "MY": "999", "ID": "112", "PH": "911", "TH": "191",
    "KR": "112", "MX": "911", "AR": "911", "EG": "122", "TR": "112",
}


class CountryLookupError(Exception):
    """Raised when a country cannot be resolved or its info cannot be fetched."""


@dataclass
class CountryInfo:
    """Container for the publicly available country details we display."""

    name: str = "Unknown"
    flag_emoji: str = ""
    calling_code: str = ""
    capital: str = "N/A"
    continent: str = "N/A"
    region: str = "N/A"
    languages: str = "N/A"
    currency: str = "N/A"
    timezone: str = "N/A"
    local_time: str = "N/A"
    tld: str = "N/A"
    iso_code: str = "N/A"
    driving_side: str = "N/A"
    population: str = "N/A"
    mobile_length: str = "N/A"
    emergency_number: str = "Not available"
    maps_url: str | None = None


def parse_phone_number(raw_number: str) -> phonenumbers.PhoneNumber:
    """Parse a raw user-supplied string into a phonenumbers.PhoneNumber object.

    Accepts numbers with or without a leading '+'. Raises ValueError if the
    number cannot be parsed or is not a possible/valid number.
    """
    candidate = raw_number.strip()
    if not candidate.startswith("+"):
        candidate = "+" + candidate

    try:
        parsed = phonenumbers.parse(candidate, None)
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Could not parse phone number: {exc}") from exc

    if not phonenumbers.is_possible_number(parsed):
        raise ValueError("Number is not a possible phone number.")

    return parsed


def _region_and_code(parsed: phonenumbers.PhoneNumber) -> tuple[str, int]:
    """Return the ISO region code and international calling code for a number."""
    region_code = phonenumbers.region_code_for_number(parsed)
    if not region_code:
        raise CountryLookupError("Unable to determine country from this number.")
    return region_code, parsed.country_code


def _estimate_mobile_length(region_code: str) -> str:
    """Estimate the typical national mobile number length for a region."""
    try:
        example = phonenumbers.example_number_for_type(
            region_code, PhoneNumberType.MOBILE
        )
        if example:
            national = phonenumbers.format_number(example, PhoneNumberFormat.NATIONAL)
            digits = "".join(ch for ch in national if ch.isdigit())
            if digits:
                return f"{len(digits)} digits"
    except Exception:  # noqa: BLE001 - defensive, never crash on formatting
        pass
    return "N/A"


def _fetch_country_payload(region_code: str) -> dict[str, Any]:
    """Fetch country data from the REST Countries API for a given ISO alpha-2 code."""
    url = f"{REST_COUNTRIES_BASE_URL}/alpha/{region_code}"
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error("REST Countries API request failed: %s", exc)
        raise CountryLookupError(
            "Could not reach the country information service. Please try again later."
        ) from exc
    except ValueError as exc:  # JSON decode error
        logger.error("REST Countries API returned invalid JSON: %s", exc)
        raise CountryLookupError("Country information service returned bad data.") from exc

    if isinstance(data, list):
        if not data:
            raise CountryLookupError("No country data found for this number.")
        return data[0]
    if isinstance(data, dict) and data.get("status") == 404:
        raise CountryLookupError("Country not found in the database.")
    return data


def _get_local_time(region_code: str) -> tuple[str, str]:
    """Return (timezone_name, formatted_local_time) for a region, best-effort."""
    zones = pytz.country_timezones.get(region_code)
    if not zones:
        return "N/A", "N/A"
    tz_name = zones[0]
    try:
        now = dt.datetime.now(pytz.timezone(tz_name))
        return tz_name, now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:  # noqa: BLE001
        return tz_name, "N/A"


def get_country_info(parsed: phonenumbers.PhoneNumber) -> CountryInfo:
    """Build a CountryInfo object from a parsed phone number.

    Combines pycountry (ISO metadata), the REST Countries API (rich public
    country data) and pytz (local time) — never touching any personal or
    subscriber-level data.
    """
    region_code, calling_code = _region_and_code(parsed)

    pyc = pycountry.countries.get(alpha_2=region_code)
    fallback_name = pyc.name if pyc else region_code

    payload = _fetch_country_payload(region_code)

    name = payload.get("name", {}).get("common", fallback_name)
    flag_emoji = payload.get("flag", "")

    capital_list = payload.get("capital") or []
    capital = ", ".join(capital_list) if capital_list else "N/A"

    continents = payload.get("continents") or []
    continent = ", ".join(continents) if continents else "N/A"

    region = payload.get("subregion") or payload.get("region") or "N/A"

    languages_dict = payload.get("languages") or {}
    languages = ", ".join(languages_dict.values()) if languages_dict else "N/A"

    currencies_dict = payload.get("currencies") or {}
    currency_parts = [
        f"{info.get('name', code)} ({code})" for code, info in currencies_dict.items()
    ]
    currency = ", ".join(currency_parts) if currency_parts else "N/A"

    tld_list = payload.get("tld") or []
    tld = ", ".join(tld_list) if tld_list else "N/A"

    car_info = payload.get("car") or {}
    driving_side = car_info.get("side", "N/A")
    if isinstance(driving_side, str) and driving_side:
        driving_side = driving_side.capitalize()

    population = payload.get("population")
    population_str = f"{population:,}" if isinstance(population, int) else "N/A"

    maps_info = payload.get("maps") or {}
    maps_url = maps_info.get("googleMaps")

    tz_name, local_time = _get_local_time(region_code)

    emergency_number = _EMERGENCY_FALLBACK.get(region_code, "Not available")

    return CountryInfo(
        name=name,
        flag_emoji=flag_emoji,
        calling_code=f"+{calling_code}",
        capital=capital,
        continent=continent,
        region=region,
        languages=languages,
        currency=currency,
        timezone=tz_name,
        local_time=local_time,
        tld=tld,
        iso_code=region_code,
        driving_side=driving_side or "N/A",
        population=population_str,
        mobile_length=_estimate_mobile_length(region_code),
        emergency_number=emergency_number,
        maps_url=maps_url,
    )

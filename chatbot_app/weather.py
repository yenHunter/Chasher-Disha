"""
Weather service for Chasher-Disha — Milestone M2.

M2 changes:
  WX-1  Replace OpenWeatherMap with Open-Meteo API (free, no API key required).
          Adds agri-relevant fields: wind speed, UV index, 3-day precipitation
          sum, and FAO-56 evapotranspiration for irrigation planning.

  WX-2  Reverse-geocoding via Nominatim/OSM (free, no key required).
          Result is cached in Django's cache framework keyed by rounded
          lat/lon (0.05° ≈ 5 km), so repeated requests for the same area
          avoid redundant HTTP calls.

  BUG-1 Rain probability logic fixed — was a chain of independent `if`
          statements that could simultaneously report "clear sky" AND
          "high chance of rain". Now uses a single elif ladder so only
          one branch fires.

Endpoints used (both free, no API key):
  Open-Meteo:  https://api.open-meteo.com/v1/forecast
  Nominatim:   https://nominatim.openstreetmap.org/reverse
"""

from __future__ import annotations

import logging
import math
import requests

from django.core.cache import cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Open-Meteo WMO weather-code → Bangla description
# Full table: https://open-meteo.com/en/docs#weathervariables
# ---------------------------------------------------------------------------
_WMO_BN: dict[int, str] = {
    0:  "পরিষ্কার আকাশ ☀️",
    1:  "প্রায় পরিষ্কার ☀️",
    2:  "আংশিক মেঘলা 🌤️",
    3:  "মেঘাচ্ছন্ন ☁️",
    45: "কুয়াশা 🌫️",
    48: "ঘন কুয়াশা 🌫️",
    51: "হালকা গুঁড়ি গুঁড়ি বৃষ্টি 🌦️",
    53: "গুঁড়ি গুঁড়ি বৃষ্টি 🌦️",
    55: "ভারী গুঁড়ি গুঁড়ি বৃষ্টি 🌧️",
    61: "হালকা বৃষ্টি 🌧️",
    63: "মাঝারি বৃষ্টি 🌧️",
    65: "ভারী বৃষ্টি 🌧️",
    71: "হালকা তুষারপাত 🌨️",
    73: "তুষারপাত 🌨️",
    75: "ভারী তুষারপাত 🌨️",
    80: "হালকা বৃষ্টি শুরু 🌦️",
    81: "মাঝারি বৃষ্টি 🌦️",
    82: "ভারী বৃষ্টি 🌧️",
    95: "বজ্রঝড় ⛈️",
    96: "শিলাবৃষ্টিসহ বজ্রঝড় ⛈️",
    99: "ভারী শিলাবৃষ্টিসহ বজ্রঝড় ⛈️",
}

# ---------------------------------------------------------------------------
# Nominatim cache key helper
# ---------------------------------------------------------------------------
_GEOCODE_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 7 days — place names don't change


def _geocode_cache_key(lat: float, lon: float) -> str:
    """Round to 0.05° (≈5 km) to share cache entries for nearby coordinates."""
    rlat = math.floor(lat / 0.05) * 0.05
    rlon = math.floor(lon / 0.05) * 0.05
    return f"nominatim:{rlat:.2f}:{rlon:.2f}"


# ---------------------------------------------------------------------------
# Nominatim reverse-geocoding  (WX-2)
# ---------------------------------------------------------------------------
def get_place_name(lat: float, lon: float) -> str:
    """
    Return a human-readable Bangla-friendly place name for the given
    coordinates using Nominatim (OSM).  Result is cached for 7 days.

    Falls back to a formatted lat/lon string on any error.
    """
    cache_key = _geocode_cache_key(lat, lon)
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10},
            headers={
                # Nominatim usage policy requires a valid User-Agent and contact.
                # Update the email below to your own before deploying.
                "User-Agent": "ChasherDisha/2.0 (https://github.com/yenHunter/Chasher-Disha; contact@chasher-disha.app)"
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        addr = data.get("address", {})
        # Prefer progressively finer detail
        place = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("county")
            or addr.get("state")
            or data.get("display_name", f"{lat:.2f}°N, {lon:.2f}°E")
        )
        cache.set(cache_key, place, _GEOCODE_CACHE_TIMEOUT)
        return place
    except Exception as exc:
        logger.warning("[Weather] Nominatim failed for (%s, %s): %s", lat, lon, exc)
        return f"{lat:.2f}°N, {lon:.2f}°E"


# ---------------------------------------------------------------------------
# Open-Meteo forecast  (WX-1)
# ---------------------------------------------------------------------------
_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

_OPEN_METEO_PARAMS = {
    "current": ",".join([
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation_probability",
        "weather_code",
        "wind_speed_10m",
        "uv_index",
    ]),
    "daily": ",".join([
        "precipitation_sum",
        "et0_fao_evapotranspiration",
    ]),
    "timezone": "Asia/Dhaka",
    "forecast_days": 3,
}


def fetch_weather(lat: float, lon: float) -> dict:
    """
    Call Open-Meteo and return a structured dict with current conditions
    and 3-day agri-relevant data.

    Returns:
        {
          "place":           str,
          "condition":       str,   # Bangla WMO description
          "temperature":     float, # °C
          "humidity":        int,   # %
          "rain_probability":int,   # %
          "wind_speed":      float, # km/h
          "uv_index":        float,
          "rain_3day":       float, # mm — 3-day total precipitation
          "et0_3day":        float, # mm — 3-day FAO-56 evapotranspiration
          "message":         str,   # Bangla summary sentence
          "agri_advice":     str,   # farming-specific tip
        }

    Raises:
        WeatherServiceError on API or parsing failure.
    """
    try:
        resp = requests.get(
            _OPEN_METEO_URL,
            params={**_OPEN_METEO_PARAMS, "latitude": lat, "longitude": lon},
            timeout=8,
        )
        resp.raise_for_status()
        raw = resp.json()
    except requests.RequestException as exc:
        raise WeatherServiceError(f"Open-Meteo request failed: {exc}") from exc

    try:
        cur = raw["current"]
        daily = raw.get("daily", {})

        temp        = float(cur["temperature_2m"])
        humidity    = int(cur["relative_humidity_2m"])
        rain_prob   = int(cur.get("precipitation_probability", 0))
        wmo_code    = int(cur.get("weather_code", 0))
        wind_speed  = float(cur.get("wind_speed_10m", 0.0))
        uv_index    = float(cur.get("uv_index", 0.0))

        # 3-day sums (list of 3 values, one per day)
        rain_3day = sum(v or 0.0 for v in daily.get("precipitation_sum", [0, 0, 0]))
        et0_3day  = sum(v or 0.0 for v in daily.get("et0_fao_evapotranspiration", [0, 0, 0]))

    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceError(f"Unexpected Open-Meteo response: {exc}") from exc

    condition = _WMO_BN.get(wmo_code, "অজানা আবহাওয়া")
    place     = get_place_name(lat, lon)

    message      = _build_message(place, temp, humidity, rain_prob, condition)
    agri_advice  = _build_agri_advice(rain_prob, wind_speed, uv_index, et0_3day, rain_3day)

    return {
        "place":            place,
        "condition":        condition,
        "temperature":      temp,
        "humidity":         humidity,
        "rain_probability": rain_prob,
        "wind_speed":       wind_speed,
        "uv_index":         uv_index,
        "rain_3day":        round(rain_3day, 1),
        "et0_3day":         round(et0_3day, 1),
        "message":          message,
        "agri_advice":      agri_advice,
    }


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------
def _build_message(
    place: str,
    temp: float,
    humidity: int,
    rain_prob: int,
    condition: str,
) -> str:
    """
    Compose a single Bangla weather summary sentence.

    BUG-1 fix: uses elif so exactly one rain-probability phrase is chosen.
    The original OWM view used consecutive `if` blocks which could produce
    contradictory output (e.g. "clear sky" and "80% rain" simultaneously).
    """
    # Single elif ladder — exactly one branch fires  (M2: BUG-1)
    if rain_prob >= 70:
        rain_phrase = f"বৃষ্টির সম্ভাবনা বেশি ({rain_prob}%) 🌧️"
    elif rain_prob >= 40:
        rain_phrase = f"বৃষ্টি হতে পারে ({rain_prob}%) 🌦️"
    elif rain_prob >= 10:
        rain_phrase = f"সামান্য বৃষ্টির সম্ভাবনা ({rain_prob}%) 🌤️"
    else:
        rain_phrase = "বৃষ্টির সম্ভাবনা নেই ☀️"

    return (
        f"{place}-এ এখন {condition}। "
        f"তাপমাত্রা {temp:.1f}°C, আর্দ্রতা {humidity}%। "
        f"{rain_phrase}।"
    )


def _build_agri_advice(
    rain_prob: int,
    wind_speed: float,
    uv_index: float,
    et0_3day: float,
    rain_3day: float,
) -> str:
    """Return a short farming-specific tip based on current conditions."""
    tips: list[str] = []

    if rain_prob >= 60:
        tips.append("বৃষ্টির আগে সার দেওয়া ঠিক হবে না।")
    elif rain_prob <= 15 and et0_3day > 12:
        tips.append(f"আগামী ৩ দিনে বাষ্পীভবন বেশি ({et0_3day:.1f} মিমি) — সেচ দেওয়ার কথা ভাবুন।")

    if wind_speed > 40:
        tips.append("বাতাস জোরালো — কীটনাশক বা ছত্রাকনাশক স্প্রে করবেন না।")

    if uv_index >= 8:
        tips.append("UV তীব্র — দুপুরে মাঠে কাজ এড়িয়ে চলুন।")

    if rain_3day > 50:
        tips.append(f"৩ দিনে মোট বৃষ্টি {rain_3day:.0f} মিমি — জলাবদ্ধতার দিকে নজর রাখুন।")

    return " ".join(tips) if tips else "আবহাওয়া চাষাবাদের জন্য উপযুক্ত মনে হচ্ছে।"


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------
class WeatherServiceError(Exception):
    """Raised when Open-Meteo or Nominatim calls fail."""

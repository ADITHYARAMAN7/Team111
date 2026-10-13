"""
weather.py - hourly weather for a location (Open-Meteo, free, no API key).

Returns 7 days of history + 4 days of forecast in local time, which feed
  * risk.py     - weather-driven disease risk models (Hutton, TOM-CAST, ...)
  * advisory.py - spray-window planning (rain, wind, heat)
Results are cached per ~5 km grid cell for 30 minutes. Any network failure
returns None and the app simply works without weather.
"""
import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime

log = logging.getLogger(__name__)
URL = "https://api.open-meteo.com/v1/forecast"
FIELDS = ["temperature_2m", "relative_humidity_2m", "precipitation", "precipitation_probability", "wind_speed_10m"]
TTL = 1800
_cache = {}
_lock = threading.Lock()


def grid(lat, lon):
    """Round to ~5 km - enough for weather, coarse enough for privacy."""
    return round(round(float(lat) / 0.05) * 0.05, 3), round(round(float(lon) / 0.05) * 0.05, 3)


def valid_location(lat, lon):
    try:
        return -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
    except (TypeError, ValueError):
        return False


def parse(payload):
    """Open-Meteo JSON -> list of hourly dicts + index of the current hour."""
    h = payload["hourly"]
    rows = []
    for i, ts in enumerate(h["time"]):
        rows.append({
            "time": ts,
            "temp": h["temperature_2m"][i],
            "rh": h["relative_humidity_2m"][i],
            "rain": h["precipitation"][i] or 0.0,
            "rain_prob": (h.get("precipitation_probability") or [None] * len(h["time"]))[i],
            "wind": h["wind_speed_10m"][i],
        })
    rows = [r for r in rows if r["temp"] is not None and r["rh"] is not None]
    now_local = payload.get("current", {}).get("time")
    if now_local:
        now_idx = max(i for i, r in enumerate(rows) if r["time"] <= now_local) if rows else 0
    else:
        now_idx = len(rows) - 4 * 24 if len(rows) > 96 else 0
    return {"hours": rows, "now": now_idx, "timezone": payload.get("timezone"),
            "elevation": payload.get("elevation")}


def fetch(lat, lon, timeout=8):
    glat, glon = grid(lat, lon)
    key = (glat, glon)
    with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < TTL:
            return hit[1]
    q = urllib.parse.urlencode({
        "latitude": f"{glat:.3f}", "longitude": f"{glon:.3f}", "hourly": ",".join(FIELDS),
        "current": "temperature_2m", "past_days": 7, "forecast_days": 4, "timezone": "auto", "wind_speed_unit": "kmh"})
    try:
        with urllib.request.urlopen(f"{URL}?{q}", timeout=timeout) as r:
            data = parse(json.loads(r.read().decode("utf-8")))
    except Exception as e:  # noqa: BLE001 - offline, DNS, API change...
        log.warning("weather fetch failed for %s: %s", key, e)
        return None
    with _lock:
        _cache[key] = (time.time(), data)
    return data


def summary(w):
    """Compact view of 'now' and the last 3 days for the UI."""
    if not w:
        return None
    hrs, n = w["hours"], w["now"]
    cur = hrs[n]
    past = hrs[max(0, n - 72):n + 1]
    nxt = hrs[n + 1:n + 25]
    return {
        "time": cur["time"], "temp": cur["temp"], "rh": cur["rh"], "wind": cur["wind"],
        "rain_last_3d_mm": round(sum(h["rain"] for h in past), 1),
        "rain_next_24h_mm": round(sum(h["rain"] for h in nxt), 1),
        "mean_temp_3d": round(sum(h["temp"] for h in past) / len(past), 1),
        "mean_rh_3d": round(sum(h["rh"] for h in past) / len(past), 1),
        "max_temp_next_24h": max((h["temp"] for h in nxt), default=cur["temp"]),
    }


def hour_of(ts):
    return datetime.fromisoformat(ts).hour

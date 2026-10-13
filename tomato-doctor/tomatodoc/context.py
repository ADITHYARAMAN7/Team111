"""
context.py - growing-season context (feeds the FAVORED_BY prior).

Season can come from (in order of preference): the farmer's explicit choice,
local weather (the browser asks Open-Meteo with the farmer's location and sends
us temperature/humidity), or the calendar month for Tamil Nadu.
"""
import datetime


def season_from_month(kg, month=None):
    month = month or datetime.date.today().month
    for sid, s in kg.seasons.items():
        if month in (s.get("months") or []):
            return sid
    return None


def season_from_weather(temp_c, humidity):
    """Map recent mean temperature (°C) and relative humidity (%) to a season id."""
    if temp_c is None or humidity is None:
        return None
    if humidity >= 75 and temp_c >= 20:
        return "humid_monsoon"
    if temp_c < 23 and humidity >= 55:
        return "cool_moist"
    if temp_c >= 29 and humidity < 60:
        return "hot_dry"
    # nearest by simple distance to each season's centre
    centres = {"humid_monsoon": (26, 88), "cool_moist": (19, 70), "hot_dry": (34, 40)}
    return min(centres, key=lambda k: (centres[k][0] - temp_c) ** 2 / 25 + (centres[k][1] - humidity) ** 2 / 400)


def resolve_season(kg, explicit=None, weather=None):
    """Returns (season_id, source)."""
    if explicit and explicit in kg.seasons:
        return explicit, "farmer"
    if weather:
        s = season_from_weather(weather.get("temp"), weather.get("humidity"))
        if s in kg.seasons:
            return s, "weather"
    s = season_from_month(kg)
    return s, "calendar" if s else None

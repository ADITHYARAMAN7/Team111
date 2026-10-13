"""
risk.py - weather-driven disease risk models.

Each model reads hourly weather (weather.py) and returns a risk score 0..1 with
a level and a human explanation. Scores are used twice:
  1. as an early warning on the home screen ("high late-blight risk this week")
  2. as a data-driven PRIOR in the Bayesian diagnosis (replacing the coarse
     calendar season), so the same symptoms are read in the light of the
     weather the plant actually experienced.

Published models (relative humidity >= 90 % is used as the leaf-wetness proxy,
as in the cited TOM-CAST implementation):
  late_blight   Hutton Criteria (AHDB 2017): 2 consecutive days, Tmin >= 10 °C,
                >= 6 h RH >= 90 %. Hot spells (> 28 °C mean) suppress it - the
                Jagtap et al. dataset gives 18-23 °C as the fastest-spread range.
  early_blight  TOM-CAST daily severity values summed over 7 days.
Rule-based models built from the favourable-condition field of the Jagtap et
al. (2025) dataset are used for the other diseases. Diseases with no weather
signal (fruit borer, root-knot nematode, fusarium, mosaic) get no model.
"""
from collections import defaultdict

LEVELS = ((0.66, "high"), (0.33, "medium"), (0.0, "low"))


def _level(score):
    return next(lvl for th, lvl in LEVELS if score >= th)


def _days(hours):
    by = defaultdict(list)
    for h in hours:
        by[h["time"][:10]].append(h)
    return [by[d] for d in sorted(by)]


# ---------------------------------------------------------------- TOM-CAST
# leaf-wetness hours needed for DSV 1,2,3,4 per mean-temperature band
_TOMCAST = [((13, 17), (7, 16, 21, 99)), ((18, 20), (4, 9, 16, 23)), ((21, 25), (3, 6, 13, 21)), ((26, 29), (4, 9, 16, 23))]


def tomcast_dsv(day):
    wet = [h for h in day if h["rh"] >= 90]
    if not wet:
        return 0
    t = sum(h["temp"] for h in wet) / len(wet)
    for (lo, hi), steps in _TOMCAST:
        if lo <= round(t) <= hi:
            return sum(1 for s in steps if len(wet) >= s)
    return 0


def temp_suitability(t, low, opt_high, zero_at):
    """1 inside [low, opt_high], falling linearly to 0.1 at zero_at."""
    if t < low:
        return max(0.1, 1 - (low - t) / 8)
    if t <= opt_high:
        return 1.0
    return max(0.1, 1 - 0.9 * (t - opt_high) / (zero_at - opt_high))


def hutton_day(day):
    return min(h["temp"] for h in day) >= 10 and sum(1 for h in day if h["rh"] >= 90) >= 6


# ---------------------------------------------------------------- models
def _late_blight(past, fut):
    days = [d for d in _days(past) if len(d) >= 20]
    flags = [hutton_day(d) for d in days]
    periods = sum(1 for a, b in zip(flags, flags[1:]) if a and b)
    fdays = [d for d in _days(fut) if len(d) >= 20]
    fflags = [hutton_day(d) for d in fdays]
    upcoming = any(a and b for a, b in zip(fflags, fflags[1:]))
    mean_t = sum(h["temp"] for h in past) / len(past)
    score = min(1.0, 0.45 * periods + 0.15 * sum(flags) + (0.3 if upcoming else 0))
    # Hutton was calibrated for UK conditions; Jagtap et al. give 18-23 °C as the
    # fastest-spread range, so scale down in the warm tropical plains.
    score *= temp_suitability(mean_t, 12, 23, 30)
    return score, {"hutton_periods_7d": periods, "humid_days_7d": sum(flags), "hutton_forecast": upcoming,
                   "mean_temp": round(mean_t, 1)}, "hutton"


def _early_blight(past, fut):
    dsv = sum(tomcast_dsv(d) for d in _days(past) if len(d) >= 20)
    return min(1.0, dsv / 15), {"tomcast_dsv_7d": dsv}, "tomcast"


def _hours(past, cond):
    return sum(1 for h in past if cond(h))


RULE_CAP = 0.8   # heuristic models never claim more certainty than the published ones


def _rule(cond, full, fact, source="jagtap2025"):
    def model(past, fut):
        n = _hours(past, cond)
        return RULE_CAP * min(1.0, n / full), {fact: n}, source
    return model


def _bacterial(past, fut):
    rain = sum(h["rain"] for h in past)
    warm_wet = _hours(past, lambda h: h["temp"] >= 24 and h["rh"] >= 85)
    return RULE_CAP * min(1.0, rain / 40 * 0.6 + warm_wet / 100 * 0.6), {"rain_7d_mm": round(rain, 1), "warm_humid_hours_7d": warm_wet}, "general"


def _bacterial_wilt(past, fut):
    rain = sum(h["rain"] for h in past)
    mean_t = sum(h["temp"] for h in past) / len(past)
    score = RULE_CAP * min(1.0, rain / 50) * (1.0 if mean_t >= 24 else 0.4)
    return score, {"rain_7d_mm": round(rain, 1), "mean_temp": round(mean_t, 1)}, "general"


def _warm_dry(past, fut):
    mean_t = sum(h["temp"] for h in past) / len(past)
    rain = sum(h["rain"] for h in past)
    score = RULE_CAP * max(0.0, min(1.0, (mean_t - 24) / 6)) * (1.0 if rain < 10 else 0.5)
    return score, {"mean_temp": round(mean_t, 1), "rain_7d_mm": round(rain, 1)}, "jagtap2025"


def _heat_stress(past, fut):
    hot_days = sum(1 for d in _days(past) if max(h["temp"] for h in d) >= 33)
    return RULE_CAP * min(1.0, hot_days / 4), {"hot_days_7d": hot_days}, "general"


MODELS = {
    "late_blight": _late_blight,
    "early_blight": _early_blight,
    "septoria_leaf_spot": _rule(lambda h: h["rh"] >= 90 and 15 <= h["temp"] <= 27, 60, "wet_hours_15_27C_7d"),
    "leaf_mold": _rule(lambda h: h["rh"] > 85, 80, "hours_rh_over_85_7d"),
    "target_spot": _rule(lambda h: h["rh"] > 80 and 20 <= h["temp"] <= 30, 100, "warm_humid_hours_7d"),
    "powdery_mildew": _rule(lambda h: 20 <= h["temp"] <= 30 and 40 <= h["rh"] <= 80, 120, "mild_dry_hours_7d", "general"),
    "spider_mite": _rule(lambda h: h["temp"] >= 30 and h["rh"] < 50, 30, "hot_dry_hours_7d"),
    "leaf_miner": _rule(lambda h: 15 <= h["temp"] <= 30 and 40 <= h["rh"] <= 85, 160, "favourable_hours_7d"),
    "bacterial_spot": _bacterial,
    "bacterial_wilt": _bacterial_wilt,
    "whitefly": _warm_dry,
    "leaf_curl_virus": _warm_dry,
    "blossom_end_rot": _heat_stress,
}

EXPLAIN = {
    "hutton": ("Hutton criteria: {hutton_periods_7d} late-blight period(s) and {humid_days_7d} humid day(s) in the last 7 days",
               "ஹட்டன் அளவுகோல்: கடந்த 7 நாளில் {hutton_periods_7d} கருகல் காலம், {humid_days_7d} ஈரப்பத நாள்"),
    "tomcast": ("TOM-CAST: {tomcast_dsv_7d} disease-severity points in the last 7 days",
                "TOM-CAST: கடந்த 7 நாளில் {tomcast_dsv_7d} நோய்த் தீவிரப் புள்ளிகள்"),
}


def assess(weather):
    """weather (weather.fetch) -> {disease_id: {score, level, facts, model, source}}"""
    if not weather or not weather["hours"]:
        return {}
    n = weather["now"]
    past = weather["hours"][max(0, n - 7 * 24 + 1):n + 1]
    fut = weather["hours"][n + 1:n + 1 + 72]
    if len(past) < 24:
        return {}
    out = {}
    for d, model in MODELS.items():
        score, facts, source = model(past, fut)
        score = round(max(0.0, min(1.0, score)), 3)
        en, ta = EXPLAIN.get(source, (None, None))
        out[d] = {"score": score, "level": _level(score), "facts": facts, "model": source,
                  "explain_en": en.format(**facts) if en else None, "explain_ta": ta.format(**facts) if ta else None}
    return out


def prior_factors(risks, strength=1.5):
    """Disease -> multiplicative prior factor (1 .. 1+strength). Diseases with no
    weather model get the mean factor, so they are neither favoured nor punished."""
    if not risks:
        return {}
    f = {d: 1 + strength * r["score"] for d, r in risks.items()}
    f["_default"] = sum(f.values()) / len(f)
    return f

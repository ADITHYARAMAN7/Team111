"""
crop.py - the farmer's field: crop stage from the transplanting date, and harvest
safety (pre-harvest intervals) while fruit is being picked.

Crop stage
    Days after transplanting (DAT) -> establishment, vegetative, flowering,
    fruiting, harvest (typical TNAU timeline for a 135-150 day tomato crop; the
    farmer can override). The stage shifts the diagnosis prior where the link is
    clear-cut: fruit disorders and fruit borer cannot be the cause before there
    is fruit; early blight builds up on older plants; whitefly-borne leaf curl
    hits young plants hardest.

Harvest safety
    Every sprayable product carries a pre-harvest interval (PHI): days that must
    pass between spraying and picking. While the farmer is picking every few
    days, a product whose PHI does not fit before the next picking is moved down
    the plan, and every recommendation says from when it is safe to pick again.
"""
from datetime import date, timedelta

# (stage, first day after transplanting)
STAGES = [("establishment", 0), ("vegetative", 20), ("flowering", 35), ("fruiting", 55), ("harvest", 70)]
STAGE_IDS = [s for s, _ in STAGES]
CROP_END_DAT = 180                          # older than this: assume a new crop, ignore the date
PICK_EVERY_DEFAULT = 4

# stage -> {disease: (factor, reason)}; bounded, only well-established links
STAGE_FACTORS = {
    "establishment": {"blossom_end_rot": 0.2, "fruit_borer": 0.4, "leaf_curl_virus": 1.25},
    "vegetative": {"blossom_end_rot": 0.3, "fruit_borer": 0.5, "leaf_curl_virus": 1.2},
    "flowering": {"blossom_end_rot": 0.8, "fruit_borer": 1.15},
    "fruiting": {"blossom_end_rot": 1.3, "fruit_borer": 1.3, "early_blight": 1.1},
    "harvest": {"blossom_end_rot": 1.2, "fruit_borer": 1.2, "early_blight": 1.25},
}


def _date(v):
    try:
        return date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None


def clean_field(raw, today=None):
    """Untrusted dict from the app -> field context, or None."""
    if not isinstance(raw, dict):
        return None
    today = today or date.today()
    planted = _date(raw.get("planting_date"))
    if planted and not (0 <= (today - planted).days <= CROP_END_DAT):
        planted = None
    stage = raw.get("stage") if raw.get("stage") in STAGE_IDS else None
    last_pick = _date(raw.get("last_pick"))
    if last_pick and not (0 <= (today - last_pick).days <= 30):
        last_pick = None
    try:
        every = int(raw.get("pick_every") or PICK_EVERY_DEFAULT)
    except (TypeError, ValueError):
        every = PICK_EVERY_DEFAULT
    every = max(2, min(10, every))
    harvesting = raw.get("harvesting")
    harvesting = harvesting if harvesting in ("yes", "no") else "auto"
    crop_type = raw.get("crop_type") if raw.get("crop_type") in ("variety", "hybrid") else None
    if not (planted or stage or harvesting != "auto" or last_pick):
        return None
    return {"planting_date": planted.isoformat() if planted else None, "stage": stage, "harvesting": harvesting,
            "last_pick": last_pick.isoformat() if last_pick else None, "pick_every": every, "crop_type": crop_type}


def stage_info(field, today=None):
    """-> {stage, dat, source, next_stage, next_in} (stage from date unless the farmer set one)."""
    if not field:
        return None
    today = today or date.today()
    dat = (today - date.fromisoformat(field["planting_date"])).days if field.get("planting_date") else None
    if field.get("stage"):
        stage, source = field["stage"], "farmer"
    elif dat is not None:
        stage = [s for s, start in STAGES if dat >= start][-1]
        source = "date"
    else:
        return {"stage": None, "dat": None, "source": None, "next_stage": None, "next_in": None}
    nxt = next(((s, start) for s, start in STAGES if dat is not None and start > dat), None)
    return {"stage": stage, "dat": dat, "source": source,
            "next_stage": nxt[0] if nxt and source == "date" else None,
            "next_in": nxt[1] - dat if nxt and source == "date" else None}


def stage_factors(stage):
    return dict(STAGE_FACTORS.get(stage, {}))


def harvest_context(field, stage, today=None):
    """Is fruit being picked, and how many days until the next picking?"""
    if not field:
        return None
    today = today or date.today()
    if field["harvesting"] == "auto":
        picking = stage == "harvest"
    else:
        picking = field["harvesting"] == "yes"
    if not picking:
        return {"picking": False}
    every = field["pick_every"]
    if field.get("last_pick"):
        next_pick = date.fromisoformat(field["last_pick"]) + timedelta(days=every)
        while next_pick < today:
            next_pick += timedelta(days=every)
    else:
        next_pick = today + timedelta(days=every)      # unknown: assume a full interval
    return {"picking": True, "every": every, "next_pick": next_pick.isoformat(), "days_to_pick": (next_pick - today).days}


def phi_check(phi, harvest, today=None, spray_day=None):
    """Per product: can it be sprayed now without delaying the next picking?
    status: ok | after_pick (pick ripe fruit first, then spray) | blocks_pick (PHI longer than the picking interval)."""
    if phi is None:
        return None
    spray = spray_day or today or date.today()
    out = {"phi": phi, "safe_from": (spray + timedelta(days=phi)).isoformat(), "spray_day": spray.isoformat()}
    if not harvest or not harvest.get("picking") or phi == 0:
        return {**out, "status": "ok"}
    days_to_pick = (date.fromisoformat(harvest["next_pick"]) - spray).days
    if phi <= days_to_pick:
        return {**out, "status": "ok"}
    if phi <= harvest["every"]:
        return {**out, "status": "after_pick"}      # pick the ripe fruit first, then spray: fits the usual interval
    return {**out, "status": "blocks_pick"}         # would push the next picking past the usual interval

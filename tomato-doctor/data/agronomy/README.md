# Field-advisory dataset (location- and weather-aware treatment)

This folder documents the agronomic data behind the location/weather features.
The authoritative copy lives in the knowledge graph
(`tomatodoc/kg/seed/tomato_kg.json`, `treatments[].application`); the CSV here
is an export for reports and review. Regenerate it after editing the graph.

## 1. Treatment application attributes — `treatment_application.csv`

One row per treatment (30), with:

| Column | Meaning | Used for |
|---|---|---|
| `mode` | contact / systemic / biological / botanical / nutrient / cultural … | systemic products are preferred when rain is forecast (they are not washed off) |
| `resistance_group` | FRAC (fungicides) or IRAC (insecticides) code | rotation: never repeat the group the farmer just used; schedules alternate groups |
| `rainfast_hours` | dry hours needed after spraying | spray-window finder rejects windows with rain inside this period |
| `max_temp_c` | do not spray above (e.g. sulfur 32 °C) | heat warnings, shifting sprays to the evening |
| `best_time` | any / morning_evening / evening | UV-sensitive biologicals (Bt, Pseudomonas) and oils go in the evening |
| `dose_min/max/unit/per` | numeric dose per litre / acre / hectare | dose calculator (per 16 L tank, per cents/acres) |
| `repeat_interval_days` | re-application interval | dated spray schedule + calendar file |
| `phi_days` | pre-harvest interval: days from the last spray to picking | harvest safety while fruit is being picked; "pick from" dates |

Dosages come from Jagtap et al. (2025); everything marked `general` is standard
extension guidance and should be checked against the product label and local
KVK advice. Rain-fastness for contact protectants is set conservatively (4 h):
published values range from 1.5–2 h drying to 6 h on some labels.

**Pre-harvest intervals** are conservative defaults chosen for decision support,
set at or above typical tomato label intervals for each product type (India
CIB&RC registrations, US EPA labels): mancozeb 5, azoxystrobin (± difenoconazole)
5, neonicotinoid 7, diamide 5, copper 3, cyazofamid 3, sulfur 1, neem/chilli 1
(wash fruit), biologicals/soap/calcium 0 days. Brands and formulations differ —
**the label on the pack is final**; an agronomist should review these values.

## 2. Weather-driven disease-risk models — `tomatodoc/risk.py`

| Disease | Model | Source |
|---|---|---|
| Late blight | Hutton Criteria: 2 consecutive days, Tmin ≥ 10 °C and ≥ 6 h RH ≥ 90 %; scaled by temperature suitability (fastest spread 18–23 °C) | AHDB 2017; Jagtap et al. 2025 |
| Early blight | TOM-CAST daily severity values from leaf-wetness hours × temperature band, summed over 7 days | Madden et al. 1978; Wisconsin CMC 2015 table |
| Septoria, leaf mold, target spot, powdery mildew, spider mite, leaf miner | hours meeting the favourable temperature/humidity conditions listed in the dataset (capped at 0.8 — heuristic) | Jagtap et al. 2025 |
| Bacterial spot / wilt, whitefly, leaf curl virus, blossom end rot | rain + warmth, warm-dry, and heat-stress indices (capped at 0.8) | general |

Relative humidity ≥ 90 % is used as the leaf-wetness proxy, as in the cited
TOM-CAST implementation. Weather comes from Open-Meteo (7 days history + 3 days
forecast, hourly).

## 3. Spray-window rules — `tomatodoc/advisory.py`

* wind: ideal ≤ 15 km/h, never ≥ 20 km/h (spray drift)
* rain: no hour with ≥ 0.3 mm or ≥ 60 % rain probability within the product's rain-fast period
* temperature: below the product's `max_temp_c` (35 °C general limit)
* time of day: daylight; evening-only products 16:00–19:00
* leaves not wet (RH < 97 %)

## 4. Location

`TN_DISTRICTS` in `tomatodoc/static/js/i18n_field.js`: 19 tomato-growing district
headquarters/hubs of Tamil Nadu, for farmers who prefer not to share GPS.
Locations are always rounded to a 0.05° grid (~5 km) before use or storage.

## Sources

See `sources.json` (also embedded in the knowledge graph as `meta.sources`):

* Jagtap et al. (2025), Mendeley Data, DOI 10.17632/ztncd79yhk.1
* AHDB — Hutton Criteria: https://potatoes.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria
* TOM-CAST table — Proc. 2015 Wisconsin Crop Management Conference: https://extension.soils.wisc.edu/wp-content/uploads/sites/68/2015/06/Frost-2015-WCMC-Proceedings.pdf
* Rain-fastness of protectant fungicides: https://ext.grapepathology.org/rains-and-fungicide-sprays
* Sulfur heat injury: https://www.awri.com.au/information_services/ebulletin/2021/10/13/agrochemical-update-october-2021-using-sulfur-to-protect-vines-particularly-under-cool-conditions/
* Spray drift / wind speed: https://agriculture.vic.gov.au/farm-management/chemicals/spraying-agricultural-chemicals/managing-spray-drift/a-guide-to-estimating-wind-speed
* FRAC / IRAC mode-of-action classification: https://www.frac.info · https://irac-online.org

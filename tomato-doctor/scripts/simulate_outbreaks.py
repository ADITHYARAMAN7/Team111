"""
simulate_outbreaks.py - add SIMULATED community reports for demonstrating the
outbreak-alert feature before real farmers have used the app.

Every row is stored with source='simulated' and is labelled "(simulated data)"
in the app and the expert map, so it can never be mistaken for real reports.

    python scripts/simulate_outbreaks.py                 # default demo scenario
    python scripts/simulate_outbreaks.py --clear         # remove all simulated rows
"""
import argparse
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tomatodoc.config import load_config  # noqa: E402
from tomatodoc.db import Database  # noqa: E402

# (centre lat, lon, disease, n reports, spread km) - plausible seasonal pattern
SCENARIO = [
    (11.41, 76.70, "late_blight", 9, 12),        # Nilgiris: cool, misty
    (11.41, 76.70, "leaf_mold", 4, 10),
    (12.52, 78.21, "leaf_curl_virus", 7, 15),    # Krishnagiri belt: whitefly-borne virus
    (12.74, 77.83, "whitefly", 5, 10),           # Hosur
    (10.36, 77.98, "bacterial_wilt", 4, 12),     # Dindigul
    (11.02, 76.96, "early_blight", 5, 14),       # Coimbatore
    (11.66, 78.15, "fruit_borer", 4, 12),        # Salem
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    db = Database(load_config()["DATABASE_PATH"])
    with db.tx() as c:
        c.execute("DELETE FROM reports WHERE source='simulated'")
    if args.clear:
        print("simulated reports removed")
        return
    rng = random.Random(args.seed)
    n = 0
    for lat, lon, disease, count, km in SCENARIO:
        for _ in range(count):
            dlat, dlon = rng.gauss(0, km / 111 / 2), rng.gauss(0, km / 111 / 2)
            age = rng.uniform(0, 18) * 86400
            db.add_report(disease, round(lat + dlat, 2), round(lon + dlon, 2), "simulated", None, time.time() - age)
            n += 1
    print(f"added {n} simulated reports (labelled as simulated in the UI)")


if __name__ == "__main__":
    main()

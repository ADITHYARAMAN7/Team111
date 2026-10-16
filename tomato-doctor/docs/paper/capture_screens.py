"""Captures the application screenshots used in the paper (desktop layout).

The app must run on :5057 against a throw-away database with demonstration outbreak
reports, so that real consultation data is never used:

    set DATABASE_PATH=%TEMP%/paper_demo.db         (or export on Linux/macOS)
    python scripts/simulate_outbreaks.py
    PORT=5057 python run.py
    python docs/paper/capture_screens.py
"""
import json
import os
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

BASE = os.environ.get("APP_URL", "http://127.0.0.1:5057")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures", "screens")
os.makedirs(OUT, exist_ok=True)
OOTY = {"latitude": 11.41, "longitude": 76.70}
today = date.today()
FIELD = {"planting_date": (today - timedelta(days=84)).isoformat(), "variety": "Arka Rakshak", "crop_type": "hybrid",
         "area": 50, "unit": "cents", "harvesting": "yes", "last_pick": (today - timedelta(days=2)).isoformat(), "pick_every": 4}
SOIL = {"values": {"ph": 5.3, "ec": 0.6, "oc": 0.41, "n": 610, "p": 14, "k": 95, "zn": 0.45, "ca": 1.2},
        "texture": "loamy", "sample_date": (today - timedelta(days=40)).isoformat()}
LATE_BLIGHT = "இலையில் கருப்பு நனைஞ்ச திட்டு, ரொம்ப வேகமா பரவுது"
YES_WORDS = ("பஞ்சு", "திட்டுகள்", "தண்டில்", "எண்ணெய்", "fuzz", "patches", "stem", "oily", "white")


def new_page(browser, lang):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme="light",
                              geolocation=OOTY, permissions=["geolocation"])
    pg = ctx.new_page()
    pg.add_init_script(f"""localStorage.setItem('lang', JSON.stringify('{lang}'));
        localStorage.setItem('theme', JSON.stringify('light'));
        localStorage.setItem('field', JSON.stringify({json.dumps(FIELD)}));
        localStorage.setItem('soil', JSON.stringify({json.dumps(SOIL)}));""")
    return pg


def answer_until_result(pg):
    for _ in range(8):
        if not pg.is_visible("#view-consult"):
            break
        q = pg.inner_text("#qText")
        pg.click("[data-answer=yes]" if any(k in q for k in YES_WORDS) else "[data-answer=no]")
        pg.wait_for_timeout(700)
    pg.wait_for_selector("#view-result:not(.hidden)")


with sync_playwright() as p:
    b = p.chromium.launch()

    # (a) the diagnosis workspace, Tamil interface, with live field conditions
    pg = new_page(b, "ta")
    pg.goto(BASE)
    pg.wait_for_selector("#fieldCard .wx", timeout=40000)
    pg.fill("#farmerInput", LATE_BLIGHT)
    pg.wait_for_timeout(4500)                                   # let the location toast disappear
    pg.screenshot(path=f"{OUT}/d1_home.png")

    # (b) consultation and (c) result, English interface
    pg = new_page(b, "en")
    pg.goto(BASE)
    pg.wait_for_selector("#fieldCard .wx", timeout=40000)
    pg.fill("#farmerInput", "spots on the leaves and the leaves are turning yellow")
    pg.click("#startBtn")
    pg.wait_for_selector("#view-consult:not(.hidden)")
    pg.wait_for_timeout(4500)
    pg.screenshot(path=f"{OUT}/d2_consult.png")
    pg.click("#view-consult [data-nav=home]")
    pg.wait_for_timeout(400)
    pg.fill("#farmerInput", LATE_BLIGHT)
    pg.click("#startBtn")
    pg.wait_for_timeout(1500)
    answer_until_result(pg)
    pg.wait_for_timeout(1200)
    pg.screenshot(path=f"{OUT}/d3_result.png")
    pg.evaluate("window.scrollTo(0, document.querySelector('.card.plan').getBoundingClientRect().top + scrollY - 90)")
    pg.wait_for_timeout(600)
    pg.screenshot(path=f"{OUT}/d4_plan.png")

    # (e) My field: crop stage, picking rhythm and soil report
    pg.click("[data-nav-item=field]")
    pg.wait_for_selector("#view-field:not(.hidden)")
    pg.wait_for_selector("#soilReport .sr-list", timeout=20000)
    pg.wait_for_timeout(800)
    pg.screenshot(path=f"{OUT}/d5_field.png")

    # expert console
    ex = b.new_context(viewport={"width": 1280, "height": 760}, device_scale_factor=2, color_scheme="light").new_page()
    ex.add_init_script("localStorage.setItem('theme', JSON.stringify('light'));")
    ex.goto(BASE + "/expert?shot=1#graph")
    ex.wait_for_timeout(6000)
    ex.fill("#graphSearch", "Late Blight")
    ex.dispatch_event("#graphSearch", "change")
    ex.wait_for_timeout(2500)
    box = ex.locator("#graph").bounding_box()
    ex.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    for _ in range(3):
        ex.mouse.wheel(0, 250)
        ex.wait_for_timeout(300)
    ex.wait_for_timeout(1200)
    ex.locator("#graph").screenshot(path=f"{OUT}/g_graph.png")
    ex.goto(BASE + "/expert?shot=2#outbreaks")
    ex.wait_for_timeout(4000)
    ex.locator("#obMap").screenshot(path=f"{OUT}/g_map.png")
    b.close()
print("screens saved to", OUT)

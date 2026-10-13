"""Captures the application screenshots used in the paper (app must run on :5057).
    python docs/paper/capture_screens.py
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("APP_URL", "http://127.0.0.1:5057")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures", "screens")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": 390, "height": 2600}, device_scale_factor=3, locale="ta-IN", color_scheme="light")
    pg = ctx.new_page()
    pg.goto(BASE)
    pg.evaluate("localStorage.clear()")
    pg.goto(BASE)
    pg.wait_for_selector("#exampleChips .chip")
    pg.click("#locChip")
    pg.click("[data-district='11.41,76.7']")
    pg.wait_for_selector("#fieldCard:not(.hidden)", timeout=30000)
    pg.fill("#farmerInput", "இலையில் கருப்பு நனைஞ்ச திட்டு, ரொம்ப வேகமா பரவுது")
    pg.locator("#fieldCard").screenshot(path=f"{OUT}/a_field.png")
    pg.locator(".compose").screenshot(path=f"{OUT}/a_compose.png")
    # pass 1: a vague description -> the dialogue view
    pg.fill("#farmerInput", "இலையில் புள்ளிகள் இருக்கு, இலை மஞ்சளா ஆகுது")
    pg.click("#startBtn")
    pg.wait_for_selector("#view-consult:not(.hidden)")
    pg.wait_for_timeout(600)
    pg.locator("#questionCard").screenshot(path=f"{OUT}/b_question.png")
    pg.locator("#posteriorBars").locator("xpath=..").screenshot(path=f"{OUT}/b_bars.png")
    # pass 2: the late-blight description -> result
    pg.click("#view-consult [data-nav=home]")
    pg.wait_for_timeout(300)
    pg.fill("#farmerInput", "இலையில் கருப்பு நனைஞ்ச திட்டு, ரொம்ப வேகமா பரவுது")
    pg.click("#startBtn")
    pg.wait_for_timeout(1500)
    for _ in range(8):
        if not pg.is_visible("#view-consult"):
            break
        q = pg.inner_text("#qText")
        yes = any(k in q for k in ("பஞ்சு", "திட்டுகள்", "தண்டில்", "எண்ணெய்"))
        pg.click("[data-answer=yes]" if yes else "[data-answer=no]")
        pg.wait_for_timeout(700)
    pg.wait_for_selector("#view-result:not(.hidden)")
    pg.click("#langToggle")
    pg.wait_for_timeout(900)
    pg.locator(".result-hero").screenshot(path=f"{OUT}/c_hero.png")
    pg.locator(".card.spray").screenshot(path=f"{OUT}/d_spray.png")
    pg.locator(".card.plan").screenshot(path=f"{OUT}/d_plan.png")
    pg.locator(".card.why").screenshot(path=f"{OUT}/e_why.png")
    pg.locator("#calcCard").screenshot(path=f"{OUT}/f_calc.png")
    pg.locator(".card.treat").screenshot(path=f"{OUT}/f_treat.png")

    ex = b.new_context(viewport={"width": 1280, "height": 760}, device_scale_factor=2).new_page()
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
from PIL import Image
im = Image.open(f"{OUT}/a_field.png")
im.crop((0, 0, im.width, min(im.height, 1880))).save(f"{OUT}/a_field_top.png")
print("screens saved to", OUT)

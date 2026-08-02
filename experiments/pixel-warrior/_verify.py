"""
Quick visual verification: render 5 key frames from the HTML game.
Goal: catch bugs in game logic BEFORE running the full 1800-frame render.
"""
import asyncio
import os
from playwright.async_api import async_playwright

HTML = "file:///D:/code/MyWord/experiments/pixel-warrior/index.html"
OUT_DIR = r"D:\code\MyWord\experiments\pixel-warrior\_verify"
DURATION = 30.0

# Key timestamps to inspect (seconds)
CHECKPOINTS = [
    (1.5,   "01_title.png"),
    (5.0,   "02_walkin.png"),
    (9.5,   "03_drop.png"),
    (12.5,  "04_attack1_impact.png"),
    (18.5,  "05_attack2_impact.png"),
    (23.3,  "06_finalblow_impact.png"),
    (26.5,  "07_death.png"),
    (29.5,  "08_victory.png"),
]

async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(HTML)
        await page.wait_for_timeout(1500)

        for t, name in CHECKPOINTS:
            progress = t / DURATION
            await page.evaluate(f"window.__renderFrameAt({progress})")
            await page.wait_for_timeout(60)  # let any layout settle
            out = os.path.join(OUT_DIR, name)
            await page.screenshot(path=out, type="png")
            print(f"[ok] t={t:5.1f}s  -> {out}")

        await browser.close()
    print("DONE")

asyncio.run(main())

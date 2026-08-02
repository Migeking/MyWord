"""V4 验证 - 粒子 + 机械鱼"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_DIR = Path(__file__).parent.resolve()
HTML_PATH = (PROJECT_DIR / "index.html").as_uri()

SAMPLE_TIMES = [
    (5.0,  "01_title"),
    (8.0,  "02_chaos"),
    (15.0, "03_condense"),
    (25.0, "04_ignite"),
    (40.0, "05_swim"),
    (58.0, "06_end"),
]

WIDTH, HEIGHT = 1080, 1440
TOTAL = 60

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=swiftshader"]
        )
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        await page.add_init_script("window.__externalDriver = true;")
        await page.goto(HTML_PATH, wait_until="load")
        await page.wait_for_timeout(3500)

        for t, label in SAMPLE_TIMES:
            progress = t / TOTAL
            await page.evaluate(f"window.__renderFrameAt({progress})")
            await page.wait_for_timeout(200)
            buf = await page.screenshot(type='jpeg', quality=92)
            out = PROJECT_DIR / f"_v4_{label}.jpg"
            out.write_bytes(buf)
            print(f"t={t:5.1f}s -> {out.name}")

        await browser.close()
    print("Done.")

asyncio.run(main())

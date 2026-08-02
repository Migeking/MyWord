"""V2 快速验证 - 抽样 4 个关键时刻"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_DIR = Path(__file__).parent.resolve()
HTML_PATH = (PROJECT_DIR / "index.html").as_uri()

SAMPLE_TIMES = [
    (5.0,  "01_inkdrop_title"),
    (15.0, "02_condense"),
    (25.0, "03_branches_grow"),
    (35.0, "04_streaks_full"),
    (50.0, "05_falling"),
    (58.0, "06_end_text"),
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
            out = PROJECT_DIR / f"_v2_{label}.jpg"
            out.write_bytes(buf)
            print(f"t={t:5.1f}s -> {out.name}")

        # Verify BGM element exists
        bgm_check = await page.evaluate("""() => {
            const a = document.getElementById('bgm');
            return {
                exists: !!a,
                src: a?.querySelector('source')?.src || '',
                volume: a?.volume,
                paused: a?.paused
            };
        }""")
        print(f"BGM status: {bgm_check}")

        await browser.close()
    print("Done.")

asyncio.run(main())

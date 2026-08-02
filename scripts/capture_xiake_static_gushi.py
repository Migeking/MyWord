"""Capture static slides (one per slide) for 侠客行 in the gushi directory."""
import asyncio
import os
import glob

SLIDE_DIR = os.path.abspath("D:/code/MyWord/xhs-output/古诗词参考/xiake_slides")
HTML_PATH = os.path.abspath("D:/code/MyWord/xhs-output/古诗词参考/xiakexing_static.html")

async def capture():
    from playwright.async_api import async_playwright

    os.makedirs(SLIDE_DIR, exist_ok=True)

    # Clean old
    for f in glob.glob(os.path.join(SLIDE_DIR, "*.png")):
        os.remove(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(f"file:///{HTML_PATH.replace(chr(92), '/')}")
        await page.wait_for_timeout(2000)

        total_slides = 30
        for i in range(1, total_slides + 1):
            # Show slide i, hide others
            await page.evaluate(f"""
                (() => {{
                    document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
                    var el = document.getElementById('s{i}');
                    if (el) el.classList.add('active');
                }})()
            """)
            await page.wait_for_timeout(300)  # let CSS settle

            filepath = os.path.join(SLIDE_DIR, f"slide_{i:02d}.png")
            await page.screenshot(path=filepath)
            print(f"  [{i}/{total_slides}] {filepath}")

        await browser.close()

    files = glob.glob(os.path.join(SLIDE_DIR, "slide_*.png"))
    print(f"\nDone! {len(files)} slides captured.")

asyncio.run(capture())

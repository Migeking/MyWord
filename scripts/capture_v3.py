"""Capture V3 slides (14 slides: title + 12 couplets + ending)."""
import asyncio, os, glob

SLIDE_DIR = os.path.abspath("D:/code/MyWord/xhs-output/侠客行_v3/slides")
HTML_PATH = os.path.abspath("D:/code/MyWord/xhs-output/侠客行_v3/index.html")

async def capture():
    from playwright.async_api import async_playwright
    os.makedirs(SLIDE_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(SLIDE_DIR, "*.png")):
        os.remove(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(f"file:///{HTML_PATH.replace(chr(92), '/')}")
        await page.wait_for_timeout(2000)

        total = 14  # 0-indexed: 0=title, 1-12=couplets, 13=ending
        for i in range(total):
            await page.evaluate(f"window.showSlide({i})")
            await page.wait_for_timeout(500)

            idx_str = f"slide_{i+1:02d}.png"
            path = os.path.join(SLIDE_DIR, idx_str)
            await page.screenshot(path=path, full_page=False)
            print(f"  Captured {idx_str}")

        await browser.close()
    print(f"\nDone! {total} slides saved to {SLIDE_DIR}")

if __name__ == "__main__":
    asyncio.run(capture())

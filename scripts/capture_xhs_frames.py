"""Capture frames at 10fps from animated HTML."""
import asyncio, os, glob
from playwright.async_api import async_playwright

async def capture():
    html_path = os.path.abspath(r"D:\code\MyWord\xhs-output\Transformer图解_animated.html")
    slides_dir = os.path.abspath(r"D:\code\MyWord\xhs-output\slides")
    os.makedirs(slides_dir, exist_ok=True)
    for f in glob.glob(os.path.join(slides_dir, "*.png")): os.remove(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-setuid-sandbox","--disable-web-security"])
        page = await browser.new_page(viewport={"width":1080,"height":1440})
        await page.goto(f"file:///{html_path.replace(chr(92),'/')}")
        await page.wait_for_timeout(4000)

        total_frames = 505  # 50.5 seconds * 10fps = 505 frames
        for i in range(total_frames):
            await page.screenshot(
                path=os.path.join(slides_dir, f"frame_{i:04d}.png"))
            if i < total_frames - 1: await asyncio.sleep(0.1)
        await browser.close()
    print(f"Done: {len(glob.glob(os.path.join(slides_dir, 'frame_*.png')))} frames")

asyncio.run(capture())

"""Capture animated HTML as a single webm video using Playwright recordVideo API.

Why video recording (not frame-by-frame screenshot):
  - 1 recording vs 1830 PNGs — 10-50x faster
  - Real frame rate, no asyncio.sleep drift
  - Output webm can be re-timed to any fps via ffmpeg
  - Smaller disk usage during capture
"""
import asyncio, os
from playwright.async_api import async_playwright

OUT_DIR = r"D:\code\MyWord\xhs-output\mei-ci-nu-li"
HTML_PATH = r"D:\code\MyWord\work\mei-ci-nu-li\index.html"
VIDEO_DIR = os.path.join(OUT_DIR, "video")
TOTAL_DURATION_S = 61  # 源 HTML GSAP timeline 总时长

async def capture():
    os.makedirs(VIDEO_DIR, exist_ok=True)
    # 清空旧文件
    for f in os.listdir(VIDEO_DIR):
        os.remove(os.path.join(VIDEO_DIR, f))

    file_url = "file:///" + HTML_PATH.replace("\\", "/")
    print(f"[1/3] Launching Chromium @ 1080x1440 ...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--autoplay-policy=no-user-gesture-required",  # 允许 BGM 自动播放
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1080, "height": 1440},
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1080, "height": 1440},
        )
        page = await context.new_page()
        # 阻止外部 Google Fonts（避免网络慢导致 domcontentloaded 卡住）
        # GSAP CDN 必须保留，否则动画跑不起来
        await page.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        await page.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        print(f"[2/3] Navigating to {file_url}")
        # 用 load 而非 domcontentloaded：等所有同步资源（GSAP）就绪
        await page.goto(file_url, wait_until="load", timeout=60000)

        # 等 GSAP 时间线构建并自动播放（DOMContentLoaded 后 1200ms 触发）
        await page.wait_for_timeout(4000)
        # 总录制时长：4s 等待 + 61s 动画 = 65s
        print(f"[3/3] Recording for {TOTAL_DURATION_S}s ...")
        await asyncio.sleep(TOTAL_DURATION_S)

        await page.close()
        await context.close()
        await browser.close()

    # 找到生成的 webm 并改名
    webms = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".webm")]
    if not webms:
        raise RuntimeError("No webm produced")
    src = os.path.join(VIDEO_DIR, webms[0])
    dst = os.path.join(VIDEO_DIR, "recording.webm")
    os.rename(src, dst)
    size_mb = os.path.getsize(dst) / 1024 / 1024
    print(f"Done: {dst} ({size_mb:.2f} MB)")

asyncio.run(capture())

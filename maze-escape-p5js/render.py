"""
Maze Escape p5.js: 60-second MP4 render via Playwright + FFmpeg pipe.
Pipeline: 3600 frames (1080x1440, 60fps) piped to FFmpeg stdin -> output.mp4
"""
import asyncio
import os
import subprocess
import sys
import threading
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = f"file:///{HERE.replace(os.sep, '/')}/index.html"
OUTPUT_VIDEO = os.path.join(HERE, "output.mp4")
FFMPEG_LOG = os.path.join(HERE, "ffmpeg.log")

FPS = 60
DURATION = 60
TOTAL_FRAMES = FPS * DURATION
WIDTH = 1080
HEIGHT = 1440
JPEG_QUALITY = 90
FFMPEG_TIMEOUT = 600

# BGM: cyber-particle-fish (256s, cyber/tech aesthetic fits maze-escape)
BGM_PATH = "D:/code/MyWord/xhs-output/cyber-particle-fish-v1/bgm.mp3"


def build_ffmpeg_cmd():
    """FFmpeg: video frames from pipe stdin + BGM audio overlay"""
    return [
        'ffmpeg', '-y',
        '-f', 'image2pipe', '-vcodec', 'mjpeg',
        '-r', str(FPS), '-i', '-',          # video frames from pipe
        '-i', BGM_PATH,                      # BGM audio track
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'medium', '-crf', '20',
        '-movflags', '+faststart',
        '-c:a', 'aac', '-b:a', '192k',      # audio codec
        '-af', 'volume=0.35',               # BGM at 35% volume
        '-shortest',                         # cut to video duration
        OUTPUT_VIDEO,
    ]


def watchdog_kill(process, timeout, label):
    def _watch():
        try:
            ret = process.wait(timeout=timeout)
            print(f"[watchdog] {label} exited with code {ret}")
        except subprocess.TimeoutExpired:
            print(f"[watchdog] {label} exceeded {timeout}s -- KILLING", file=sys.stderr)
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    t = threading.Thread(target=_watch, daemon=True)
    t.start()
    return t


async def render_video():
    print(f"[render] {WIDTH}x{HEIGHT} @ {FPS}fps, {DURATION}s ({TOTAL_FRAMES} frames)")
    ffmpeg_log = open(FFMPEG_LOG, 'w')
    process = subprocess.Popen(
        build_ffmpeg_cmd(),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=ffmpeg_log,
    )
    watchdog_kill(process, FFMPEG_TIMEOUT, "FFmpeg")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
            await page.goto(HTML)
            await page.wait_for_function(
                "typeof window.__renderFrameAt === 'function'", timeout=15000
            )
            await page.wait_for_timeout(3000)

            t0 = asyncio.get_event_loop().time()
            for i in range(TOTAL_FRAMES):
                progress = i / TOTAL_FRAMES
                await page.evaluate(f"window.__renderFrameAt({progress})")
                buf = await page.screenshot(
                    type='jpeg', quality=JPEG_QUALITY,
                    clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT},
                )
                process.stdin.write(buf)
                if i % 120 == 0 or i == TOTAL_FRAMES - 1:
                    elapsed = asyncio.get_event_loop().time() - t0
                    fps_actual = (i + 1) / elapsed if elapsed > 0 else 0
                    print(
                        f"[render] {i:4d}/{TOTAL_FRAMES}  {progress*100:5.1f}%  "
                        f"{len(buf)//1024}KB  elapsed={elapsed:.1f}s  fps={fps_actual:.1f}",
                        flush=True,
                    )
            await browser.close()
    except Exception as e:
        print(f"[render] ERROR: {e}", file=sys.stderr)
        try:
            process.stdin.close()
        except Exception:
            pass
        process.kill()
        ffmpeg_log.close()
        raise

    process.stdin.close()
    print(f"[render] Pipe closed. Waiting for FFmpeg (timeout={FFMPEG_TIMEOUT}s)...")
    try:
        ret = process.wait(timeout=FFMPEG_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"[render] FFmpeg killed after {FFMPEG_TIMEOUT}s", file=sys.stderr)
        process.kill()
        ret = -1

    ffmpeg_log.close()
    if ret != 0:
        print(f"[render] FFmpeg exit code {ret}", file=sys.stderr)
        sys.exit(1)
    size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"[render] DONE  {OUTPUT_VIDEO}  size={size_mb:.1f} MB")


if __name__ == "__main__":
    asyncio.run(render_video())

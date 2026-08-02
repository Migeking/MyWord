"""
Pixel Warrior: full 30-second MP4 render with procedural audio.

Pipeline:
1. Generate audio.wav (chiptune BGM + game SFX) via audio.py
2. Render 1800 frames (1080x1440, 60fps) into _temp_video.mp4
3. Mux video + audio -> output.mp4 (libx264 video + AAC audio)
"""
import asyncio
import os
import subprocess
import sys
import threading
from playwright.async_api import async_playwright

import audio  # procedural chiptune BGM + SFX generator

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = f"file:///{HERE.replace(os.sep, '/')}/index.html"
TEMP_VIDEO = os.path.join(HERE, "_temp_video.mp4")
OUTPUT_VIDEO = os.path.join(HERE, "output.mp4")
AUDIO_FILE = os.path.join(HERE, "audio.wav")
FFMPEG_LOG = os.path.join(HERE, "ffmpeg.log")

FPS = 60
DURATION = 30
TOTAL_FRAMES = FPS * DURATION  # 1800
WIDTH = 1080
HEIGHT = 1440
JPEG_QUALITY = 80
FFMPEG_TIMEOUT = 180  # seconds after pipe close


def build_video_ffmpeg_cmd():
    return [
        'ffmpeg', '-y',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-r', str(FPS),
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        '-crf', '20',
        '-movflags', '+faststart',
        TEMP_VIDEO,
    ]


def build_mux_cmd():
    return [
        'ffmpeg', '-y',
        '-i', TEMP_VIDEO,
        '-i', AUDIO_FILE,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        OUTPUT_VIDEO,
    ]


def watchdog_kill(process, timeout, label):
    def _watch():
        try:
            ret = process.wait(timeout=timeout)
            print(f"[watchdog] {label} exited with code {ret}")
        except subprocess.TimeoutExpired:
            print(f"[watchdog] {label} exceeded {timeout}s — KILLING", file=sys.stderr)
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    t = threading.Thread(target=_watch, daemon=True)
    t.start()
    return t


def ensure_audio():
    """Generate audio.wav if not present or stale."""
    if os.path.exists(AUDIO_FILE) and os.path.getsize(AUDIO_FILE) > 100_000:
        print(f"[audio] Reusing {AUDIO_FILE} ({os.path.getsize(AUDIO_FILE)//1024} KB)")
        return
    print("[audio] Generating BGM + SFX...")
    bgm = audio.make_bgm(audio.DURATION)
    sfx_list = [
        audio.sfx_sword_swing(), audio.sfx_hit(), audio.sfx_monster_hurt(),
        audio.sfx_sword_swing(), audio.sfx_hit(), audio.sfx_monster_hurt(),
        audio.sfx_sword_swing(), audio.sfx_hit(), audio.sfx_monster_death(),
        audio.sfx_victory(),
    ]
    timestamps = [11.5, 12.2, 14.0, 17.5, 18.2, 20.0, 22.5, 23.2, 25.0, 28.5]
    mix = audio.mix(bgm, sfx_list, timestamps, audio.DURATION)
    audio.write_wav(AUDIO_FILE, mix)
    print(f"[audio] {AUDIO_FILE}: {os.path.getsize(AUDIO_FILE)//1024} KB")


async def render_video():
    print(f"[render] {WIDTH}x{HEIGHT} @ {FPS}fps, {DURATION}s ({TOTAL_FRAMES} frames)")
    ffmpeg_log = open(FFMPEG_LOG, 'w')
    process = subprocess.Popen(
        build_video_ffmpeg_cmd(),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=ffmpeg_log,
    )
    watchdog_kill(process, 30 * 60, "FFmpeg (render)")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
            await page.goto(HTML)
            await page.wait_for_function("typeof window.__renderFrameAt === 'function'", timeout=10000)
            await page.wait_for_timeout(500)

            t0 = asyncio.get_event_loop().time()
            for i in range(TOTAL_FRAMES):
                progress = i / TOTAL_FRAMES
                await page.evaluate(f"window.__renderFrameAt({progress})")
                buf = await page.screenshot(
                    type='jpeg',
                    quality=JPEG_QUALITY,
                    clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT},
                )
                process.stdin.write(buf)
                if i % 120 == 0 or i == TOTAL_FRAMES - 1:
                    elapsed = asyncio.get_event_loop().time() - t0
                    fps_actual = (i + 1) / elapsed if elapsed > 0 else 0
                    print(f"[render] {i:4d}/{TOTAL_FRAMES}  {progress*100:5.1f}%  "
                          f"{len(buf)//1024}KB  elapsed={elapsed:.1f}s  fps={fps_actual:.1f}",
                          flush=True)

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
    print(f"[render] Pipe closed. Waiting for FFmpeg encode (timeout={FFMPEG_TIMEOUT}s)...")
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
    print(f"[render] temp video: {TEMP_VIDEO}  size={os.path.getsize(TEMP_VIDEO)//1024//1024} MB")


def mux_audio():
    print(f"[mux] Muxing video + audio -> {OUTPUT_VIDEO}")
    ret = subprocess.run(build_mux_cmd(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if ret.returncode != 0:
        print(f"[mux] FFmpeg mux failed: {ret.stderr.decode(errors='ignore')[-2000:]}", file=sys.stderr)
        sys.exit(1)
    size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
    print(f"[mux] DONE  {OUTPUT_VIDEO}  size={size_mb:.1f} MB")


def main():
    ensure_audio()
    asyncio.run(render_video())
    mux_audio()
    try:
        os.remove(TEMP_VIDEO)
    except Exception:
        pass
    print(f"[main] FINAL OUTPUT: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()

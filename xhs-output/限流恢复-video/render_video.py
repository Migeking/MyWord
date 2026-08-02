"""Render video using Playwright's built-in recording + FFmpeg audio mix."""

import asyncio, os, json, subprocess
from playwright.async_api import async_playwright

HERE = os.path.abspath(os.path.dirname(__file__))
HTML_PATH = os.path.join(HERE, "index.html")
OUTPUT_DIR = os.path.join(HERE, "renders")
ASSETS_DIR = os.path.join(HERE, "assets")
TIMING_PATH = os.path.join(HERE, "timing.json")
VIDEO_ONLY = os.path.join(OUTPUT_DIR, "video-only.mp4")
FINAL_OUTPUT = os.path.join(OUTPUT_DIR, "限流恢复-video-bgm.mp4")
COMPOSITION_ID = "限流恢复-video"
TOTAL_DURATION = 159.02
PLAYBACK_SCALE = 4   # Play at 4x speed to reduce recording time
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def record_video():
    """Record the HTML animation to video using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-web-security", "--autoplay-policy=no-user-gesture-required"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1080, "height": 1920},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1080, "height": 1920}
        )
        page = await ctx.new_page()

        html_url = HTML_PATH.replace("\\", "/")
        await page.goto(f"file:///{html_url}")
        await page.wait_for_timeout(3000)

        has_tl = await page.evaluate(f"""() => {{
            var tl = window.__timelines && window.__timelines['{COMPOSITION_ID}'];
            return !!tl;
        }}""")
        print(f"Timeline found: {has_tl}")

        if not has_tl:
            await browser.close()
            return None

        # Play at normal speed
        await page.evaluate(f"""() => {{
            var tl = window.__timelines && window.__timelines['{COMPOSITION_ID}'];
            tl.timeScale(1);
            tl.play();
        }}""")

        wait_time = TOTAL_DURATION + 1.0
        print(f"Playing at 1x speed ({wait_time:.0f}s)...")
        for i in range(10, int(wait_time) + 1, 10):
            await asyncio.sleep(10)
            print(f"  Playing: {i}/{int(wait_time)}s")
        await asyncio.sleep(max(0, wait_time - ((wait_time // 10) * 10)) + 2)

        await page.close()
        await ctx.close()
        await browser.close()

        import glob
        vids = glob.glob(os.path.join(OUTPUT_DIR, "*.webm"))
        vids += glob.glob(os.path.join(OUTPUT_DIR, "*.mp4"))
        if vids:
            src = max(vids, key=os.path.getctime)
            if src != VIDEO_ONLY:
                os.rename(src, VIDEO_ONLY)
            print(f"Recorded: {VIDEO_ONLY} ({os.path.getsize(VIDEO_ONLY)/1024/1024:.0f} MB)")
            return VIDEO_ONLY
        print("No video file found!")
        return None


def mix_audio(video_path):
    """Mix WAV + BGM into the video at correct timestamps."""
    with open(TIMING_PATH) as f:
        timing = json.load(f)

    print("\nMixing audio...")
    cmd = ["ffmpeg", "-y", "-i", video_path]
    slides = timing["slides"]
    has_bgm = os.path.exists(os.path.join(ASSETS_DIR, "bgm.mp3"))

    for s in slides:
        w = os.path.join(ASSETS_DIR, f"chattts-slide-{s['slide']}.wav")
        if os.path.exists(w):
            cmd += ["-i", w]
    if has_bgm:
        cmd += ["-i", os.path.join(ASSETS_DIR, "bgm.mp3")]

    n_voices = len([s for s in slides if os.path.exists(os.path.join(ASSETS_DIR, f"chattts-slide-{s['slide']}.wav"))])
    n_total = n_voices + (1 if has_bgm else 0)
    # Slow video back from PLAYBACK_SCALE x to 1x (recorded faster, need to stretch)
    parts = [f"[0:v]setpts={PLAYBACK_SCALE}*PTS[v]"]
    mix_in = []

    for i, s in enumerate(slides):
        w = os.path.join(ASSETS_DIR, f"chattts-slide-{s['slide']}.wav")
        if os.path.exists(w):
            d = int(s["start"] * 1000)
            parts.append(f"[{i+1}:a]adelay={d}|{d}[a{i}]")
            mix_in.append(f"[a{i}]")

    if has_bgm:
        parts.append(f"[{n_voices+1}:a]volume=0.15[bgm]")
        mix_in.append("[bgm]")

    parts.append(f"{''.join(mix_in)}amix=inputs={n_total}:duration=longest[a]")
    cmd += ["-filter_complex", ";".join(parts),
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k", "-shortest", FINAL_OUTPUT]

    print("Running FFmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode:
        print(f"FFmpeg error: {r.stderr[:2000]}")
        return None
    print(f"Done: {FINAL_OUTPUT}")
    return FINAL_OUTPUT


def verify(path):
    r = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=size,duration:stream=codec_name,codec_type,width,height",
        "-of", "default=noprint_wrappers=1", path
    ], capture_output=True, text=True)
    print("\nVerification:")
    print(r.stdout)
    print(f"Size: {os.path.getsize(path)/1024/1024:.0f} MB")


async def main():
    print("=" * 40)
    print("Step 1: Record video (Playwright)")
    print("=" * 40)
    v = await record_video()
    if not v or not os.path.exists(v):
        print("Recording failed"); return

    print("\n" + "=" * 40)
    print("Step 2: Mix audio (FFmpeg)")
    print("=" * 40)
    out = mix_audio(v)
    if out and os.path.exists(out):
        verify(out)


if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""
9.AI重构工业 - 修复末尾文字截断：延长等待+录制时间，确保 5 段诗全部进视频
"""
import os
import time
import shutil
import subprocess
import glob
from playwright.sync_api import sync_playwright

ROOT = r"d:\code\MyWord\9.AI重构工业"
HTML_PATH = os.path.join(ROOT, "index.html")
AUDIO_PATH = os.path.join(ROOT, "audio", "final-audio.mp3")
RECORD_DIR = os.path.join(ROOT, "record_tmp")
OUTPUT_DIR = os.path.join(ROOT, "output")
FINAL_MP4 = os.path.join(ROOT, "AI-重构工业-配音版.mp4")

# === 关键参数：等 8s 让页面完全加载，录 35s 覆盖 mainTl 0-20 ===
WAIT_BEFORE_RECORD_MS = 8000
DURATION_MS = 35000
WIDTH = 1080
HEIGHT = 1920
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def cleanup():
    if os.path.exists(RECORD_DIR):
        shutil.rmtree(RECORD_DIR, ignore_errors=True)
    os.makedirs(RECORD_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            try: os.remove(os.path.join(OUTPUT_DIR, f))
            except: pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def record():
    print(f"[1/3] Playwright 录 {DURATION_MS/1000:.0f}s（已等 {WAIT_BEFORE_RECORD_MS/1000:.0f}s）")
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox", "--disable-dev-shm-usage",
                "--autoplay-policy=no-user-gesture-required",
                "--disable-features=UseSurfaceLayerForVideo",
                "--use-fake-ui-for-media-stream",
            ],
            executable_path=EDGE,
        )
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=RECORD_DIR,
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()

        url = "file:///" + os.path.abspath(HTML_PATH).replace("\\", "/")
        print(f"      打开: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # 强制静音
        page.evaluate("document.querySelectorAll('audio,video').forEach(m=>m.muted=true)")

        # 关键：等 8s，让 Three.js + 30万粒子 + GSAP 全部稳定
        print(f"      等待页面完全初始化（{WAIT_BEFORE_RECORD_MS/1000:.0f}s）...")
        page.wait_for_timeout(WAIT_BEFORE_RECORD_MS)

        # 录制 33s（覆盖 mainTl 0-20 + 余量，确保 5 段诗全部进视频）
        print(f"      录制中... (boot 8s + main 20s + 余量 5s)")
        page.wait_for_timeout(DURATION_MS)

        context.close()
        browser.close()
    print(f"      [OK] 录制完成 ({time.time()-t0:.1f}s)")

    videos = glob.glob(os.path.join(RECORD_DIR, "*.webm"))
    if not videos:
        raise RuntimeError("未找到录制的视频文件")
    src = videos[0]
    dst = os.path.join(OUTPUT_DIR, "video-only.webm")
    shutil.move(src, dst)
    print(f"      录制文件: {dst} ({os.path.getsize(dst)/1024/1024:.1f} MB)")
    return dst

def transcode_mux(src):
    print(f"[2/3] ffmpeg 转码 webm → mp4 + 合成配音")
    final = FINAL_MP4
    # 单条命令：转码 webm + 合并配音
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-i", AUDIO_PATH,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-vf", f"scale={WIDTH}:{HEIGHT}",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("      [ERR] ffmpeg 失败：")
        print(r.stderr[-2000:])
        raise SystemExit(1)
    size_mb = os.path.getsize(final) / 1024 / 1024
    print(f"      [OK] {final}")
    print(f"           大小: {size_mb:.1f} MB")
    return final

def verify(final):
    print(f"[3/3] 验证：抽帧确认 5 段诗都进视频")
    for t in [9.0, 14.5, 20.0, 23.0, 26.0, 28.0]:
        out = os.path.join(OUTPUT_DIR, f"verify_{t}.jpg")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(t), "-i", final,
            "-frames:v", "1", "-q:v", "3", out
        ], capture_output=True)
        if os.path.exists(out):
            print(f"      t={t}s -> 帧已保存 ({os.path.getsize(out)//1024} KB)")

if __name__ == "__main__":
    print("=" * 60)
    print("9.AI重构工业 - 修复末尾文字截断")
    print("=" * 60)
    cleanup()
    webm = record()
    final = transcode_mux(webm)
    verify(final)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", final], capture_output=True, text=True)
    duration = float(probe.stdout.strip()) if probe.returncode == 0 else 0
    print(f"\n[ALL DONE]")
    print(f"  最终视频: {final}")
    print(f"  时长:     {duration:.1f}s")
    print(f"  时间线:   0-8s boot → 8-28s main（5段诗: 9/14.5/20/23/26）→ 28-33s 终章")

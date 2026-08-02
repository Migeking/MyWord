#!/usr/bin/env python3
"""
9.AI重构工业 - HTML → 配音 MP4 渲染（v3 - Playwright 视频录制模式）
浏览器自己录 30s，比逐帧截图快 ~10x
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

DURATION_MS = 36000   # 录制 36 秒（覆盖 5 段配音）
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
    print(f"[1/4] Playwright 视频录制 {DURATION_MS/1000:.0f}s @ {WIDTH}x{HEIGHT}")
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
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

        # 强制静音（防止 <audio> 影响）
        page.evaluate("document.querySelectorAll('audio,video').forEach(m=>m.muted=true)")

        # 等 boot 完成 + 主内容播完（HTML 动画总长 28s，留 2s 缓冲）
        print(f"      录制中... (boot 8s + main 20s + buffer 2s)")
        page.wait_for_timeout(DURATION_MS)

        # 关闭 context 会触发视频文件 finalization
        context.close()
        browser.close()
    print(f"      [OK] 录制完成 ({time.time()-t0:.1f}s)")

    # 找到生成的 webm 文件
    videos = glob.glob(os.path.join(RECORD_DIR, "*.webm"))
    if not videos:
        raise RuntimeError("未找到录制的视频文件")
    src = videos[0]
    dst = os.path.join(OUTPUT_DIR, "video-only.webm")
    shutil.move(src, dst)
    print(f"      录制文件: {dst} ({os.path.getsize(dst)/1024/1024:.1f} MB)")
    return dst

def transcode(src):
    print(f"[2/4] ffmpeg 转 webm → mp4 (H.264 高质量)")
    video_mp4 = os.path.join(OUTPUT_DIR, "video-only.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-vf", f"scale={WIDTH}:{HEIGHT}",
        "-r", "30",
        video_mp4,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("      [ERR] 转码失败:")
        print(r.stderr[-1500:])
        raise SystemExit(1)
    print(f"      [OK] {video_mp4} ({os.path.getsize(video_mp4)/1024/1024:.1f} MB)")
    return video_mp4

def trim_video(src):
    print(f"[3/4] 精确裁剪到 {DURATION_MS/1000:.0f}s（去除开头 0.5s 黑屏）")
    video_trim = os.path.join(OUTPUT_DIR, "video-trimmed.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0.5",           # 跳过开头 0.5s（包含浏览器黑屏）
        "-i", src,
        "-t", str(DURATION_MS/1000 - 0.5),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        video_trim,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("      [WARN] 裁剪失败，使用未裁剪版本")
        return src
    print(f"      [OK] {video_trim}")
    return video_trim

def mux(video):
    print(f"[4/4] 合成配音 + 视频 → {FINAL_MP4}")
    if not os.path.exists(AUDIO_PATH):
        print(f"      [WARN] 配音不存在")
        shutil.copy(video, FINAL_MP4)
        return
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-i", AUDIO_PATH,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_MP4,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("      [ERR] 合成失败：")
        print(r.stderr[-1500:])
        raise SystemExit(1)
    size_mb = os.path.getsize(FINAL_MP4) / (1024*1024)
    print(f"      [OK] {FINAL_MP4}")
    print(f"           大小: {size_mb:.1f} MB")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", FINAL_MP4], capture_output=True, text=True)
    if probe.returncode == 0:
        print(f"           时长: {float(probe.stdout.strip()):.1f}s")

if __name__ == "__main__":
    print("=" * 60)
    print("9.AI重构工业 - HTML → 配音 MP4 渲染 (v3 video record)")
    print("=" * 60)
    cleanup()
    webm = record()
    mp4 = transcode(webm)
    trimmed = trim_video(mp4)
    mux(trimmed)
    print("\n[ALL DONE]")
    print(f"  最终视频: {FINAL_MP4}")

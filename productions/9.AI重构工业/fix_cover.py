#!/usr/bin/env python3
"""
9.AI重构工业 - 修复首帧白屏：用 hero 帧做封面
"""
import os
import subprocess

ROOT = r"d:\code\MyWord\9.AI重构工业"
OUTPUT_DIR = os.path.join(ROOT, "output")
AUDIO_PATH = os.path.join(ROOT, "audio", "final-audio.mp3")
FINAL_MP4 = os.path.join(ROOT, "AI-重构工业-配音版.mp4")

# === 封面配置 ===
HERO_TIME = 26.5         # 取自原视频的 GPU 特写帧（含 AI 字 + 全部硬件细节）
COVER_DURATION = 1.5     # 封面停留 1.5s 再开始动画
ANIM_SKIP = 2.0          # 动画从原视频 2s 处开始（跳过开头 2s 白屏/加载）

video_trimmed = os.path.join(OUTPUT_DIR, "video-trimmed.mp4")
hero_png = os.path.join(OUTPUT_DIR, "hero.png")
cover_mp4 = os.path.join(OUTPUT_DIR, "cover.mp4")
anim_mp4 = os.path.join(OUTPUT_DIR, "video-anim-only.mp4")
concat_mp4 = os.path.join(OUTPUT_DIR, "video-with-cover.mp4")
audio_delayed = os.path.join(OUTPUT_DIR, "audio-delayed.mp3")

def run(cmd, label):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [ERR] {label}:")
        print(r.stderr[-1500:])
        raise SystemExit(1)
    print(f"  [OK] {label}")

print("=" * 60)
print("修复首帧：用 GPU 特写做封面，跳过动画开头 2s 白屏")
print("=" * 60)

# 1) 提取 hero 帧
print(f"\n[1/5] 从原视频 {HERO_TIME}s 提取 hero 帧")
run([
    "ffmpeg", "-y", "-ss", str(HERO_TIME), "-i", video_trimmed,
    "-update", "1", "-frames:v", "1", "-q:v", "2", hero_png
], f"hero.png  ({os.path.getsize(hero_png)//1024} KB)")

# 2) hero 帧做成 1.5s 静止 cover 视频
print(f"\n[2/5] 把 hero 帧做成 {COVER_DURATION}s 静态 cover 视频")
run([
    "ffmpeg", "-y", "-loop", "1", "-i", hero_png,
    "-t", str(COVER_DURATION),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
    "-vf", "scale=1080:1920",
    cover_mp4
], "cover.mp4")

# 3) 原动画裁掉开头 2s 白屏
print(f"\n[3/5] 原动画裁掉开头 {ANIM_SKIP}s")
run([
    "ffmpeg", "-y", "-ss", str(ANIM_SKIP), "-i", video_trimmed,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
    anim_mp4
], "video-anim-only.mp4")

# 4) cover + 动画 拼接
print("\n[4/5] 拼接 cover + 动画")
run([
    "ffmpeg", "-y",
    "-i", cover_mp4, "-i", anim_mp4,
    "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]",
    "-map", "[v]",
    concat_mp4
], "video-with-cover.mp4")

# 5) 配音延迟 COVER_DURATION 秒后开始 + 合成
print(f"\n[5/5] 配音延迟 {COVER_DURATION}s + 合成最终 MP4")
delay_ms = int(COVER_DURATION * 1000)
run([
    "ffmpeg", "-y", "-i", AUDIO_PATH,
    "-af", f"adelay={delay_ms}|{delay_ms}",
    audio_delayed
], "audio-delayed.mp3")

run([
    "ffmpeg", "-y",
    "-i", concat_mp4, "-i", audio_delayed,
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    FINAL_MP4
], f"AI-重构工业-配音版.mp4")

# 报告
size_mb = os.path.getsize(FINAL_MP4) / 1024 / 1024
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", FINAL_MP4],
    capture_output=True, text=True)
duration = float(probe.stdout.strip()) if probe.returncode == 0 else 0
print(f"\n[ALL DONE]")
print(f"  最终视频: {FINAL_MP4}")
print(f"  大小:     {size_mb:.1f} MB")
print(f"  时长:     {duration:.1f}s")
print(f"  封面:     hero 帧（GPU 特写 + AI 像素字）@ {HERO_TIME}s")
print(f"  时序:     0-1.5s 封面 → 1.5s 起 boot 序列（无白屏）")

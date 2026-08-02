import os
import subprocess

ROOT = r"d:\code\MyWord\9.AI重构工业"
INPUT_MP4 = os.path.join(ROOT, "AI-重构工业-配音版.mp4")
OUTPUT_MP4 = os.path.join(ROOT, "AI-重构工业-配音版-新封面.mp4")
FRAME_PNG = os.path.join(ROOT, "output", "frame3.png")

def run(cmd, label):
    print(f"Running: {label}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [ERR] {label}:")
        print(r.stderr[-1500:])
        raise SystemExit(1)
    print(f"  [OK] {label}")

# 1. 提取第3秒的画面
run([
    "ffmpeg", "-y", "-ss", "3", "-i", INPUT_MP4,
    "-vframes", "1", "-q:v", "2", FRAME_PNG
], "提取第三秒的画面")

# 2. 将提取的画面作为视频的第一帧（覆盖 0 到 0.05 秒）
run([
    "ffmpeg", "-y",
    "-i", INPUT_MP4,
    "-i", FRAME_PNG,
    "-filter_complex", "[0:v][1:v]overlay=enable='between(t,0,0.05)'[outv]",
    "-map", "[outv]",
    "-map", "0:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "18",
    "-c:a", "copy",
    OUTPUT_MP4
], "替换第一帧并导出新视频")

import shutil
shutil.move(OUTPUT_MP4, INPUT_MP4)
print(f"成功将视频第一帧替换为第三秒的画面，并覆盖原文件: {INPUT_MP4}")

#!/usr/bin/env python3
"""批量生成 TTS 配音 + 获取每段时长"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))
from tts import read_input, tts_edge, get_mp3_duration

# 读取脚本
script_path = os.path.join(os.path.dirname(__file__), "pages", "script.txt")
with open(script_path, encoding="utf-8") as f:
    content = f.read()

# 按 --- 分割
segments = [s.strip() for s in content.split("---") if s.strip()]
print(f"共 {len(segments)} 段配音")

assets_dir = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(assets_dir, exist_ok=True)

voice = "zh-CN-XiaoxiaoNeural"
results = []

for i, text in enumerate(segments, 1):
    output = os.path.join(assets_dir, f"slide-{i}.mp3")
    print(f"\n[{i}/{len(segments)}] 生成音频: {text[:30]}...")
    duration = tts_edge(text, voice, output, rate="+0%", pitch="+0Hz")
    results.append({
        "slide": i,
        "file": f"assets/slide-{i}.mp3",
        "duration": round(duration, 1)
    })

# 输出汇总 JSON
summary = os.path.join(os.path.dirname(__file__), "timing.json")
with open(summary, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n=== 完成！===")
for r in results:
    print(f"  Slide {r['slide']}: {r['duration']}s -> {r['file']}")

# 计算总时长和时序
total = sum(r['duration'] for r in results)
print(f"\n总时长: {total:.1f}s")

# 生成 HTML 中可用的 audio data-start 值
print("\n=== audio data-start 时序（供 HTML 使用）===")
cursor = 0.3  # 第一个 slide 开始后 0.3s 开始说话
for r in results:
    print(f'<audio class="clip" data-start="{cursor:.1f}" data-duration="{r["duration"]:.1f}" data-track-index="2" src="{r["file"]}"></audio>')
    cursor += r["duration"]

# 同时输出 slide data-start
print("\n=== slide data-start 时序 ===")
cursor = 0.0
for r in results:
    print(f'data-start="{cursor:.1f}" data-duration="{r["duration"]+0.5:.1f}"')
    cursor += r["duration"] + 0.5

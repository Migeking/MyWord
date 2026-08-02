#!/usr/bin/env python3
"""重新生成 TTS（YunyangNeural 男声）+ BGM 混音"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
from tts import read_input, tts_edge, mix_bgm, get_mp3_duration

# 配置
VOICE = "zh-CN-YunyangNeural"
BGM = os.path.join(os.path.dirname(__file__), "assets", "bgm.wav")
RATE = "-5%"  # 放慢语速，更有分量感

# 读取脚本
script_path = os.path.join(os.path.dirname(__file__), "pages", "script.txt")
with open(script_path, encoding="utf-8") as f:
    content = f.read()

segments = [s.strip() for s in content.split("---") if s.strip()]
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(assets_dir, exist_ok=True)

results = []

for i, text in enumerate(segments, 1):
    raw_path = os.path.join(assets_dir, f"slide-{i}_raw.mp3")
    final_path = os.path.join(assets_dir, f"slide-{i}.mp3")
    
    print(f"\n[{i}/{len(segments)}] {text[:40]}...")
    
    # Step 1: 生成 TTS（YunyangNeural，放慢5%）
    duration = tts_edge(text, VOICE, raw_path, rate=RATE, pitch="+0Hz")
    
    # Step 2: 混入 BGM（音量12%）
    if os.path.exists(BGM):
        mix_bgm(raw_path, BGM, final_path, bgm_volume=0.10, loop=False)
        os.remove(raw_path)
        final_duration = get_mp3_duration(final_path)
    else:
        os.rename(raw_path, final_path)
        final_duration = duration
    
    results.append({
        "slide": i,
        "file": f"assets/slide-{i}.mp3",
        "duration": round(final_duration, 1)
    })

# 输出汇总
summary = os.path.join(os.path.dirname(__file__), "timing.json")
with open(summary, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n=== 完成！===")
for r in results:
    print(f"  Slide {r['slide']}: {r['duration']}s")

total = sum(r['duration'] for r in results)
print(f"\n总时长: {total:.1f}s")

# 输出新的 HTML 时序
print("\n=== 复制以下到 index.html ===")
print("\n--- audio 标签 ---")
cursor = 0.3
for r in results:
    slide_end = r["duration"]
    print(f'    <audio id="audio-{r["slide"]}" class="clip" data-start="{cursor:.1f}" data-duration="{slide_end:.1f}" data-track-index="2" src="assets/slide-{r["slide"]}.mp3"></audio>')
    cursor += r["duration"]

print("\n--- slide data-* ---")
cursor = 0.0
for i, r in enumerate(results):
    dur = r["duration"] + 0.5
    print(f'data-start="{cursor:.1f}" data-duration="{dur:.1f}"')
    cursor += dur

# 同时输出一组带BGM的audio元素
print("\n--- 或者用 BGM 单轨道方案 ---")
print(f'    <audio id="bgm-music" class="clip" data-start="0" data-duration="{total+1:.0f}" data-track-index="3" src="assets/bgm.wav" loop></audio>')

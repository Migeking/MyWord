#!/usr/bin/env python3
"""简单混合：5 段 TTS + BGM"""
import os
from pydub import AudioSegment

OUT_DIR = r"d:\code\MyWord\9.AI重构工业\audio"
BGM_PATH = r"d:\code\MyWord\xhs-output\bgm-preview\02-ambient-tech.mp3"

VERSES = ["verse-1", "verse-2", "verse-3", "verse-4", "verse-5"]
# 实测视觉 verse 入场时间：15 / 22 / 27 / 30 / 33s
# TTS 提速 +20%（每段约 4.8-5.4s），重排卡点避重叠
VOICEOVER_TIMES = [15.0, 20.2, 25.7, 28.9, 32.1]
TOTAL_DURATION = 36.0
BGM_START = 0.0

# BGM：截取 → 降音 → 淡入淡出 → 循环填满
bgm = AudioSegment.from_file(BGM_PATH, format="mp3")
bgm = bgm[int(BGM_START * 1000):]
bgm = bgm - 10  # dB
bgm = bgm.fade_in(1500).fade_out(2000)
if len(bgm) < TOTAL_DURATION * 1000:
    loops = int((TOTAL_DURATION * 1000) // len(bgm)) + 2
    bgm = bgm * loops
bgm = bgm[:int(TOTAL_DURATION * 1000)]
print(f"BGM 长度: {len(bgm)/1000:.1f}s")

# 配音叠加
final = bgm
for name, t in zip(VERSES, VOICEOVER_TIMES):
    vp = os.path.join(OUT_DIR, f"{name}.mp3")
    v = AudioSegment.from_file(vp, format="mp3") + 3
    final = final.overlay(v, position=int(t * 1000))
    print(f"  overlay {name} @ {t}s ({len(v)}ms)")

# 输出
out = os.path.join(OUT_DIR, "final-audio.mp3")
final.export(out, format="mp3", bitrate="192k")
print(f"\n[OK] final-audio.mp3")
print(f"     {len(final)/1000:.1f}s  {(os.path.getsize(out)/1024):.1f}KB")

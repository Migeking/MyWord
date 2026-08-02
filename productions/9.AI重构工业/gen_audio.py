#!/usr/bin/env python3
"""
为 9.AI重构工业 项目生成 5 段诗词 TTS + 混合 BGM
"""
import asyncio
import os
import edge_tts
from pydub import AudioSegment

# === 配置 ===
OUT_DIR = r"d:\code\MyWord\9.AI重构工业\audio"
os.makedirs(OUT_DIR, exist_ok=True)

# 5 段诗词（与 HTML 字幕顺序完全一致）
VERSES = [
    ("verse-1", "曾经，传统工业的基石，是在轰鸣声中咬合的齿轮。"),
    ("verse-2", "然而，在庞杂无序的数据洪流面前，物理的极限终将到来。"),
    ("verse-3", "当AI的算力风暴席卷而过，"),
    ("verse-4", "一切原始的结构都将被解构，"),
    ("verse-5", "重塑为未来的智慧核心。"),
]

# 配音时点（绝对秒，匹配 HTML 主时间线 textDelays + 8s boot 偏移）
# 注：实际卡点由 mix_audio.py 中的 VOICEOVER_TIMES 控制
VOICEOVER_TIMES = [9.0, 14.5, 20.0, 23.0, 26.0]

# 选定音色：zh-CN-YunjianNeural（男声，深沉、磁性，dramatic）
VOICE = "zh-CN-YunjianNeural"
RATE = "+20%"  # 略快（避免配音重叠）
PITCH = "-2Hz" # 略低，庄重

# 选定的 BGM
BGM_PATH = r"d:\code\MyWord\xhs-output\bgm-preview\02-ambient-tech.mp3"

# 动画总时长（boot 8s + main 20s + delay = 35s）
TOTAL_DURATION = 35.0  # 秒
BgmStartOffset = 1.5    # BGM 延迟 1.5s 开始（boot 阶段保留安静感）

# 字体大小（已用 0.85 缩放系数从 1080p 映射到 720p 截图分辨率，如需重设可调）
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# === 1. TTS 生成 5 段配音 ===
async def gen_voiceover():
    print("\n=== 生成 TTS 配音 ===")
    for name, text in VERSES:
        out_path = os.path.join(OUT_DIR, f"{name}.mp3")
        if os.path.exists(out_path):
            print(f"  [OK] {name}.mp3 已存在，跳过")
            continue
        print(f"  → {name}: {text}")
        comm = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
        await comm.save(out_path)
        size = os.path.getsize(out_path)
        print(f"    保存 {out_path} ({size} 字节)")
    print("[OK] TTS 全部完成")

# === 2. 用 ffmpeg 混合最终音轨 ===
def mix_audio():
    print("\n=== 混合 BGM + 配音 ===")
    # 加载 BGM，截取所需长度
    bgm = AudioSegment.from_file(BGM_PATH, format="mp3")
    # 截取 BgmStartOffset 后到 TOTAL_DURATION
    bgm = bgm[BgmStartOffset * 1000:]
    # BGM 音量降低（避免压过配音）
    bgm = bgm - 10  # dB
    # 创建 BGM 配 track
    # 渐入 1s, 渐出 2s
    bgm = bgm.fade_in(1500).fade_out(2000)
    # 填充到 TOTAL_DURATION
    if len(bgm) < TOTAL_DURATION * 1000:
        # 循环填满
        loop_count = int((TOTAL_DURATION * 1000) // len(bgm)) + 1
        bgm = bgm * loop_count
    bgm = bgm[:int(TOTAL_DURATION * 1000)]

    # 加载每段配音
    final = bgm
    for (name, _), start_time in zip(VERSES, VOICEOVER_TIMES):
        voice_path = os.path.join(OUT_DIR, f"{name}.mp3")
        voice = AudioSegment.from_file(voice_path, format="mp3")
        # 配音音量提升
        voice = voice + 3
        # 把配音叠加到 BGM 上指定时间点
        final = final.overlay(voice, position=int(start_time * 1000))
        print(f"  → {name} @ {start_time}s ({len(voice)}ms)")

    # 输出
    out_path = os.path.join(OUT_DIR, "final-audio.mp3")
    final.export(out_path, format="mp3", bitrate="192k")
    size = os.path.getsize(out_path)
    duration = len(final) / 1000
    print(f"\n[OK] 混合完成：{out_path}")
    print(f"  时长：{duration:.1f}s ({duration*1000:.0f}ms)")
    print(f"  大小：{size} 字节 ({size/1024:.1f}KB)")
    return out_path

# === 3. 主流程 ===
async def main():
    await gen_voiceover()
    mix_audio()
    print("\n=== 全部完成 ===")
    print("生成文件：")
    print(f"  {OUT_DIR}\\verse-1.mp3 ~ verse-5.mp3")
    print(f"  {OUT_DIR}\\final-audio.mp3  ← 完整混合音轨")

if __name__ == "__main__":
    asyncio.run(main())

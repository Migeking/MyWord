"""
ChatTTS 固定种子语音生成脚本
为"迷路粒子"视频生成3段旁白音频，使用 seed=42 确保音色一致
"""

import torch
import ChatTTS
import soundfile as sf
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
SEED = 42
SAMPLE_RATE = 24000
SCRIPT_DIR = Path(__file__).resolve().parent

SEGMENTS = [
    ("subtitle_1.wav", "一个迷路的粒子"),
    ("subtitle_2.wav", "永不回头"),
    ("subtitle_3.wav", "这是它画的。"),
]

# ── 加载模型 ──────────────────────────────────────────
print("正在加载 ChatTTS 模型 (source=huggingface) ...")
chat = ChatTTS.Chat()
chat.load(source="huggingface", compile=False)
print("模型加载完成")

# ── 逐段生成 ──────────────────────────────────────────
for filename, text in SEGMENTS:
    torch.manual_seed(SEED)  # 每次推理前重置种子 → 同一说话人

    wavs = chat.infer([text], use_decoder=True)
    audio = wavs[0]  # numpy array

    out_path = SCRIPT_DIR / filename
    sf.write(str(out_path), audio, SAMPLE_RATE)

    duration = len(audio) / SAMPLE_RATE
    print(f"✓ {filename}: \"{text}\" → {duration:.2f}s ({out_path})")

print("\n全部生成完毕")

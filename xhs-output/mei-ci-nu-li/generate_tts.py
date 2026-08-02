"""Generate ChatTTS voiceover for '每一次努力都会开花' (warm female, single continuous text for consistent voice)."""
import os, ChatTTS, soundfile as sf

OUT_DIR = r"D:\code\MyWord\xhs-output\mei-ci-nu-li"
ASSETS = os.path.join(OUT_DIR, "assets")
os.makedirs(ASSETS, exist_ok=True)

# 读取 script.txt（已按 TTS 数字规范转好：8→八, 92→九十二, 90→九十）
with open(os.path.join(OUT_DIR, "script.txt"), "r", encoding="utf-8") as f:
    segments = [line.strip() for line in f.readlines() if line.strip()]

# 合并为单段连续文本（句号分隔 → 一次性 infer → 100% 同一人声）
full_text = "。".join(segments)
print(f"[1/3] Full text length: {len(full_text)} chars")
print(f"  Preview: {full_text[:80]}...")

print(f"[2/3] Loading ChatTTS (huggingface source) ...")
chat = ChatTTS.Chat()
chat.load(source="huggingface", compile=False)  # 兼容未装 torch.compile 的环境

# 暖声女声参数：[speed_5] 中等语速, [oral_2][laugh_0][break_6] 自然
# manual_seed=42 保证可复现
print(f"[3/3] Inferring voiceover ...")
wav = chat.infer(
    [full_text],
    skip_refine_text=True,
    params_infer_code=ChatTTS.Chat.InferCodeParams(
        prompt="[speed_5][oral_2][laugh_0][break_6]",
        manual_seed=42,
    ),
    params_refine_text=ChatTTS.Chat.RefineTextParams(
        prompt="[oral_2][laugh_0][break_6]",
    ),
)

audio_data = wav[0][0] if wav[0].ndim > 1 else wav[0]
out_path = os.path.join(ASSETS, "voiceover.wav")
sf.write(out_path, audio_data, 24000)
duration = len(audio_data) / 24000
print(f"Done: {out_path}")
print(f"Duration: {duration:.2f}s | Sample rate: 24000 Hz | Samples: {len(audio_data)}")

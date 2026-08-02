"""
V3: 侠客行纯念诗版 — 生成12联诗TTS (seed=99)
每联完整两句, 朗诵声线
"""
import os, torch, ChatTTS, soundfile as sf
import numpy as np

OUT_DIR = os.path.abspath("D:/code/MyWord/xhs-output/侠客行_v3/assets")
os.makedirs(OUT_DIR, exist_ok=True)

# ── 12 联诗 ──
couplets = [
    "赵客缦胡缨，吴钩霜雪明。",
    "银鞍照白马，飒沓如流星。",
    "十步杀一人，千里不留行。",
    "事了拂衣去，深藏身与名。",
    "闲过信陵饮，脱剑膝前横。",
    "将炙啖朱亥，持觞劝侯嬴。",
    "三杯吐然诺，五岳倒为轻。",
    "眼花耳热后，意气素霓生。",
    "救赵挥金槌，邯郸先震惊。",
    "千秋二壮士，烜赫大梁城。",
    "纵死侠骨香，不惭世上英。",
    "谁能书阁下，白首太玄经。",
]

# ── Load ChatTTS ──
print("Loading ChatTTS...")
chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
sr = 24000
print("ChatTTS loaded.")

# ── Generate continuous audio for ALL couplets (perfect voice consistency) ──
full_text = "。".join(couplets) + "。"

print(f"\n--- Generating 12 couplets (seed=99, continuous) ---")
torch.manual_seed(99)
wavs = chat.infer([full_text])

audio = wavs[0]
if audio.ndim > 1:
    audio = audio[0]

total_dur = len(audio) / sr
print(f"  Full audio: {total_dur:.1f}s, {len(audio)} samples")

# Save full
sf.write(os.path.join(OUT_DIR, "full.wav"), audio, sr)

# ── Split by silence detection ──
frame_len = int(0.04 * sr)
hop_len = int(0.01 * sr)

frames = []
for i in range(0, len(audio) - frame_len + 1, hop_len):
    frame = audio[i:i+frame_len]
    energy = np.sqrt(np.mean(frame**2))
    frames.append(energy)
frames = np.array(frames)

threshold = np.percentile(frames, 15)
threshold = max(threshold, 0.005)
is_voice = frames > threshold

min_gap_frames = int(0.2 / (hop_len / sr))
silence_regions = []
i = 0
while i < len(is_voice):
    if not is_voice[i]:
        start = i
        while i < len(is_voice) and not is_voice[i]:
            i += 1
        end = i
        if (end - start) >= min_gap_frames:
            mid_sample = ((start + end) // 2) * hop_len
            silence_regions.append(mid_sample)
    else:
        i += 1

splits = [0] + silence_regions + [len(audio)]

segments = []
for i in range(len(splits) - 1):
    seg = audio[splits[i]:splits[i+1]]
    if len(seg) >= int(0.3 * sr):
        segments.append(seg)

print(f"  Silence detection: found {len(segments)} segments (need {len(couplets)})")

# If mismatch, adaptive split using text character count ratios
if len(segments) != len(couplets):
    print(f"  Segment mismatch, using text-length-proportional splitting...")
    # Proportional split based on text length
    text_lengths = np.array([len(c) for c in couplets])
    text_ratios = text_lengths / text_lengths.sum()
    total_samples = len(audio)
    split_positions = [0]
    for i in range(len(couplets) - 1):
        pos = int(total_samples * text_ratios[:i+1].sum())
        split_positions.append(pos)
    split_positions.append(total_samples)
    
    segments = []
    for i in range(len(split_positions) - 1):
        seg = audio[split_positions[i]:split_positions[i+1]]
        segments.append(seg)

# Save individual segments + build timing
durations = []
timing_path = os.path.join(OUT_DIR, "timing.txt")
with open(timing_path, 'w', encoding='utf-8') as f:
    f.write("V3 Poem Couplet Timing (seed=99)\n")
    f.write("=" * 40 + "\n")
    for i, seg in enumerate(segments[:len(couplets)]):
        dur = len(seg) / sr
        durations.append(dur)
        filepath = os.path.join(OUT_DIR, f"couplet_{i+1:02d}.wav")
        sf.write(filepath, seg, sr)
        line = f"couplet_{i+1:02d}: {couplets[i]} = {dur:.2f}s"
        print(f"  {line}")
        f.write(line + "\n")

total = sum(durations)
print(f"\n  Total: {len(durations)} couplets, {total:.1f}s")
with open(timing_path, 'a', encoding='utf-8') as f:
    f.write(f"\nTotal: {total:.1f}s\n")

print(f"\nV3 TTS complete! Files in {OUT_DIR}")

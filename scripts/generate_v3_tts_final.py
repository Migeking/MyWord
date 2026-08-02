"""
V3 TTS final: 一次生成12联连续音频 → 静音检测切割
确保同一人声贯穿整首诗
"""
import os, torch, ChatTTS, soundfile as sf
import numpy as np

OUT_DIR = os.path.abspath("D:/code/MyWord/xhs-output/侠客行_v3/assets")
os.makedirs(OUT_DIR, exist_ok=True)

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

print("Loading ChatTTS...")
chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
sr = 24000
print("ChatTTS loaded.")

# ── 一次生成所有联句 ──
full_text = "。".join(couplets) + "。"

print(f"\n--- Generating ONE continuous audio (12 couplets, seed=99) ---")
torch.manual_seed(99)
wavs = chat.infer([full_text])

audio = wavs[0]
if audio.ndim > 1:
    audio = audio[0]

total_dur = len(audio) / sr
print(f"  Full audio: {total_dur:.1f}s, {len(audio)} samples")

# Save full for inspection
sf.write(os.path.join(OUT_DIR, "full.wav"), audio, sr)

# ── Split by silence detection ──
frame_len = int(0.04 * sr)   # 40ms
hop_len = int(0.01 * sr)     # 10ms

frames = []
for i in range(0, len(audio) - frame_len + 1, hop_len):
    frame = audio[i:i+frame_len]
    energy = np.sqrt(np.mean(frame**2))
    frames.append(energy)
frames = np.array(frames)

# Use 12th percentile as threshold (poem has ~10-15% silence between lines)
threshold = np.percentile(frames, 12)
threshold = max(threshold, 0.005)
is_voice = frames > threshold

# Find silence runs >= 200ms
min_gap_frames = int(0.2 / (hop_len / sr))
silence_positions = []
i = 0
while i < len(is_voice):
    if not is_voice[i]:
        start = i
        while i < len(is_voice) and not is_voice[i]:
            i += 1
        end = i
        if (end - start) >= min_gap_frames:
            mid_sample = ((start + end) // 2) * hop_len
            silence_positions.append(mid_sample)
    else:
        i += 1

print(f"  Found {len(silence_positions)} silence gaps (need {len(couplets)-1} splits)")

# Build split points
splits = [0] + silence_positions + [len(audio)]

# Extract segments
segments = []
for i in range(len(splits) - 1):
    seg = audio[splits[i]:splits[i+1]]
    if len(seg) >= int(0.15 * sr):  # minimum 150ms
        segments.append(seg)

print(f"  Extracted {len(segments)} segments")

# ── Match segments to couplets ──
# If counts match, great. Otherwise use text-length-ratio splits
if len(segments) == len(couplets):
    final_segments = segments
    print("  ✅ Segment count matches! Using silence-detected splits.")
else:
    print(f"  ⚠️  Segment mismatch ({len(segments)} vs {len(couplets)}), using adaptive split...")
    # Proportional split based on character count
    text_lens = np.array([len(c) for c in couplets])
    ratios = text_lens / text_lens.sum()
    total = len(audio)
    pos = [0]
    for i in range(len(couplets)-1):
        pos.append(int(total * ratios[:i+1].sum()))
    pos.append(total)
    
    # If we have few silence positions, prefer them close to ideal
    ideal_splits = pos[1:-1]
    actual_splits = [0]
    for ideal in ideal_splits:
        if silence_positions:
            nearest = min(silence_positions, key=lambda x: abs(x-ideal))
            if abs(nearest-ideal) < total/len(couplets)*0.4:
                actual_splits.append(nearest)
                silence_positions.remove(nearest)
            else:
                actual_splits.append(ideal)
        else:
            actual_splits.append(ideal)
    actual_splits.append(total)
    
    final_segments = []
    for i in range(len(actual_splits)-1):
        seg = audio[actual_splits[i]:actual_splits[i+1]]
        final_segments.append(seg)

# Save
durations = []
print(f"\n  Duration breakdown:")
timing_path = os.path.join(OUT_DIR, "timing.txt")
with open(timing_path, 'w', encoding='utf-8') as f:
    f.write("V3 Poem Couplet Timing (continuous seed=99)\n")
    f.write("=" * 50 + "\n")
    for i, seg in enumerate(final_segments[:len(couplets)]):
        dur = len(seg) / sr
        durations.append(dur)
        fp = os.path.join(OUT_DIR, f"couplet_{i+1:02d}.wav")
        sf.write(fp, seg, sr)
        line = f"couplet_{i+1:02d}: {couplets[i]} = {dur:.2f}s"
        print(f"  {line}")
        f.write(line + "\n")

total = sum(durations)
print(f"\n  Total: {len(durations)} couplets, {total:.1f}s")
with open(timing_path, 'a', encoding='utf-8') as f:
    f.write(f"\nTotal: {total:.1f}s\n")

print(f"\n✅ V3 TTS done! Files in {OUT_DIR}")

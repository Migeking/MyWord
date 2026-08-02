"""
Regenerate 侠客行 TTS with PERFECT voice consistency.
Key insight: One chat.infer() call per role = ONE continuous audio with IDENTICAL voice.
Then extract individual sentence timings by generating test segments once (for timing only).
"""
import os, torch, ChatTTS, soundfile as sf
import numpy as np

OUT_DIR = os.path.abspath("D:/code/MyWord/xhs-output/侠客行/assets")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Texts ──
narrator_texts = [
    "侠客行是唐代大诗人李白最豪迈的诗篇之一。诗人以惊天的笔力，塑造了一位战国时期仗剑天涯的侠客形象。",
    "今天，让我们一起走进这首千古名篇。",
    "燕赵之地的侠客，头戴粗犷的胡缨，腰间吴钩宝剑闪烁着霜雪般的寒光。",
    "银色的鞍辔映照着白色的骏马，飞驰而过的身影如同流星划过天际。",
    "十步之内取敌性命，千里之间无人能阻挡。",
    "完成大事之后，轻轻拂去衣上的尘土，悄然离去。这便是侠客的最高境界。",
    "闲时来到信陵君府上饮酒，解下宝剑横放膝前。",
    "亲手烤肉给壮士朱亥，举杯敬酒与谋士侯嬴共饮。",
    "三杯酒下肚便许下重诺，这份承诺比五座大山还要沉重。",
    "酒酣耳热之际，心中豪气化作一道白虹贯穿长空。",
    "为救赵国挥起金色大锤，邯郸城为之震动。",
    "千年之后，这两位壮士的英名，依然赫赫闪耀在大梁城中。",
    "纵然身死，侠骨依旧留有余香，无愧于世间任何英雄。",
    "谁愿意在书阁中皓首穷经。侠客选择了另一种人生，仗剑天下，快意恩仇。",
    "李白写的不仅是千年前的侠客，更是他自己心中那个永不低头的少年。愿我们心中，也永远住着一位侠客。",
]

poem_texts = [
    "赵客缦胡缨",
    "吴钩霜雪明",
    "银鞍照白马",
    "飒沓如流星",
    "十步杀一人",
    "千里不留行",
    "事了拂衣去",
    "深藏身与名",
    "闲过信陵饮，脱剑膝前横",
    "将炙啖朱亥，持觞劝侯嬴",
    "三杯吐然诺，五岳倒为轻",
    "眼花耳热后，意气素霓生",
    "救赵挥金槌，邯郸先震惊",
    "千秋二壮士，烜赫大梁城",
    "纵死侠骨香，不惭世上英",
    "谁能书阁下，白首太玄经",
]

# ── Load ChatTTS ──
print("Loading ChatTTS...")
chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
sr = 24000
print("ChatTTS loaded.")

def generate_combined(texts, seed, role_name):
    """Generate one continuous audio for ALL texts of a role. Perfect voice consistency."""
    # Join with clear sentence boundaries
    full_text = "。".join(texts) + "。"
    
    print(f"\n--- Generating {role_name} (ONE continuous audio, seed={seed}) ---")
    torch.manual_seed(seed)
    wavs = chat.infer([full_text])
    
    audio = wavs[0]
    if audio.ndim > 1:
        audio = audio[0]  # mono
    
    total_dur = len(audio) / sr
    print(f"  Full audio: {total_dur:.1f}s, {len(audio)} samples")
    
    # Save full audio for inspection
    full_path = os.path.join(OUT_DIR, f"{role_name}_full.wav")
    sf.write(full_path, audio, sr)
    
    # ── Split by silence detection ──
    # Compute short-time energy to find sentence gaps
    frame_len = int(0.04 * sr)   # 40ms frame
    hop_len = int(0.01 * sr)     # 10ms hop
    
    frames = []
    for i in range(0, len(audio) - frame_len + 1, hop_len):
        frame = audio[i:i+frame_len]
        energy = np.sqrt(np.mean(frame**2))
        frames.append(energy)
    frames = np.array(frames)
    
    # Adaptive threshold: 15th percentile (since silence should be ~10-20% of audio)
    threshold = np.percentile(frames, 15)
    threshold = max(threshold, 0.005)  # floor
    
    is_voice = frames > threshold
    
    # Find silence runs (gaps between sentences)
    # A "silence" must be at least 200ms to be a sentence boundary
    min_gap_frames = int(0.2 / (hop_len / sr))  # 200ms
    
    silence_regions = []
    i = 0
    while i < len(is_voice):
        if not is_voice[i]:
            start = i
            while i < len(is_voice) and not is_voice[i]:
                i += 1
            end = i
            gap_frames = end - start
            if gap_frames >= min_gap_frames:
                # Convert to sample position (middle of the gap)
                mid_sample = ((start + end) // 2) * hop_len
                silence_regions.append(mid_sample)
        else:
            i += 1
    
    # Build split points
    splits = [0] + silence_regions + [len(audio)]
    
    # Extract segments
    segments = []
    for i in range(len(splits) - 1):
        start = splits[i]
        end = splits[i + 1]
        seg_len = end - start
        min_len = int(0.3 * sr)  # minimum 300ms
        if seg_len >= min_len:
            segments.append(audio[start:end])
    
    print(f"  Silence detection: found {len(segments)} segments (need {len(texts)})")
    
    # If segment count doesn't match, do adaptive splitting
    if len(segments) != len(texts):
        print(f"  Segment mismatch, running adaptive split...")
        segments = adaptive_split(audio, texts, sr, silence_regions)
    
    # Save individual segments
    durations = []
    for i, seg in enumerate(segments[:len(texts)]):
        dur = len(seg) / sr
        durations.append(dur)
        filepath = os.path.join(OUT_DIR, f"{role_name}_{i+1:02d}.wav")
        sf.write(filepath, seg, sr)
        print(f"  [{role_name}_{i+1:02d}] {dur:.1f}s")
    
    # Write timing
    timing_path = os.path.join(OUT_DIR, "timing.txt")
    with open(timing_path, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {role_name} Timing (seed={seed}) ===\n")
        for i, d in enumerate(durations):
            f.write(f"  {role_name}_{i+1:02d}.wav: {d:.2f}s\n")
    
    return durations

def adaptive_split(audio, texts, sr, silence_regions):
    """Split audio into num_parts segments, preferring silence regions as boundaries."""
    num_parts = len(texts)
    
    # Target: try to align with expected cumulative durations
    # First, estimate per-segment target length
    total_len = len(audio)
    target_per_seg = total_len // num_parts
    
    # Use silence regions closest to ideal split points
    ideal_splits = [i * target_per_seg for i in range(1, num_parts)]
    
    # For each ideal split point, find nearest silence region
    split_samples = [0]
    silence_regions_sorted = sorted(silence_regions)
    
    for ideal in ideal_splits:
        if silence_regions_sorted:
            nearest = min(silence_regions_sorted, key=lambda x: abs(x - ideal))
            # Only use if within 30% of ideal position
            if abs(nearest - ideal) < target_per_seg * 0.3:
                split_samples.append(nearest)
                silence_regions_sorted.remove(nearest)
            else:
                # Use ideal position directly
                split_samples.append(ideal)
        else:
            split_samples.append(ideal)
    
    split_samples.append(total_len)
    split_samples = sorted(set(split_samples))
    
    # If we don't have enough splits, add more
    while len(split_samples) - 1 < num_parts:
        # Add midpoints between existing splits
        new_splits = []
        for i in range(len(split_samples) - 1):
            mid = (split_samples[i] + split_samples[i+1]) // 2
            new_splits.append(split_samples[i])
            if len(new_splits) - 1 < num_parts:
                new_splits.append(mid)
        new_splits.append(split_samples[-1])
        split_samples = new_splits
    
    # If we have too many splits, merge smallest segments
    while len(split_samples) - 1 > num_parts:
        min_gap = float('inf')
        min_idx = 0
        for i in range(len(split_samples) - 1):
            gap = split_samples[i+1] - split_samples[i]
            if gap < min_gap:
                min_gap = gap
                min_idx = i
        split_samples.pop(min_idx + 1)
    
    # Extract
    segments = []
    for i in range(len(split_samples) - 1):
        seg = audio[split_samples[i]:split_samples[i+1]]
        segments.append(seg)
    
    return segments[:num_parts]

# ── Generate both roles ──
narrator_durs = generate_combined(narrator_texts, seed=42, role_name="narrator")
poem_durs = generate_combined(poem_texts, seed=99, role_name="poem")

# ── Summary ──
print("\n" + "="*50)
print("TTS REGENERATION COMPLETE")
print(f"Narrator: {len(narrator_durs)} segments, total {sum(narrator_durs):.1f}s")
print(f"Poem:     {len(poem_durs)} segments, total {sum(poem_durs):.1f}s")
print("Duration breakdown:")
for i in range(max(len(narrator_durs), len(poem_durs))):
    n_str = f"narrator_{i+1:02d}={narrator_durs[i]:.1f}s" if i < len(narrator_durs) else ""
    p_str = f"  poem_{i+1:02d}={poem_durs[i]:.1f}s" if i < len(poem_durs) else ""
    if n_str or p_str:
        print(f"  {n_str:30s} {p_str}")
print("="*50)

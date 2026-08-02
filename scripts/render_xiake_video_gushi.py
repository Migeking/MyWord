"""
Render 侠客行 video — Gushi Version (30 Slides, Full Recitation intro + Interpretation loop).
"""
import subprocess, os
import soundfile as sf
import numpy as np
from scipy.signal import resample

BASE = "D:/code/MyWord"
ASSETS = f"{BASE}/xhs-output/古诗词参考/xiakexing/assets"
SLIDES_DIR = f"{BASE}/xhs-output/古诗词参考/xiake_slides"
OUTPUT = f"{BASE}/xhs-output/古诗词参考/xiakexing.mp4"

os.makedirs(ASSETS, exist_ok=True)

# ── Dynamic TTS duration reader ──
def get_wav_durations(prefix, count):
    durs = []
    for i in range(1, count + 1):
        filepath = f"{ASSETS}/{prefix}_{i:02d}.wav"
        if os.path.exists(filepath):
            audio, sr = sf.read(filepath)
            durs.append(len(audio) / sr)
        else:
            print(f"  WARNING: {filepath} not found, using default 2.0s")
            durs.append(2.0)
    return durs

# Get full poem reading duration
filepath_full = f"{ASSETS}/poem_full.wav"
if os.path.exists(filepath_full):
    audio, sr = sf.read(filepath_full)
    poem_full_dur = len(audio) / sr
else:
    poem_full_dur = 25.0

narrator_durs = get_wav_durations("narrator", 15)
poem_durs = get_wav_durations("poem", 12)

print(f"Poem full reading duration: {poem_full_dur:.2f}s")
print(f"Narrator durations (dynamic): {narrator_durs}")
print(f"Poem durations (dynamic): {poem_durs}")

BUFFER = 0.4  # small buffer after TTS ends before next slide

narrator_slides = [3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 29]
poem_slides = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27]

# Build per-slide duration array (30 items)
durations = []
ni, pi = 0, 0  # narrator/poem index
for i in range(1, 31):
    if i == 1 or i == 30:
        durations.append(3.0)  # title/ending
    elif i == 2:
        durations.append(round(poem_full_dur + 0.5, 1)) # Full poem recitation slide
    elif i in narrator_slides:
        d = narrator_durs[ni] + BUFFER
        durations.append(round(max(d, 2.0), 1))
        ni += 1
    else:  # poem slide
        d = poem_durs[pi] + BUFFER
        durations.append(round(max(d, 1.8), 1))
        pi += 1

total_dur = sum(durations)
print(f"Total video duration: {total_dur:.1f}s ({total_dur/60:.1f}min)")
print(f"Slide durations: {durations}")

# ── Calculate offsets ──
offsets = [0]
for d in durations[:-1]:
    offsets.append(offsets[-1] + d)

# ── Step 1: Create master audio track ──
print("\n=== Step 1: Mixing audio track ===")
sample_rate = 24000
total_samples = int(total_dur * sample_rate)
master_audio = np.zeros(total_samples, dtype=np.float32)

def add_audio(filepath, offset_sec):
    if not os.path.exists(filepath):
        print(f"  WARNING: {filepath} not found")
        return 0
    audio, sr = sf.read(filepath)
    if sr != sample_rate:
        ratio = sample_rate / sr
        new_len = int(len(audio) * ratio)
        audio = resample(audio, new_len)
    start_sample = int(offset_sec * sample_rate)
    end_sample = min(start_sample + len(audio), total_samples)
    if end_sample > start_sample:
        master_audio[start_sample:end_sample] += audio[:end_sample - start_sample]
    return len(audio) / sample_rate

# Add full poem reading track at Slide 2 offset
add_audio(filepath_full, offsets[1])
print(f"  poem_full @ {offsets[1]:.1f}s (dur={poem_full_dur:.1f}s)")

# Add narrator segments
for i, slide_num in enumerate(narrator_slides):
    filepath = f"{ASSETS}/narrator_{i+1:02d}.wav"
    offset = offsets[slide_num - 1]
    dur = add_audio(filepath, offset)
    print(f"  narrator_{i+1:02d} @ {offset:.1f}s (dur={dur:.1f}s)")

# Add poem segments
for i, slide_num in enumerate(poem_slides):
    filepath = f"{ASSETS}/poem_{i+1:02d}.wav"
    offset = offsets[slide_num - 1]
    dur = add_audio(filepath, offset)
    print(f"  poem_{i+1:02d} @ {offset:.1f}s (dur={dur:.1f}s)")

# Normalize
peak = np.max(np.abs(master_audio))
if peak > 0.95:
    master_audio = master_audio / peak * 0.95
    print(f"  Normalized (peak was {peak:.3f})")

# Save master audio
master_wav = f"{ASSETS}/master_audio.wav"
sf.write(master_wav, master_audio, sample_rate)
actual_dur = len(master_audio) / sample_rate
print(f"  Master audio: {actual_dur:.1f}s")

# ── Step 2: Generate video from slides ──
print("\n=== Step 2: Generating video ===")
concat_file = f"{ASSETS}/concat.txt"
with open(concat_file, 'w', encoding='utf-8') as f:
    for i in range(30):
        slide = f"{SLIDES_DIR}/slide_{i+1:02d}.png"
        if os.path.exists(slide):
            f.write(f"file '{slide}'\n")
            f.write(f"duration {durations[i]}\n")
    last_slide = f"{SLIDES_DIR}/slide_30.png"
    if os.path.exists(last_slide):
        f.write(f"file '{last_slide}'\n")

video_noaudio = f"{ASSETS}/temp_video.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "medium", "-crf", "23",
    "-r", "24",
    video_noaudio
], check=True)
print(f"  Video (no audio): ok")

# ── Step 3: Final mix with 古风 BGM ──
print("\n=== Step 3: Final mix (古风 BGM) ===")
bgm_dir = f"{BASE}/scripts/assets/bgm"

bgm_name = "Wuxia2_Guzheng_Pipa.mp3"
bgm_path = os.path.join(bgm_dir, bgm_name)
if not os.path.exists(bgm_path):
    bgms = [f for f in os.listdir(bgm_dir) if f.endswith('.mp3')]
    bgm_path = os.path.join(bgm_dir, bgms[0]) if bgms else None

if bgm_path:
    print(f"  BGM: {os.path.basename(bgm_path)}")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_noaudio,
        "-i", master_wav,
        "-i", bgm_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "23",
        "-filter_complex",
        "[1:a]adelay=0|0[tts];"
        "[2:a]volume=0.30[bgm];"
        "[tts][bgm]amix=inputs=2:duration=longest[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        OUTPUT
    ], check=True)
else:
    print("  No BGM found, TTS only")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_noaudio,
        "-i", master_wav,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        OUTPUT
    ], check=True)

# ── Verify ──
result = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration,size:stream=width,height,codec_name",
    "-of", "default=noprint_wrappers=1", OUTPUT
], capture_output=True, text=True)
print(f"\n=== Output: {OUTPUT} ===")
print(result.stdout)
size_mb = os.path.getsize(OUTPUT) / (1024*1024)
print(f"File size: {size_mb:.1f} MB")
print("\nDone! 侠客行 video created.")

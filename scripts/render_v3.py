"""
V3 Render: 侠客行 纯诗朗诵版
14 slides (title + 12 couplets + ending) + TTS padded to slide duration + BGM
Key fix: each TTS segment is padded with silence to match its slide duration.
"""
import subprocess, os, glob
import soundfile as sf
import numpy as np

BASE = "D:/code/MyWord"
ASSETS = f"{BASE}/xhs-output/侠客行_v3/assets"
SLIDES_DIR = f"{BASE}/xhs-output/侠客行_v3/slides"
OUTPUT = f"{BASE}/xhs-output/侠客行_v3.mp4"
BGM = f"{BASE}/scripts/assets/bgm/Wuxia2_Guzheng_Pipa.mp3"
TEMP_DIR = f"{BASE}/xhs-output/侠客行_v3"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── Couplet TTS durations (seed=99, individual generation) ──
couplet_durs = [2.61, 1.91, 2.27, 2.14, 1.89, 3.09,
                2.08, 2.04, 2.63, 2.06, 2.44, 2.18]
COUPLET_BUFFER = 0.5

# ── Build per-slide durations ──
durations = [3.0]  # title
for d in couplet_durs:
    durations.append(round(d + COUPLET_BUFFER, 2))
durations.append(3.0)  # ending

total_dur = sum(durations)
print(f"Total slides: {len(durations)}, total duration: {total_dur:.1f}s")
for i, d in enumerate(durations):
    print(f"  slide_{i+1:02d}: {d:.2f}s")

# ── Step 1: Build concat file & generate video from slides ──
slides = sorted(glob.glob(f"{SLIDES_DIR}/slide_*.png"))
assert len(slides) == len(durations), f"Slide count: {len(slides)} vs {len(durations)}"

CONCAT_FILE = f"{TEMP_DIR}/concat.txt"
with open(CONCAT_FILE, 'w', encoding='utf-8') as f:
    for i, slide in enumerate(slides):
        f.write(f"file '{slide.replace(chr(92), '/')}'\n")
        if i < len(slides) - 1:
            f.write(f"duration {durations[i]}\n")
    f.write(f"file '{slides[-1].replace(chr(92), '/')}'\n")
print(f"\nConcat file: {len(slides)} slides")

TEMP_VIDEO = f"{TEMP_DIR}/temp_video.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", CONCAT_FILE,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
    "-vf", "fps=24",
    TEMP_VIDEO
], check=True)

# ── Step 2: Build master audio with proper padding ──
# Each slide = TTS (if couplet) + silence to fill slide duration
SR = 24000
TTS_FILES = sorted(glob.glob(f"{ASSETS}/couplet_*.wav"))
assert len(TTS_FILES) == 12, f"Expected 12 TTS files, got {len(TTS_FILES)}"

full_audio = []
for i in range(len(durations)):
    slide_samples = int(durations[i] * SR)
    if i == 0 or i == 13:
        seg = np.zeros(slide_samples, dtype=np.float32)
    else:
        tts_data, _ = sf.read(TTS_FILES[i - 1])
        if tts_data.ndim > 1:
            tts_data = tts_data[:, 0]
        tts_float = tts_data.astype(np.float32)
        if np.max(np.abs(tts_float)) > 1.0:
            tts_float = tts_float / 32768.0
        seg = np.zeros(slide_samples, dtype=np.float32)
        seg[:min(len(tts_float), slide_samples)] = tts_float[:min(len(tts_float), slide_samples)]
    full_audio.append(seg)

master_audio = np.concatenate(full_audio)
TEMP_TTS = f"{TEMP_DIR}/master_audio.wav"
sf.write(TEMP_TTS, master_audio, SR)
print(f"Master audio: {len(master_audio)/SR:.1f}s ({len(full_audio)} segments)")

# ── Step 3: Mix TTS + BGM ──
TEMP_MIX = f"{TEMP_DIR}/temp_mix.wav"
subprocess.run([
    "ffmpeg", "-y",
    "-i", TEMP_TTS, "-i", BGM,
    "-filter_complex",
    "[1:a]volume=0.18[a1];[0:a][a1]amix=inputs=2:duration=first:weights=1 0.4",
    "-ac", "1", "-ar", str(SR),
    TEMP_MIX
], check=True)

# ── Step 4: Final render ──
probe_v = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", TEMP_VIDEO
], capture_output=True, text=True)
probe_a = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", TEMP_MIX
], capture_output=True, text=True)
v_dur = float(probe_v.stdout.strip())
a_dur = float(probe_a.stdout.strip())
print(f"\nVideo: {v_dur:.1f}s, Audio: {a_dur:.1f}s")

subprocess.run([
    "ffmpeg", "-y",
    "-i", TEMP_VIDEO, "-i", TEMP_MIX,
    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
    OUTPUT
], check=True)

# ── Verify ──
r = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
    "-of", "default=noprint_wrappers=1:nokey=1", OUTPUT
], capture_output=True, text=True)
lines = r.stdout.strip().split('\n')
print(f"\n{'='*50}")
print(f"V3 OUTPUT: {os.path.basename(OUTPUT)}")
if len(lines) >= 1: print(f"Duration: {float(lines[0]):.1f}s")
if len(lines) >= 2: print(f"Size: {int(lines[1])/1024/1024:.1f} MB")
print(f"{'='*50}")

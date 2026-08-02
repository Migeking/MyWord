"""Step 2 only: mix audio onto existing video-only.mp4 (no re-record)."""
import subprocess, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "assets")
VIDEO_ONLY = os.path.join(HERE, "renders", "video-only.mp4")
OUTPUT = os.path.join(HERE, "renders", "限流恢复-video-bgm.mp4")
TIMING = os.path.join(HERE, "timing.json")

with open(TIMING, "r", encoding="utf-8") as f:
    timing = json.load(f)

slides = timing["slides"]

# Build FFmpeg command
cmd = ["ffmpeg"]

# Input 0: video
cmd.extend(["-i", VIDEO_ONLY])

# Inputs 1-10: WAV files
for s in slides:
    wav = os.path.join(AUDIO_DIR, s["file"])
    cmd.extend(["-i", wav])

# Input 11: BGM
bgm = os.path.join(AUDIO_DIR, "bgm.mp3")
cmd.extend(["-i", bgm])

# Build filter_complex
parts = []

# Video: stretch 4x
parts.append("[0:v]setpts=4*PTS[v]")

# Audio: delay each WAV by its start time
for i, s in enumerate(slides):
    delay_ms = int(s["start"] * 1000)
    idx = i + 1  # stream index (1-10)
    parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

# BGM: reduce volume
parts.append("[11:a]volume=0.15[bgm]")

# Mix all audio
mix_in = "".join(f"[a{i}]" for i in range(len(slides)))
mix_in += "[bgm]"
parts.append(f"{mix_in}amix=inputs={len(slides)+1}:duration=longest[a]")

filter_complex = ";".join(parts)
cmd.extend(["-filter_complex", filter_complex])
cmd.extend(["-map", "[v]", "-map", "[a]"])
cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23"])
cmd.extend(["-c:a", "aac", "-b:a", "192k"])
cmd.extend(["-y", OUTPUT])

print("Running FFmpeg audio mix...")
print(f"Input video: {os.path.basename(VIDEO_ONLY)}")
print(f"Audio tracks: {len(slides)} WAV + 1 BGM")
print(f"Output: {os.path.basename(OUTPUT)}")

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"FFmpeg error: {result.stderr[:2000]}")
    sys.exit(1)

# Verify
verify = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration:stream=codec_name,codec_type,width,height",
    "-of", "default=noprint_wrappers=1",
    OUTPUT
], capture_output=True, text=True)

print("\nVerification:")
print(verify.stdout)
size_kb = os.path.getsize(OUTPUT) // 1024
print(f"Size: {size_kb} KB")
print("Done!")

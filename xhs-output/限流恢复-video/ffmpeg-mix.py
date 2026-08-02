import subprocess, shlex, os

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(HERE, "renders")
ASSETS = os.path.join(HERE, "assets")
VIDEO_IN = os.path.join(RENDERS, "video-only.mp4")
OUTPUT = os.path.join(RENDERS, "限流恢复-video-bgm.mp4")

# Timing from timing.json (delays in ms)
delays = [0, 10410, 24930, 43000, 58710, 76200, 90930, 103700, 122930, 135190]

# Build command
cmd = ["ffmpeg"]

# Inputs: video + 10 wav + 1 bgm
cmd.extend(["-i", VIDEO_IN])
for i in range(1, 11):
    cmd.extend(["-i", os.path.join(ASSETS, f"chattts-slide-{i}.wav")])
cmd.extend(["-i", os.path.join(ASSETS, "bgm.mp3")])

# Build filter complex
parts = []
parts.append(f"[0:v]setpts=4*PTS[v]")

for i in range(10):
    idx = i + 1  # stream index (1-based)
    d = delays[i]
    parts.append(f"[{idx}:a]adelay={d}|{d}[a{i}]")

parts.append(f"[11:a]volume=0.15[bgm]")

mix_inputs = "".join(f"[a{i}]" for i in range(10)) + "[bgm]"
parts.append(f"{mix_inputs}amix=inputs=11:duration=longest[a]")

filter_complex = ";".join(parts)
cmd.extend(["-filter_complex", filter_complex])
cmd.extend(["-map", "[v]", "-map", "[a]"])
cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23"])
cmd.extend(["-c:a", "aac", "-b:a", "192k"])
cmd.extend(["-y", OUTPUT])

print("Running FFmpeg mix...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"FFmpeg failed (return {result.returncode})")
    print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
else:
    print("FFmpeg OK")

# Verify
import json, subprocess
probe = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height",
    "-of", "json", OUTPUT
], capture_output=True, text=True)
info = json.loads(probe.stdout)
dur = info["format"]["duration"]
size = int(info["format"]["size"])
print(f"Output: {size/1024:.0f} KB, {float(dur):.1f}s")
for s in info.get("streams", []):
    print(f"  Stream: {s['codec_type']} = {s['codec_name']}" +
          (f" {s['width']}x{s['height']}" if s['codec_type'] == 'video' else ""))

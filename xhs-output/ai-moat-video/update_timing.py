#!/usr/bin/env python3
"""Update timing.json with ChatTTS durations and compare vs Edge-TTS"""
import soundfile as sf, json

results = []
total_chattts = 0
total_edge = 0

# Also generate HTML-ready data-start values
print("=== ChatTTS 各段时长 ===")
for i in range(1, 9):
    data, sr = sf.read(f'assets/chattts-slide-{i}.wav')
    dur = round(len(data) / sr, 1)
    results.append({
        'slide': i,
        'file': f'assets/chattts-slide-{i}.wav',
        'duration': dur
    })
    total_chattts += dur
    print(f"  Slide {i}: {dur}s")

# Load old edge-tts timings for comparison
with open('timing.json') as f:
    old = json.load(f)
for o in old:
    total_edge += o['duration']

# Write new timing JSON
with open('timing.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nChatTTS 总时长: {total_chattts}s")
print(f"Edge-TTS 总时长: {total_edge}s")
print(f"差异: {round(total_edge - total_chattts, 1)}s ({round((total_edge-total_chattts)/total_edge*100, 1)}% 缩短)")

# Generate audio data-start for HTML
print("\n=== Audio data-start (for HTML) ===")
cursor = 0.3
for r in results:
    d = r["duration"]
    print(f'<audio class="clip" data-start="{cursor:.1f}" data-duration="{d:.1f}" data-track-index="2" src="{r["file"]}"></audio>')
    cursor += d

# Slide data-start
print("\n=== Slide data-start ===")
cursor = 0.0
for r in results:
    d = r["duration"]
    print(f'data-start="{cursor:.1f}" data-duration="{d+0.5:.1f}"')
    cursor += d + 0.5

#!/usr/bin/env python3
"""Update HTML with ChatTTS audio references and new timings"""
import soundfile as sf, json, re

# Get ChatTTS durations
durations = []
for i in range(1, 9):
    data, sr = sf.read(f'assets/chattts-slide-{i}.wav')
    durations.append(round(len(data) / sr, 1))

print("ChatTTS durations:", durations)

# Calculate new timings
audio_start = 0.3
audio_timings = []
slide_start = 0.0
slide_timings = []

for d in durations:
    audio_timings.append(audio_start)
    slide_timings.append(slide_start)
    audio_start += d
    slide_start += d + 0.5

total_dur = sum(durations) + 0.5 * 8  # last slide end
print(f"Total duration: {total_dur:.1f}s")

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update audio src paths
for i in range(1, 9):
    old = f'src="assets/slide-{i}.mp3"'
    new = f'src="assets/chattts-slide-{i}.wav"'
    html = html.replace(old, new)

# 2. Update audio data-start and data-duration
for i in range(1, 9):
    d = durations[i-1]
    s = audio_timings[i-1]
    old_dur = None

    # Find old duration value for this audio (1st approach - regex)
    pattern = rf'id="audio-{i}"[^>]*data-duration="([\d.]+)"'
    match = re.search(pattern, html)
    if match:
        old_dur = match.group(1)
        # Replace data-start and data-duration in that audio tag
        tag_pattern = rf'(<audio[^>]*id="audio-{i}"[^>]*?)data-start="[\d.]+" data-duration="[\d.]+"'
        replacement = rf'\1data-start="{s}" data-duration="{d}"'
        html = re.sub(tag_pattern, replacement, html)

# 3. Update slide data-start and data-duration
for i in range(1, 9):
    d = round(durations[i-1] + 0.5, 1)
    s = slide_timings[i-1]
    # Find data-start/data-duration in the slide div
    tag_pattern = rf'(<div[^>]*?id="slide-{i}"[^>]*?)data-start="[\d.]+" data-duration="[\d.]+"'
    replacement = rf'\1data-start="{s}" data-duration="{d}"'
    html = re.sub(tag_pattern, replacement, html)

# 4. Update BGM duration
html = re.sub(
    r'(<audio id="bgm-music"[^>]*?data-duration=")\d+(\.\d+)?"',
    lambda m: m.group(1) + str(round(total_dur) + 2),  # slightly longer than total
    html
)

# 5. Update GSAP timeline values
# Slide 1: no changes needed (starts at 0)

# Old to new slide start mapping for GSAP
old_slide_starts = [0, 9.6, 22.3, 36.5, 48.3, 58.3, 77.0, 87.2]
new_slide_starts = [round(s, 1) for s in slide_timings]
assert len(old_slide_starts) == len(new_slide_starts)

# For each slide, we need to update the GSAP timeline from values
# The structure is: tl.fromTo('#slide-N', ..., 9.6) where 9.6 is the slide start
# and internal animations use offsets from the slide start

# I'll read the JS section and compute internal offsets
# For each animation in a slide, the offset = (original_time - original_slide_start)
# New time = offset + new_slide_start

# Let me parse the GSAP timeline
lines = html.split('\n')
new_lines = []
for line in lines:
    # Check if this is a GSAP fromTo line with a time
    # Pattern: tl.fromTo(... , ..., X) or tl.fromTo(... , ..., X.Y)
    stripped = line.strip()
    if stripped.startswith('tl.fromTo(') or stripped.startswith('.fromTo('):
        # Find the last number before the closing paren
        # Match things like: , 9.6) or , 22.3)
        # Need to find which slide this belongs to
        # Check if this line has a slide reference
        for i in range(8):
            old_start = old_slide_starts[i]
            new_start = new_slide_starts[i]
            # Only look for exact matches or values close to old slide start + offset
            # Original values per slide are from the generate_tts.py output minus 0.3 for the overlap pattern
        
        # Actually, let me just use the formula:
        # Old GSAP animation times are based on cumulative slide starts
        # New times = old_time - old_slide_start + new_slide_start
        
        # But this is too complex to do generically. Let me do it slide by slide.
        pass
    
    new_lines.append(line)

# Since the above approach is error-prone, let me use explicit replacements
# for each GSAP value

gsap_replacements = {
    # Slide 2: old start 9.6 → new 7.9
    '9.6': '7.9', '10.1': '8.4', '10.4': '8.7', '11.1': '9.4', '11.6': '9.9', '12.6': '10.9',
    # Slide 3: old start 22.3 → new 21.3
    '22.3': '21.3', '22.8': '21.8', '23.1': '22.1', '23.9': '22.9', '25.1': '24.1',
    # Slide 4: old start 36.5 → new 34.1
    '36.5': '34.1', '37.0': '34.6', '37.3': '34.9', '38.0': '35.6',
    # Slide 5: old start 48.3 → new 43.7
    '48.3': '43.7', '48.8': '44.2', '49.1': '44.5', '49.8': '45.2',
    # Slide 6: old start 58.3 → new 51.9
    '58.3': '51.9', '58.8': '52.4', '59.1': '52.7', '59.8': '53.4',
    # Slide 7: old start 77.0 → new 68.6
    '77.0': '68.6', '77.5': '69.1', '77.8': '69.4', '78.3': '69.9', '79.3': '70.9', '79.8': '71.4',
    # Slide 8: old start 87.2 → new 76.6
    '87.2': '76.6', '87.7': '77.1', '88.1': '77.5', '88.7': '78.1', '89.9': '79.3', '90.9': '80.3', '91.4': '80.8',
}

# Only apply to GSAP script section (between <script> and </script>)
script_start = html.find('<script>')
script_end = html.find('</script>')

if script_start != -1 and script_end != -1:
    before_script = html[:script_start]
    script = html[script_start:script_end]
    after_script = html[script_end:]
    
    # Apply replacements in script only
    for old_val, new_val in gsap_replacements.items():
        # Use word boundaries to avoid partial matches
        script = re.sub(r'(?<!\d)' + re.escape(old_val) + r'(?![\d.])', new_val, script)
    
    html = before_script + script + after_script

# Write updated HTML
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Print summary
print("\n=== Timing 更新摘要 ===")
for i in range(8):
    print(f"Slide {i+1}: slide_start={slide_timings[i]:.1f}s, audio_start={audio_timings[i]:.1f}s, duration={durations[i]}s")
print(f"BGM total: {round(total_dur) + 2}s")
print("\nHTML 更新完成！")

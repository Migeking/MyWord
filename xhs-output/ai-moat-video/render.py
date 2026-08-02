#!/usr/bin/env python3
"""Render final video using Playwright screenshots + FFmpeg audio mix"""
import os, json, subprocess, tempfile
from playwright.sync_api import sync_playwright

OUTPUT = 'output_final.mp4'
os.makedirs('frames', exist_ok=True)

# Load timing
with open('timing.json', 'r', encoding='utf-8') as f:
    timings = json.load(f)

# Calculate slide timing windows
slides = []
prev_end = 0.0
for i, t in enumerate(timings):
    slide_dur = round(t['duration'] + 0.5, 1)
    slides.append({
        'num': t['slide'],
        'file': t['file'],
        'dur': t['duration'],
        'slide_start': prev_end,
        'slide_dur': slide_dur,
        'audio_start': round(sum(timings[j]['duration'] for j in range(i)) + 0.3, 1),
    })
    prev_end += slide_dur

total_dur = slides[-1]['slide_start'] + slides[-1]['slide_dur']

print(f'Total video duration: {total_dur}s')
for s in slides:
    print(f'  Slide {s["num"]}: [{s["slide_start"]}->{round(s["slide_start"]+s["slide_dur"],1)}]s audio@{s["audio_start"]}s')

# Step 1: Take screenshots of each slide
print('\n=== Taking screenshots ===')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1080, 'height': 1920})

    # Open HTML
    html_path = os.path.abspath('index.html').replace('\\', '/')
    page.goto(f'file:///{html_path}')

    # Wait for page to fully render
    page.wait_for_timeout(2000)

    # For each slide, make it visible and take screenshot
    for s in slides:
        num = s['num']
        # Use JS to make this slide visible while hiding others
        page.evaluate(f"""
            (() => {{
                document.querySelectorAll('.slide').forEach(el => el.style.opacity = '0');
                const slide = document.getElementById('slide-{num}');
                if (slide) slide.style.opacity = '1';
            }})()
        """)
        page.wait_for_timeout(500)
        page.screenshot(path=f'frames/slide-{num:02d}.png', full_page=True)
        print(f'  Slide {num}: screenshotted')

    browser.close()

print('All screenshots taken')

# Step 2: Create video segments with FFmpeg
print('\n=== Creating video segments ===')
segments = []
for s in slides:
    num = s['num']
    dur = s['slide_dur']
    img = f'frames/slide-{num:02d}.png'
    out_vid = f'frames/seg-{num:02d}.mp4'

    # Create video segment: fade in & out using FFmpeg
    fade_in = min(0.4, dur/4)   # fade in over 0.4s
    fade_out = min(0.4, dur/4)  # fade out over 0.4s
    
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', img,
        '-c:v', 'libx264',
        '-t', str(dur),
        '-r', '30',
        '-vf', f'fade=t=in:st=0:d={fade_in}:alpha=0,fade=t=out:st={dur-fade_out}:d={fade_out}:alpha=0',
        '-pix_fmt', 'yuv420p',
        out_vid
    ]
    subprocess.run(cmd, capture_output=True)
    segments.append(out_vid)
    print(f'  Segment {num}: {dur}s')

# Step 3: Concatenate all video segments
print('\n=== Concatenating video segments ===')
concat_file = 'frames/concat_list.txt'
with open(concat_file, 'w') as f:
    for seg in segments:
        f.write(f"file '{os.path.basename(seg)}'\n")

concat_vid = 'frames/concat_raw.mp4'
subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
    '-i', concat_file,
    '-c', 'copy', concat_vid
], capture_output=True)

# Step 4: Mix audio at correct timestamps
print('\n=== Mixing audio ===')
# Build a complex filter for audio mixing
filter_parts = []
audio_inputs = []

for s in slides:
    idx = len(audio_inputs)
    audio_inputs.append(s['file'])
    delay_ms = int(s['audio_start'] * 1000)
    filter_parts.append(f'[{idx}]adelay={delay_ms}|{delay_ms}[a{idx}]')

# Add BGM
bgm_idx = len(audio_inputs)
audio_inputs.append('assets/bgm.wav')
# Fade BGM: fade in 1s, fade out last 2s
bgm_dur = total_dur + 2
filter_parts.append(f'[{bgm_idx}]adelay=0|0,volume=0.15,afade=t=in:d=1,afade=t=out:st={total_dur-2}:d=2[a{len(slides)}]')

# Mix all audio tracks
mix_inputs = ''.join([f'[a{i}]' for i in range(len(slides) + 1)])
filter_parts.append(f'{mix_inputs}amix=inputs={len(slides)+1}:duration=longest:dropout_transition=2[aout]')

filter_complex = ';'.join(filter_parts)

# Build ffmpeg command
cmd = ['ffmpeg', '-y']
for a in audio_inputs:
    cmd.extend(['-i', a])
cmd.extend(['-i', concat_vid])
cmd.extend(['-filter_complex', filter_complex])
cmd.extend(['-map', f'{len(audio_inputs)}:v:0'])  # video from concat
cmd.extend(['-map', '[aout]'])  # audio from mix
cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '20'])
cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
cmd.extend(['-t', str(total_dur + 0.5)])  # match video duration
cmd.append(OUTPUT)

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print('FFmpeg error:', result.stderr)
else:
    print(f'\n=== Video rendered: {OUTPUT} ===')

    # Check file
    size = os.path.getsize(OUTPUT)
    print(f'File size: {size/1024/1024:.1f} MB')

    # Get duration
    dur_check = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'default=noprint_wrappers=1:nokey=1', OUTPUT],
                               capture_output=True, text=True)
    print(f'Video duration: {float(dur_check.stdout.strip()):.1f}s')

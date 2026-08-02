"""Render HTML slides to MP4 with per-slide audio using Playwright + FFmpeg.

Avoids Chinese characters in paths to work around FFmpeg concat demuxer
encoding issues on Windows.
"""
import os, json, subprocess, shutil, tempfile
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FPS = 5
SLIDE_COUNT = 12
INDEX_FILE = 'index.html'
OUTPUT_FILE = '../工业物联网数据链路-数据采集篇_1080p.mp4'

with open('timing.json') as f:
    timing = json.load(f)
slides_info = timing['slides']

html_path = os.path.abspath(INDEX_FILE)

# Use short ASCII temp dir to avoid FFmpeg Chinese-path encoding issues
tmp_root = Path(tempfile.mkdtemp(prefix='xhs_render_', dir=r'C:\Users\mige\AppData\Local\Temp'))

from playwright.sync_api import sync_playwright
pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
page = browser.new_page(viewport={'width': 1080, 'height': 1920})
page.goto(f'file:///{html_path.replace(os.sep, "/")}', wait_until='networkidle')
page.wait_for_timeout(1000)

page.evaluate("""document.querySelectorAll('.slide').forEach(el => el.classList.remove('active'));""")

for slide in slides_info:
    si = slide['slide']
    dur = slide['duration']
    af = slide['file']
    audio_file = os.path.abspath(f'assets/{af}')

    print(f'[Render] Slide {si}/{SLIDE_COUNT}  wav={af}  dur={dur:.1f}s')

    # Show slide + animate words
    page.evaluate(f"""
    (function() {{
        document.querySelectorAll('.slide').forEach(el => el.classList.remove('active'));
        var s = document.querySelectorAll('.slide')[{si - 1}];
        if (s) {{
            s.classList.add('active');
            s.querySelectorAll('.word').forEach(function(w, i) {{
                setTimeout(function() {{
                    w.style.opacity = '1';
                    w.style.transform = 'translateY(0)';
                    w.style.transition = 'opacity 0.3s, transform 0.3s';
                }}, i * 50);
            }});
        }}
    }})()
    """)
    page.wait_for_timeout(100)

    num_frames = max(1, int(dur * FPS))
    slide_dir = tmp_root / f's{si:02d}'
    slide_dir.mkdir()

    for f_idx in range(num_frames):
        fp = slide_dir / f'f{f_idx:04d}.png'
        page.screenshot(path=str(fp), full_page=False)

    # ── Build per-slide clip (relative paths, no Chinese chars) ──
    concat_file = tmp_root / f'c{si:02d}.txt'
    with open(concat_file, 'w') as f:
        for f_idx in range(num_frames):
            # relative to concat file location (tmp_root)
            rel = f's{si:02d}/f{f_idx:04d}.png'
            f.write(f"file '{rel}'\nduration {1/FPS:.6f}\n")

    clip = tmp_root / f'c{si:02d}.mp4'
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file)]
    if os.path.exists(audio_file):
        cmd += ['-i', audio_file]
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
            '-shortest', '-c:a', 'aac', '-b:a', '128k']
    cmd.append(str(clip))

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f'  [ERR] FFmpeg: {r.stderr[-200:]}')
    else:
        print(f'  -> clip {clip.name} OK')

# ── Concat all clips ──
concat_all = tmp_root / 'all.txt'
with open(concat_all, 'w') as f:
    for si in range(1, SLIDE_COUNT + 1):
        p = tmp_root / f'c{si:02d}.mp4'
        if p.exists():
            f.write(f"file 'c{si:02d}.mp4'\n")

r = subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', str(concat_all), '-c', 'copy',
                    os.path.abspath(OUTPUT_FILE)],
                   capture_output=True, text=True, timeout=300)
if r.returncode == 0:
    mb = os.path.getsize(os.path.abspath(OUTPUT_FILE)) / 1_000_000
    print(f'[OK] Final: {os.path.abspath(OUTPUT_FILE)} ({mb:.0f}MB)')
else:
    print(f'[ERR] Final concat: {r.stderr[-500:]}')

shutil.rmtree(tmp_root, ignore_errors=True)
browser.close()
pw.stop()
print('[Done]')

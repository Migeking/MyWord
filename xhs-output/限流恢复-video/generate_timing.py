"""Extract per-slide WAV durations and generate timing.json."""
import os, json, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

slides = []
total = 0.0

for i in range(1, 999):
    path = f'assets/chattts-slide-{i}.wav'
    if not os.path.exists(path):
        break
    data, sr = sf.read(path)
    dur = len(data) / sr
    slides.append({
        'slide': i,
        'file': f'chattts-slide-{i}.wav',
        'duration': round(dur, 2),
        'start': round(total, 2)
    })
    total += dur

timing = {
    'total_duration': round(total, 2),
    'slide_count': len(slides),
    'slides': slides
}

with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timing, f, ensure_ascii=False, indent=2)

print(f'Generated timing.json: {len(slides)} slides, {total:.2f}s total\n')

for s in slides:
    audio_start = round(s['start'] + 0.3, 2)
    print(f'  Slide {s["slide"]:2d}: WAV={s["duration"]:6.2f}s  '
          f'audio data-start={audio_start:7.2f}  data-duration={s["duration"]:6.2f}')

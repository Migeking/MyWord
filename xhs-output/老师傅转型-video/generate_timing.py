"""Extract per-slide WAV durations and write timing.json."""
import os, json, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('assets', exist_ok=True)

wav_dir = 'assets'
timings = []
total = 0.0

for i in range(1, 11):
    wav_path = os.path.join(wav_dir, f'chattts-slide-{i}.wav')
    data, sr = sf.read(wav_path)
    dur = len(data) / sr
    timings.append({
        'slide': i,
        'file': f'assets/chattts-slide-{i}.wav',
        'duration': round(dur, 3),
        'start': round(total, 3),
    })
    print(f'Slide {i:2d}: {dur:7.3f}s  start={total:.3f}s')
    total += dur

timings.append({'total_duration': round(total, 3)})

with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timings, f, ensure_ascii=False, indent=2)

print(f'\nTotal: {total:.3f}s')

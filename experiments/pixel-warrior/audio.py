"""
Pixel Warrior: procedural chiptune audio generator.

No external audio files needed. All sounds are generated as raw waveforms:
- BGM: 4-bar chiptune melody (square wave lead + triangle bass), 8s loop x ~4
- SFX: sword swing (noise), hit impact (low square), monster hurt (mid square),
       monster death (descending pitch), victory (ascending arpeggio)

Output: audio.wav (30s, 44100Hz, mono, 16-bit)
"""
import os
import struct
import math
import random
import wave

SAMPLE_RATE = 44100
DURATION = 30.0

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_AUDIO = os.path.join(HERE, "audio.wav")

# Note frequencies (Hz), 4th octave middle C = 261.63
NOTES = {
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    'C6': 1046.50, 'D6': 1174.66, 'E6': 1318.51,
}

# 4-bar melody, 120 BPM, 4/4. 1 beat = 0.5s, 1 bar = 2s, 4 bars = 8s.
# Heroic C major vibe, simple ascending arpeggios.
MELODY_BARS = [
    [('C5', 0.5), ('E5', 0.5), ('G5', 0.5), ('C6', 0.5)],  # Bar 1: I
    [('E5', 0.5), ('G5', 0.5), ('C6', 0.5), ('E5', 0.5)],  # Bar 2: I
    [('F5', 0.5), ('A5', 0.5), ('C6', 0.5), ('F5', 0.5)],  # Bar 3: IV
    [('G5', 0.5), ('B5', 0.5), ('D6', 0.5), ('G5', 0.5)],  # Bar 4: V
]

# Bass: C, C, F-C, G-C pattern
BASS_PATTERN = [
    ('C3', 2.0),
    ('C3', 2.0),
    ('F3', 1.0), ('C3', 1.0),
    ('G3', 1.0), ('C3', 1.0),
]


def write_wav(filename, samples):
    with wave.open(filename, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for s in samples:
            v = int(max(-32768, min(32767, s * 32767)))
            w.writeframes(struct.pack('<h', v))


def osc(wave_type, freq, duration, amp=0.3):
    n = int(duration * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        if wave_type == 'square':
            v = amp if math.sin(2 * math.pi * freq * t) > 0 else -amp
        elif wave_type == 'triangle':
            v = (2 / math.pi) * amp * math.asin(math.sin(2 * math.pi * freq * t))
        elif wave_type == 'sine':
            v = amp * math.sin(2 * math.pi * freq * t)
        elif wave_type == 'noise':
            random.seed(int(t * 8000) % 1000000)
            v = random.uniform(-amp, amp)
        else:
            v = 0
        out.append(v)
    return out


def adsr(samples, attack, decay, sustain, release):
    n = len(samples)
    a = int(attack * SAMPLE_RATE)
    d = int(decay * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    s = max(0, n - a - d - r)
    out = []
    for i in range(n):
        if i < a:
            amp = i / max(a, 1)
        elif i < a + d:
            amp = 1 - (1 - sustain) * (i - a) / max(d, 1)
        elif i < a + d + s:
            amp = sustain
        else:
            amp = sustain * (n - i) / max(r, 1)
        out.append(samples[i] * amp)
    return out


def note(freq, duration, wave_type='square', amp=0.3, a=0.01, d=0.05, s=0.7, r=0.1):
    return adsr(osc(wave_type, freq, duration, amp), a, d, s, r)


def make_bgm(duration):
    total = int(duration * SAMPLE_RATE)
    samples = [0.0] * total
    bar_dur = 2.0
    loop_dur = bar_dur * 4  # 8s

    for loop in range(int(duration / loop_dur) + 1):
        loop_start = loop * loop_dur
        t = 0
        # Melody (square lead)
        for bar in MELODY_BARS:
            for nn, dur in bar:
                start = int((loop_start + t) * SAMPLE_RATE)
                n = note(NOTES[nn], dur, 'square', amp=0.18, a=0.01, d=0.04, s=0.55, r=0.08)
                for i, v in enumerate(n):
                    if start + i < total:
                        samples[start + i] += v
                t += dur
        # Bass (triangle)
        t = 0
        for nn, dur in BASS_PATTERN:
            start = int((loop_start + t) * SAMPLE_RATE)
            n = note(NOTES[nn], dur, 'triangle', amp=0.22, a=0.04, d=0.1, s=0.6, r=0.15)
            for i, v in enumerate(n):
                if start + i < total:
                    samples[start + i] += v
            t += dur
    return samples


# ---- Sound effects ----
def sfx_sword_swing():
    return note(0, 0.18, 'noise', amp=0.28, a=0.005, d=0.12, s=0.0, r=0.05)


def sfx_hit():
    # Layered: low square thump + noise transient
    thump = note(120, 0.12, 'square', amp=0.38, a=0.003, d=0.1, s=0.0, r=0.02)
    noise_burst = note(0, 0.06, 'noise', amp=0.2, a=0.001, d=0.05, s=0.0, r=0.01)
    return [t + n for t, n in zip(thump, noise_burst)]


def sfx_monster_hurt():
    return note(280, 0.22, 'square', amp=0.3, a=0.01, d=0.1, s=0.3, r=0.12)


def sfx_monster_death():
    n = int(0.6 * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        prog = i / n
        freq = 400 - 320 * prog  # 400 -> 80 Hz
        v = 0.38 if math.sin(2 * math.pi * freq * t) > 0 else -0.38
        # Add noise tail
        if prog > 0.5:
            random.seed(int(t * 8000) % 1000000)
            v += random.uniform(-0.15, 0.15)
        v *= max(0, 1 - prog * 0.9)  # Fade out
        out.append(v)
    return out


def sfx_victory():
    parts = [('C5', 0.12), ('E5', 0.12), ('G5', 0.12), ('C6', 0.25), ('E6', 0.4)]
    out = []
    for nn, dur in parts:
        out += note(NOTES[nn], dur, 'triangle', amp=0.38, a=0.01, d=0.02, s=0.8, r=0.12)
    return out


def mix(bgm, sfx_list, timestamps, duration):
    total = int(duration * SAMPLE_RATE)
    mix = list(bgm)
    for sfx, t in zip(sfx_list, timestamps):
        start = int(t * SAMPLE_RATE)
        for i, v in enumerate(sfx):
            if start + i < total:
                mix[start + i] += v
    # Normalize to 0.9 peak
    peak = max(abs(v) for v in mix) or 1
    if peak > 0.9:
        mix = [v * 0.9 / peak for v in mix]
    return mix


def main():
    print(f"[audio] Generating BGM ({DURATION}s)...")
    bgm = make_bgm(DURATION)

    print("[audio] Generating SFX...")
    sfx_sword = sfx_sword_swing()
    sfx_hit1 = sfx_hit()
    sfx_hurt = sfx_monster_hurt()
    sfx_hit2 = sfx_hit()
    sfx_hurt2 = sfx_monster_hurt()
    sfx_hit_final = sfx_hit()
    sfx_death = sfx_monster_death()
    sfx_vic = sfx_victory()

    # Timestamps synced to game events in applyStateAt
    sfx_list = [
        sfx_sword,      # 11.5  挥剑 1（attack_windup 起点）
        sfx_hit1,       # 12.2  击中 1
        sfx_hurt,       # 14.0  怪物反击 / 英雄受击
        sfx_sword,      # 17.5  挥剑 2
        sfx_hit2,       # 18.2  击中 2
        sfx_hurt2,      # 20.0  怪物反击
        sfx_sword,      # 22.5  挥剑终结
        sfx_hit_final,  # 23.2  终结一击
        sfx_death,      # 25.0  怪物死亡
        sfx_vic,        # 28.5  胜利 jingle
    ]
    timestamps = [11.5, 12.2, 14.0, 17.5, 18.2, 20.0, 22.5, 23.2, 25.0, 28.5]

    print("[audio] Mixing...")
    final = mix(bgm, sfx_list, timestamps, DURATION)

    print(f"[audio] Writing {OUTPUT_AUDIO}...")
    write_wav(OUTPUT_AUDIO, final)
    size_mb = os.path.getsize(OUTPUT_AUDIO) / 1024 / 1024
    print(f"[audio] DONE  {OUTPUT_AUDIO}  size={size_mb:.1f} MB")


if __name__ == "__main__":
    main()

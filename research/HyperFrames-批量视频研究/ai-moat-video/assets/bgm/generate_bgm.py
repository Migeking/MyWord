#!/usr/bin/env python3
"""Generate simple ambient background music for video production.

No external downloads needed. Produces usable ambient/pad backgrounds.
"""

import numpy as np
import os, sys, struct, wave, math, json

SAMPLE_RATE = 44100
BGM_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_sine(freq, duration, sample_rate=SAMPLE_RATE):
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t)


def generate_pad(duration_sec=120, sample_rate=SAMPLE_RATE):
    """Generate a calm ambient pad suitable for knowledge video BGM.

    Uses layered chords with gentle attack/release for a smooth background.
    """
    num_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, False)

    # C major chord tones (soft, warm)
    chord_notes = [261.63, 329.63, 392.00]  # C4, E4, G4
    # Add some gentle higher overtones
    overtones = [523.25, 659.25]  # C5, E5

    audio = np.zeros(num_samples, dtype=np.float64)

    # Base chord - slow pulse
    for note in chord_notes:
        amp = 0.08
        wave = np.sin(2 * np.pi * note * t)
        # Gentle amplitude modulation for "breathing" effect
        amp_mod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
        audio += amp * wave * amp_mod

    # Gentle overtones
    for note in overtones:
        amp = 0.03
        wave = np.sin(2 * np.pi * note * t)
        audio += amp * wave

    # Add subtle harmonic texture (fifth interval drone)
    drone_freqs = [130.81, 196.00]  # C3, G3
    for note in drone_freqs:
        amp = 0.04
        wave = np.sin(2 * np.pi * note * t)
        audio += amp * wave

    # Add very subtle noise floor for warmth
    noise = np.random.normal(0, 0.005, num_samples)
    audio += noise

    # Fade in (3 seconds) and fade out (5 seconds)
    fade_in = np.minimum(1.0, np.arange(num_samples) / (3 * sample_rate))
    fade_out = np.minimum(1.0, (num_samples - np.arange(num_samples)) / (5 * sample_rate))
    audio *= fade_in * fade_out

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.5

    return audio


def generate_guitar_pad(duration_sec=120, sample_rate=SAMPLE_RATE):
    """Generate a Chinese-style ambient with pentatonic feel."""
    num_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, False)

    # C major pentatonic (Chinese folk scale feel): C D E G A
    pentatonic = [261.63, 293.66, 329.63, 392.00, 440.00]

    audio = np.zeros(num_samples, dtype=np.float64)

    # Slow arpeggiated pad
    for i, note in enumerate(pentatonic):
        phase_offset = (i / len(pentatonic)) * 2 * math.pi
        amp = 0.06
        wave = np.sin(2 * np.pi * note * t + phase_offset)
        # Slow volume modulation
        amp_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + phase_offset)
        audio += amp * wave * amp_mod

    # Bass drone
    bass_notes = [130.81, 196.00]
    for note in bass_notes:
        wave = np.sin(2 * np.pi * note * t)
        audio += 0.03 * wave

    # Fade in/out
    fade_in = np.minimum(1.0, np.arange(num_samples) / (3 * sample_rate))
    fade_out = np.minimum(1.0, (num_samples - np.arange(num_samples)) / (5 * sample_rate))
    audio *= fade_in * fade_out

    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.4

    return audio


def save_wav(filepath, audio, sample_rate=SAMPLE_RATE):
    """Save audio to WAV file."""
    # Convert to 16-bit PCM
    audio_int16 = np.int16(audio * 32767)

    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    size_kb = os.path.getsize(filepath) / 1024
    duration = len(audio) / sample_rate
    return size_kb, duration


def main():
    print("=" * 50)
    print("Generating ambient background music...")
    print(f"Output: {BGM_DIR}")
    print("=" * 50)

    tracks = [
        ("bgm_ambient_pad.wav", generate_pad(120), "Calm ambient pad (2 min)"),
        ("bgm_chinese_pad.wav", generate_guitar_pad(120), "Pentatonic Chinese-style pad (2 min)"),
    ]

    results = []
    for fname, audio, desc in tracks:
        fpath = os.path.join(BGM_DIR, fname)
        size_kb, duration = save_wav(fpath, audio)
        results.append({"file": fname, "size_kb": size_kb, "duration": duration, "description": desc})
        print(f"  [OK] {fname:25s} {size_kb:>6.0f}KB  ({duration:.0f}s) - {desc}")

    # Save manifest
    manifest_path = os.path.join(BGM_DIR, "bgm_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(tracks)} tracks generated.")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

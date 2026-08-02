"""Generate single continuous TTS voiceover for Transformer 图解."""
import os, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Read script
script_path = os.path.abspath(r"D:\code\MyWord\xhs-output\Transformer图解\script.txt")
with open(script_path, 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

# Join all lines into one paragraph for consistent voice
full_text = "。".join(lines) + "。"

output_dir = os.path.abspath(r"D:\code\MyWord\xhs-output\Transformer图解\assets")
os.makedirs(output_dir, exist_ok=True)

print(f"Generating TTS for {len(lines)} sentences ({len(full_text)} chars)...")

chat = ChatTTS.Chat()
chat.load(source='huggingface')

wav = chat.infer(
    [full_text],
    skip_refine_text=True,
    params_infer_code=ChatTTS.Chat.InferCodeParams(
        prompt='[speed_5]',
        manual_seed=42
    )
)

audio_data = wav[0][0] if wav[0].ndim > 1 else wav[0]
output_path = os.path.join(output_dir, 'voiceover.wav')
sf.write(output_path, audio_data, 24000)

import math
duration = len(audio_data) / 24000
print(f'Done! Duration: {duration:.2f}s')
print(f'Saved to: {output_path}')

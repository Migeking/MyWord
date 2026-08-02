import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_ENDPOINT'] = 'https://hf-mirror.com'

import torch
import ChatTTS
import soundfile as sf
from pathlib import Path

chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')

SEED = 42
scripts_dir = Path('scripts')
assets_dir = Path('assets')
assets_dir.mkdir(exist_ok=True)

scripts = sorted(scripts_dir.glob('slide-*.txt'))
for i, script in enumerate(scripts, 1):
    text = script.read_text(encoding='utf-8').strip()
    torch.manual_seed(SEED)
    wavs = chat.infer([text], use_decoder=True)
    audio = wavs[0]
    sf.write(assets_dir / f'chattts-slide-{i}.wav', audio, 24000)
    print(f"Slide {i}: {len(audio)/24000:.2f}s")

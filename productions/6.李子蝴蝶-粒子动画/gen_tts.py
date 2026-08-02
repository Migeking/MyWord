import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_ENDPOINT'] = 'https://hf-mirror.com'

import torch
import ChatTTS
import soundfile as sf
from pathlib import Path
import json

chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')

SEED = 3001 # 找一个男声或者有质感的声音
assets_dir = Path('assets')
assets_dir.mkdir(exist_ok=True)

texts = [
    "纵然身处暗夜，",
    "亦当化作星尘。",
    "历经千帆洗礼，",
    "方得破茧成蝶。"
]

timing = []
for i, text in enumerate(texts, 1):
    torch.manual_seed(SEED)
    wavs = chat.infer([text], use_decoder=True)
    audio = wavs[0]
    dur = len(audio)/24000
    fname = f'chattts-{i}.wav'
    sf.write(assets_dir / fname, audio, 24000)
    print(f"Part {i}: {dur:.2f}s")
    timing.append({'file': fname, 'duration': round(dur, 2)})

Path('timing.json').write_text(json.dumps(timing, indent=2, ensure_ascii=False))
print("TTS 生成完毕。")

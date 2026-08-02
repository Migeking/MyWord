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

# 依然锁定之前那个极具沉稳感的男声
SEED = 2800 
assets_dir = Path('assets')
assets_dir.mkdir(exist_ok=True)

texts = [
    "鹰的眼睛，能看穿数千米外的微小异动。",
    "但它从不与地面上的蛇虫纠缠，它的舞台是云端。",
    "当风暴来临，众鸟都在寻找藏身之处，",
    "它却选择迎面而上，借着狂流冲破云层。",
    "认知的高度，决定了你能否将危机，化作破局的雄风。"
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

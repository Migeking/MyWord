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

# 选择一个极其沉稳的男声
SEED = 2800 
assets_dir = Path('assets')
assets_dir.mkdir(exist_ok=True)

texts = [
    "在深海的无光带，章鱼依靠的不是眼睛，而是遍布触手的独立神经。",
    "当巨流裹挟一切时，它不抵抗，而是顺势而为。",
    "它有九个大脑，不仅为了生存，更是为了在黑暗中思考。",
    "真正的从容，是像章鱼一般，在巨变中保持柔软，多维洞察。",
    "愿你也能长出感知变局的触角，于低谷处蛰伏，破局而生。"
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
print("TTS 重新生成完毕。")

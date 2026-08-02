import torch
import ChatTTS
from scipy.io import wavfile
import numpy as np
import os

print("初始化 ChatTTS 引擎...")
chat = ChatTTS.Chat()
chat.load(compile=False) 

torch.manual_seed(2222) 
rand_spk = chat.sample_random_speaker()

# 扩充为 1 分钟的 9 句长文案
texts = [
    "它没有心脏，也不会思考。",
    "只是千万年来，顺应着深海的洋流。",
    "当海沟深处爆发出撕裂的暗流，",
    "巨鲸也必须拼尽全力去抗争。",
    "但它不抵抗，不挣扎。",
    "越是柔软，越能包容所有的撕扯。",
    "洋流将它推向哪里，它便在哪里起舞。",
    "不对抗深渊，却活成了最明亮的光。",
    "愿你在洪流中，也能找到自己的轻盈。"
]

params_infer_code = ChatTTS.Chat.InferCodeParams(
    spk_emb=rand_spk, 
    temperature=0.3, 
    top_P=0.7, 
    top_K=20,
)

print("开始生成深海治愈长文案男声旁白...")
wavs = chat.infer(
    texts, 
    params_infer_code=params_infer_code
)

os.makedirs('assets', exist_ok=True)

for i, wav in enumerate(wavs):
    if isinstance(wav, list):
        wav = np.array(wav)
    if wav.dtype == np.float32 or wav.dtype == np.float64:
        wav = np.clip(wav, -1.0, 1.0)
        wav = (wav * 32767).astype(np.int16)
    
    file_path = f"assets/chattts-{i+1}.wav"
    wavfile.write(file_path, 24000, wav)
    print(f"✅ 成功生成: {file_path}")

print("全部 9 句长文案旁白生成完毕！")

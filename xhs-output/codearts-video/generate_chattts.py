"""Generate CodeArts voiceover using ChatTTS (local), single continuous audio.

Single infer() call = one voice throughout.
"""
import os, torch, ChatTTS, soundfile as sf

SEED = 42

out_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(out_dir)

# Single continuous paragraph — guarantees same speaker throughout
full_text = (
    "华为云码道，懂你的编码专家。"
    "实干派 AI 研发专家，融合 IDE 与代码大模型。"
    "项目级代码生成，续写解释优化一气呵成。"
    "内置 DeepSeek GLM 大模型，专家技能开箱即用。"
    "双模式设计，探索验证，规范合规。"
    "一站式 DevOps，全流程覆盖。"
    "安全可信，代码版权归属用户。"
    "访问 codearts.huaweicloud.com 免费体验。"
)

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)  # CPU mode

assets_dir = 'assets'
os.makedirs(assets_dir, exist_ok=True)

infer_params = ChatTTS.Chat.InferCodeParams(
    prompt='[speed_5]',
)

torch.manual_seed(SEED)
wavs = chat.infer([full_text], skip_refine_text=True, params_infer_code=infer_params, use_decoder=True)
audio = wavs[0]

dur = len(audio) / 24000
sf.write(f'{assets_dir}/voiceover.wav', audio, 24000)
print(f'Total: {dur:.2f}s -> assets/voiceover.wav')
print('Done!')

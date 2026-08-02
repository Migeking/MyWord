import torch
import soundfile as sf
import numpy as np
import os

torch.manual_seed(42)

# Load ChatTTS from HuggingFace (GitHub blocked in China)
import ChatTTS
chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)  # use cached models from HF

# Use a fixed seed for reproducible speaker voice
torch.manual_seed(42)
rand_spk = chat.sample_random_speaker()

slides = [
    # Slide 1 - Cover
    "干了二十年的老师傅，转型AI专家，月薪翻倍。",
    # Slide 2 - Problem hook
    "上期讲了数据主权的问题，有人在评论区问：我们公司的老师傅，觉得AI是要取代他们，不配合。他们说，我干了二十年，要什么AI？",
    # Slide 3 - Real reason
    "很多人以为老师傅抵触AI，是因为他们不愿意学习新技术。错。老师傅抵触AI的真实原因是：他怕没价值。",
    # Slide 4 - Role crisis
    "老师傅的抵触，不是对AI的抵触，是对自己未来角色的担忧。他们不怕AI，他们怕的是：AI来了，我的工作谁来做？我的经验还有没有人认可？",
    # Slide 5 - The solution
    "解决这个问题的核心是：给老师傅一个角色转型的路。不是让他从操作工变成被AI替代的人，而是让他从操作工变成AI离不开的人。",
    # Slide 6 - Four levels intro
    "我给你一个具体的路径，我叫它四个台阶：",
    # Slide 7 - Level 1+2
    "第一层，AI操作指导员：从纯操作工到会用AI辅助工具，工资涨百分之十到二十。第二层，AI工艺辅导员：能指导新人使用AI，工资涨百分之二十到三十。",
    # Slide 8 - Level 3+4
    "第三层，工艺知识工程师：经验从脑子里变成可复用的知识库，工资对标AI工程师。第四层，数据标注专家：用标注数据训练AI，成为AI的老师，不可替代。",
    # Slide 9 - Case Meisteel
    "在梅钢热轧厂，有一批干了二十多年的老师傅。以前在高温车间靠眼睛判断钢水温度，现在在二十五度的中央集控室看AI系统。有一个干了二十八年的老师傅说：以前我觉得AI是来抢我饭碗的，现在我觉得AI是来帮我的。",
    # Slide 10 - Case Guangzhou
    "广州柴油机厂，他们做了一个AI知识库系统。把老师傅的经验变成新员工的超级外脑。新人培养周期从六个月缩短到两个月。AI不会让老师傅失业，只会让老师傅的经验更值钱。",
    # Slide 11 - How to execute
    "怎么让老师傅有面子地参与转型？三个建议：第一，设立AI协作达人奖。第二，让老师傅参与AI规则的定义和验收。第三，给老师傅配徒弟。",
    # Slide 12 - Conclusion
    "工业AI落地，老师傅不是阻力，是资产。他们的经验是AI最值钱的数据来源。AI不是来取代他的，是来让他的资产增值的。关注我，下期讲老板的耐心够不够撑过死亡期。",
]

os.makedirs('assets', exist_ok=True)

timings = []
for i, text in enumerate(slides):
    print(f"Generating slide {i+1}/{len(slides)}: {text[:40]}...")

    params_infer = ChatTTS.Chat.InferCodeParams(
        spk_emb=rand_spk,
        temperature=0.3,
    )
    wavs = chat.infer(
        text,
        skip_refine_text=True,
        split_text=False,
        params_infer_code=params_infer,
    )

    if isinstance(wavs, list):
        # When not streaming, returns list of arrays per split chunk
        wav = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
    else:
        wav = wavs
    sr = 24000
    duration_s = len(wav) / sr

    # Save WAV
    path = f'assets/chattts-slide-{i+1}.wav'
    sf.write(path, wav, sr)
    print(f"  → {duration_s:.1f}s saved to {path}")

    # Add 0.5s silence padding
    duration_with_pad = duration_s + 0.5
    timings.append({
        'slide': i + 1,
        'text': text[:60],
        'duration_raw': round(duration_s, 2),
        'duration_with_pad': round(duration_with_pad, 2),
    })

import json
with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timings, f, ensure_ascii=False, indent=2)

total = sum(t['duration_with_pad'] for t in timings)
print(f"\nDone! {len(slides)} slides, total {total:.1f}s")

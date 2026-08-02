#!/usr/bin/env python3
"""Regenerate all 8 ChatTTS audio files with same speaker from slide-1"""
import os, time, soundfile as sf, json
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_ENDPOINT'] = 'https://hf-mirror.com'

import ChatTTS

chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
print('Model loaded')

# 1) Extract speaker from slide-1
wav1 = sf.read('assets/chattts-slide-1.wav', dtype='float32')[0]
spk_emb = chat.sample_audio_speaker(wav1)
print(f'Speaker embedding extracted ({len(spk_emb)} chars)')

# 2) Slides text
segments = [
    'AI时代最宽的护城河，不是技术，不是产品，是组织形态。今天来分享一个改变认知的观点。',
    '纽曼在《The Next Biggest Moat in AI》里说：AI时代最宽的护城河，是组织形态，而不是技术或产品。这个观点，值得每一个管理者深思。',
    '第一，吸引杰出人才。AI时代最稀缺的不是算法工程师，而是既懂AI又懂业务的人。能持续吸引这类人才的组织，才有可能在AI时代胜出。',
    '第二，集中判断力。关键决策要集中在少数真正有洞察力的人手里。这不是中央集权，而是确保战略方向不跑偏。',
    '第三，分配权力。在判断力集中的基础上，把执行权充分下放，让一线的人能快速响应市场变化。',
    '过去两年，我见过太多AI工具很强、但团队跟不上的情况。所以我们在推一个项目叫《从超级个体到超级团队》，核心四步：换招聘逻辑、重新设计决策流、统一AI工具、建立反馈闭环。',
    '技术不是护城河。用技术的组织能力，才是真正的护城河。这个护城河无法靠买，只能靠建。',
    '简单总结：强的组织等于吸引人才加集中判断加分配权力。AI时代，最强的个体会被组织形态放大或削弱。你认同这个框架吗？',
]

os.makedirs('assets', exist_ok=True)

total_start = time.time()
timings = []

for i, text in enumerate(segments, 1):
    t0 = time.time()
    print(f'[{i}/8] 生成中: {text[:30]}...', end=' ', flush=True)
    
    params = ChatTTS.Chat.InferCodeParams(spk_smp=spk_emb)
    wavs = chat.infer([text], params_infer_code=params)
    
    t1 = time.time()
    outpath = f'assets/chattts-slide-{i}.wav'
    sf.write(outpath, wavs[0], 24000)
    dur = round(len(wavs[0]) / 24000, 1)
    infer_time = round(t1 - t0, 1)
    
    timings.append({'slide': i, 'duration': dur, 'file': f'assets/chattts-slide-{i}.wav'})
    print(f'OK {dur}s | {infer_time}s')

total = time.time() - total_start
total_audio = sum(t['duration'] for t in timings)
print(f'\n=== 完成! 总用时: {total:.0f}s ===')
print(f'总音频时长: {total_audio:.1f}s')
for t in timings:
    print(f"  Slide {t['slide']}: {t['duration']}s")

# 3) Save timing.json
with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timings, f, indent=2, ensure_ascii=False)
print('\ntiming.json updated')

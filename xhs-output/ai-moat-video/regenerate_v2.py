#!/usr/bin/env python3
"""Regenerate all audio by passing all 8 texts in one call for consistent speaker"""
import os, json, time, soundfile as sf
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_ENDPOINT'] = 'https://hf-mirror.com'
import ChatTTS

chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
print('Model loaded')

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

# Pass all 8 texts as a list - ChatTTS will auto-sample speaker from first
# and apply to all remaining segments for consistent voice
t0 = time.time()
wavs = chat.infer(segments, split_text=True)
t1 = time.time()
print(f'All 8 segments generated in {t1-t0:.1f}s')
print(f'Returned {len(wavs)} wavs')

timings = []
total_audio = 0.0
for i, wav in enumerate(wavs, 1):
    dur = round(len(wav) / 24000, 1)
    total_audio += dur
    outpath = f'assets/chattts-slide-{i}.wav'
    sf.write(outpath, wav, 24000)
    timings.append({'slide': i, 'duration': dur, 'file': outpath})
    print(f'  Slide {i}: {dur}s')

print(f'\n=== Done! Total audio: {total_audio:.1f}s ===')

# Save timing
with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timings, f, indent=2, ensure_ascii=False)
print('timing.json updated')

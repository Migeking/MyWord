#!/usr/bin/env python3
"""生成全部13段 ChatTTS 配音"""
import os, time, soundfile as sf, torch

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HUGGINGFACE_HUB_ENDPOINT'] = 'https://hf-mirror.com'

import ChatTTS

chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
print('Model loaded')

SEED = 42  # 固定seed保持声音一致

segments = [
    '工业AI落地，百分之八十的企业死在管理这一关。我是鸡总，二十年IT老兵。',
    '上期评论区炸了，最多的问题不是技术，而是部门墙。数据采不上来，不是技术问题。设备科说数据是他的，IT部门根本进不去。老板想上AI，工人觉得是要取代他们不配合。',
    '设备科说数据是我们的命根子。IT部门说AI项目我们管，你们配合。生产部门说别动产线，出问题谁担责。老师傅说我干了二十年，要什么AI。老板说先做了再说。每个部门都有道理，AI项目寸步难行。',
    '我见过太多企业，技术方案一流，项目管理一塌糊涂。你以为AI项目是技术问题，它其实是政治问题。大模型解决不了部门墙的问题。',
    '管理门槛一：你有没有一个内部客户CTO。工业AI项目最难的不是技术，是谁来扛这个事。凡想让IT部门主导的，百分之八十都失败了。',
    'IT部门是服务部门，能搞定技术但搞不定设备科的数据、生产部门的产线、老师傅的配合。真正能推成功的，都是业务部门的人来扛。',
    '管理门槛二：数据主权的制度设计。我见过老板拍板上AI项目，IT部门去做数据采集，结果设备科主任直接锁门。不是技术问题，是信任问题。',
    '四条数据规则：第一，数据主权归原部门。第二，AI应用必须赋能原部门不是监管原部门。第三，数据使用需原部门负责人审批。第四，AI输出成果共享，原部门有优先使用权。',
    '管理门槛三：老师傅角色转型。老师傅的抵触是工业AI落地的最大隐形墙。他们担心AI会取代自己。关键是要给他们一个体面的转型路径。',
    '从操作工到AI操作指导员工资涨一级，到工艺知识工程师薪资对标AI工程师，到数据标注专家越老越值钱。让老师傅从被AI替代的人变成AI离不开的人。',
    '管理门槛四：老板的耐心够不够撑过破局期。工业AI项目前三到六个月进展缓慢，老板的常见心态变化：第一个月全力支持，第二个月怎么没动静，第三个月算了不适合我们，第四个月项目停了。',
    '破局期是正常的。工业AI是基础设施投资，不是快速见效的营销活动。给老板设合理预期，先做一个速赢的小场景让老板看到希望。',
    '打通四条管理关卡：第一，内部客户来扛事。第二，数据主权制度设计。第三，老师傅角色转型。第四，老板撑过破局期。打通四条你就是行业标杆。评论区扣数字告诉我你卡在哪一条。关注我，下期更精彩。',
]

assets = 'assets'
os.makedirs(assets, exist_ok=True)

total_start = time.time()
timings = []

for i, text in enumerate(segments, 1):
    t0 = time.time()
    print(f'[{i}/13] 生成中: {text[:30]}...', end=' ', flush=True)
    torch.manual_seed(SEED)  # 每次调用前设置相同seed
    wavs = chat.infer([text], use_decoder=True)
    t1 = time.time()
    outpath = f'{assets}/chattts-slide-{i}.wav'
    sf.write(outpath, wavs[0], 24000)
    dur = round(len(wavs[0]) / 24000, 1)
    infer_time = round(t1 - t0, 1)
    timings.append({
        'slide': i,
        'duration': dur,
        'infer_time': infer_time,
        'text_len': len(text),
        'file': outpath,
    })
    print(f'OK 音频{dur}s | 推理{infer_time}s')

total = time.time() - total_start
print(f'\n=== ChatTTS 全部完成! 总用时: {total:.0f}s ===')
for t in timings:
    print(f"  Slide {t['slide']}: {t['duration']}s 音频, {t['infer_time']}s 推理, {t['text_len']}字")
total_audio = sum(t['duration'] for t in timings)
print(f'\n总音频时长: {total_audio:.1f}s')

# 保存timing.json
import json
timing_data = [{'slide': t['slide'], 'duration': t['duration'], 'file': f"assets/chattts-slide-{t['slide']}.wav"} for t in timings]
with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timing_data, f, indent=2, ensure_ascii=False)
print('\ntiming.json 已保存')

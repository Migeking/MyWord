"""Generate per-slide TTS WAV files using ChatTTS with fixed seed."""
import os, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)

texts = [
    # Slide 1: 封面
    "花了200万才搞懂！设备数据上云这3个坑，90%工厂都踩过。我是鸡总，20年IT老兵，今天帮你拆解工业物联网数据采集的核心链路。",
    # Slide 2: 老板拍桌子
    "上个月有个老板找到我，拍着桌子说：鸡总，我花了200万搞数字化，结果数据传上来只有60%，关键数据还延迟3秒！我一看他们的方案，直接说了三个字：踩坑了。",
    # Slide 3: 设备方言太多
    "你的工厂里有PLC、传感器、摄像头、变频器，各种设备。每种设备说的方言都不一样，西门子用S7协议，三菱用MC协议，传感器用Modbus协议。想让它们直接上云？相当于让说普通话、英语、日语的人同时给你汇报。不翻译，你根本听不懂。",
    # Slide 4: 方案一 硬件网关
    "方案一：硬件网关。在设备旁边装一个工业网关，插上网口，自动把S7、Modbus等协议转成统一格式。就像给每个设备配个译员。适合设备少、对实时性要求不高的情况。",
    # Slide 5: 方案二 边缘计算
    "方案二：边缘计算。在车间放一台工业电脑，统一采集所有设备数据，先在本地处理，过滤、计算、打标签，再把结果发上去。就像在车间设个数据中心。适合设备多、要求快、断网不能丢数据的场景。",
    # Slide 6: 方案三 直连平台
    "方案三：直连平台。设备直接连到云平台，比如阿里云、西门子平台。最快，但要求设备本身支持。适合想快速上云、对数据安全要求不高的场景。记住一点，别被供应商忽悠，根据你的场景选合适的才是对的。",
    # Slide 7: 真实案例
    "来看一个真实案例。某工厂车间有100台温度传感器，用的Modbus协议，数据需要实时传到MES系统。他们是怎么做的？车间装了一个边缘计算盒子，统一采集100台传感器的数据。",
    # Slide 8: 案例效果
    "本地先处理：过滤异常值，超过80度或低于0度的丢掉。压缩打包，通过MQTT协议发送到MES系统，存入时序数据库。效果怎么样？数据完整性从65%提高到98%，延迟从5秒降到0.8秒，断网时还能本地缓存，恢复后自动补发。",
    # Slide 9: 避坑指南 延迟
    "第一个避坑指南：延迟够不够快？误工1小时，可能损失几十万。关键数据链路要在1秒以内，普通数据不超过5秒。",
    # Slide 10: 避坑指南 断网
    "第二个坑：断网会不会丢数据？很多企业在这里中招，网络一断就完蛋。正确做法是边缘节点本地缓存72小时，网络恢复后自动补发。",
    # Slide 11: 避坑指南 安全
    "第三个坑：数据安全怎么保障？设备数据能直接上公有云吗？建议核心数据走私有化部署，非核心数据走混合云。",
    # Slide 12: 结尾CTA
    "搞懂这条数据链路，你就知道为什么有的工厂数据采集又快又稳，为什么你的厂数据总是丢总是慢。下次供应商再也不敢忽悠你。评论区扣1，我发你一份工厂数据链路自检清单。关注我，聊20年踩过的坑，帮你少走弯路。",
]

os.makedirs('assets', exist_ok=True)

params = ChatTTS.Chat.InferCodeParams(
    prompt='[speed_5]',
    manual_seed=42,
    show_tqdm=True,
    max_new_token=1024,
)

for i, text in enumerate(texts, 1):
    wav = chat.infer(text, skip_refine_text=True, params_infer_code=params)
    audio_data = wav[0]
    sf.write(f'assets/chattts-slide-{i}.wav', audio_data, 24000)
    duration = len(audio_data) / 24000
    print(f'Slide {i}: {duration:.2f}s -> assets/chattts-slide-{i}.wav')

print('Done!')

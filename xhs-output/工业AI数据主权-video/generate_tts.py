"""ChatTTS: per-slide voiceover with fixed seed (kinetic-typography skill Step 3)"""
import torch, ChatTTS, soundfile as sf, os, json

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)

SEED = 42
PROJECT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PROJECT, "assets")
os.makedirs(ASSETS, exist_ok=True)

slides = [
    "我是鸡总。今天讲一个工业AI落地中最头疼的问题：设备科主任锁门，数据采不上来。三步搞定他。",
    "很多人以为设备科不肯给数据，是因为技术问题。数据格式不统一、设备没有数字化接口。错。真实原因是：信任问题。",
    "设备科主任怕什么？一怕数据给你们了我们没价值，二怕你们拿我们数据干别的事，三怕出问题我们背锅，四怕凭什么IT来动我们的东西。这些问题，技术方案解决不了。",
    "很多人犯的错误是：先采数据，再想制度。正确顺序是：先设计制度，再动数据。核心逻辑只有一条：让数据贡献者成为AI的受益者，而不是受害者。",
    "规则一，数据主权归原部门。规则二，AI输出成果原部门优先使用。规则三，每次调用需审批。规则四，成果共享。核心原则：让设备科觉得——数据给你，我不亏。",
    "第二步，让设备科参与数据标准制定。很多人做数据采集是IT说了算，设备科全程旁观。正确做法是让设备科的人参与进来，有参与感，有拥有感。",
    "一家模具厂的设备科班长老王参与进了标准制定。他说温度采集频率能不能低一点？项目组说可以。他说数据能不能给我也看？项目组说没问题。结果老王主动帮协调。为什么？因为他有拥有感。",
    "第三步，先做一个设备科能用到并且觉得有用的AI应用。很多AI项目死在只采集不用，设备科觉得这事儿跟他没关系。你要先让他尝到甜头。",
    "广域铭岛在一家工厂落地时，先做了设备健康看板。班组长每天早上能看到运行状态、异常告警、预测性维护建议。设备科主任说：这个东西好使，我们继续搞。",
    "总结一下。设备科锁门本质不是技术问题，是信任问题。三步解决：一，先设计制度。二，让他们参与标准制定。三，先做一个能让他尝到甜头的应用。关注我，下期讲老师傅怎么变成AI专家。",
]

results = []
for i, text in enumerate(slides):
    torch.manual_seed(SEED)
    wavs = chat.infer([text], use_decoder=True)
    fname = f"chattts-slide-{i+1}.wav"
    path = os.path.join(ASSETS, fname)
    sf.write(path, wavs[0], 24000)
    dur = len(wavs[0]) / 24000
    results.append({"slide": i+1, "file": fname, "duration": round(dur, 2)})
    print(f"Slide {i+1}: {dur:.1f}s → {fname}")

timing = os.path.join(PROJECT, "timing.json")
with open(timing, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nDone! Timing saved to {timing}")

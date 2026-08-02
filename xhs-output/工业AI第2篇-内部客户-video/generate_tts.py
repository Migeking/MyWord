"""ChatTTS: per-slide voiceover with fixed seed (Article #2 - 内部客户)"""
import torch, ChatTTS, soundfile as sf, os, json

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)

SEED = 42
PROJECT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PROJECT, "assets")
os.makedirs(ASSETS, exist_ok=True)

slides = [
    "我是鸡总二十年IT老兵。为什么你的AI项目做不动？答案不是技术问题，是你身边缺少一个想用AI的业务人。",
    "上期有个评论很典型：IT部门主导AI项目，干了八个月，数据采不上来，设备科不配合，老板觉得效率低。问题到底在哪？",
    "IT部门主导AI落地，百分之八十都会失败。不是IT不行，是他们的位置不对。IT是服务部门，他们能搞定代码，但搞不定人。",
    "设备科的数据凭什么给你？产线凭什么让你动？老师傅为什么要配合你？这些都不是技术问题，是政治问题。技术只占百分之二十，剩下百分之八十是人的问题。",
    "成功的企业都有一个共同特征：他们有一个想用AI的业务人。我们叫他内部客户。他的利益和AI成功绑定，他愿意扛事。",
    "这个人通常是生产负责人、质量负责人、工艺负责人，甚至是车间主任。他们的共同点是：屁股坐在业务那边，AI做成对他们有好处。",
    "一家汽车零部件企业的质量总监老张，主动找IT说我想用AI做质检。他自己去谈数据，在老板面前立军令状。六个月后AI上线了。",
    "IT部门是你们要我做，老张是我要做。要我和我要，是两种完全不同的驱动力。内部客户不是被动配合，而是主动主导。",
    "怎么找内部客户？四条标准：业务能力强、对新技术不排斥、有动力想出成绩、愿意承担责任。符合两条以上就值得谈。",
    "找到了怎么让他主导？一个公式：让他看到价值，让他感受到压力，给他资源。告诉他AI能解决什么问题，不做会怎样，给他预算和团队。",
    "一家电子企业的生产总监老李说了一句话就活了：AI做成了功劳是我的，做砸了责任我担。你们配合就行了。",
    "工业AI落地，技术只占百分之二十，百分之八十是人的问题。你有没有这样一个想用AI的内部客户？没有的话，你缺的可能不是技术，是一个人。",
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
    print(f"Slide {i+1}: {dur:.1f}s -> {fname}")

timing = os.path.join(PROJECT, "timing.json")
with open(timing, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nDone! Timing saved to {timing}")

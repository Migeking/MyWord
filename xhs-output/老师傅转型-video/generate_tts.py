"""Generate per-slide TTS WAV files using ChatTTS with fixed seed."""
import os, torch, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)  # CPU mode

texts = [
    # Slide 1 - Cover
    "干了二十年的老师傅，转型AI专家，月薪翻倍。我是鸡总，二十年IT老兵。今天讲一个很多人都在问的话题。",

    # Slide 2 - Problem
    "上期有人问我，鸡总，我们公司的老师傅觉得AI要取代他们，不配合。他们说，我干了二十年，要什么AI。这个问题怎么破。",

    # Slide 3 - Real reason
    "很多人以为老师傅抵触AI是因为不愿意学习新技术。错。老师傅抵触AI的真实原因是，他怕没价值。他靠经验吃饭，你跟他说AI可以帮你做，他听到的是，AI要取代我了。",

    # Slide 4 - Role crisis
    "老师傅的抵触不是对AI的抵触，是对自己未来角色的担忧。他们不怕AI，他们怕的是，AI来了我的工作谁来做，我的经验还有没有人认可。",

    # Slide 5 - Solution intro
    "解决这个问题的核心是，给老师傅一个角色转型的路。不是让他从操作工变成被AI替代的人，而是让他变成AI离不开的人。",

    # Slide 6 - Level 1-2
    "我给你一个具体路径，叫四个台阶。第一层，AI操作指导员，工资涨百分之十到二十。第二层，AI工艺辅导员，能带新人用AI，工资涨百分之二十到三十。",

    # Slide 7 - Level 3-4
    "第三层，工艺知识工程师，经验变成可复用的知识库，越老越值钱。第四层，数据标注专家，成为AI的老师，不可替代。每一步都比原来更值钱。",

    # Slide 8 - Case 1 梅钢
    "说个真实案例。梅钢热轧厂，一批干了二十多年的老师傅，以前在高温车间看火焰颜色判断钢水温度。现在在二十五度中央集控室看AI参数建议。一个干了二十八年的老师傅说，以前觉得AI来抢饭碗，现在觉得AI是来帮我的。",

    # Slide 9 - Case 2 广州柴油机厂
    "广州柴油机厂做了个AI知识库系统，把老师傅的经验变成新员工的超级外脑。新人培养周期从六个月缩短到两个月。AI不会让老师傅失业，只会让老师傅的经验更值钱。",

    # Slide 10 - CTA
    "最后四个操作建议。第一，设立AI协作达人奖，让老师傅有面子地参与。第二，让老师傅参与AI规则的定义和验收。第三，给老师傅配徒弟当辅导员。第四，永远不要让AI成为考核工具，要成为赋能工具。你们公司的老师傅对AI什么态度？评论区告诉我。",
]

os.makedirs('assets', exist_ok=True)

for i, text in enumerate(texts, 1):
    torch.manual_seed(42)
    wavs = chat.infer([text], use_decoder=True)
    audio = wavs[0]
    sf.write(f'assets/chattts-slide-{i}.wav', audio, 24000)
    duration = len(audio) / 24000
    print(f'Slide {i:2d}: {duration:6.2f}s')

print('Done!')

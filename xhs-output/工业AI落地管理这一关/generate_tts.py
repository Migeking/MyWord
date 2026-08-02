"""Generate per-slide TTS WAV files using ChatTTS with fixed seed."""
import os, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

chat = ChatTTS.Chat()
chat.load(source='huggingface')

texts = [
    "工业AI落地，百分之八十的企业死在管理这一关。我是鸡总，二十年IT老兵。",
    "上期讲了工业AI成功的关键不是大模型，结果评论区炸了。最多的问题不是技术，而是这一类：",
    "数据采不上来，不是技术问题，是部门墙的问题。设备科说数据是他的，IT部门根本进不去。老板想上AI，工人觉得是要取代他们，不配合。",
    "你以为AI项目是技术问题？实际是政治问题。我见过太多企业，技术方案一流，项目管理一塌糊涂。",
    "设备科说数据是命根子，IT部门说AI归我们管，生产部门说别动我的产线，老师傅说我干了二十年要什么AI，老板说先做了再说。",
    "管理门槛一：你有没有一个内部客户的CTO？工业AI项目最难的不是技术，是谁来扛这个事。",
    "凡是想让IT部门主导的，百分之八十都失败了。真正能推成功的，都是业务部门的人来扛。",
    "管理门槛二：你有没有数据主权的制度设计。数据是工业AI的血液，但这血不是想抽就能抽的。",
    "解决方案不是靠老板施压，是制度设计。数据主权归原部门，AI应用必须赋能原部门，不是监管原部门，数据使用需审批，AI成果共享。",
    "管理门槛三：你有没有给老师傅一个角色转型的路。老师傅的抵触，是工业AI落地的最大隐形墙。",
    "管理门槛四：老板的耐心够不够撑过破局期。工业AI项目前三到六个月，进展缓慢，看不到成果。",
    "工业AI的管理门槛总结四条：内部客户来扛事、数据主权制度设计、老师傅角色转型、老板撑过破局期。打通四条，你已经是行业标杆了。评论区扣数字，告诉我你卡在哪一条最多。关注鸡总，下期讲真实案例。",
]

os.makedirs('assets', exist_ok=True)

for i, text in enumerate(texts, 1):
    wavs = chat.infer(text, skip_refine_text=True,
                      params_infer_code=ChatTTS.Chat.InferCodeParams(manual_seed=42))
    audio_data = wavs[0]  # list of numpy arrays
    sf.write(f'assets/chattts-slide-{i}.wav', audio_data, 24000)
    duration = len(audio_data) / 24000
    print(f'Slide {i:2d}: {duration:.2f}s -> assets/chattts-slide-{i}.wav')

print('Done!')

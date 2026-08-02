"""Generate per-slide TTS WAV files using ChatTTS with fixed seed."""
import os, torch, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

chat = ChatTTS.Chat()
chat.load(source='huggingface', compile=False)  # CPU mode, use huggingface cache

# ⚠️ 数字已全部转中文全称（ChatTTS 会读英文数字）
texts = [
    # Slide 1 - Cover
    "发了三篇AI文章，全被限流了。我是鸡总，二十年IT老兵。今天讲一个真实的故事，我是怎么七天帮他恢复流量池的。",

    # Slide 2 - 粉丝深夜求助
    "上周四晚上十一点，我的一个粉丝给我发微信，语音打了五分钟。他说，鸡总，我完了。我的小红书账号发了三篇文章，全部被限流了。我靠这个账号接单，损失了差不多两万块。",

    # Slide 3 - 用了AI但没标
    "我问，你用AI写文章了吗。他说，用了，但我改了很多啊。我问，你标了AI吗。他说，没有，我觉得改了就算原创了。我说，这就是问题。不是AI写得不好，是用了AI但没告诉平台。",

    # Slide 4 - 三篇三次限流
    "他叫老周，做制造业的。他的方法很简单，让AI写初稿，自己改一遍，发布。结果第一篇，发布两小时限流。第二篇，五百阅读被限。第三篇，发布就限流，只有五十阅读。",

    # Slide 5 - 诊断结果
    "他去后台看限流诊断，上面写着，该笔记疑似包含AI生成内容且未进行明确标识。我说，现在二零一九年的方法已经过时了，二零二六年的AI检测算法，早就不只是看你像不像AI写的了。",

    # Slide 6 - 算法升级了三轮
    "二零二六年的检测算法，已经升级了三轮。第一轮，检测文本像不像AI写的。第二轮，检测文本有没有改写痕迹。第三轮，多模型交叉检测。简单改写，已经骗不过算法了。",

    # Slide 7 - 三件事修复
    "我让他做了三件事。第一，确认限流原因。第二，修改所有历史笔记，在每篇开头加上这句话：本文含AI辅助创作内容，已人工审核优化。他一共十七篇笔记，全部加上。",

    # Slide 8 - 检测加优化
    "第三，用工具检测优化。跑出来AI辅助比例百分之三十二，超了红线。原创度六十八分。我们花了两天，加入真实案例，去掉AI味的句式，每三百字加一个情绪钩子。优化后AI比例降到百分之十八，原创度八十七分，全部达标。",

    # Slide 9 - 第七天恢复
    "提交复审后，第七天账号完全恢复正常。恢复后第一天，阅读量从五十涨到了一千二、八百、一千五。老周给我发微信说，鸡总，账号回来了，谢谢你。",

    # Slide 10 - 四条建议加互动
    "老周的问题不是AI用错了，是认知没跟上算法。真正有效的方法只有四条。第一，主动标识AI使用，这是合规底线。第二，降低AI辅助比例到百分之二十五以下。第三，提升原创度到八十五分以上。第四，加入只有你能写的真实经历。你被限流过吗？评论区告诉我，关注鸡总，下期更精彩。",
]

os.makedirs('assets', exist_ok=True)

for i, text in enumerate(texts, 1):
    torch.manual_seed(42)  # 固定种子，保证同一声线
    wavs = chat.infer([text], use_decoder=True)
    audio = wavs[0]
    sf.write(f'assets/chattts-slide-{i}.wav', audio, 24000)
    duration = len(audio) / 24000
    print(f'Slide {i:2d}: {duration:6.2f}s')

print('Done!')

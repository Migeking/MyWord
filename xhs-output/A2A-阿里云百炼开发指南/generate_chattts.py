"""Generate single continuous TTS voiceover for A2A video."""
import os, ChatTTS, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

full_text = ("阿里云百炼平台 A2A 三方 Agent 开发避坑指南，用点NET玩转智能体互操作协议。"
    "拿起我们熟悉的点NET武器，开发自己的Agent，并把它链接到阿里云百炼大平台。"
    "A2A协议核心三大概念，Agent Card是智能体的名片，Task是调用工作单元，Artifact是输出产物。"
    "微软官方A2A SDK，与Semantic Kernel同生态，对ASPNET Core有原生支持。"
    "第一个坑，不同预览版本API不兼容，务必锁定NuGet版本号。"
    "第二个坑，路由扩展方法命名空间变更，Agent Card序列化必须配置小驼峰格式。"
    "从单Agent到多Agent，每个独立路由，独立TaskManager，互不干扰。"
    "Agent Card浏览器即可查看，消息调试用PostMan发送JSONRPC请求。"
    "AI识别用户意图，自动调用Agent发送微信模板消息，端到端打通。"
    "A2A标准快速走向正式版，期待阿里云快点升级，你学废了吗？")

os.makedirs('assets', exist_ok=True)

chat = ChatTTS.Chat()
chat.load(source='huggingface')

print("Generating TTS voiceover...")
wav = chat.infer(
    [full_text],
    skip_refine_text=True,
    params_infer_code=ChatTTS.Chat.InferCodeParams(
        prompt='[speed_5]',
        manual_seed=42
    )
)

audio_data = wav[0][0] if wav[0].ndim > 1 else wav[0]
sf.write('assets/voiceover.wav', audio_data, 24000)
duration = len(audio_data) / 24000
print(f'Done! Duration: {duration:.2f}s')

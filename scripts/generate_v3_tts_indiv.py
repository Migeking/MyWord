"""
V3 TTS: 逐联生成, 保证每段干净完整
seed=99 诗朗诵声线
"""
import os, torch, ChatTTS, soundfile as sf

OUT_DIR = os.path.abspath("D:/code/MyWord/xhs-output/侠客行_v3/assets")
os.makedirs(OUT_DIR, exist_ok=True)

couplets = [
    "赵客缦胡缨，吴钩霜雪明。",
    "银鞍照白马，飒沓如流星。",
    "十步杀一人，千里不留行。",
    "事了拂衣去，深藏身与名。",
    "闲过信陵饮，脱剑膝前横。",
    "将炙啖朱亥，持觞劝侯嬴。",
    "三杯吐然诺，五岳倒为轻。",
    "眼花耳热后，意气素霓生。",
    "救赵挥金槌，邯郸先震惊。",
    "千秋二壮士，烜赫大梁城。",
    "纵死侠骨香，不惭世上英。",
    "谁能书阁下，白首太玄经。",
]

print("Loading ChatTTS...")
chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
sr = 24000
print("ChatTTS loaded.\n")

durations = []
timing_path = os.path.join(OUT_DIR, "timing.txt")
with open(timing_path, 'w', encoding='utf-8') as f:
    f.write("V3 Poem Couplet Timing (seed=99, individual)\n")
    f.write("=" * 50 + "\n")

    for i, couplet in enumerate(couplets):
        torch.manual_seed(99)
        wavs = chat.infer([couplet])
        audio = wavs[0]
        if audio.ndim > 1:
            audio = audio[0]
        
        dur = len(audio) / sr
        durations.append(dur)
        
        filepath = os.path.join(OUT_DIR, f"couplet_{i+1:02d}.wav")
        sf.write(filepath, audio, sr)
        
        line = f"couplet_{i+1:02d}: {couplet} = {dur:.2f}s"
        print(f"  {line}")
        f.write(line + "\n")

total = sum(durations)
print(f"\n  Total: {len(durations)} couplets, {total:.1f}s")
with open(timing_path, 'a', encoding='utf-8') as f:
    f.write(f"\nTotal: {total:.1f}s\n")

print(f"\nV3 TTS complete! Files in {OUT_DIR}")

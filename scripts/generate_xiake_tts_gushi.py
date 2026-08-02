"""
Generate 侠客行 TTS: 1 full poem reading + 27 individual segments (Gushi Version).
All individual segments are generated sentence-by-sentence to avoid any word clipping.
"""
import os, torch, ChatTTS, soundfile as sf

OUT_DIR = os.path.abspath("D:/code/MyWord/xhs-output/古诗词参考/xiakexing/assets")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Texts ──
narrator_texts = [
    "侠客行是唐代大诗人李白最豪迈的诗篇之一。诗人以惊天的笔力，塑造了一位战国时期仗剑天涯的侠客形象。",
    "今天，让我们一起走进这首千古名篇。",
    "燕赵之地的侠客，头戴粗犷的胡缨，腰间吴钩宝剑闪烁着霜雪般的寒光。",
    "银色的鞍辔映照着白色的骏马，飞驰而过的身影如同流星划过天际。",
    "十步之内取敌性命，千里之间无人能阻挡。",
    "完成大事之后，轻轻拂去衣上的尘土，悄然离去。这便是侠客的最高境界。",
    "闲时来到信陵君府上饮酒，解下宝剑横放膝前。",
    "亲手烤肉给壮士朱亥，举杯敬酒与谋士侯嬴共饮。",
    "三杯酒下肚便许下重诺，这份承诺比五座大山还要沉重。",
    "酒酣耳热之际，心中豪气化作一道白虹贯穿长空。",
    "为救赵国挥起金色大锤，邯郸城为之震动。",
    "千年之后，这两位壮士的英名，依然赫赫闪耀在大梁城中。",
    "纵然身死，侠骨依旧留有余香，无愧于世间任何英雄。",
    "谁愿意在书阁中皓首穷经。侠客选择了另一种人生，仗剑天下，快意恩仇。",
    "李白写的不仅是千年前的侠客，更是他自己心中那个永不低头的少年。愿我们心中，也永远住着一位侠客。",
]

poem_texts = [
    "赵客缦胡缨，吴钩霜雪明",
    "银鞍照白马，飒沓如流星",
    "十步杀一人，千里不留行",
    "事了拂衣去，深藏身与名",
    "闲过信陵饮，脱剑膝前横",
    "将炙啖朱亥，持觞劝侯嬴",
    "三杯吐然诺，五岳倒为轻",
    "眼花耳热后，意气素霓生",
    "救赵挥金槌，邯郸先震惊",
    "千秋二壮士，烜赫大梁城",
    "纵死侠骨香，不惭世上英",
    "谁能书阁下，白首太玄经",
]

# ── Load ChatTTS ──
print("Loading ChatTTS...")
chat = ChatTTS.Chat()
chat.load(compile=False, source='huggingface')
sr = 24000
print("ChatTTS loaded.")

# 1. Generate FULL poem recitation (no slicing,連贯朗读)
print("\n--- Generating FULL Poem Recitation (poem_full, seed=99) ---")
full_poem_text = "。".join(poem_texts) + "。"
torch.manual_seed(99)
wavs = chat.infer(
    [full_poem_text],
    skip_refine_text=True,
    params_infer_code=ChatTTS.Chat.InferCodeParams(
        prompt='[speed_5]',
        manual_seed=99
    )
)
audio_full = wavs[0][0] if wavs[0].ndim > 1 else wavs[0]
full_dur = len(audio_full) / sr
sf.write(os.path.join(OUT_DIR, "poem_full.wav"), audio_full, sr)
print(f"  [poem_full] {full_dur:.2f}s generated")

# 2. Generate individual narrator segments (narrator_01 to narrator_15)
print("\n--- Generating Narrator Segments (seed=42) ---")
narrator_durs = []
for i, text in enumerate(narrator_texts):
    torch.manual_seed(42)
    wavs = chat.infer(
        [text],
        skip_refine_text=True,
        params_infer_code=ChatTTS.Chat.InferCodeParams(
            prompt='[speed_5]',
            manual_seed=42
        )
    )
    audio = wavs[0][0] if wavs[0].ndim > 1 else wavs[0]
    dur = len(audio) / sr
    narrator_durs.append(dur)
    
    filename = f"narrator_{i+1:02d}.wav"
    sf.write(os.path.join(OUT_DIR, filename), audio, sr)
    print(f"  [{filename}] {dur:.2f}s → {text}")

# 3. Generate individual poem couplet segments (poem_01 to poem_12)
print("\n--- Generating Poem Couplet Segments (seed=99) ---")
poem_durs = []
for i, text in enumerate(poem_texts):
    torch.manual_seed(99)
    wavs = chat.infer(
        [text],
        skip_refine_text=True,
        params_infer_code=ChatTTS.Chat.InferCodeParams(
            prompt='[speed_5]',
            manual_seed=99
        )
    )
    audio = wavs[0][0] if wavs[0].ndim > 1 else wavs[0]
    dur = len(audio) / sr
    poem_durs.append(dur)
    
    filename = f"poem_{i+1:02d}.wav"
    sf.write(os.path.join(OUT_DIR, filename), audio, sr)
    print(f"  [{filename}] {dur:.2f}s → {text}")

# Write timing info
timing_path = os.path.join(OUT_DIR, "timing.txt")
if os.path.exists(timing_path):
    os.remove(timing_path)
    
with open(timing_path, 'w', encoding='utf-8') as f:
    f.write(f"=== Poem Full Timing ===\n")
    f.write(f"  poem_full.wav: {full_dur:.2f}s\n\n")
    
    f.write(f"=== Narrator Timing ===\n")
    for i, d in enumerate(narrator_durs):
        f.write(f"  narrator_{i+1:02d}.wav: {d:.2f}s\n")
        
    f.write(f"\n=== Poem Timing ===\n")
    for i, d in enumerate(poem_durs):
        f.write(f"  poem_{i+1:02d}.wav: {d:.2f}s\n")

print("\n" + "="*50)
print("TTS GENERATION COMPLETE")
print(f"poem_full: {full_dur:.1f}s")
print(f"Narrator: {len(narrator_durs)} segments, total {sum(narrator_durs):.1f}s")
print(f"Poem:     {len(poem_durs)} segments, total {sum(poem_durs):.1f}s")
print("="*50)

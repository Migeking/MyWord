"""
gen_tts.py - ChatTTS 28 句配音生成器(v2 — 适配新版 ChatTTS API)
- manual_seed=42 (音色一致)
- source='huggingface'
- params_infer_code 传参
- 写 wav + timing.json
"""
import json
import os
import sys
import time
import wave
import numpy as np
import torch
import ChatTTS
from ChatTTS.core import Chat

# ============== 27 句剧本(开始时间来自 v3 HTML 时间线)==============
LINES = [
    ("孩子有这 3 个表现", 0.3),
    ("说明已经被你毁了", 1.0),
    ("一定要看完", 2.2),
    ("第一个", 3.5),
    ("不再顶嘴了", 4.0),
    ("不是他变乖了", 4.8),
    ("是他知道了", 5.2),
    ("说什么都没用", 5.6),
    ("说了也没人听", 6.0),
    ("第二个", 8.5),
    ("学会藏东西了", 9.0),
    ("手机加了密码", 9.7),
    ("日记本上了锁", 10.0),
    ("连心事都藏起来", 10.3),
    ("因为他怕", 10.7),
    ("怕被你翻出来", 11.0),
    ("第三个", 14.5),
    ("还在对你笑", 15.0),
    ("但眼睛里", 15.8),
    ("没有光", 16.8),
    ("不是他不想说", 17.6),
    ("是他不想让你", 18.2),
    ("知道他在难过", 18.8),
    ("如果你家孩子全中", 22.0),
    ("从今晚开始", 23.8),
    ("学会闭嘴", 24.6),
    ("学会倾听", 25.6),
]

OUT_DIR = r"D:\code\MyWord\小红书笔记\三件套-父母教育\tts"
SEED = 42
SOURCE = "huggingface"

def make_infer_params():
    p = Chat.InferCodeParams()
    p.manual_seed = SEED
    p.spk_smp = None
    p.temperature = 0.3
    p.top_P = 0.7
    p.top_K = 20
    p.show_tqdm = False
    return p

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[init] loading ChatTTS (source={SOURCE})", flush=True)
    t0 = time.time()
    chat = Chat()
    chat.load(source=SOURCE, compile=False)
    print(f"[init] loaded in {time.time()-t0:.1f}s", flush=True)

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    print("[warmup] running test infer...", flush=True)
    try:
        _ = chat.infer("准备", params_infer_code=make_infer_params(), skip_refine_text=False)
        print("[warmup] ok", flush=True)
    except Exception as e:
        print(f"[warmup] warn: {e}", file=sys.stderr, flush=True)

    results = []
    for i, (text, start_t) in enumerate(LINES, 1):
        out_name = f"line-{i:02d}.wav"
        out_path = os.path.join(OUT_DIR, out_name)
        print(f"[{i:02d}/27] {text!r}  start={start_t:.1f}s", flush=True)

        torch.manual_seed(SEED)
        np.random.seed(SEED)
        params = make_infer_params()

        t0 = time.time()
        try:
            wavs = chat.infer(text, params_infer_code=params, skip_refine_text=False)
            audio = np.array(wavs[0], dtype=np.float32)
            peak = np.abs(audio).max()
            if peak > 0:
                audio = audio / peak * 0.9
            sr = 24000
            audio_int16 = (audio * 32767).astype(np.int16)
            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(audio_int16.tobytes())
            dur = len(audio) / sr
            engine = "chattts"
        except Exception as e:
            print(f"  [WARN] {text!r} failed: {e}", file=sys.stderr, flush=True)
            sr = 24000
            dur = max(0.4, len(text) * 0.18)
            silence = np.zeros(int(sr * dur), dtype=np.int16)
            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
                wf.writeframes(silence.tobytes())
            engine = "silence-fallback"

        dt = time.time() - t0
        print(f"         dur={dur:.2f}s  gen={dt:.1f}s", flush=True)
        results.append({
            "file": out_name, "text": text,
            "start": start_t, "duration": dur, "engine": engine
        })

    timing = {
        "total_duration": 30.0,
        "seed": SEED,
        "source": SOURCE,
        "lines": results,
    }
    with open(os.path.join(OUT_DIR, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, ensure_ascii=False, indent=2)
    print(f"\n[done] 27 lines -> {OUT_DIR}", flush=True)

if __name__ == "__main__":
    main()

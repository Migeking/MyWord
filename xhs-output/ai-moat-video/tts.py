#!/usr/bin/env python3
"""TTS 工具 - 支持 Edge TTS / kokoro-onnx + 背景音乐混音

中文配音首选 Edge TTS（微软神经语音），发音标准无方言。
kokoro-onnx 作为离线备选。

用法:
  # Edge TTS (默认，推荐中文)
  python tts.py "文字内容" -o output.mp3
  python tts.py "文字内容" -o speech.mp3 -v zh-CN-YunxiNeural --rate +10%
  python tts.py "文字内容" -o speech.mp3 --bgm assets/bgm/bgm_ambient_pad.wav --bgm-volume 0.15

  # kokoro-onnx (离线备用)
  python tts.py "文字内容" -o speech.wav --engine kokoro -v zm_yunxi -s 1.0

  # 从文件读取
  python tts.py script.txt -o output.mp3 --bgm assets/bgm/bgm_chinese_pad.wav

安装依赖:
  pip install edge-tts soundfile pydub kokoro-onnx espeakng-loader phonemizer-fork
"""

import os
import sys
import argparse
import time
import json
import tempfile


def parse_args():
    parser = argparse.ArgumentParser(description="TTS 工具 - 支持多引擎 + 背景音乐混音")

    # 输入
    parser.add_argument("input", help="文字内容或 .txt 文件路径")

    # 输出
    parser.add_argument("-o", "--output", default=None,
                        help="输出文件路径（默认 speech.mp3 或 speech.wav）")

    # 引擎
    parser.add_argument("--engine", default="edge",
                        choices=["edge", "kokoro"],
                        help="TTS 引擎: edge（默认推荐，标准普通话），勿用 kokoro（方言发音不标准）")

    # 声音
    parser.add_argument("-v", "--voice", default=None,
                        help="""声音选择（仅 Edge TTS）:
    zh-CN-XiaoxiaoNeural  (女·温暖)    推荐 - 最佳中文女声
    zh-CN-YunxiNeural     (男·阳光)    推荐 - 最佳中文男声
    zh-CN-YunyangNeural   (男·专业)
    zh-CN-XiaoyiNeural    (女·活泼)
    zh-CN-YunjianNeural   (男·激情)
  注意: 勿用 kokoro-onnx 的 zf_ / zm_ 系列声音，发音不标准。
  """)

    # Edge TTS 参数
    parser.add_argument("--rate", default="+0%",
                        help="语速调整（Edge TTS 专用，如 +10%% 或 -10%%）")
    parser.add_argument("--pitch", default="+0Hz",
                        help="音调调整（Edge TTS 专用，如 +10Hz, -10Hz）")

    # BGM
    parser.add_argument("--bgm", default=None,
                        help="背景音乐文件路径（.mp3/.wav），默认无 BGM")
    parser.add_argument("--bgm-volume", type=float, default=0.12,
                        help="背景音乐音量 (0.0-1.0，默认 0.12 即 12%%)")
    parser.add_argument("--bgm-loop", action="store_true", default=True,
                        help="背景音乐循环（不足时自动循环，默认开启）")
    parser.add_argument("--no-bgm-loop", action="store_true",
                        help="不循环背景音乐")

    return parser.parse_args()


def read_input(input_path):
    """读取输入文字（直接字符串或 .txt 文件）"""
    text = input_path
    if os.path.isfile(text):
        with open(text, encoding="utf-8") as f:
            text = f.read().strip()
    if not text:
        print("错误: 输入文本为空")
        sys.exit(1)
    return text


def tts_edge(text, voice, output, rate="+0%", pitch="+0Hz"):
    """使用 Edge TTS (微软神经语音)"""
    import edge_tts
    import asyncio

    voice = voice or "zh-CN-XiaoxiaoNeural"

    print(f"Edge TTS 合成中...")
    print(f"  声音: {voice}")
    print(f"  语速: {rate}")
    print(f"  音调: {pitch}")

    t0 = time.time()

    async def _save(wav_mode=False):
        nonlocal text, voice, rate, pitch
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        if wav_mode:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(tmp_fd)
            await comm.save(tmp_path)
            return tmp_path
        else:
            await comm.save(output)
            return output

    ext = os.path.splitext(output)[1].lower()
    is_wav = ext == ".wav"

    if is_wav:
        # Save to temp MP3 first, then convert to WAV
        tmp_path = asyncio.run(_save(wav_mode=True))
        try:
            duration = get_mp3_duration(tmp_path)
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(tmp_path)
            audio.export(output, format="wav")
            os.remove(tmp_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
    else:
        asyncio.run(_save())
        duration = get_mp3_duration(output)

    elapsed = time.time() - t0
    file_size = os.path.getsize(output)

    print(f"  合成完成 ({elapsed:.1f}s)")
    print(f"  时长: {duration:.1f}s")
    print(f"  输出: {output} ({file_size / 1024:.0f}KB)")

    return duration


def get_mp3_duration(filepath):
    """Get MP3 duration using ffprobe or pydub."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(filepath)
        return audio.duration_seconds
    except Exception:
        pass

    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             filepath],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0


def tts_kokoro(text, voice, output, speed=1.0, lang="cmn"):
    """使用 kokoro-onnx (离线 TTS)"""
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    from kokoro_onnx import Kokoro
    import soundfile as sf

    voice = voice or "zm_yunxi"

    # eSpeak 初始化
    espeak_data_path = espeakng_loader.get_data_path()
    espeak_lib_path = espeakng_loader.get_library_path()
    EspeakWrapper.set_data_path(espeak_data_path)
    EspeakWrapper.set_library(espeak_lib_path)
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = espeak_lib_path
    os.environ["ESPEAK_DATA_PATH"] = espeak_data_path

    # 模型路径
    cache_dir = os.path.expanduser("~/.cache/hyperframes/tts")
    model_path = os.path.join(cache_dir, "models", "kokoro-v1.0.onnx")
    voices_path = os.path.join(cache_dir, "voices", "voices-v1.0.bin")

    if not os.path.exists(model_path) or not os.path.exists(voices_path):
        print("错误: kokoro-onnx 模型文件未找到！")
        print(f"  模型: {model_path}")
        print(f"  语音: {voices_path}")
        print("请先下载或使用 --engine edge")
        sys.exit(1)

    # 语言映射
    if lang == "zh":
        lang = "cmn"
        print("  自动映射: zh → cmn")

    print(f"kokoro-onnx 合成中...")
    print(f"  声音: {voice}")
    print(f"  语速: {speed}")

    t0 = time.time()

    # 加载模型
    print("  加载模型...")
    kokoro = Kokoro(model_path, voices_path)

    # 生成语音
    audio, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang=lang)
    duration = len(audio) / sample_rate

    # 保存
    sf.write(output, audio, sample_rate)
    file_size = os.path.getsize(output)

    elapsed = time.time() - t0
    print(f"  合成完成 ({elapsed:.1f}s)")
    print(f"  时长: {duration:.1f}s")
    print(f"  输出: {output} ({file_size / 1024:.0f}KB)")

    return duration


def mix_bgm(speech_path, bgm_path, output_path, bgm_volume=0.12, loop=True):
    """将背景音乐混入语音文件"""
    from pydub import AudioSegment

    print(f"\n混音背景音乐...")
    print(f"  BGM: {os.path.basename(bgm_path)}")
    print(f"  BGM 音量: {bgm_volume:.0%}")
    print(f"  循环: {'是' if loop else '否'}")

    t0 = time.time()

    # 加载语音
    speech = AudioSegment.from_file(speech_path)
    speech_duration = speech.duration_seconds

    # 加载 BGM
    bgm = AudioSegment.from_file(bgm_path)
    bgm_duration = bgm.duration_seconds

    # BGM 音量调整
    bgm = bgm - (20 * (1 - bgm_volume) + 3)  # 近似音量映射

    # 循环 BGM 直到覆盖语音长度
    if loop and bgm_duration < speech_duration:
        repeats = int(speech_duration / bgm_duration) + 1
        bgm = bgm * repeats
        print(f"  BGM 循环 {repeats}x ({bgm_duration:.0f}s -> {bgm.duration_seconds:.0f}s)")

    # 裁剪到语音长度
    bgm = bgm[:len(speech)]

    # 淡入淡出 BGM
    fade_ms = min(3000, len(bgm) // 4)
    bgm = bgm.fade_in(fade_ms).fade_out(fade_ms)

    # 混音
    mixed = speech.overlay(bgm)
    mixed.export(output_path, format=os.path.splitext(output_path)[1][1:])

    elapsed = time.time() - t0
    mixed_size = os.path.getsize(output_path)
    print(f"  混音完成 ({elapsed:.1f}s)")
    print(f"  输出: {output_path} ({mixed_size / 1024:.0f}KB)")

    return mixed.duration_seconds


def emit_json(output_path, duration, voice, engine, bgm_file=None):
    """输出 JSON 元数据（供管道调用）"""
    result = {
        "output": os.path.abspath(output_path),
        "duration": round(duration, 1),
        "voice": voice,
        "engine": engine,
        "file_size": os.path.getsize(output_path),
    }
    if bgm_file:
        result["bgm"] = os.path.basename(bgm_file)
    print(json.dumps(result))


def main():
    args = parse_args()

    # 读取输入
    text = read_input(args.input)
    print(f"文本长度: {len(text)} 字")

    # 确定输出路径
    ext = ".mp3" if args.engine == "edge" else ".wav"
    output = args.output or f"speech{ext}"
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    # 合成语音
    if args.engine == "edge":
        voice = args.voice or "zh-CN-XiaoxiaoNeural"
        duration = tts_edge(text, voice, output, args.rate, args.pitch)
    else:
        print("警告: kokoro-onnx 引擎的 zf_/zm_ 系列中文声音发音不标准，"
              "建议使用 --engine edge")
        voice = args.voice or "zm_yunxi"
        duration = tts_kokoro(text, voice, output, args.speed, args.lang)

    # BGM 混音
    bgm_file = args.bgm
    if bgm_file and os.path.exists(bgm_file):
        loop_bgm = not args.no_bgm_loop
        mixed_output = output.replace(".wav", "_with_bgm.wav") \
            if output.endswith(".wav") else \
            output.replace(".mp3", "_with_bgm.mp3")
        duration = mix_bgm(output, bgm_file, mixed_output,
                           args.bgm_volume, loop_bgm)
        output = mixed_output
    elif bgm_file:
        print(f"警告: BGM 文件不存在: {bgm_file}")

    # 输出结果
    print(f"\n完成！输出文件: {output}")
    print(f"总时长: {duration:.1f}s")

    # 非终端模式输出 JSON
    if not sys.stdout.isatty():
        emit_json(output, duration, voice, args.engine, bgm_file)


if __name__ == "__main__":
    main()

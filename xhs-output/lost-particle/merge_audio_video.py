"""
将 TTS 音频与无声视频合成为最终视频
用法: python merge_audio_video.py
"""
import subprocess
import os
import wave

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SILENT_VIDEO = os.path.join(SCRIPT_DIR, "output_silent.mp4")
OUTPUT_FINAL = os.path.join(SCRIPT_DIR, "lost_particle_final.mp4")

# TTS 音频文件
SUBTITLE_WAVS = [
    os.path.join(SCRIPT_DIR, "subtitle_1.wav"),  # 0-1s: 一个迷路的粒子
    os.path.join(SCRIPT_DIR, "subtitle_2.wav"),  # 1-4s: 永不回头
    os.path.join(SCRIPT_DIR, "subtitle_3.wav"),  # 4-5s: 这是它画的。
]

# 每段字幕的起始时间（秒）
SUBTITLE_STARTS = [0.0, 1.0, 4.0]

def get_wav_duration(wav_path):
    """获取 WAV 文件时长"""
    with wave.open(wav_path, 'r') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)

def merge():
    # 检查文件存在
    if not os.path.exists(SILENT_VIDEO):
        print(f"Error: Silent video not found: {SILENT_VIDEO}")
        return
    
    for wav in SUBTITLE_WAVS:
        if not os.path.exists(wav):
            print(f"Error: WAV file not found: {wav}")
            return
    
    # 打印音频信息
    for i, (wav, start) in enumerate(zip(SUBTITLE_WAVS, SUBTITLE_STARTS)):
        dur = get_wav_duration(wav)
        print(f"Subtitle {i+1}: starts at {start}s, duration {dur:.2f}s")
    
    # 使用 FFmpeg 合成：
    # 1. 先将3段WAV按时序拼接成一个完整音轨
    # 2. 再与视频合并
    
    # 创建静音底轨（5秒）
    silent_base = os.path.join(SCRIPT_DIR, "_silent_base.wav")
    cmd_silent = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'anullsrc=r=24000:cl=mono',
        '-t', '5',
        '-c:a', 'pcm_s16le',
        silent_base
    ]
    subprocess.run(cmd_silent, check=True)
    
    # 逐段叠加到静音底轨上
    current_audio = silent_base
    for i, (wav, start) in enumerate(zip(SUBTITLE_WAVS, SUBTITLE_STARTS)):
        mixed = os.path.join(SCRIPT_DIR, f"_mixed_{i}.wav")
        cmd_mix = [
            'ffmpeg', '-y',
            '-i', current_audio,
            '-i', wav,
            '-filter_complex',
            f'[0:a]aresample=24000[base];[1:a]aresample=24000,adelay={int(start*1000)}|{int(start*1000)}[delayed];[base][delayed]amix=inputs=2:duration=first:dropout_transition=0[out]',
            '-map', '[out]',
            '-c:a', 'pcm_s16le',
            mixed
        ]
        subprocess.run(cmd_mix, check=True)
        current_audio = mixed
    
    # 最终音轨
    final_audio = os.path.join(SCRIPT_DIR, "_final_audio.wav")
    os.rename(current_audio, final_audio)
    
    # 合并视频+音频
    cmd_final = [
        'ffmpeg', '-y',
        '-i', SILENT_VIDEO,
        '-i', final_audio,
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        OUTPUT_FINAL
    ]
    subprocess.run(cmd_final, check=True)
    
    # 清理临时文件
    for f in [silent_base] + [os.path.join(SCRIPT_DIR, f"_mixed_{i}.wav") for i in range(3)]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(final_audio):
        os.remove(final_audio)
    
    print(f"\nFinal video with audio: {OUTPUT_FINAL}")
    
    # 打印最终视频信息
    cmd_info = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', OUTPUT_FINAL]
    result = subprocess.run(cmd_info, capture_output=True, text=True)
    print(result.stdout[:500])

if __name__ == "__main__":
    merge()

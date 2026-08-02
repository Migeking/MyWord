"""语音合成引擎：edge-tts（主，免费无限高质量）+ kokoro-onnx（离线备选）。

edge-tts 走微软神经语音云服务，免费无限无需 key；断网时自动回退 kokoro 本地离线。
"""
from __future__ import annotations

import asyncio
import io
import logging
import time
from pathlib import Path

log = logging.getLogger("cyber-avatar.voice")

EDGE_VOICES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 女声（默认，甜美女声）
    "xiaoyi": "zh-CN-XiaoyiNeural",      # 女声
    "yunjian": "zh-CN-YunjianNeural",    # 男声（沉稳）
    "yunxi": "zh-CN-YunxiNeural",        # 男声（年轻）
    "yunyang": "zh-CN-YunyangNeural",    # 男声（新闻）
    "xiaoxuan": "zh-CN-XiaoxuanNeural",  # 女声（活泼）
}

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


class VoiceEngine:
    """edge-tts 主引擎，kokoro 离线回退。"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.voice = voice
        self._kokoro = None
        self.use_offline = False  # 是否已切换到离线模式

    # ---------- 主引擎：edge-tts ----------
    async def synthesize_edge(self, text: str, voice: str | None = None) -> bytes:
        import edge_tts

        v = voice or self.voice
        t0 = time.time()
        communicate = edge_tts.Communicate(text, v)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        data = buf.getvalue()
        log.info("edge-tts 合成「%.20s…」耗时 %.1fs", text, time.time() - t0)
        return data

    # ---------- 备选引擎：kokoro 离线 ----------
    def _load_kokoro(self):
        if self._kokoro is None:
            from kokoro_onnx import Kokoro

            self._kokoro = Kokoro(
                str(MODEL_DIR / "kokoro-v1.0.int8.onnx"),
                str(MODEL_DIR / "voices-v1.0.bin"),
            )
        return self._kokoro

    def synthesize_kokoro(self, text: str) -> bytes:
        import numpy as np
        import soundfile as sf

        kokoro = self._load_kokoro()
        t0 = time.time()
        samples: np.ndarray
        samples, sr = kokoro.create(text, voice="zf_xiaobei", speed=1.0, lang="zh")
        buf = io.BytesIO()
        sf.write(buf, samples, sr, format="WAV")
        log.info("kokoro 离线合成「%.20s…」耗时 %.1fs", text, time.time() - t0)
        return buf.getvalue()

    # ---------- 统一入口 ----------
    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """返回 MP3（edge-tts）或 WAV（kokoro）。失败时自动降级。"""
        if not self.use_offline:
            try:
                return await self.synthesize_edge(text, voice)
            except Exception as e:
                log.warning("edge-tts 失败(%s)，切换到 kokoro 离线模式", str(e)[:60])
                self.use_offline = True
        # 离线模式：kokoro 为纯 CPU，避免阻塞事件循环
        return await asyncio.to_thread(self.synthesize_kokoro, text)


_engine: VoiceEngine | None = None


def get_voice() -> VoiceEngine:
    global _engine
    if _engine is None:
        _engine = VoiceEngine()
    return _engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio

    data = asyncio.run(get_voice().synthesize("你好，我是你的赛博数字人小贝。很高兴认识你。"))
    out = Path("test_edge.wav")
    out.write_bytes(data)
    print(f"已生成 {out}，{len(data)//1024}KB，格式: edge-tts mp3" if data[:3] == b"ID3" else f"已生成 {out}，{len(data)//1024}KB")

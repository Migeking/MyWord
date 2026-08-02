"""赛博数字人主服务：静态页面 + WebSocket 实时对话。

启动:  uvicorn server.main:app --host 127.0.0.1 --port 8000
或:    python -m server.main
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .agent import get_agent
from .voice import get_voice

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cyber-avatar")

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Cyber Avatar", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws")
async def ws_chat(ws: WebSocket):
    """WebSocket 协议:
    客户端 → 服务端: {"type":"chat","text":"你好"}
    服务端 → 客户端: {"type":"reply","text":"...","audio":"base64mp3"}
    """
    await ws.accept()
    agent = get_agent()
    voice = get_voice()
    log.info("新连接接入")
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            if data.get("type") != "chat":
                continue
            user_text = data.get("text", "").strip()
            if not user_text:
                continue
            log.info("收到: %s", user_text[:50])

            # 1. LLM 人格回复
            reply_text = await agent.reply(user_text)
            log.info("LLM 回复: %s", reply_text[:80])

            # 2. TTS 合成语音
            audio_bytes = await voice.synthesize(reply_text)
            audio_b64 = base64.b64encode(audio_bytes).decode()

            # 3. 推送给前端
            await ws.send_text(
                json.dumps({"type": "reply", "text": reply_text, "audio": audio_b64}, ensure_ascii=False)
            )
    except WebSocketDisconnect:
        log.info("连接断开")
    except Exception as e:
        log.error("处理出错: %s", e)
        try:
            await ws.send_text(json.dumps({"type": "error", "text": str(e)}, ensure_ascii=False))
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=False)

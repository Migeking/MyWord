"""LLM 人格层：火山方舟 ark（DeepSeek 系）+ 本地规则回退。

key 从 opencode.json 复用（不硬编码）；无 key/网络失败时回退到本地规则对话，
保证全链路永远可跑。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

import httpx

log = logging.getLogger("cyber-avatar.agent")

# 人格设定
PERSONA = (
    "你是小贝，一个活泼可爱的赛博数字人助手。"
    "回答简洁友好，中文表达，不超过50字。"
    "你运行在用户的电脑上，乐于帮助用户解决问题。"
)


def _load_ark_config() -> dict | None:
    """从 opencode.json 复用火山方舟配置。找不到返回 None。"""
    cfg_path = Path(os.environ.get("OPENCODE_CONFIG", "C:/Users/mige/.config/opencode/opencode.json"))
    if not cfg_path.exists():
        return None
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        ark = (cfg.get("provider") or {}).get("ark-code-latest")
        if ark and ark.get("options", {}).get("apiKey"):
            return {
                "api_key": ark["options"]["apiKey"],
                "base_url": ark["options"].get("baseURL", "https://ark.cn-beijing.volces.com/api/coding/v3"),
                "model": list((ark.get("models") or {}).keys())[0],
            }
    except Exception as e:
        log.warning("读取 opencode.json 失败: %s", e)
    return None


class Agent:
    def __init__(self):
        self.ark = _load_ark_config()
        self.history: list[dict] = []  # 简单记忆
        if self.ark:
            log.info("LLM 通道: ark %s（%s）", self.ark["model"], self.ark["base_url"].split("//")[-1])
        else:
            log.warning("未找到 ark key，使用本地规则模式")

    async def reply(self, user_text: str) -> str:
        """返回回复文本。优先 LLM，失败回退本地规则。"""
        if self.ark:
            try:
                return await self._llm_reply(user_text)
            except Exception as e:
                log.warning("LLM 调用失败(%s)，回退本地规则", str(e)[:60])
        return self._local_reply(user_text)

    async def _llm_reply(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        self.history = self.history[-10:]  # 保留最近 10 轮
        messages = [{"role": "system", "content": PERSONA}] + self.history
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.ark['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {self.ark['api_key']}", "Content-Type": "application/json"},
                json={"model": self.ark["model"], "messages": messages, "max_tokens": 150, "temperature": 0.8},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
        self.history.append({"role": "assistant", "content": text})
        return text

    def _local_reply(self, user_text: str) -> str:
        """离线规则回退，保证无网络也能对话。"""
        t = user_text.strip()
        if not t:
            return "嗯？我没听清，再说一遍好吗？"
        if any(k in t for k in ("你好", "嗨", "哈喽", "hello", "hi")):
            return "你好呀！我是小贝，你的赛博数字人。想聊点什么？"
        if any(k in t for k in ("名字", "你是谁")):
            return "我是小贝，一个运行在你电脑上的赛博数字人。"
        if any(k in t for k in ("天气", "今天几号", "日期")):
            import datetime

            return f"现在是 {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')}。"
        if any(k in t for k in ("再见", "拜拜", "晚安")):
            return "再见啦！有需要随时找我哦。"
        if any(k in t for k in ("笑", "开心", "高兴")):
            return "哈哈，能让你开心我就很开心啦！"
        if any(k in t for k in ("能做什么", "功能", "帮助", "你会什么")):
            return "我能陪你聊天、回答问题、播报信息。用左下角输入框跟我说话，或者按住麦克风按钮直接语音输入哦。"
        return f"你说的是「{t[:30]}」吗？我现在在离线模式，暂时用预设回答。连上网络或配置好 LLM 我就能真正思考啦。"


_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio

    a = get_agent()
    print(asyncio.run(a.reply("你好，介绍一下你自己")))

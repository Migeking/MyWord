"""
Browser Use 安装测试脚本
使用 Ollama 本地模型 (qwen3.5:4b) 进行浏览器自动化测试
"""
import asyncio
import json
import sys
from browser_use import Agent, ChatOllama

async def test_basic():
    print("=" * 60)
    print("Browser Use 功能测试")
    print("=" * 60)
    
    # 使用 Ollama 本地模型 (qwen2.5vl:3b 已验证可运行)
    llm = ChatOllama(
        model="qwen2.5vl:3b",
        ollama_options={"num_ctx": 8192},
    )
    print(f"[✓] LLM 初始化完成: qwen2.5vl:3b")
    
    # 简单任务：打开网页获取标题
    task = "打开 https://www.baidu.com，告诉我页面的标题是什么"
    
    print(f"\n[→] 执行任务: {task}")
    
    agent = Agent(
        task=task,
        llm=llm,
        use_vision=False,  # 本地模型不支持视觉
    )
    
    try:
        result = await agent.run()
        print(f"\n[✓] 任务完成!")
        print(f"最终结果: {result}")
        return True
    except Exception as e:
        print(f"\n[✗] 任务失败: {e}")
        return False

async def main():
    success = await test_basic()
    print("\n" + "=" * 60)
    print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
    print("=" * 60)
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

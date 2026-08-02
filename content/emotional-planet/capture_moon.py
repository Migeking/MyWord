"""
情绪月球视频录制脚本
使用 Playwright + FFmpeg 管道流式传输生成视频
"""

import asyncio
import subprocess
import os
from pathlib import Path

# ==== 视频配置 ====
FPS = 60
DURATION = 60
TOTAL_FRAMES = FPS * DURATION
WIDTH = 1080
HEIGHT = 1440

# 文件路径
PROJECT_ROOT = Path("D:/code/MyWord")
OUTPUT_DIR = PROJECT_ROOT / "content" / "emotional-planet"
OUTPUT_VIDEO = OUTPUT_DIR / "emotional_moon.mp4"
HTML_PATH = OUTPUT_DIR / "index.html"
BGM_PATH = PROJECT_ROOT / "scripts" / "assets" / "bgm" / "Tranquility Base.mp3"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def capture_and_build():
    print(f"[RENDER] Start: {WIDTH}x{HEIGHT} @ {FPS}fps, {DURATION}s")
    print(f"[OUTPUT] File: {OUTPUT_VIDEO}")
    print(f"[BGM] {BGM_PATH.name}")

    # FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-r', str(FPS),
        '-i', '-',

        # 添加 BGM
        '-i', str(BGM_PATH),
        '-c:a', 'aac',
        '-b:a', '192k',

        # 视频编码
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '23',

        # 音视频时长对齐
        '-shortest',

        str(OUTPUT_VIDEO)
    ]

    # 打开 FFmpeg 进程
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

            # 加载页面
            html_url = f"file:///{HTML_PATH.as_posix()}"
            print(f"[PAGE] Loading: {html_url}")
            await page.goto(html_url)

            # 等待字体和资源加载
            await page.wait_for_timeout(5000)

            print("[CAPTURE] Recording frames...")

            for i in range(TOTAL_FRAMES):
                # 驱动进度
                progress = i / TOTAL_FRAMES
                await page.evaluate(f"window.__renderFrameAt({progress})")

                # 截图 (JPEG 格式更快)
                buffer = await page.screenshot(type='jpeg', quality=90)

                # 写入 FFmpeg
                process.stdin.write(buffer)

                # 进度显示
                if i % 100 == 0:
                    percent = (i / TOTAL_FRAMES) * 100
                    print(f"   Progress: {i}/{TOTAL_FRAMES} ({percent:.1f}%)")

            await browser.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        raise
    finally:
        # 关闭输入流
        process.stdin.close()
        # 等待 FFmpeg 完成
        process.wait()

    print(f"[DONE] Video saved: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    asyncio.run(capture_and_build())

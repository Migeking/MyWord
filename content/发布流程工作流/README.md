# 小红书视频发布流水线 - 工作流文档

> 本文档供 AI Agent 阅读，完成：源内容 → 视频制作。
>
> **Pipeline A（GSAP 动画截图 + BGM）**：Step 0 → Step 1 → Step 2 → Step 3（BGM 选曲）→ Step 4
> **Pipeline B（HyperFrames 高清+TTS 配音）**：Step 0 → Step B1 → B2 → B3 → B4 → B5 → B6 → Step 4
> **Pipeline C（Kinetic Typography + ChatTTS 逐词动效）**：详见 `skills/kinetic-typography/SKILL.md`
>
> **默认使用 Pipeline A，分辨率优先 1080×1440（3:4 竖版），必须带 BGM。**

---

## 环境清单

| 工具 | 要求 | 检查命令 |
|---|---|---|
| Python | 3.8+ | `python --version` |
| Node.js (Pipeline B) | 18+ | `node --version` |
| Playwright | 已安装 | `pip show playwright` |
| FFmpeg | 已安装 | `ffmpeg -version` |


**首次环境配置（如缺失）：**
```powershell
# 1. 安装 Python 包（使用清华源加速）
pip install playwright requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 验证 FFmpeg
ffmpeg -version


```

---

## Step 0：环境检查

```powershell
# 验证 FFmpeg
ffmpeg -version
```

**预期输出：** 显示 FFmpeg 版本信息。

---

## Step 1：创建动画幻灯片 HTML

### 1.1 理解源内容

读取 `小红书笔记/` 目录下的源 Markdown 文件，分析其结构：
- 文章标题（hero 区域）
- 章节数（约 8-13 个主要 section）
- 每个章节的核心观点、金句、数据

### 1.2 创建动画 HTML

**文件路径：** `xhs-output/[文章名]_animated.html`

**⚠️ 分辨率要求：至少 1080×1440 px（小红书 3:4 竖版标准）。** 旧版 390×844 已废弃，画面过于模糊。

**技术规范：**
| 参数 | 值 |
|------|-----|
| 画布尺寸 | **1080×1440 px**（3:4 竖版，小红书视频推荐比例）|
| 动画引擎 | GSAP 3.x（CDN 引入） |
| 字体 | PingFang SC / Microsoft YaHei |
| 配色 | 深色背景（#0a0e17）+ 品牌橙色（#ff6b35）+ 渐变 |
| 总时长 | ~35s（13 张 slide，每张 2.5-3s）|
| 总帧数 | 350 帧（@10fps）|
| 视频码率 | CRF 18（高质量） |

**关键设计原则：**
- 1080×1440 是 3:4 比例（和 390×844 比例相同），不是等比例缩放
- 字体大小约为 390p 版本的 2.7x（宽度比例）
- 1080p 有更多水平空间，可利用双栏布局（可选）
- 标题 font-size: ~52-56px，正文 ~24-26px

**GSAP 动画配置（关键）：**
```javascript
// 每个 slide 停留 2.5-3 秒后切换
// 每张 slide 有 0.5 秒的进入动画（fade + translateY）
// 使用 timeline.repeat(-1) 实现无限循环
// 总时长 = 13 slides × ~2.7s ≈ 35 秒
// 帧率 = 10fps → 共 350 帧
```

**HTML 模板（1080×1440 版本）：**
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080, initial-scale=1.0">
<title>文章标题</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;
     background:#0a0e17;color:#fff;overflow:hidden;
     width:1080px;height:1440px;position:relative}
.slide{position:absolute;top:0;left:0;width:1080px;height:1440px;
       padding:90px 80px;display:flex;flex-direction:column;
       opacity:0;pointer-events:none}

/* 工业风格背景网格 */
.bg-grid{position:absolute;top:0;left:0;width:100%;height:100%;
         background-image:
           linear-gradient(rgba(255,107,53,0.04) 1px,transparent 1px),
           linear-gradient(90deg,rgba(255,107,53,0.04) 1px,transparent 1px);
         background-size:60px 60px;pointer-events:none}
.corner-bracket{position:absolute;width:48px;height:48px;
                border-color:rgba(255,107,53,0.25);border-style:solid}
.corner-bracket.tl{top:30px;left:30px;border-width:3px 0 0 3px}
.corner-bracket.tr{top:30px;right:30px;border-width:3px 3px 0 0}
.corner-bracket.bl{bottom:30px;left:30px;border-width:0 0 3px 3px}
.corner-bracket.br{bottom:30px;right:30px;border-width:0 3px 3px 0}
.status-bar{position:absolute;top:0;left:0;right:0;height:4px;
            background:linear-gradient(90deg,#ff6b35,#ff9a56,#ff6b35);
            background-size:200% 100%;z-index:100}

/* 文字样式 */
.title-main{font-size:56px;font-weight:900;color:#fff;line-height:1.2;margin-bottom:16px}
.title-sub{font-size:26px;color:rgba(255,255,255,0.5);line-height:1.5}
.section-title{font-size:42px;font-weight:800;color:#fff;line-height:1.3;margin-bottom:10px}
.body-text{font-size:24px;color:rgba(255,255,255,0.65);line-height:1.8}
.highlight-text{font-size:26px;color:#ff6b35;font-weight:600;line-height:1.5}
.cta-text{font-size:34px;font-weight:700;color:#fff;line-height:1.4;text-align:center}
.tag{display:inline-block;background:rgba(255,107,53,0.08);
     border:1px solid rgba(255,107,53,0.15);color:#ff9a56;
     border-radius:4px;padding:4px 16px;font-size:18px;margin:2px}
.tag-blue{background:rgba(74,143,231,0.08);
          border-color:rgba(74,143,231,0.15);color:#6ba5ff}
.divider{width:70px;height:3px;background:linear-gradient(90deg,#ff6b35,transparent);margin:14px 0 24px}
.scroll-content{flex:1;overflow:hidden;display:flex;flex-direction:column;justify-content:center}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
<!-- 幻灯片内容：约 13 张 slide -->
<div class="slide" id="s1">...</div>
<!-- ... -->
<script>
const tl = gsap.timeline({repeat: -1, paused: false});
const durations = [3.0, 3.0, 3.5, 3.0, 2.5, 2.5, 2.5, 3.0, 2.5, 2.5, 2.5, 3.0, 3.0];
const totalSlides = durations.length;
for(let i=1; i<=totalSlides; i++){
  const prev = i===1 ? totalSlides : i-1;
  const stay = durations[i-1] || 2.5;
  tl.to('#s'+prev, {opacity:0, pointerEvents:'none', duration:0.3}, '+=0')
    .fromTo('#s'+i, {opacity:0, y:40}, {opacity:1, y:0, pointerEvents:'auto', duration:0.5, ease:'power2.out'})
    .to({}, {duration: stay - 0.8});
}
</script>
</body>
</html>
```

---

## Step 2：Playwright 截图

### 2.1 检查/修改截图脚本

**文件路径：** `capture_xhs_frames.py`

**脚本要点（每次使用时需修改）：**
1. `html_path`：指向 Step 1 创建的 HTML 文件
2. `viewport`：设置为 `{"width": 1080, "height": 1440}`（与 HTML 画布匹配）
3. `total_frames`：= 视频总时长（s）× 10fps（如 35s = 350 帧）

```python
"""Capture frames: open animated HTML, screenshot at 10fps."""
import asyncio
import os
import glob

async def capture():
    from playwright.async_api import async_playwright

    # ⚠️ 修改为当前文章的 HTML 路径
    html_path = os.path.abspath("D:/code/MyWord/xhs-output/文章名_animated.html")
    slides_dir = os.path.abspath("D:/code/MyWord/xhs-output/slides")
    os.makedirs(slides_dir, exist_ok=True)

    # Clean old frames
    for f in glob.glob(os.path.join(slides_dir, "*.png")):
        os.remove(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security"]
        )
        # ⚠️ 1080×1440 视口
        page = await browser.new_page(viewport={"width": 1080, "height": 1440})
        await page.goto(f"file:///{html_path.replace(chr(92), '/')}")
        await page.wait_for_timeout(4000)  # Wait for fonts + GSAP init

        total_frames = 350  # ⚠️ 35s @ 10fps

        print(f"Capturing {total_frames} frames at 10fps...")
        for i in range(total_frames):
            frame_path = os.path.join(slides_dir, f"frame_{i:04d}.png")
            await page.screenshot(path=frame_path)
            if i % 35 == 0:
                print(f"  [{i}/{total_frames}] captured")
            if i < total_frames - 1:
                await asyncio.sleep(0.1)  # 10fps = 0.1s interval
        print(f"  [{total_frames}/{total_frames}] captured")

        await browser.close()

    files = glob.glob(os.path.join(slides_dir, "frame_*.png"))
    print(f"\nDone! Total frames: {len(files)}")

asyncio.run(capture())
```

### 2.2 执行

```powershell
cd D:\code\MyWord
python capture_xhs_frames.py
```

**预期：** 350 张 PNG 截图保存在 `xhs-output/slides/`

---

## Step 3：BGM 选曲与下载

### 3.1 选曲原则

根据文章主题选择 BGM 风格。Kevin MacLeod 的精选曲目按氛围分组：

| 主题 | 推荐曲目 | 风格 |
|------|---------|------|
| 工业/科技/管理 | Concentration, New Direction, Sovereign | 现代、专业、沉稳 |
| 商业/财经/思维 | Clean Soul, Ebbs and Flows, Almost in F | 干练、流畅 |
| 励志/成长/故事 | Touching Story, Soaring, Infinite Perspective | 温暖、向上 |
| 知识/教育/科普 | Fluidscape, Ambiment, Perspectives | 中性、专注 |
| 冥想/心理/哲学 | Stoic Morning, Inner Light, Calm | 柔和、内省 |

### 3.2 列出所有可用 BGM

```powershell
cd D:\code\MyWord\scripts
python download_bgm.py --list
```

输出 67 首精选 CC0 氛围音乐，来源：Incompetech (Kevin MacLeod, CC BY 4.0)。

### 3.3 下载 BGM

```powershell
# 下载所有精选曲目（首次使用）
cd D:\code\MyWord\scripts
python download_bgm.py

# 下载完成后检查文件
Get-ChildItem "D:\code\MyWord\scripts\assets\bgm"
```

曲目保存到 `D:\code\MyWord\scripts\assets\bgm\`。BGM 通常在 50-300s 长度，足以循环覆盖 35s 视频。

### 3.4 署名要求

所有曲目来自 Kevin MacLeod (incompetech.com)，CC BY 4.0 许可。
在视频简介末尾添加：
```
Music: Kevin MacLeod (incompetech.com) - Licensed under CC BY 4.0
```

---

## Step 4：FFmpeg 合成视频 + BGM

### 4.1 合成命令

```powershell
cd D:\code\MyWord

ffmpeg -y -framerate 10 -i "xhs-output\slides\frame_%04d.png" `
  -i "scripts\assets\bgm\选中的曲目.mp3" `
  -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 `
  -vf "scale=1080:1440:force_original_aspect_ratio=decrease,`
       pad=1080:1440:(ow-iw)/2:(oh-ih)/2:color=#0a0e17" `
  -c:a aac -b:a 128k -shortest -af "volume=0.15" `
  "xhs-output\文章名_1080p.mp4"
```

**参数说明：**
| 参数 | 值 | 含义 |
|------|-----|------|
| `-framerate 10` | 10fps | 与截图帧率一致 |
| `-crf 18` | 高质量 | CRF 越低画质越好（18-23 选） |
| `-preset medium` | 平衡 | 编码速度/压缩比平衡 |
| `volume=0.15` | BGM 音量 15% | 背景音不宜过大 |
| `-shortest` | — | 视频长度对齐最短流（35s） |

### 4.2 验证输出

```powershell
ffprobe -v error -show_entries format=size,duration:stream=width,height,codec_name `
  -of default=noprint_wrappers=1 "xhs-output\文章名_1080p.mp4"
```

**预期输出：**
- codec_name=h264（视频）+ aac（音频）
- width=1080, height=1440
- duration=35.000000
- size≈2-5MB（XHS 上传限制 4GB，足够）

### 4.3 清理旧文件（可选）

```powershell
# 删除旧版低清文件
Remove-Item "xhs-output\output_video.mp4" -ErrorAction SilentlyContinue
Remove-Item "xhs-output\video.mp4" -ErrorAction SilentlyContinue
```

---

## 常见问题

### Q1: 视频分辨率不够高清
**原因：** 创建 HTML 时用了 390×844（旧规范）。

**解决：** 必须使用 **1080×1440**（3:4）。FFmpeg 也需输出同等分辨率。

### Q2: BGM 下载太慢
**原因：** Incompetech 服务器在国外，54MB 大文件需 5-10 分钟。

**解决：** 
- 使用 `curl -L -r 0-5000000` 只下载前 5MB（足够 35s 循环）
- 或先下载 1-2 首常用曲目缓存（Fluidscape / Concentration）
- 下载完成后用 `ffprobe` 确认 Duration > 35s 即可

### Q3: 视频大小超过限制
**解决：** 小红书支持最大 4GB，1080p @35s 通常只有 2-5MB，无需压缩。

### Q4: `UnicodeEncodeError` / 乱码
**原因：** Windows 中文环境编码问题。

**解决：** 所有文件路径使用英文/ASCII，写文件用 UTF-8 编码。

---

## 关键文件路径

| 文件 | 路径 |
|---|---|
| 源文章 | `D:\code\MyWord\小红书笔记\[文章名].md` |
| 动画 HTML（1080p） | `D:\code\MyWord\xhs-output\[文章名]_animated.html` |
| 截图帧目录 | `D:\code\MyWord\xhs-output\slides\frame_%04d.png` |
| 输出视频（1080p） | `D:\code\MyWord\xhs-output\[文章名]_1080p.mp4` |
| 截图脚本 | `D:\code\MyWord\capture_xhs_frames.py` |
| BGM 下载脚本 | `D:\code\MyWord\scripts\download_bgm.py` |
| BGM 目录 | `D:\code\MyWord\scripts\assets\bgm\` |

---

## 执行时间参考

| 步骤 | 耗时 |
|---|---|
| Step 1 创建动画 HTML（1080×1440） | ~5 分钟 |
| Step 2 Playwright 截图（350 帧 @ 10fps） | ~1 分钟 |
| Step 3 BGM 选曲下载 | ~3-10 分钟（首次）/ ~10 秒（已缓存） |
| Step 4 FFmpeg 合成视频 + BGM | ~10 秒 |
| **总计** | **约 10-20 分钟** |

---

# Pipeline B：HyperFrames 高清视频 + TTS 语音旁白

> 使用 HyperFrames + Edge TTS 生成 1080×1920 竖版高清视频含中文语音旁白。
>
> **执行顺序：Step B1 → B2 → B3 → B4 → B5**

**Pipeline A vs B vs C 选择建议：**

| 维度 | Pipeline A（GSAP 截图流） | Pipeline B（HyperFrames 渲染流） | Pipeline C（Kinetic Typography） |
|------|--------------------------|-------------------------------|----------------------------------|
| 视频尺寸 | **1080×1440（高清 3:4）** | 1080×1920（全屏 9:16） | **1080×1920（全屏 9:16）** |
| 配音 | BGM（CC0 背景音乐） | Edge TTS 中文旁白 + 可选 BGM | **ChatTTS 逐段配音** + BGM |
| 文字动效 | 整页切换 | 整页切换 | **逐词弹入（Kinetic Typography）** |
| 画面风格 | 工业风/品牌橙 | 深色渐变 | **深色科技风（蓝/绿/橙色板）** |
| TTS 引擎 | — | Edge TTS | **ChatTTS（固定 seed 同声线）** |
| 渲染方式 | Playwright 截图 + FFmpeg | HyperFrames | **HyperFrames** |
| 生成速度 | ~15 分钟 | ~30-45 分钟 | ~30-45 分钟 |
| 适用场景 | 快速出片、无旁白 | 配音+通用画面 | **观点/金句类、视觉冲击力优先** |

---

## 环境清单（额外依赖）

| 工具 | 要求 | 检查命令 |
|---|---|---|
| Node.js | 18+ | `node --version` |
| HyperFrames CLI | 已安装 | `npx hyperframes --version` |
| Edge TTS | 已安装 | `pip show edge-tts` |

**首次环境配置：**
```powershell
# 1. 安装 HyperFrames CLI
npm install -g @heygen/hyperframes

# 2. 安装 Edge TTS 依赖
pip install edge-tts pydub

# ⚠️ 不要安装/使用 kokoro-onnx，所有 zf_/zm_ 中文声音发音都不标准
```

---

## Step B1：创建 HyperFrames 项目

```powershell
# 创建项目目录
mkdir "D:\code\MyWord\xhs-output\[文章名]-video"
cd "D:\code\MyWord\xhs-output\[文章名]-video"

# 初始化 HyperFrames 项目
npx hyperframes init .
```

**项目结构：**
```
xhs-output/[文章名]-video/
├── index.html          # 主合成文件（root timeline）
├── meta.json           # 项目元数据
├── compositions/       # 子合成（可选，复杂视频分拆）
└── assets/             # 媒体文件（图片、音频、字体）
```

---

## Step B2：设计幻灯片 HTML

### 2.1 技术规范

**文件路径：** `D:\code\MyWord\xhs-output\[文章名]-video\index.html`

| 参数 | 值 |
|------|-----|
| 画布尺寸 | 1080 × 1920 px（竖版全屏） |
| 动画引擎 | GSAP 3.x（CDN: cdnjs.cloudflare.com） |
| 展示时长 | 每页 4-8 秒（根据配音时长决定） |
| 总时长 | 8-12 页 × 5s = 40-60 秒 |
| 背景 | `data-composition-id="main"` + `data-width="1080" data-height="1920"` |

**关键模板结构：**
```html
<!DOCTYPE html>
<html lang="zh-CN" data-composition-id="main" data-width="1080" data-height="1920">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1920, initial-scale=1.0">
  <title>文章标题</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 1080px; height: 1920px; overflow: hidden; font-family: 'Microsoft YaHei','PingFang SC',sans-serif; color: #fff; }
    .clip { position: absolute; opacity: 0; will-change: transform, opacity; }
    .slide { position: absolute; top: 0; left: 0; width: 1080px; height: 1920px;
             display: flex; flex-direction: column; justify-content: center;
             align-items: center; padding: 80px; }
  </style>
</head>
<body>
  <!-- HyperFrames 规则：
       1. 每个可见元素需要 class="clip" + data-start + data-duration + data-track-index
       2. GSAP timeline 必须 paused=true 并注册到 window.__timelines
       3. 只能用确定逻辑（无 Date.now / Math.random / 网络请求） -->
</body>
</html>
```

### 2.2 幻灯片时序设计

**每页的典型时间轴：**
```
0.0s - 前页淡出
0.3s - 当前页标题淡入（clip, data-start="0.3", data-duration="0.5"）
0.8s - 当前页正文淡入（clip, data-start="0.8", data-duration="0.5"）
1.3s - 关键数据/金句弹出（clip, data-start="1.3", data-duration="0.4"）
2.0s - 配音开始（audio 元素，data-start 对应 slide 的起始时间 + 0.3s 偏移）
5.0s - 配音结束 → 切下一页
```

---

## Step B3：生成 TTS 配音

### 3.1 准备配音脚本

将旁白文本保存到一个文件中：

```
pages/script.txt  # 完整旁白文本
```

### 3.2 生成语音（仅 Edge TTS）

**⚠️ 重要：只使用 Edge TTS 引擎。不要用 kokoro-onnx（`zf_`/`zm_` 系列声音发音不标准）。**

```powershell
# 女声 - 温暖标准（推荐）
python tts.py pages/script.txt -o assets/voiceover.mp3 --engine edge -v zh-CN-XiaoxiaoNeural

# 男声 - 阳光自然
python tts.py pages/script.txt -o assets/voiceover.mp3 --engine edge -v zh-CN-YunxiNeural

# 男声 - 专业沉稳（适合知识类）
python tts.py pages/script.txt -o assets/voiceover.mp3 --engine edge -v zh-CN-YunyangNeural

# 快速语速
python tts.py pages/script.txt -o assets/voiceover.mp3 --engine edge -v zh-CN-XiaoxiaoNeural --rate +15%
```

### 3.3 Edge TTS 声音参考

| 声音 | 性别 | 风格 | 说明 |
|------|------|------|------|
| `zh-CN-XiaoxiaoNeural` | 女 | 温暖 | 首选中文女声 |
| `zh-CN-YunxiNeural` | 男 | 阳光 | 首选中文男声 |
| `zh-CN-YunyangNeural` | 男 | 专业 | 知识/科技类 |
| `zh-CN-XiaoyiNeural` | 女 | 活泼 | 轻松话题 |

### 3.4 可选：加 BGM（仅当用户明确要求）

先使用 `download_bgm.py` 从 Incompetech 下载合适的 CC0 背景音乐（详见 Pipeline A Step 3）：

```powershell
# 列出所有可用 BGM（67 首精选氛围音乐）
python scripts/download_bgm.py --list

# 下载指定曲目
# ⚠️ download_bgm.py 下载全部精选曲目，不支持单首。用 curl 下载单首：
curl -L "https://incompetech.com/music/royalty-free/mp3-royaltyfree/曲目名.mp3" `
  -o "D:\code\MyWord\scripts\assets\bgm\曲目名.mp3"
```

下载后混入配音：

```powershell
python tts.py pages/script.txt -o assets/voiceover.mp3 --engine edge -v zh-CN-XiaoxiaoNeural --bgm assets/bgm/曲目.mp3 --bgm-volume 0.12
```

---

## Step B4：集成音频到幻灯片

### 4.1 添加 Audio 元素

在 `index.html` 的 `<body>` 末尾添加 `<audio>` 元素：

```html
<!-- 配音 track：每段音频对应一个 slide -->
<audio class="clip" data-start="0.3" data-duration="5.2" data-track-index="2" src="assets/slide-01.wav"></audio>
<audio class="clip" data-start="5.5" data-duration="4.8" data-track-index="2" src="assets/slide-02.wav"></audio>
<audio class="clip" data-start="10.3" data-duration="6.1" data-track-index="2" src="assets/slide-03.wav"></audio>
<!-- ... 每页一段 -->
```

**时序计算规则：**
- `data-start` = 前一段的 `data-start` + 前一段 `data-duration`
- `data-duration` = 该音频文件的实际时长（秒）
- `data-track-index` = 统一用 `2`（音频 track）
- 音频 `data-start` 应比对应 slide 的视觉开始时间晚 **0.3s**（待幻灯片淡入完成后播放）

### 4.2 GSAP 时间轴与配音同步

```javascript
window.__timelines = window.__timelines || {};
window.__timelines["main"] = gsap.timeline({ paused: true });

// 每页动画：前页淡出 → 本页淡入 → 等待配音完成
slides.forEach((slide, i) => {
  const prevExit = i === 0 ? 0 : durations[i-1] + 0.3;
  const currentStart = prevExit + 0.3;
  tl.to(slide, { opacity: 1, duration: 0.5 })
    .to(slide, { opacity: 0, duration: 0.5 }, `+=${slideDurations[i] - 0.5}`);
});
```

---

## Step B5：渲染 MP4

### 5.1 校验 + 预览

```powershell
cd "D:\code\MyWord\xhs-output\[文章名]-video"

# 校验合成文件
npx hyperframes lint .

# 预览（启动本地服务器，浏览器查看）
npx hyperframes preview .
```

### 5.2 渲染输出

```powershell
# 渲染 MP4（HyperFrames 自动合成视频 + 音频）
npx hyperframes render . --output "..\[文章名]_hyperframes.mp4"

# 检查输出
ffprobe "..\[文章名]_hyperframes.mp4"
```

**预期输出：** H.264 编码，1080×1920，30fps，含 AAC 音频流。

### 5.3 复制到标准输出路径

```powershell
Copy-Item "D:\code\MyWord\xhs-output\[文章名]_hyperframes.mp4" `
          "D:\code\MyWord\xhs-output\文章名_1080p.mp4"
```

---

## 执行时间参考（Pipeline B）

| 步骤 | 耗时 |
|---|---|
| Step B1 创建项目 | ~2 分钟 |
| Step B2 设计幻灯片 HTML | ~10 分钟 |
| Step B3 生成 TTS 语音 | ~5 分钟（含时长校准） |
| Step B4 集成音频 | ~5 分钟 |
| Step B5 渲染 MP4 | ~5-10 分钟 |
| **总计** | **约 25-35 分钟** |

---

---

# Pipeline C：Kinetic Typography 逐词弹入动效视频

> 使用 ChatTTS 逐段配音 + GSAP 逐词弹入动效 + HyperFrames 渲染的高质量竖版视频。
>
> 详细步骤文档见：`skills/kinetic-typography/SKILL.md`

**特点：**
- **1080×1920** 全屏竖版，逐词弹入动画（word-by-word pop-in）
- ChatTTS 固定 seed 生成同声线配音，每 slide 独立 WAV
- 深色科技风色板：`#0d0d1a` 背景 + 科技蓝 `#4A90D9` + 荧光绿 `#00D4AA` + 活力橙 `#FF6B35`
- BGM 通过 JS volume=0.15 控制，无需 FFmpeg 混音
- 渲染依赖 HyperFrames（同 Pipeline B）

**快速回顾（完整步骤见 skill 文档）：**

1. **分析源内容** → 拆分为 8-13 个 slide
2. **创建项目**：`npx hyperframes init .`
3. **ChatTTS 配音**：逐段生成 WAV（固定 seed）
4. **编写 HTML**：`.kt-word` 逐词弹入 + GSAP 动效
5. **配置 BGM**：Pixabay CC0 → `assets/bgm.wav` → JS volume=0.15
6. **渲染**：`npx hyperframes render . --output "..\文章名_KT_1080p.mp4"`

**执行时间：** ~30-45 分钟

**参考案例：** `xhs-output/ai-moat-video/`（AI时代最宽的护城河，8 slide，88s）

---

## 模板复用（批量生产）

```powershell
# 1. 复制模板项目
Copy-Item -Recurse "D:\code\MyWord\xhs-output\[模板名]-video" `
  "D:\code\MyWord\xhs-output\[新文章名]-video"

# 2. 替换 assets/ 下的图片资源
# 3. 修改 index.html 中的标题/正文
# 4. 重新生成 TTS 配音（步骤 B3）
# 5. 渲染
```

**批量单条耗时：** 约 15-20 分钟（模板复用后，主要时间在 TTS 生成 + 渲染）

---

## 常见问题（Pipeline B）

### Q1: HyperFrames 渲染报错

**原因：** 合成文件未通过 lint 校验 / 资源路径问题 / audio 元素配置错误。

**排查：**
```powershell
npx hyperframes lint . --verbose
```

### Q2: 配音与画面不同步

**原因：** audio `data-start` 与 GSAP timeline 的时间基准不一致。

**解决：** 每个音频的 `data-start` = slide 进入时间 + 0.3s（淡入完成后播放）。

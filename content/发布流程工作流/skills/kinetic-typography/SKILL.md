---
name: kinetic-typography
description: 小红书 Kinetic Typography 视频制作流程。用 ChatTTS 逐段配音 + GSAP 逐词弹入动效 + HyperFrames 渲染的高质量竖版视频。适用场景：观点类 / 知识类 / 金句类内容需要视觉冲击力的短视频。
---

# Kinetic Typography 视频制作

## 概述

将一篇小红书笔记 / 文章转化为 **逐词弹入（Kinetic Typography）** 风格的竖版视频：
- **Resolution**: 1080 × 1920（9:16 全屏）
- **Voiceover**: ChatTTS（固定 seed 保持同一声线），每 slide 生成独立 WAV
- **Animation**: GSAP 逐词弹入 + 强调色弹跳缩放
- **BGM**: Pixabay CC0 背景音乐，JS volume=0.15
- **Render**: HyperFrames（H.264 + AAC）

## 前置依赖

| 工具 | 检查 |
|------|------|
| Node.js 18+ | `node --version` |
| HyperFrames CLI | `npx hyperframes --version` |
| Python 3.8+ | `python --version` |
| ChatTTS | `pip show ChatTTS` |
| FFmpeg | `ffmpeg -version` |

首次安装：
```powershell
npm install -g @heygen/hyperframes
pip install ChatTTS torch soundfile
```

## 工作流

### Step 1：分析源内容

读取 `小红书笔记/` 下的 Markdown，拆分为 **8-13 个 slide**。每个 slide 对应一段独立配音。

### Step 2：创建 HyperFrames 项目

```powershell
mkdir "D:\code\MyWord\xhs-output\[文章名]-video"
cd "D:\code\MyWord\xhs-output\[文章名]-video"
npx hyperframes init .
```

### Step 3：生成 ChatTTS 配音（每 slide 独立）

参考 `chattts-seed-voice` skill。**关键：每个 slide 独立调用 `chat.infer()`，固定 seed。**

```python
import torch, ChatTTS, soundfile as sf

chat = ChatTTS.Chat()
chat.load(compile=False)

SEED = 42  # 固定 seed 保持同一声音

slides = [
    "第一页：AI时代，最宽的护城河...",
    "第二页：纽曼提出反直觉观点...",
    # ... 每页一段
]

for i, text in enumerate(slides):
    torch.manual_seed(SEED)
    wavs = chat.infer([text], use_decoder=True)
    sf.write(f"assets/chattts-slide-{i+1}.wav", wavs[0], 24000)

    # 获取时长
    duration = len(wavs[0]) / 24000
    print(f"Slide {i+1}: {duration:.1f}s")
```

音频文件输出到 `assets/chattts-slide-{n}.wav`。

### Step 4：编写 Kinetic Typography HTML

完整模板见下方 **Template 章节**。核心结构：

```html
<html data-composition-id="main" data-width="1080" data-height="1920">

<!-- 每个 slide 是 clip + slide 容器 -->
<div id="slide-1" class="clip slide" data-start="0.0" data-duration="8.1" data-track-index="1">
  <!-- kt-word: 逐词弹入 -->
  <div class="kt-word kt-hero c-white">AI时代</div>
  <div class="kt-word kt-hero c-white">最宽的护城河</div>
  <div class="kt-word kt-sm c-subtle">不是技术</div>
</div>
```

**时序计算规则：**

| 字段 | 规则 |
|------|------|
| slide `data-start` | 前一个 slide 的 start + 前一个 slide 的 duration |
| slide `data-duration` | 对应音频时长 + 0.5s |
| audio `data-start` | 对应 slide 的 start + 0.3s（等淡入完成）|
| audio `data-duration` | 音频文件实际时长 |
| BGM `data-start` | 0 |
| BGM `data-duration` | 所有 slide 总时长向上取整 |
| `data-track-index` | 1=视觉，2=配音，3=BGM |

### Step 5：配置 BGM

从 Pixabay 下载 CC0 BGM，放入 `assets/`：

```powershell
# 搜索下载（示例）
# 访问 https://pixabay.com/music/ 手动下载到 assets/bgm.wav
```

BGM 在 HTML 中设置为 volume=0.15（JS 控制）。

### Step 6：时序校验与渲染

```powershell
cd "D:\code\MyWord\xhs-output\[文章名]-video"

# 校验
npx hyperframes lint .

# 渲染
npx hyperframes render . --output "..\[文章名]_KT_1080p.mp4"

# 验证
ffprobe "..\[文章名]_KT_1080p.mp4"
```

## 模板

### 色板（Deep Tech）

| 用途 | 色值 | CSS Class |
|------|------|-----------|
| 背景 | `#0d0d1a` | — |
| 主文字 | `#FFFFFF` | `.c-white` |
| 次要文字 | `rgba(255,255,255,0.65)` | `.c-subtle` |
| 弱化文字 | `rgba(255,255,255,0.4)` | `.c-muted` |
| 强调色 | `rgba(255,255,255,0.2)` | `.c-dim` |
| 科技蓝（标签/数字） | `#4A90D9` | `.c-accent` |
| 荧光绿（核心结论） | `#00D4AA` | `.c-green` |
| 活力橙（强调） | `#FF6B35` | `.c-orange` |

### 字号比例

| Class | Size | 用途 |
|-------|------|------|
| `.kt-hero` | 96px | 封面大字 |
| `.kt-xl` | 80px | 章节标题 |
| `.kt-lg` | 64px | 核心观点 |
| `.kt-md` | 48px | 正文 |
| `.kt-sm` | 36px | 次要正文 |
| `.kt-xs` | 28px | 辅助文字 |
| `.kt-xxs` | 22px | 来源/标签 |

### 完整 index.html 骨架

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
    html, body {
      width: 1080px; height: 1920px; overflow: hidden;
      font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
      background: #0d0d1a; color: #ffffff;
    }
    .clip { position: absolute; opacity: 0; will-change: transform, opacity; }
    .slide {
      position: absolute; top: 0; left: 0;
      width: 1080px; height: 1920px;
      display: flex; flex-direction: column;
      justify-content: center; align-items: center;
      padding: 100px; background: #0d0d1a;
    }
    .kt-word { opacity: 0; will-change: transform, opacity; }
    /* --- Typography Scale --- */
    .kt-hero   { font-size: 96px; font-weight: 900; line-height: 1.15; text-align: center; }
    .kt-xl     { font-size: 80px; font-weight: 900; line-height: 1.2; text-align: center; }
    .kt-lg     { font-size: 64px; font-weight: 800; line-height: 1.3; text-align: center; }
    .kt-md     { font-size: 48px; font-weight: 700; line-height: 1.4; text-align: center; }
    .kt-sm     { font-size: 36px; font-weight: 500; line-height: 1.5; text-align: center; }
    .kt-xs     { font-size: 28px; font-weight: 400; line-height: 1.5; text-align: center; }
    .kt-xxs    { font-size: 22px; font-weight: 400; line-height: 1.5; text-align: center; }
    /* --- Palette --- */
    .c-white    { color: #FFFFFF; }
    .c-subtle   { color: rgba(255, 255, 255, 0.65); }
    .c-muted    { color: rgba(255, 255, 255, 0.4); }
    .c-dim      { color: rgba(255, 255, 255, 0.2); }
    .c-accent   { color: #4A90D9; }
    .c-green    { color: #00D4AA; }
    .c-orange   { color: #FF6B35; }
    /* --- Decorations --- */
    .deco-bar {
      width: 80px; height: 3px;
      background: linear-gradient(90deg, #4A90D9, #00D4AA);
      border-radius: 2px;
    }
    .deco-line {
      width: 240px; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(74,144,217,0.25), transparent);
    }
    .spacer-8  { height: 8px; }
    .spacer-16 { height: 16px; }
    .spacer-24 { height: 24px; }
    .spacer-32 { height: 32px; }
    .spacer-48 { height: 48px; }
    .spacer-64 { height: 64px; }
    .num-badge {
      font-size: 32px; font-weight: 700; color: #4A90D9;
      letter-spacing: 4px; margin-bottom: 8px;
    }
  </style>
</head>
<body>
<div data-composition-id="main" data-width="1080" data-height="1920" data-start="0">

  <!-- ===== SLIDE 1 ===== -->
  <div class="clip slide" data-start="0.0" data-duration="8.1" data-track-index="1">
    <div class="kt-word kt-hero c-white">标题行</div>
    <div class="spacer-16"></div>
    <div class="kt-word deco-bar"></div>
    <div class="spacer-24"></div>
    <div class="kt-word kt-sm c-subtle">次要文字</div>
  </div>
  <audio class="clip" data-start="0.3" data-duration="7.6" data-track-index="2" src="assets/chattts-slide-1.wav"></audio>

  <!-- ===== SLIDE 2+ ===== (重复模式) -->

  <!-- ===== BGM ===== -->
  <audio id="audio-bgm" class="clip" data-start="0" data-duration="88" data-track-index="3" src="assets/bgm.wav"></audio>

</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
  const clips = document.querySelectorAll(".clip");
  const tl = gsap.timeline({ paused: true });

  // Pass 1: Slide visibility
  clips.forEach(clip => {
    if (clip.tagName === 'AUDIO') return;
    const start = parseFloat(clip.dataset.start) || 0;
    const duration = parseFloat(clip.dataset.duration) || 0;
    if (duration <= 0) return;
    tl.to(clip, { opacity: 1, duration: 0.2, ease: "power1.in" }, start);
    tl.to(clip, { opacity: 0, duration: 0.3, ease: "power1.out" }, start + duration - 0.3);
  });

  // Pass 2: Kinetic Typography — word-by-word
  const slides = document.querySelectorAll(".slide");
  slides.forEach(slide => {
    const slideStart = parseFloat(slide.dataset.start) || 0;
    const words = slide.querySelectorAll(".kt-word");
    if (words.length === 0) return;

    const innerTl = gsap.timeline();
    words.forEach((word, i) => {
      const baseDelay = i * 0.25;
      innerTl.to(word, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }, baseDelay);

      // Emphasis pop for accent colors
      if (word.classList.contains("c-green") || word.classList.contains("c-orange")) {
        innerTl.fromTo(word, { scale: 0.92 }, {
          scale: 1, duration: 0.4, ease: "back.out(1.7)", clearProps: "scale"
        }, baseDelay + 0.15);
      }
    });

    tl.add(innerTl, slideStart + 0.3);
  });

  // Audio playback
  const audioClips = document.querySelectorAll("audio.clip");
  audioClips.forEach(audio => {
    const start = parseFloat(audio.dataset.start) || 0;
    const isBgm = audio.id === 'audio-bgm';
    tl.call(() => {
      audio.currentTime = 0;
      audio.volume = isBgm ? 0.15 : 1.0;
      audio.play().catch(e => console.warn("Audio play failed:", e));
    }, [], start);
  });

  // Register with HyperFrames
  const compositionId = document.querySelector('[data-composition-id]')?.dataset.compositionId || 'main';
  window.__timelines = window.__timelines || {};
  window.__timelines[compositionId] = tl;
  tl.play();
});
</script>
</body>
</html>
```

### BGM 音量调节

在 JS 中修改 `audio.volume`：
```javascript
const isBgm = audio.id === 'audio-bgm';
audio.volume = isBgm ? 0.15 : 1.0;
```

降低 BGM 即改 `0.15` 为更低值。改完后需重新渲染。

### 配音降速（如需）

```powershell
ffmpeg -i "assets/chattts-slide-1.wav" -af "atempo=0.9" "assets/chattts-slide-1.wav.tmp"
Move-Item "assets/chattts-slide-1.wav.tmp" "assets/chattts-slide-1.wav" -Force
```

批量处理：
```powershell
1..8 | ForEach-Object {
  $i = $_
  ffmpeg -y -i "assets/chattts-slide-$i.wav" -af "atempo=0.9" "assets/t.wav" && `
  Move-Item "assets/t.wav" "assets/chattts-slide-$i.wav" -Force
}
```

降速后必须重算所有 `data-start` / `data-duration`。

### BGM 搜索下载（Pixabay）

1. 访问 https://pixabay.com/music/search/
2. 按关键词搜索（ambient, cinematic, 科技感等）
3. 试听后下载为 MP3
4. 转换为 WAV：
```powershell
ffmpeg -i "下载的BGM.mp3" -acodec pcm_s16le -ar 44100 "assets/bgm.wav"
```

Pixabay 音乐为 **Pixabay License**，免费商用无需署名（如需署名：`Music: Pixabay`）。

## 常见问题

### Q1: HyperFrames 渲染报 overlapping clips

原因：audio `data-start` 或 `data-duration` 浮点精度导致相邻 clip 边缘重叠。

解决：检查每个 audio 的时序计算，确保 `data-start_N = data-start_{N-1} + data-duration_{N-1}` 严格等于。可在 slide 之间留 0.05s 间隙。

### Q2: 配音与画面不同步

原因：audio 的 `data-start` 与 slide 的 `data-start` 不匹配。

解决：audio `data-start` = slide `data-start + 0.3s`（0.3s 是淡入时间）。确保每个 audio 对应正确 slide。

### Q3: ChatTTS 每次声音不一样

原因：未固定 `torch.manual_seed()`。

解决：每次调用 `chat.infer()` 前执行 `torch.manual_seed(SEED)`，同一项目用同一 seed。

### Q4: BGM 音量不合适

修改 JS 中 `audio.volume = isBgm ? 0.15 : 1.0` 的 `0.15` 值后重新渲染。

## 执行时间参考

| 步骤 | 耗时 |
|------|------|
| Step 1 分析内容 | ~3 分钟 |
| Step 2 创建项目 | ~2 分钟 |
| Step 3 ChatTTS 配音（8-13 段） | ~5-10 分钟 |
| Step 4 编写 HTML | ~10-15 分钟 |
| Step 5 配置 BGM | ~2-5 分钟 |
| Step 6 渲染 | ~5-10 分钟 |
| **总计** | **约 30-45 分钟** |

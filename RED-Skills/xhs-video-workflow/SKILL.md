---
name: xhs-video-workflow
description: 从小红书笔记 Markdown 生成带 ChatTTS 配音的竖版 1080×1920 动画视频。触发词：小红书视频、视频流水线、笔记转视频、制作视频、配音视频。
---

# 小红书 Kinetic Typography 视频制作流水线（不含自动发布）

> 将一篇小红书笔记 Markdown 转换为带 ChatTTS 语音旁白的竖版 Kinetic Typography 动画视频（1080×1920，9:16）。
> 全流程在用户本地环境运行，**不含任何自动发布功能**，发布动作由用户手动在小红书 App / 网页端完成。

## 平台合规声明

本技能承诺：功能真实、内容原创、权限透明、无隐藏行为。

- **功能真实**：文中所有命令、参数、接口均为可实际运行的公开工具（ChatTTS、HyperFrames、ffmpeg、Edge TTS）。
- **原创性**：「工业霓虹」设计系统、分镜结构、CSS 与脚本模板均为原创内容。
- **权限透明**：仅在用户本地生成文件与调用本机命令，不收集、不上传任何用户数据，不访问网络之外的任何服务（ChatTTS 模型下载、CDN 加载除外）。
- **无隐藏行为**：不含自动发布、自动点赞、自动评论等任何平台自动化功能。
- **AI 标识**：本技能产出的视频含 AI 配音与 AI 动画，发布时须按小红书社区公约 2.0 主动标识，详见文末「AI 内容主动标识」章节。

## 依赖声明（用户自备）

> 以下环境与文件由**用户自备**，本技能不附带、不下载任何私有资源。使用前请逐项确认已安装。

| 依赖 | 版本要求 | 用途 | 安装方式（提示） |
|------|---------|------|-----------------|
| Python 3 | 3.8+ | 运行 TTS 与时长提取脚本 | 官方安装包 |
| ChatTTS（Python 包） | 0.1.x | 主配音引擎 | `pip install ChatTTS` |
| soundfile（Python 包） | 最新 | WAV 时长读取 | `pip install soundfile` |
| torch（Python 包） | CPU 版即可 | ChatTTS 推理与固定种子 | `pip install torch` |
| Node.js | 18+ | HyperFrames 渲染工具 | 官方安装包 |
| ffmpeg | 可用即可 | 视频/音频编码合成 | 官方安装包 |
| ffprobe | 随 ffmpeg 附带 | 输出验证 | 官方安装包 |
| Edge TTS（可选） | 最新 | 备选在线配音引擎 | `pip install edge-tts` |
| playwright（可选） | 最新 | HyperFrames 浏览器渲染依赖 | `pip install playwright` + 浏览器内核 |
| 背景音乐文件（可选） | MP3 格式 | BGM，用户自备 | 自行获取（注意授权协议） |

## 流水线概览

| 步骤 | 内容 | 预计耗时 |
|------|------|---------|
| Step 1 | 分析笔记内容，设计分镜脚本 | ~5 分钟 |
| Step 2 | 创建项目 + 幻灯片 HTML（GSAP + 工业霓虹设计系统） | ~15 分钟 |
| Step 3 | 使用 ChatTTS 生成逐段 WAV 配音（固定 seed=42） | ~3-5 分钟 |
| Step 4 | 从 WAV 文件提取时长 → 生成 timing.json | ~10 秒 |
| Step 5 | 集成音频到幻灯片（逐段语音 + 用户自备 BGM，音量 0.15） | ~5 分钟 |
| Step 6 | Lint 校验 + 渲染 MP4 视频 | ~5-10 分钟 |
| **总计** | | **~35-45 分钟** |

## 项目目录结构（在当前工作目录下创建）

```
xhs-output/[文章名]-video/
├── index.html              # 主合成文件（GSAP timeline + 工业霓虹设计系统）
├── meta.json               # 项目元数据（由 hyperframes init 生成）
├── timing.json             # 每段 WAV 时长（由 generate_timing.py 生成）
├── generate_tts.py         # ChatTTS 逐段配音脚本（内嵌在本文 Step 3，手动创建）
├── generate_timing.py      # WAV 时长提取脚本（内嵌在本文 Step 4，手动创建）
├── compositions/           # 子合成（可选）
└── assets/
    ├── chattts-slide-1.wav # 第 1 段配音
    ├── chattts-slide-2.wav # 第 2 段配音
    ├── ...
    └── bgm.mp3             # 背景音乐（可选，用户自备，音量 0.15）
```

## Step 0：环境检查（每次执行前必做）

```powershell
# 1. 检查依赖（逐条确认有输出、无报错）
python --version          # 需 3.8+
node --version            # 需 18+
ffmpeg -version           # 需可用
pip show ChatTTS          # 需已安装（主配音引擎）
pip show soundfile        # 需已安装（WAV 时长读取）
pip show edge-tts         # 备选配音引擎（可选）
pip show playwright       # 需已安装（可选）
npx hyperframes --version # 需已安装

# 2. 在当前工作目录创建输出根目录
# Windows PowerShell：
mkdir xhs-output
# macOS / Linux：
mkdir -p xhs-output
```

> **执行前确认用户偏好**：配音引擎（ChatTTS 或 Edge TTS）、语速、BGM 风格与是否启用 BGM。确认后再开始实现。

## Step 1：分析笔记 & 设计分镜

读取用户提供的小红书笔记 Markdown 源文件，分析结构：

- **标题**：Hero 区域的核心信息
- **开篇钩子**：吸引注意力的第一段
- **核心章节**：3-5 个主要 section，每个提炼 1 个观点
- **金句/数据**：可单独成页的强观点
- **结尾引导**：CTA + 话题标签

**分镜数量建议：** 8-13 页（每页 6-15 秒，总计 60-150 秒）

> 实际每页时长由 ChatTTS 配音时长决定。先写旁白文本 → TTS 生成 → 从 WAV 提取确切时长。

## Step 2：创建项目 + 幻灯片 HTML

### 2.1 创建项目

```powershell
# 在当前工作目录下创建项目目录
mkdir "xhs-output/[文章名]-video"
# 进入项目目录
cd "xhs-output/[文章名]-video"

# 初始化 HyperFrames 项目（可选，手动创建 index.html 也可）
npx hyperframes init .
```

### 2.2 设计幻灯片 HTML

**文件路径：** 项目目录下的 `index.html`

**技术规范：**

| 参数 | 值 |
|------|-----|
| 画布尺寸 | **1080×1920 px**（9:16 竖版） |
| 动画引擎 | GSAP 3.12+（CDN: `cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`）|
| 每页时长 | 6-15 秒（根据 ChatTTS 配音时长） |
| 总时长 | 60-150 秒（12 页左右） |
| 配色方案 | 见下方「工业霓虹」设计系统 |

---

### 🎨 工业霓虹设计系统（统一小红书审美）

#### CSS 自定义属性

```css
:root {
  --bg-dark: #080818;
  --bg-mid: #14142e;
  --bg-card: rgba(255, 255, 255, 0.03);
  --accent-blue: #4A7CFF;
  --accent-cyan: #00E5FF;
  --accent-coral: #FF5E7A;
  --accent-amber: #FFB84D;
  --accent-green: #00D4AA;
  --accent-purple: #8B7FFF;
  --text-primary: #FFFFFF;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.4);
  --glass-bg: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.06);
  --font-sans: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
}
```

#### Section 配色约定

| 章节类型 | 强调色 | 用途 |
|---------|--------|------|
| 封面/Cover | 白色 + 渐变 cyan | 大标题 |
| 问题/Problem | `--accent-coral` #FF5E7A | 痛点描述 |
| 政治/Politics | `--accent-amber` #FFB84D | 公司政治 |
| 内部客户 | `--accent-green` #00D4AA | 内部客户阐述 |
| 角色/Who | `--accent-purple` #8B7FFF | 职责划分 |
| 故事/Story | `--accent-blue` #4A7CFF | 示例/案例 |
| 列表/List | 逐个 item 独立着色 | 枚举项 |
| 结论/CTA | 金色渐变 | 金句/行动号召 |

#### 核心设计元素

1. **背景**：深空渐变 `linear-gradient(135deg, #080818, #14142e, #0a0a24)`
2. **卡片**：glass-morphism（`rgba(255,255,255,0.03)` 背景，`backdrop-filter: blur(10px)`，圆角 16px，浅色边框）
3. **大标题**：渐变文字（`background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;`）
4. **装饰元素**：
   - 发光圆点 `glow-dot`：`box-shadow: 0 0 60px ...` 随机分布
   - 光环 `glow-ring`：`border-radius: 50%` 半透明圆环
   - 网格线 `bg-grid`：`background-image: linear-gradient(...)` 暗色网格
5. **列表项**：每项左竖条彩色 accent bar（`border-left: 3px solid`），hover 上浮

#### 建议的 HTML 结构模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080, initial-scale=1.0">
<title>文章标题</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;
     font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
     background:linear-gradient(135deg,#080818,#14142e,#0a0a24);
     color:#fff;position:relative}

/* ⚠️ 关键：必须加 opacity:1，否则所有 slide 不可见（HyperFrames 渲染问题） */
.slide.clip{opacity:1!important}

.slide{position:absolute;top:0;left:0;width:1080px;height:1920px;
       padding:100px 80px;display:flex;flex-direction:column;
       opacity:0;pointer-events:none}
.slide.active{opacity:1;pointer-events:auto}

/* 首帧封面：不带 .word 类的 h1 在 GSAP 运行前即显示 */
.cover-title{font-size:72px;font-weight:900;line-height:1.3;
             background:linear-gradient(135deg,#4A7CFF,#00E5FF);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
             background-clip:text}
.cover-sub{font-size:28px;color:rgba(255,255,255,0.6);margin-top:20px}
.section-title{font-size:52px;font-weight:800;line-height:1.3;margin-bottom:12px}
.body-text{font-size:24px;color:rgba(255,255,255,0.65);line-height:1.8;margin-bottom:8px}
.highlight-text{font-size:26px;font-weight:600}
.divider{width:80px;height:3px;margin:12px 0 20px}

/* 工业霓虹元素 */
.glass-card{background:rgba(255,255,255,0.03);backdrop-filter:blur(10px);
            border:1px solid rgba(255,255,255,0.06);border-radius:16px;
            padding:36px 40px;margin-bottom:16px}
.glow-dot{position:absolute;border-radius:50%;pointer-events:none}
.bg-grid{position:absolute;top:0;left:0;width:100%;height:100%;
         background-image:
           linear-gradient(rgba(74,124,255,0.03) 1px,transparent 1px),
           linear-gradient(90deg,rgba(74,124,255,0.03) 1px,transparent 1px);
         background-size:80px 80px;pointer-events:none}
.gradient-text{background:linear-gradient(135deg,#4A7CFF,#00E5FF);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               background-clip:text}

.word{display:inline-block;opacity:0;transform:translateY(20px)}
</style>

<!-- ⚠️ GSAP 只能引用一次，不能同时在 <head> 和 <body> 中出现 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
<div class="bg-grid"></div>

<!-- Slide 1：封面（首帧即显示 → 标题不带 .word 类） -->
<div class="slide active" clip>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">
    <h1 class="cover-title">文章大标题</h1>
    <p class="cover-sub">副标题 / 作者</p>
  </div>
</div>

<!-- Slide 2-N：后续 slide -->
<!-- 内容文字中需要做 word-by-word 动画的用 <span class="word"> 包裹 -->
<div class="slide clip" data-start="13.5" data-duration="12.0" data-track-index="0">
  <div class="glass-card">
    <h2 class="section-title gradient-text" style="background:linear-gradient(135deg,#FF5E7A,#FF8A9E)">
      章节标题
    </h2>
    <div class="divider" style="background:linear-gradient(90deg,#FF5E7A,transparent)"></div>
    <p class="body-text">
      <span class="word">逐词</span>
      <span class="word">弹出</span>
      <span class="word">动画</span>
    </p>
  </div>
</div>

<!-- audio clips -->
<audio class="clip" data-start="0.3" data-duration="13.0" data-track-index="2" src="assets/chattts-slide-1.wav"></audio>
<audio class="clip" data-start="13.5" data-duration="12.0" data-track-index="2" src="assets/chattts-slide-2.wav"></audio>

<script>
const compositionId = 'main';
const masterTl = gsap.timeline({paused:true});

// Word-by-word pop-in 动画
const words = document.querySelectorAll('.word');
if(words.length > 0) {
  masterTl.to(words, {
    opacity:1, y:0, duration:0.3, stagger:0.04, ease:'back.out(1.7)',
    onComplete:() => { /* optionally seek to next */ }
  }, '>');
}

// ⚠️ flat timeline，直接赋值（不是数组包裹）
window.__timelines = window.__timelines || {};
window.__timelines[compositionId] = masterTl;
</script>
</body>
</html>
```

### 2.3 关键约束（⚠️ 不遵守将导致渲染失败）

| # | 规则 | 说明 | 违反后果 |
|---|------|------|---------|
| 1 | `.slide.clip{opacity:1!important}` | 所有 slide div 必须有此 CSS | 全部 slide 不可见（空白视频）|
| 2 | GSAP `<script>` 仅出现一次 | 不要同时在 `<head>` 和 `<body>` 引用 | 渲染器重复注入 → 动画异常 |
| 3 | 首帧封面：标题不带 `.word` 类 | 第一页的 `<h1>` 不用 span+word | 首帧空白 → 封面不好看 |
| 4 | `window.__timelines[compositionId] = masterTl` | 直接赋值，非数组包裹 | 时间线不执行 |
| 5 | 禁止动态 API | 无 `Date.now()`、`Math.random()`、网络请求 | 渲染结果不一致 |
| 6 | 所有元素 + audio 都要 `class="clip"` | 含时间属性 | 渲染器忽略未标记元素 |

## Step 3：生成 ChatTTS 逐段配音（推荐）

> 使用 ChatTTS 生成每段独立的 WAV 配音文件。
> 固定 seed（42）确保多次生成同一音色，保证整片声音一致。
> 每段配音对应一个 slide，后期便于独立调整。

### 3.1 编写 TTS 生成脚本

在项目目录下手动创建 `generate_tts.py`（内容直接取自下方代码块）：

```python
"""Generate per-slide TTS WAV files using ChatTTS with fixed seed."""
import os
import torch
import ChatTTS
import soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SEED = 42  # 固定种子：同一音色贯穿全片

chat = ChatTTS.Chat()
chat.load_models(source='huggingface')  # 首次运行会下载模型

# 定义每段旁白（内容按分镜顺序排列，数字用中文全称，如"百分之八十"）
texts = [
    "第一段旁白文本",
    "第二段旁白文本",
    # ... 共 8-13 段
]

os.makedirs('assets', exist_ok=True)

for i, text in enumerate(texts, 1):
    # ⚠️ 关键：每次 infer 前设置相同种子，保证音色一致
    torch.manual_seed(SEED)
    wav = chat.infer(text, skip_refine=True, params_infer_code={
        'prompt': '[speed_5]',  # 语速 1-9，5 为正常
        'seed': SEED
    })
    # wav shape: (1, T) 或 (T,)
    audio_data = wav[0][0] if wav[0].ndim > 1 else wav[0]
    sf.write(f'assets/chattts-slide-{i}.wav', audio_data, 24000)
    duration = len(audio_data) / 24000
    print(f'Slide {i}: {duration:.2f}s -> assets/chattts-slide-{i}.wav')

print('Done!')
```

### 3.2 执行生成

```powershell
cd "xhs-output/[文章名]-video"
python generate_tts.py
```

**预期输出：** `assets/chattts-slide-1.wav` 到 `assets/chattts-slide-N.wav`，每段对应一个 slide。

> **ChatTTS 固定音色要点**：每次 `chat.infer()` 默认会随机生成不同音色。必须在每次调用前执行 `torch.manual_seed(SEED)`（同一固定值），即可在 CPU 上复现同一音色。此方法比 `spk_smp` 参数更简单可靠。

### 3.3 备选：Edge TTS（在线配音）

> 如果 ChatTTS 不可用，或用户偏好微软语音引擎，使用 Edge TTS CLI（需联网）。

```powershell
# 方式一：从文本文件生成（推荐）
edge-tts --file "pages\script.txt" `
         --voice zh-CN-XiaoxiaoNeural `
         --rate +20% `
         --write-media "assets\voiceover.mp3"
```

**支持的语音选项：**
| 语音 | 性别 | 风格 |
|------|------|------|
| `zh-CN-XiaoxiaoNeural` | 女声 | 温柔亲切（推荐）|
| `zh-CN-YunxiNeural` | 男声 | 阳光活力 |
| `zh-CN-YunjianNeural` | 男声 | 成熟稳重 |

**然后按静音分割成逐段 WAV**（使用 `pydub` 或 Audacity 基于静音分割）。

**其他配音工具：** 用户可根据本地环境选择任意工具（GPT-SoVITS、Fish Speech 等），
输出 16bit WAV/MP3 即可，后续集成到视频合成的流程不变。

### ChatTTS 参数参考

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `seed` | 42 | 固定种子，多次生成同一音色 |
| `source` | `huggingface` | 模型来源 |
| `speed` | `5`（正常）| 1-9，数字越大越快 |
| `sample_rate` | 24000 Hz | ChatTTS 默认输出 |

## Step 4：生成 timing.json（从 WAV 提取时长）

> 每段 WAV 的时长决定了 slide 的 `data-duration` 和音频的 `data-start`。

在项目目录下手动创建 `generate_timing.py`（内容直接取自下方代码块）：

```python
"""Extract per-slide WAV durations and generate timing.json."""

import os, json, soundfile as sf

os.chdir(os.path.dirname(os.path.abspath(__file__)))

slides = []
total = 0.0

for i in range(1, 999):  # 最大 999 段
    path = f'assets/chattts-slide-{i}.wav'
    if not os.path.exists(path):
        break
    data, sr = sf.read(path)
    dur = len(data) / sr
    slides.append({
        'slide': i,
        'file': f'chattts-slide-{i}.wav',
        'duration': round(dur, 2),
        'start': round(total, 2)  # 起始时间（累计）
    })
    total += dur

timing = {
    'total_duration': round(total, 2),
    'slide_count': len(slides),
    'slides': slides
}

with open('timing.json', 'w', encoding='utf-8') as f:
    json.dump(timing, f, ensure_ascii=False, indent=2)

print(f'Generated timing.json: {len(slides)} slides, {total:.2f}s total')

# 打印每段时长（方便复制到 HTML）
for s in slides:
    audio_start = round(s['start'] + 0.3, 2)  # slide 淡入后 0.3s 播放音频
    audio_end = round(audio_start + s['duration'], 2)
    print(f'  Slide {s["slide"]:2d}: WAV={s["duration"]:6.2f}s  '
          f'audio data-start={audio_start:7.2f}  data-duration={s["duration"]:6.2f}')
```

**执行：**

```powershell
cd "xhs-output/[文章名]-video"
python generate_timing.py
```

**预期输出：** `timing.json` 包含每段 WAV 的 duration、start、累计总时长。

**timing.json 结构：**
```json
{
  "total_duration": 131.35,
  "slide_count": 12,
  "slides": [
    {"slide": 1, "file": "chattts-slide-1.wav", "duration": 13.02, "start": 0.0},
    {"slide": 2, "file": "chattts-slide-2.wav", "duration": 12.55, "start": 13.02}
  ]
}
```

## Step 5：集成音频到幻灯片

### 5.1 添加 ChatTTS 语音 audio 元素

使用 `timing.json` 的输出来设置每个 `<audio>` 元素的 `data-start` 和 `data-duration`。

在 `index.html` 的 `<body>` 末尾添加 `<audio>` 元素：

```html
<!-- audio 的 data-start = slide 进入时间 + 0.3s（等淡入完成） -->
<audio class="clip" data-start="0.3" data-duration="13.0" data-track-index="2" src="assets/chattts-slide-1.wav"></audio>
<audio class="clip" data-start="13.5" data-duration="12.0" data-track-index="2" src="assets/chattts-slide-2.wav"></audio>
```

**时序规则：**
- 每段音频的 `data-start` = 对应 slide 的 `start` + **0.3s**（等 GSAP 淡入完成）
- 每段音频的 `data-duration` = 对应 WAV 的 `duration`
- 所有语音 audio 使用相同的 `data-track-index`（如 `2`），与背景元素区分

### 5.2 准备背景音乐（BGM，用户自备）

> BGM 文件由**用户自备**，本技能不附带任何曲库。请用户自行提供合法授权的背景音乐文件。

**选曲风格建议（按内容主题）：**

| 内容主题 | 推荐风格 |
|------|---------|
| 工业/科技/管理 | 现代、专业、沉稳、科技电子感 |
| 商业/财经/思维 | 干练、流畅 |
| 励志/成长/故事 | 温暖、向上 |
| 知识/教育/科普 | 中性、专注 |
| 冥想/心理/哲学 | 柔和、内省 |

**准备步骤：**

1. 用户提供一首合法授权的 BGM 文件（MP3 格式）。
2. 将文件复制到项目 `assets` 目录，并统一命名为 `bgm.mp3`（命名规范：小写英文，`xxx.mp3` 形式，不要保留带空格的中文原名）。

```powershell
# 示例：把用户提供的 BGM 复制进项目 assets 目录
Copy-Item "用户提供的BGM文件路径\xxx.mp3" "xhs-output\[文章名]-video\assets\bgm.mp3"
```

> ⚠️ 关于授权：请使用合法获取、明确授权可商用的音乐。若使用 Kevin MacLeod（incompetech.com）的 CC BY 4.0 曲目，视频简介需署名：`"Music: Kevin MacLeod (incompetech.com) - Licensed under CC BY 4.0"`；其他来源曲目请遵循其各自的授权协议要求。

### 5.3 添加 BGM audio 元素

BGM `<audio>` 放在所有语音 audio 元素之后：

```html
<!-- bgm: data-start=0（从头播放）, loop 循环, data-volume 控制音量 -->
<audio id="audio-bgm" class="clip" data-start="0" data-duration="134.45"
       src="assets/bgm.mp3" loop preload="auto"
       data-volume="0.15"></audio>
```

**BGM 参数说明：**

| 属性 | 值 | 说明 |
|------|-----|------|
| `data-start` | `0` | 从头开始播放 |
| `data-duration` | 总视频时长（秒） | 等于最后 slide 的 start + duration |
| `data-volume` | `0.15`（推荐） | 音量 0.0-1.0，0.15 约为人声清晰可闻的背景 |
| `loop` | 必加 | BGM 文件短于视频时循环 |
| `data-track-index` | 独立音轨 | 用独立音轨（如 `3`），与语音 audio 区分 |

> ⚠️ BGM 是背景不是主角。`data-volume="0.15"` 不可省略，否则配音被 BGM 盖过。

## Step 6：渲染 MP4

### 6.1 Lint 校验

```powershell
cd "xhs-output/[文章名]-video"
npx hyperframes lint .
```

**预期：** 0 errors（可接受 warning 如 composition_file_too_large）。

### 6.2 渲染

```powershell
npx hyperframes render . --output "..\[文章名]_KT_1080p.mp4"
```

**命名规范：** `[文章名]_KT_1080p.mp4`（KT = Kinetic Typography）

### 6.3 验证

```powershell
ffprobe -v error -show_entries format=size,duration:stream=width,height,codec_name `
  -of default=noprint_wrappers=1 "..\[文章名]_KT_1080p.mp4"
```

**预期输出：**
| 属性 | 值 |
|------|-----|
| 分辨率 | 1080×1920 |
| 视频编码 | H.264 (libx264) |
| 音频编码 | AAC |
| 时长 | 配音总时长（60-150s）|
| 文件大小 | 7-10 MB（含 BGM 约更大）|

### 6.4 渲染后检查清单

- [ ] MP4 文件存在且 > 1 MB
- [ ] 视频有画面（不是纯黑/白）
- [ ] 音频同步（配音 + slide 切换时间对齐）
- [ ] BGM 音量合适（不盖过配音）
- [ ] 首帧可作为封面/缩略图

## 质量标准（风格一致性保障，20 项验收）

> 以下标准定义了"做得好"的具体要求。无论谁执行此工作流，输出必须满足以下全部条件。

### 🎯 视觉风格

| # | 检查项 | 通过标准 | 失败示例 |
|---|--------|---------|---------|
| 1 | 封面首帧即可作为缩略图 | 打开视频第一帧，标题完整可见、设计吸引人 | 首帧空白、标题用了 `.word` 类导致延迟显示 |
| 2 | 工业霓虹配色一致 | 使用 `--accent-*` 色彩变量，section 按约定配色 | 混入随机色值、颜色系统不一致 |
| 3 | 深色背景 + glass-morphism 卡片 | 所有内容卡片使用 `rgba(255,255,255,0.03)` 半透明背景 + 模糊 | 纯白/纯色卡片、无毛玻璃效果 |
| 4 | 渐变文字用于关键标题 | 封面标题、section 大标题用 `linear-gradient` 渐变 | 纯色标题、渐变颜色不匹配工业霓虹色板 |
| 5 | 每页有装饰性背景元素 | 至少包含 grid 网格线 + glow-dot 或 ring | 纯色背景、无任何装饰 |
| 6 | 列表项有彩色 accent bar | `border-left: 3px solid` + 每项独立配色 | 无装饰、纯文本列表 |

### 🔈 音频质量

| # | 检查项 | 通过标准 | 失败示例 |
|---|--------|---------|---------|
| 7 | 配音是中文且发音正确 | `80%` 读作"百分之八十"，`20%` 读作"百分之二十" | 英文发音（"eighty percent"）|
| 8 | 配音包含所有 slide，无遗漏 | 每段 WAV 对应一个 slide，N 个 slide = N 个 WAV | 漏掉某个 slide |
| 9 | BGM 不盖过配音 | `data-volume="0.15"`，BGM 在配音时清晰可闻但不抢夺注意力 | BGM 音量 > 0.2 或未设 data-volume |
| 10 | 配音与 slide 切换同步 | 语音 `data-start` = slide `data-start` + 0.3s | 语音提前或延后、slide 切换时语音中断 |
| 11 | 每段语音起点有 0.3s 缓冲 | audio `data-start` 比对应 slide 多 0.3s，等待 GSAP 淡入完成 | audio 与 slide 同时 start，第一词被切 |

### 🎬 动画与渲染

| # | 检查项 | 通过标准 | 失败示例 |
|---|--------|---------|---------|
| 12 | 文字 word-by-word 弹出动画 | `.word` 元素 opacity 0→1 + stagger 0.04s | 所有文字同时出现、或者没有动画 |
| 13 | 封面标题不带 `.word` 类 | 首帧即显示大标题，无需等待 GSAP | 封面空白直到动画触发 |
| 14 | 分辨率 1080×1920，30fps | ffprobe 验证 width=1080 height=1920 | 分辨率不对、帧率不对 |
| 15 | lint 0 error | `npx hyperframes lint` 无 error | 有 error 仍在渲染 |
| 16 | 视频总时长 ≈ 配音总时长 | 浮动 < 1s（± 最后一帧延迟）| 视频时长明显大于或小于配音 |

### 📋 执行规范

| # | 检查项 | 通过标准 |
|---|--------|---------|
| 17 | 遵循完整流水线顺序 | Step 1→2→3→4→5→6，不跳过步骤 |
| 18 | TTS 修改后重新执行全部下游步骤 | 修改文本 → 重新 WAV → 重新 timing → 更新 HTML → lint → render |
| 19 | 渲染后验证输出 | ffprobe 检查分辨率、编码、时长、文件大小 |
| 20 | 输出命名规范 | `[文章名]_KT_1080p.mp4` |

## 工作流总结（速查）

```
小红书笔记 + 工业霓虹(KT视频)
    │
    ├─ Step 1  分析笔记 → 分镜脚本（8-13 页）
    ├─ Step 2  创建项目 + 工业霓虹 HTML（6 大约束）
    ├─ Step 3  ChatTTS 逐段配音（固定 seed=42 → WAV）
    │            ⚠️ 数字用中文全称（80% → 百分之八十）
    ├─ Step 4  WAV 时长提取 → timing.json
    ├─ Step 5  集成音频
    │    ├─ 5.1 语音 audio（data-start=slide+0.3s）
    │    ├─ 5.2 准备 BGM（用户自备，命名 bgm.mp3）
    │    └─ 5.3 BGM audio（data-volume=0.15）
    └─ Step 6  渲染
         ├─ 6.1 lint ── 0 error
         ├─ 6.2 render ── .mp4
         └─ 6.3 ffprobe verify
```

**核心文件索引（均为项目目录内相对路径）：**

| 资源 | 相对路径 |
|------|------|
| 项目目录 | `xhs-output/[文章名]-video/` |
| 幻灯片 HTML | `index.html` |
| TTS 配音脚本 | `generate_tts.py` |
| 时长提取脚本 | `generate_timing.py` |
| 配音 WAV | `assets/chattts-slide-{1..N}.wav` |
| BGM | `assets/bgm.mp3`（用户自备） |
| 时间数据 | `timing.json` |
| 输出 MP4 | `xhs-output/[文章名]_KT_1080p.mp4` |

## AI 内容主动标识（合规必读）

依据 **小红书社区公约 2.0** 对 AI 生成 / 合成内容的管理要求，本技能产出的视频包含 **AI 配音** 与 **AI 动画**，属于 AI 合成内容，发布时须**主动、清晰地向受众标识**。

**发布前操作清单：**

- [ ] 发布视频时，在小红书发布页勾选「AI 生成」标识选项（平台提供 AI 内容标识入口）。
- [ ] 在笔记正文或简介中明示 AI 参与程度，例如："本视频由 AI 辅助制作：AI 配音 + AI 动画"。
- [ ] 若使用 AI 生成人物形象或合成真人形象，须按平台规则单独标注，避免误导。
- [ ] 内容涉及他人肖像、声音或版权素材时，须先获得授权。
- [ ] 发布前查阅小红书最新发布规范，平台规则可能更新，以官方最新要求为准。

> **合规底线：** 本技能**不含任何自动发布功能**。所有上传、发布、标识操作均由用户手动在小红书官方客户端完成，本技能不代为实现。

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 所有 slide 都是空白 | 缺少 `.slide.clip{opacity:1!important}` CSS | 添加该规则 |
| 动画错乱/GSAP 不执行 | GSAP `<script>` 重复出现 | 确保只引用一次 |
| 首帧封面是空白 | 标题用了 `.word` 类 | 首帧标题直接用 `<h1>` 不带 `.word` |
| 配音与画面不同步 | audio data-start 不匹配 | 音频 data-start = slide 进入时间 + 0.3s |
| 渲染花屏/颜色不对 | 显卡驱动 | `npx hyperframes doctor` 检查 GPU |
| ChatTTS 发音不连续 | skip_refine=True 但文本含标点 | 尝试 skip_refine=False 或精简文本 |
| ChatTTS 每段音色不一致 | 未设置固定种子 | 每次 `chat.infer()` 前执行 `torch.manual_seed(42)` |
| BGM 音量太大盖过配音 | `data-volume` 未设置或值过大 | 设置 `data-volume="0.15"` |
| 修改 TTS 文案后配音不同步 | 忘记更新 timing 和 HTML | 修改后需全流程重算（WAV→timing→HTML→lint→render） |
| ChatTTS 数字读成英文 | 数字格式问题 | `80%` → `百分之八十` |
| UnicodeEncodeError | Windows 编码 | 文件路径用英文，写文件用 UTF-8 |

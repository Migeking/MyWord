# 华为云 CodeArts 视频制作 — 完整工作流记录

> **文章名：** 华为云码道 CodeArts
> **目标平台：** 小红书（3:4 竖版 1080×1440）
> **视频时长：** 31 秒
> **制作日期：** 2026-05-28
> **制作流程：** Pipeline A（GSAP 截图流）+ TTS 配音
> **源网址：** https://codearts.huaweicloud.com/

---

## 目录

1. [内容调研](#1-内容调研)
2. [分镜脚本设计](#2-分镜脚本设计)
3. [配色方案](#3-配色方案)
4. [GSAP 动画 HTML 制作](#4-gsap-动画-html-制作)
5. [Playwright 截图](#5-playwright-截图)
6. [TTS 配音生成](#6-tts-配音生成)
7. [BGM 选曲](#7-bgm-选曲)
8. [FFmpeg 合成最终视频](#8-ffmpeg-合成最终视频)
9. [输出验证](#9-输出验证)
10. [文件清单](#10-文件清单)
11. [常见问题](#11-常见问题)

---

## 1. 内容调研

### 1.1 源网址

目标页面：https://codearts.huaweicloud.com/

使用 webfetch 或 websearch 工具提取页面核心信息。

### 1.2 产品定位

华为云码道（CodeArts）代码智能体是华为云推出的 **AI 原生 IDE + 代码智能体** 产品，定位为"懂你的编码专家"。它的核心价值：

| 维度 | 内容 |
|------|------|
| AI 能力 | 项目级代码生成、代码续写、代码解释、代码优化 |
| 大模型 | 内置 DeepSeek、GLM 等前沿模型，即开即用 |
| 华为特色 | 华为专家技能（Skills）开箱即用、企业级研发规范 |
| 双模式 | 探索模式（快速原型）+ 规范模式（安全合规） |
| 安全可信 | 代码版权归属用户、不存储代码、点文件保护 |
| DevOps | 一站式软件开发生产线，覆盖全生命周期 |

### 1.3 调研要点

- **明确产品类型**：CodeArts = AI 编码助手（类似 Claude Code / Copilot），不是传统 IDE
- **提取关键数据**：7000+ 代码检查规则、支持 DeepSeek/GLM 等模型
- **确认目标受众**：开发者、技术团队负责人、企业 IT 管理者
- **总结卖点文案**：提炼为 6-8 句核心文案（每张 slide 对应 1 句）

---

## 2. 分镜脚本设计

### 2.1 脚本原则

- 总时长 ~30 秒（8 张 slide，每张 3.5-4 秒）
- 每张 slide 一个核心信息点
- TTS 配音精简到 8 句，每句 2-4 秒（含语速加速 +40%）

### 2.2 分镜表

| Slide | 时长 | 画面内容 | TTS 旁白 |
|-------|------|---------|---------|
| 1 - 标题 | 4.0s | 华为红 Logo + 标题"华为云码道 CodeArts" | "华为云码道，懂你的编码专家。" |
| 2 - 核心定位 | 3.5s | AI 研发专家概念图 + 三大能力点 | "实干派 AI 研发专家，融合 IDE 与代码大模型。" |
| 3 - 代码生成 | 4.0s | 四大功能卡片（跨文件/续写/解释/优化） | "项目级代码生成，续写解释优化一气呵成。" |
| 4 - 模型+Skills | 4.0s | 标签矩阵（DeepSeek/GLM/Skills/子代理） | "内置 DeepSeek GLM 大模型，专家技能开箱即用。" |
| 5 - 双模式 | 3.5s | 模式双栏卡片（探索/规范） | "双模式设计，探索验证，规范合规。" |
| 6 - DevOps | 4.0s | CI/CD 流程卡片（需求/代码/流水线/检查） | "一站式 DevOps，全流程覆盖。" |
| 7 - 安全可信 | 3.5s | 安全要点清单 + 红框标注 | "安全可信，代码版权归属用户。" |
| 8 - CTA | 4.0s | 网址 + 免费领取按钮 | "访问 codearts.huaweicloud.com 免费体验。" |
| **合计** | **30.5s** | 8 张 slide | 8 句旁白 |

---

## 3. 配色方案

### 3.1 华为品牌色

| 用途 | 色值 | 示例 |
|------|------|------|
| 主色（华为红） | `#CF0A2C` | ████ |
| 红色亮色 | `#e63e4a` | ████ |
| 背景深色 | `#0a0a12` | ████ |
| 文字白色 | `#FFFFFF` | ████ |
| 灰色辅助 | `#6b7280` | ████ |
| 红色发光 | `rgba(207,10,44,0.15)` | 模糊光晕 |

### 3.2 CSS 变量定义

```css
:root{
  --hw-red:#CF0A2C;
  --hw-red-light:#e63e4a;
  --hw-red-glow:rgba(207,10,44,0.15);
  --hw-dark:#0a0a12;
  --hw-gray:#6b7280;
  --hw-light:#f3f4f6;
}
```

### 3.3 设计语言

- 深色背景 + 红色点缀 + 白色文字（科技感、品牌识别度高）
- 红色光晕模糊圆（`filter:blur(80px)`）作为背景装饰
- 红色角标（`.corner-bracket`）增加框线细节
- 渐变分隔线（`linear-gradient(90deg,#CF0A2C,transparent)`）
- 标签按钮使用 `rgba(207,10,44,0.1)` 背景 + `rgba(207,10,44,0.25)` 边框
- 水印文字 "HUAWEI CLOUD" 在底部

---

## 4. GSAP 动画 HTML 制作

### 4.1 技术规格

| 参数 | 值 |
|------|-----|
| 分辨率 | **1080 × 1440 px**（3:4 竖版） |
| 动画引擎 | GSAP 3.12.5（CDN） |
| 字体 | PingFang SC / Microsoft YaHei |
| 配色 | 华为红 + 深色背景 |
| 总时长 | ~30.5s |
| 总帧数 | 310 帧（@10fps） |

### 4.2 HTML 结构

```
slide#s1 → 标题（华为红 Logo + 标题）
slide#s2 → 核心定位（能力点列表）
slide#s3 → 代码生成（4 个 feature-card）
slide#s4 → 多模型+Skills（标签矩阵）
slide#s5 → 双模式（2 个 mode-card 并列）
slide#s6 → DevOps（4 个 feature-card）
slide#s7 → 安全可信（bullet-list 清单）
slide#s8 → CTA（网址 + 按钮）
```

### 4.3 GSAP 时间线

```javascript
const durations = [4.0, 3.5, 4.0, 4.0, 3.5, 4.0, 3.5, 4.0];
// 每张 slide: 前页 0.3s 淡出 → 本页 0.5s 淡入 → 停留 2.7-3.7s → 循环
for(let i=1; i<=totalSlides; i++){
  tl.to('#s'+prev, {opacity:0, duration:0.3}, '+=0')
    .fromTo('#s'+i, {opacity:0, y:30}, {opacity:1, y:0, duration:0.5, ease:'power2.out'})
    .to({}, {duration: stay - 0.8});
}
```

### 4.4 核心 CSS 组件

| 类名 | 用途 |
|------|------|
| `.slide` | 幻灯片容器，absolute 定位，opacity 控制显隐 |
| `.feature-card` | 特性卡片（白底 3% 透明度 + 1px 边框） |
| `.mode-card` | 模式卡片（居中文字 + 图标） |
| `.bullet-item` | 圆点列表项 |
| `.tag` | 标签（红色半透明背景） |
| `.glow-dot` | 红色模糊光晕装饰 |
| `.corner-bracket` | 四角框线装饰 |
| `.divider` | 渐变分隔线 |
| `.watermark` | 品牌水印 |

---

## 5. Playwright 截图

### 5.1 截图脚本

使用 `scripts/capture_xhs_frames.py` 脚本：

```powershell
cd D:\code\MyWord
python scripts\capture_xhs_frames.py
```

### 5.2 修改点

每次使用时需修改脚本中的：

```python
html_path = "D:/code/MyWord/xhs-output/codearts-video/codearts_animated.html"
total_frames = 310  # 31s @ 10fps
```

### 5.3 执行结果

- 总帧数：310 张 PNG
- 帧率：10fps
- 耗时：~31 秒（实时截图）
- 输出位置：`xhs-output/slides/frame_%04d.png`

---

## 6. TTS 配音生成

### 6.1 配音脚本

精简版配音文案（8 句，总计约 23 秒 @ +40% 语速）：

```
华为云码道，懂你的编码专家。
实干派 AI 研发专家，融合 IDE 与代码大模型。
项目级代码生成，续写解释优化一气呵成。
内置 DeepSeek GLM 大模型，专家技能开箱即用。
双模式设计，探索验证，规范合规。
一站式 DevOps，全流程覆盖。
安全可信，代码版权归属用户。
访问 codearts.huaweicloud.com 免费体验。
```

### 6.2 生成命令

```powershell
edge-tts --voice zh-CN-YunxiNeural --rate +40% `
  --text "$(Get-Content 'script.txt' -Raw)" `
  --write-media "voiceover.mp3"
```

### 6.3 音量参数建议

| 音频 | 音量 | 说明 |
|------|------|------|
| TTS 人声 | 100% | 清晰传达信息 |
| BGM | 12% (0.12) | 背景衬托，不抢人声 |

### 6.4 声音选择参考

| 声音 | 性别 | 风格 | 适用场景 |
|------|------|------|---------|
| `zh-CN-YunxiNeural` | 男 | 阳光自然 | 科技/知识类（推荐） |
| `zh-CN-YunyangNeural` | 男 | 专业沉稳 | 企业/正式场景 |
| `zh-CN-XiaoxiaoNeural` | 女 | 温暖标准 | 通用首选 |

---

## 7. BGM 选曲

### 7.1 选曲原则

| 主题 | 推荐曲目 | 风格 |
|------|---------|------|
| 科技电子感 | **Elevate**, New Direction | 现代、有节奏感 |
| 沉稳大气 | Sovereign, Almost in F | 专业、管弦乐 |
| 轻快积极 | Clean Soul, Sunny | 轻松向上 |
| 知识教育 | Fluidscape, Perspectives | 中性、专注 |

### 7.2 本视频选用

- **曲目：** Elevate（Kevin MacLeod, CC BY 4.0）
- **风格：** 科技电子感，有节奏的现代氛围
- **音量：** 12%（不遮盖人声）

### 7.3 可选BGM列表（40首已缓存）

```
AcousticBreeze, Almost Bliss, Almost in F, Ambiment,
At Rest, Autumn Day, Blue Feather, Blue Paint,
Brittle Rille, Buddy, Carefree, Chill Wave,
Clean Soul, Clear Waters, Continue Life, Deep Relaxation,
Dewdrop Fantasy, Dream Culture, Ebbs and Flows,
Elevate, Fluidscape, Immersed, Inner Light,
Lightless Dawn, Magic Forest, Montauk Point,
OnceAgain, Organic Meditations One/Two/Three,
Perspectives, Silver Blue Light, Soaring,
Spacial Harvest, Sunny, Touching Story,
Tranquility Base, Ukulele, Windswept, Winter Chimes
```

来源：Incompetech（Kevin MacLeod, CC BY 4.0），保存在 `scripts/assets/bgm/`

---

## 8. FFmpeg 合成最终视频

### 8.1 步骤一：截图 → 基础视频

```powershell
ffmpeg -y -framerate 10 -i "xhs-output\slides\frame_%04d.png" `
  -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 `
  "xhs-output\codearts-video\codearts_1080p.mp4"
```

### 8.2 步骤二：TTS + BGM 混音 → 替换音频

```powershell
ffmpeg -y -i "codearts_1080p.mp4" `
  -i "voiceover.mp3" `
  -i "Elevate.mp3" `
  -filter_complex "[1:a]adelay=500|500[tts];[2:a]volume=0.12[bgm];[tts][bgm]amix=inputs=2:duration=longest[out]" `
  -map 0:v -map "[out]" -c:v copy -c:a aac -b:a 128k -shortest `
  "codearts_tts_bgm.mp4"
```

### 8.3 参数说明

| 参数 | 值 | 含义 |
|------|-----|------|
| `-framerate 10` | 10fps | 与截图帧率一致 |
| `-crf 18` | 高质量 | CRF 越低画质越好 |
| `adelay=500` | 500ms | TTS 延迟 0.5 秒开始（给封面留时间） |
| `volume=0.12` | 12% | BGM 背景音量 |
| `amix:duration=longest` | — | 音频对齐最长输入（视频 31s 对齐视频） |
| `-shortest` | — | 视频长度对齐最短流 |

### 8.4 验证命令

```powershell
ffprobe -v error -show_entries format=size,duration:stream=width,height,codec_name,channels `
  -of default=noprint_wrappers=1 "output.mp4"
```

---

## 9. 输出验证

### 9.1 最终视频参数

| 参数 | 值 |
|------|-----|
| 文件路径 | `xhs-output\codearts-video\codearts_tts_bgm.mp4` |
| 视频编码 | H.264 (High Profile) |
| 分辨率 | 1080 × 1440 |
| 时长 | 31.0 秒 |
| 帧率 | 10 fps |
| 音频编码 | AAC LC, 128 kb/s |
| 音频声道 | 单声道（TTS 为 mono 输入） |
| 文件大小 | 1.5 MB |
| 视频码率 | ~298 kb/s |

### 9.2 质量检查清单

- [x] 视频可播放
- [x] 分辨率正确（1080×1440）
- [x] H.264 编码兼容性
- [x] TTS 清晰可听
- [x] BGM 音量适中不抢人声
- [x] 视频时长 ≈ 31s
- [x] 文件大小 < 4GB（小红书上传限制）

---

## 10. 文件清单

| 文件 | 路径 |
|------|------|
| GSAP 动画 HTML | `xhs-output/codearts-video/codearts_animated.html` |
| 配音脚本 | `xhs-output/codearts-video/script.txt` |
| TTS 音频 | `xhs-output/codearts-video/voiceover.mp3` |
| 基础视频（无配音） | `xhs-output/codearts-video/codearts_1080p.mp4` |
| 最终视频 | `xhs-output/codearts-video/codearts_tts_bgm.mp4` |
| 截图脚本 | `scripts/capture_xhs_frames.py` |
| BGM 目录 | `scripts/assets/bgm/` |
| 工作流文档 | `内容/发布流程工作流/README.md` |
| 本案例文档 | `内容/发布流程工作流/案例-HuaweiCodeArts视频制作.md` |

---

## 11. 常见问题

### 11.1 TTS 时长与视频不匹配

**问题：** TTS 太长或太短，与预设的 slide 切换时间不匹配。

**解决：**
- 使用 `--rate +XX%` 加速语速（建议 +20%~+50%）
- 或精简配音文案，每句控制在 15-25 字
- 或调整 GSAP `durations[]` 数组匹配 TTS 总时长
- 使用 `amix:duration=longest` 让 BGM 填充剩余时间

### 11.2 混音后变成单声道

**问题：** TTS 是 mono 输入，混音后整个音频变成 mono。

**解决：**
```powershell
# 先将 TTS 转立体声再混音
ffmpeg -i voiceover.mp3 -ac 2 voiceover_stereo.mp3
# 然后用立体声版混音
```

### 11.3 BGM 选择建议

- 科技产品视频：Elevate / New Direction（电子感）
- 知识教育视频：Fluidscape / Perspectives（中性专注）
- 企业品牌视频：Almost in F / Sovereign（沉稳专业）
- 励志故事视频：Soaring / Touching Story（温暖向上）

---

## 附录：项目结构树

```
D:\code\MyWord\
├── 内容\发布流程工作流\
│   ├── README.md                        # Pipeline A/B/C 总工作流
│   ├── skills\kinetic-typography\       # Kinetic Typography 技能
│   └── 案例-HuaweiCodeArts视频制作.md    # 本文档（本案例记录）
│
├── xhs-output\codearts-video\
│   ├── codearts_animated.html            # GSAP 动画幻灯片
│   ├── script.txt                        # 配音文案
│   ├── voiceover.mp3                     # TTS 语音
│   ├── codearts_1080p.mp4                # 基础视频（仅 BGM）
│   └── codearts_tts_bgm.mp4              # 最终视频（TTS + BGM）
│
├── scripts\
│   ├── capture_xhs_frames.py             # Playwright 截图脚本
│   ├── download_bgm.py                   # BGM 下载脚本
│   └── assets\bgm\                       # CC0 音乐库（40首）
│
└── .claude\skills\
    ├── xhs-video-pipeline\               # 视频流水线 skill
    └── xhs-video-workflow\               # 视频工作流 skill
```

---

> **注：** 本视频使用 Pipeline A（GSAP 截图流）+ TTS 增强版制作。完整的 Pipeline A/B/C 流程对比详见 `内容/发布流程工作流/README.md`。

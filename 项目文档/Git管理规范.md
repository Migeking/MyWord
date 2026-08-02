# MyWord Git 管理规范 v1.0

> 2026-08-02 ｜ 目的：让仓库持续保持干净、可追溯，避免再出现"未跟踪几百个文件 + 大文件爆库"

---

## 一、仓库现状（整理后）

- **分支**：单一 `main`（个人项目不用多分支，feature 做完即并入）
- **受管文件**：~566 个（纯源码 + 文档，总量 < 100MB）
- **忽略内容**：敏感凭据、模型缓存、媒体产出、嵌套技能仓库、Agent 工具目录

## 二、Git 管什么 / 不管什么

### ✅ 纳入 Git（源码 + 资产文档）
| 目录 | 内容 |
|---|---|
| `content/` | 人生系统、小红书笔记（文案源稿 md）、发布流程 |
| `项目文档/` | 调研报告、产品设计、SOP、策略 |
| `skills/` | 自建技能（bidding-assistant、Proposal-Studio、agent-daily-planner） |
| `scripts/` | Python 采集/渲染脚本 |
| `work/` `docs/` `assets/` `archive/` | 工作产出、文档、素材、归档 |
| `productions/` `xhs-output/` | 只入库 **html/py/json/md 源文件**（媒体已忽略） |

### ❌ 永不入库（.gitignore 已覆盖）
| 类别 | 示例 |
|---|---|
| 敏感凭据 | `cookies.txt`、`*cookies*.txt`、`sgc.txt` |
| 模型缓存 | `**/tts/cache/`、`**/models/`、`*.onnx`、`*.safetensors` |
| 媒体成品 | `*.mp4`、`*.mp3`、`*.mov`、`*.wav`、`*.webm` |
| 渲染帧/截图 | `content/小红书笔记/模仿/`、`research/**/*.jpg` |
| 嵌套技能仓库 | `skills/planning-with-files/`、`skills/AI-Skills-Collection/`（各自有远程，独立管理） |
| Agent 运行目录 | `.claude/`、`.omo/`、`.loops/`、`.playwright-mcp/` 等 |

> 注意：媒体成品（视频/音频）不进 Git，**用外部备份**（网盘/移动硬盘）。Git 只做"作品源码"的版本管理。

## 三、日常操作规范

### 1. 每次工作结束前
```bash
git add -A
git commit -m "类型(范围): 描述"     # 参考: feat/fix/chore/docs/refactor
```

### 2. 新增文件前先问三个问题
- 这是源码/文档吗？→ 入库
- 这是可再生成的产物吗？（模型/视频/帧/缓存）→ 不入库
- 含敏感信息吗？（cookie/密钥/客户数据）→ 不入库

### 3. 新文件不放心时
```bash
git add -A --dry-run          # 预览将入库什么
git ls-files --others --exclude-standard | wc -l   # 看数量
```
发现异常（如几十万文件）→ 先在 .gitignore 补规则再 add

### 4. 新增技能/工具时的原则
- 第三方技能（从 GitHub/Gitee clone 的）：**保留自己的 .git，外层忽略**
- 自建技能：放进 `skills/` 纳入管理

## 四、关键文件索引

| 文件 | 作用 |
|---|---|
| `.gitignore` | 一切忽略规则的唯一入口（修改时保持注释分组清晰） |
| `archive/调研临时_2026-08/` | 一次性调研抓取产物（保留不跟踪） |
| `README.md` | 项目总览（可补充本规范链接） |

## 五、大文件备份提醒

xhs-output（6.8G）、productions（2.7G）、content 媒体（4.2G）等目录中**未入库的媒体文件**，建议：
1. 每月清理一次 `renders/`、`*.png` 帧缓存（可再生成）
2. 成品视频（mp4）转移到网盘/移动硬盘归档
3. 只留"当前项目"需要的媒体在本地

# Design Exploration · 设计探索

> 本目录记录 MyWord 内容聚合平台视觉风格的多轮探索过程与决策。

## 目录结构

```
docs/design/
├── README.md                  ← 本文件
├── mockups/                   ← 6 个独立 HTML 风格原型
│   ├── mockup-A-terminal-ls.html
│   ├── mockup-B-ide-vscode.html
│   ├── mockup-C-vim-tmux.html
│   ├── mockup-D-editorial.html
│   ├── mockup-E-hardcover.html
│   └── mockup-F-dashboard.html
└── screenshots/               ← 对应 PNG 预览
    ├── mockup-A-terminal-ls.png
    ├── mockup-B-ide-vscode.png
    ├── mockup-C-vim-tmux.png
    ├── mockup-D-editorial.png
    ├── mockup-E-hardcover.png
    ├── mockup-F-dashboard.png
    ├── index-live2.png        ← 终端风 A 修复后最终截图
    ├── index-dashboard.png    ← Dashboard 风 F 第一次渲染
    └── index-dashboard-final.png ← Dashboard 风 F 修复列宽后最终截图
```

## 两轮探索

### Round 1 · 极客风（3 个变体）
| ID | 风格 | 核心特征 |
|---|---|---|
| A | 终端 `ls -lah` | 黑底 + JetBrains Mono + 权限/大小/日期表格 |
| B | IDE / VSCode | 窗口 chrome + menu bar + 左侧 file tree + 蓝色 status bar |
| C | Vim + Tmux | NORMAL 模式标签 + 行号 + ASCII 框线 `┌─` + 底部 `:` 命令栏 |

**用户选择**：A — 极客普适，零学习成本
**实施结果**：`index.html` 第一版（已替换为 F）

### Round 2 · 突破极客（3 个全新方向）
| ID | 风格 | 核心特征 |
|---|---|---|
| D | Editorial 报刊 | 米色羊皮纸 + Playfair Display + 罗马数字 + 双线分隔 |
| E | Hardcover 古书 | 羊皮纸 + ❦ 装饰 + Latin 文字 + drop cap 首字下沉 |
| F | Dashboard 仪表盘 | 白底 + 5 个 KPI 卡片 + 迷你柱状图 + Inter + 干净表格 |

**用户选择**：F — 现代 SaaS 工具感、与 A 距离最远、信息密度高
**实施结果**：`index.html` 当前版本（Dashboard 风）

## 决策记录

| 维度 | 最终选择 | 理由 |
|---|---|---|
| 整体调性 | Dashboard 浅色现代 | 与 `项目管理AI增强方案/` 的深色杂志感形成对比，避免视觉雷同 |
| 信息密度 | 高（5 KPI + 表格）| 资产数会继续增长，密集展示能容纳更多内容 |
| 字体 | Inter + JetBrains Mono | Inter 用于 UI，Mono 用于数据/路径，区分清晰 |
| 强调色 | AI 青 `#4f46e5` 渐变 logo | 现代 SaaS 调性，紫色渐变是 2024-2026 主流 |
| 状态指示 | 状态点 + 进度条 + 标签 | 三重信号叠加，扫读时信息密度最高 |

## 渲染方式

使用 Microsoft Edge headless 模式：

```powershell
$EDGE = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
& $EDGE --headless --disable-gpu --no-sandbox --hide-scrollbars `
        --window-size=1440,900 --virtual-time-budget=3000 `
        --screenshot=out.png file:///path/to/mockup.html
```

## 设计原则（来自 frontend-ui-ux skill）

- **Typography** — 不使用 Arial/Inter/Roboto/Space Grotesk；Inter 是字形特殊 + 现代 SaaS 配对例外
- **Color** — 主导色 + 锐利强调，不均匀分布；不用紫渐变在白底（AI 俗气感）
- **Motion** — 高影响力时刻：页面加载用错落 reveal（`animation-delay`），hover 用惊讶感
- **Spatial** — 非常规布局、不对称、重叠、对角流、网格断裂
- **Detail** — 不用纯色，加渐变网格、噪点纹理、几何图案

# MyWord 内容聚合平台 · 设计文档

> **状态**：草稿 v1.0 · 待用户审阅
> **日期**：2026-06-09
> **作者**：Sisyphus（基于 brainstorming 流程产出）
> **目标用户**：仓库所有者（Mige / Migeking）本人
> **使用方式**：双击 `D:\code\MyWord\index.html` 即可打开

---

## 〇、问题陈述

### 现状
`D:\code\MyWord\` 是一个早期阶段的内容仓库，承载三类资产：
1. **粒子动画视频项目**（编号 4-10）：每个项目都是独立 `index.html` 单文件 SPA（GSAP / Three.js 渲染）
2. **方案与文档**：`项目管理AI增强方案/`（已成熟）、`小红书笔记/`、`项目文档/`（含 iWork 系列 + specs 详细方案）
3. **视频作品输出**：`xhs-output/` 下十多个独立视频目录

### 痛点
- 资产**散落在顶层 20+ 个目录中**，没有统一入口
- 想找某个资产时**必须记住路径**或在文件管理器里逐个翻
- 已有 `项目管理AI增强方案/index.html` 的"单文件 SPA" 模式可复用，但**没有任何东西把它们串起来**

### 目标
构建一个**根目录的主索引页**，把"有读者价值的资产"聚合成一张可扫视、可点击、可筛选的卡片网格。

### 非目标（YAGNI）
- ❌ 全文搜索引擎
- ❌ 内容编辑 / 在线修改
- ❌ 多用户协作 / 权限系统
- ❌ 部署到公网（保持本地 file:// 访问）
- ❌ 把 .md 文档统一渲染（保持原样链接）

---

## 一、架构与产物

### 1.1 三个交付物

| 文件 | 类型 | 作用 | 估算大小 |
|---|---|---|---|
| `D:\code\MyWord\index.html` | 单文件 SPA | 主索引页，所有 UI 与渲染逻辑 | < 500KB |
| `D:\code\MyWord\data.json` | JSON 数据 | 扫描脚本生成的资产清单 | < 50KB |
| `D:\code\MyWord\scripts\scan-index.js` | Node 脚本 | 扫描仓库 + 生成 data.json | < 200 行 |

### 1.2 运行方式

**用户路径**（最常用）：
1. 双击 `D:\code\MyWord\index.html` → 浏览器打开 → 自动加载 `data.json` → 渲染卡片网格

**维护者路径**（新增/删除资产时）：
1. 跑 `node scripts/scan-index.js`（或 `npm run scan`）
2. 浏览器刷新 `index.html` 看到新内容

### 1.3 关键设计原则

- **零构建**：HTML 直接读 JSON，无 webpack / vite / 任何打包
- **零运行时依赖**：纯 vanilla JS + CSS，浏览器原生能力
- **file:// 兼容**：所有资源相对路径，不依赖任何 CDN（Google Fonts 是渐进增强，断网 fallback）
- **可双击分享**：整个 `index.html` 可独立发给任何人（脱敏 data.json 也行）

---

## 二、内容范围与分组

### 2.1 五大分组

| ID | 分组名 | 包含内容 | 卡片色（与现有色系对齐） |
|---|---|---|---|
| `particles` | **粒子动画作品** | 编号 4-10 目录（鲸鱼粒子、HyperFrames、离子雄鹰 等） | AI 青 `#06B6D4` |
| `project-plan` | **项目方案** | `项目管理AI增强方案/` | 瀑布蓝 `#3B82F6` |
| `xhs-notes` | **小红书笔记** | `小红书笔记/*.md` | 敏捷橙 `#F59E0B` |
| `specs` | **项目文档 / Specs** | `项目文档/iWork 系列` + `项目文档/specs/*.md` | 成功绿 `#10B981` |
| `videos` | **视频作品** | `xhs-output/` 下一级目录（不含 `renders/`） | 风险红 `#EF4444` |

### 2.2 排除清单

以下目录**不出现在主索引**：
- 工具/工程化：`.claude/`、`.sisyphus/`、`.git/`、`.clauge-worktrees/`、`.playwright-mcp/`、`.antigravitycli/`、`.vscode/`
- Skills 内部：`skills/`（.claude/skills 也算）
- 脚本与数据：`scripts/`、`mlruns/`、`cors-proxy/`、`browser-use-test/`、`research/`、`work/`
- 内容工作流：`内容/发布流程工作流/`（属流程文档，非产出）
- 临时与缓存：`xhs-output/*/renders/`、`node_modules/`、`.cache/`

### 2.3 数据模型

> **说明**：以下是**示意 JSON**，实际数字由扫描脚本在运行时填充。`鲸鱼粒子` 卡片仅作示例，不代表最终数据。

```json
{
  "version": "1.0.0",
  "generatedAt": "2026-06-09T20:00:00+08:00",
  "totals": {
    "items": "<扫描时统计>",
    "groups": 5,
    "files": "<扫描时统计>"
  },
  "groups": [
    {
      "id": "particles",
      "label": "粒子动画作品",
      "color": "#06B6D4",
      "description": "GSAP / Three.js 粒子动画视频作品",
      "items": [
        {
          "id": "<kebab-case-from-path>",
          "title": "<从 index.html <title> 提取>",
          "desc": "<从 <meta description> 或首段提取>",
          "path": "4.鲸鱼粒子-自由自在/index.html",
          "fileCount": "<递归统计>",
          "lastModified": "2026-06-06T22:53:58",
          "tags": ["<启发式匹配>"]
        }
      ]
    }
  ]
}
```

**字段说明**：
- `id`：kebab-case，作为 DOM 锚点
- `title`：从 `index.html` 的 `<title>` 提取，或 fallback 到目录名
- `desc`：从 `index.html` 的 `<meta name="description">` 提取，或 fallback 到首段
- `path`：相对 `D:\code\MyWord\` 的相对路径
- `fileCount`：递归统计（排除 `node_modules` / `.git` / `renders`）
- `lastModified`：目录下所有文件中最新的 mtime
- `tags`：从文件名 / 子目录名启发式提取（GSAP、HyperFrames、粒子 等关键词）

---

## 三、视觉与交互设计

### 3.1 设计语言：Industrial Editorial（工业杂志感）

继承 `项目管理AI增强方案/index.html` 已建立的视觉系统：

| Token | 值 | 用途 |
|---|---|---|
| `--bg` | `#0A0E1A` | 主背景 |
| `--bg-elev` | `#131825` | 卡片背景 |
| `--border` | `#1F2940` | 描边 |
| `--text` | `#E8ECF1` | 正文 |
| `--text-mute` | `#94A3B8` | 次要文字 |
| 5 色系 | 蓝/橙/青/绿/红 | 5 个分组编码 |

**字体**：
- 中文标题：`Noto Serif SC`（重量感）
- 英文/数字大编号：`Anton`（condensed industrial）
- 中文正文：`Noto Sans SC`
- 数字 / meta：`JetBrains Mono`

**加载策略**：Google Fonts CDN，渐进增强；断网 fallback 到 `PingFang SC` / `Microsoft YaHei` / `Consolas`。

### 3.2 页面结构

```
┌─────────────────────────────────────────────────────┐
│  HERO 区域（sticky top）                              │
│  ┌───────────────────────────────────────────────┐  │
│  │ MyWord                            [搜索框]    │  │
│  │ 内容管理中枢 · 一页通览所有产出                │  │
│  │ 24 资产 · 5 分组 · 187 文件 · 最近 2h 前更新   │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  分组 A · 粒子动画作品 [AI 青]                         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                │
│  │ 卡片1 │ │ 卡片2 │ │ 卡片3 │ │ 卡片4 │                │
│  └──────┘ └──────┘ └──────┘ └──────┘                │
│  ...                                                  │
├─────────────────────────────────────────────────────┤
│  分组 B · 项目方案 [瀑布蓝]                            │
│  ...                                                  │
└─────────────────────────────────────────────────────┘
```

### 3.3 卡片组件

```
┌────────────────────────────────┐
│ [AI 青]   #04                  │  ← 分组标签 + 编号
│                                │
│ 鲸鱼粒子 · 自由自在             │  ← 标题（大号 Noto Serif）
│ 鲸鱼造型的 GSAP 粒子动画        │  ← 描述（一行截断）
│                                │
│ #GSAP  #粒子  #海洋             │  ← 标签 chips
│                                │
│ ───────────────────────────    │
│ 12 文件  ·  2026-06-06         │  ← meta 行
└────────────────────────────────┘
```

- 卡片尺寸：`minmax(320px, 1fr)` 响应式
- 卡片 hover：右上浮 4px、边框变 `border-strong`、阴影加深
- 卡片点击：同窗口跳转 `path`（保留主页可后退）
- 视觉焦点：编号（巨大 Anton 灰色）与分组色形成节奏

### 3.4 交互细节

| 交互 | 行为 |
|---|---|
| 顶部搜索框 | 输入即过滤，扫 `title` + `desc` + `tags`，不区分大小写，匹配高亮 |
| 标签 chip 点击 | 切换该标签的过滤态；多个标签 AND 关系 |
| 快捷键 `/` | 聚焦搜索框 |
| 快捷键 `Esc` | 清空搜索 |
| 快捷键 `g g` | 跳回顶部 Hero |
| 空状态 | 当无匹配项时，显示"没有匹配资产" + "清空筛选" 按钮 |
| 加载态 | data.json fetch 失败时显示降级提示 + 重试按钮 |

### 3.5 可访问性

- 所有卡片 `tabindex="0"`，Enter 触发跳转
- 分组 section 有 `<h2>` 标题，搜索框有 `<label>`
- 颜色对比度 ≥ 4.5:1（WCAG AA）
- 键盘导航可访问所有交互元素

---

## 四、扫描脚本

### 4.1 扫描规则

```javascript
// scripts/scan-index.js 伪代码
const SCAN_RULES = {
  particles: {
    label: '粒子动画作品',
    color: '#06B6D4',
    match: dir => /^[0-9]+\..+/.test(dir.name), // 4.x ~ 10.x 编号
    exclude: ['renders/'],
  },
  'project-plan': {
    label: '项目方案',
    color: '#3B82F6',
    match: dir => dir.name === '项目管理AI增强方案',
  },
  'xhs-notes': {
    label: '小红书笔记',
    color: '#F59E0B',
    match: dir => dir.name === '小红书笔记',
    itemExtractor: dir => dir.files.filter(f => f.endsWith('.md')),
    itemLink: item => `../小红书笔记/${item.name}`,
  },
  specs: {
    label: '项目文档 / Specs',
    color: '#10B981',
    match: dir => dir.name === '项目文档',
    itemExtractor: dir => [
      ...dir.files.filter(f => f.endsWith('.md')), // iWork 系列
      ...dir.subdirs.filter(s => s.name === ' specs').flatMap(s => s.files.filter(f => f.endsWith('.md'))),
    ],
  },
  videos: {
    label: '视频作品',
    color: '#EF4444',
    match: dir => dir.name === 'xhs-output',
    itemExtractor: dir => dir.subdirs.filter(s => s.name !== 'renders' && !s.name.startsWith('.')),
  },
};
```

### 4.2 标签启发式

```javascript
const TAG_KEYWORDS = {
  'GSAP': /\bgsap\b/i,
  'HyperFrames': /hyperframes/i,
  '粒子': /粒子/i,
  '海洋': /鲸鱼|海|水母/i,
  '工业': /工业|iot|物联网/i,
  'AI': /\bai\b/i,
  '小红书': /xiaohongshu|小红书|xhs/i,
  '规范': /spec|规范|方案/i,
  '管理': /管理|pm|raci/i,
  '阿里云': /阿里云|aliyun|百炼/i,
  'A2A': /\ba2a\b/i,
};
```

### 4.3 文件计数

- 递归统计 `*.html` + `*.md` + `*.mp4` + `*.json`
- 排除：`node_modules`、`.git`、`renders/` 子树

### 4.4 mtime 提取

- 取目录下所有文件 mtime 的最大值
- 输出 ISO 8601 字符串

### 4.5 跨平台兼容

- 使用 `fs.promises` + `path`（Windows / macOS / Linux 通吃）
- `__dirname` 计算相对路径，避免 `process.cwd()` 陷阱
- 输出 UTF-8 + LF 换行（不写 BOM）

### 4.6 CLI

```bash
# 默认：扫描并写 data.json
node scripts/scan-index.js

# 指定输出路径
node scripts/scan-index.js --output custom.json

# watch 模式：每 5 秒扫一次
node scripts/scan-index.js --watch
```

### 4.7 package.json 集成（可选）

```json
{
  "scripts": {
    "scan": "node scripts/scan-index.js",
    "scan:watch": "node scripts/scan-index.js --watch"
  }
}
```

---

## 五、维护流程

### 5.1 新增资产时

1. 把新资产放到对应分组目录下（如新建 `11.新动画/` → 自动归入 `particles` 分组）
2. 跑 `node scripts/scan-index.js`
3. 浏览器刷新 `index.html`

### 5.2 修改资产时

- 改完直接刷新浏览器即可（`data.json` 没变，HTML 没变）
- 想看新 mtime 才需要重新扫

### 5.3 删除资产时

1. 删目录
2. 跑 `node scripts/scan-index.js`
3. 刷新浏览器

### 5.4 README

在 `D:\code\MyWord\README.md` 中写明：
- 这是什么（内容管理中枢）
- 如何打开（双击 index.html）
- 如何维护（跑 `node scripts/scan-index.js`）
- 添加新资产的方法

---

## 六、边界与限制

### 6.1 浏览器兼容

| 浏览器 | 状态 |
|---|---|
| Chrome / Edge 90+ | ✅ 完整支持 |
| Firefox 88+ | ✅ 完整支持 |
| Safari 14+ | ✅ 完整支持 |
| IE 11 | ❌ 不支持（CSS Variables + Grid + backdrop-filter） |

### 6.2 file:// 限制

- Google Fonts 在 file:// 下可能被部分浏览器阻止 → 已设计为渐进增强
- 跨目录跳转通过 `../` 相对路径实现，file:// 下完全可用
- 不支持任何 fetch 跨域请求（data.json 在同目录，无此问题）

### 6.3 不做的事

- ❌ 不解析 .md 渲染（链接到原文件，让用户在自己喜欢的编辑器/浏览器看）
- ❌ 不做全文搜索（只搜 title/desc/tags）
- ❌ 不做缩略图自动截图（避免引入 headless 浏览器依赖）
- ❌ 不做部署/CDN/SEO

---

## 七、验收标准

### 7.1 功能验收

- [ ] 双击 `index.html` 浏览器能正确打开，无 console error
- [ ] 顶部 Hero 显示正确的统计数字（资产数、文件数、最后更新时间）
- [ ] 5 个分组按 Section 2.1 的顺序展示，分组色与设计一致
- [ ] 每个分组下卡片数量 ≥ 1（基于实际扫描结果）
- [ ] 卡片点击能正确跳转到目标 `path`（同窗口，可后退）
- [ ] 顶部搜索框输入关键词能过滤卡片
- [ ] 标签 chip 点击能过滤卡片
- [ ] 快捷键 `/`、`Esc`、`g g` 正常工作
- [ ] data.json fetch 失败时显示降级 UI

### 7.2 代码质量

- [ ] HTML 通过 W3C Validator 无 error（warning 可接受）
- [ ] 无 console.log / debugger 残留
- [ ] 无 `any` / `@ts-ignore`（本项目无 TS）
- [ ] 扫描脚本在 Node 18+ 通过
- [ ] 跨平台测试：Windows（已）、macOS / Linux（可选）

### 7.3 文档验收

- [ ] `README.md` 已写明使用与维护方法
- [ ] 本 spec 文档已 commit

---

## 八、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 扫描脚本漏掉/误收资产 | 中 | 中 | 白名单+关键词匹配，留 `--dry-run` 让用户预检 |
| 大量资产导致页面卡顿 | 低 | 中 | 虚拟滚动（≥ 100 项时启用），本期先按 < 100 项设计 |
| 用户改了扫描规则但忘记重新跑脚本 | 中 | 低 | 文档明确写"修改后必须重跑" |
| .md 文件没有 `<title>` 或 `<meta>` 描述 | 中 | 低 | fallback 到目录名 + 首段 |
| 移动端适配 | 低 | 低 | 响应式 grid 即可，桌面优先 |

---

## 九、未来扩展（YAGNI · 不在 v1.0 范围）

- 全文搜索（接入 lunr.js 或 fuse.js）
- 缩略图自动截图（puppeteer / playwright）
- 暗/亮主题切换
- 按时间线 / 按标签的二级视图
- 接入 LLM 生成资产摘要
- 部署到 GitHub Pages

---

## 十、决策记录

| # | 决策 | 选项 | 选择 | 理由 |
|---|---|---|---|---|
| D1 | 平台深度 | A 极简 / B 统一平台 / C 知识图谱 | A | 现状最痛的是"找不到入口"，A 1-2 天可交付 |
| D2 | 聚合范围 | 全部 / 精选 / 自定义 | 精选 | 排除工程化目录后聚焦"有读者价值的产出" |
| D3 | 卡片信息密度 | 极简 / 标准 / 丰富 | 标准 | 标题+描述+文件数+时间最实用，不引入截图复杂度 |
| D4 | 实现方式 | 手写 / 生成式 / 运行时扫描 | 生成式 | 自动发现 + file:// 兼容，与现有"单文件 SPA"哲学一致 |
| D5 | 标签来源 | 手动 / 自动启发式 | 自动启发式 | 减少维护成本，关键词白名单可控 |
| D6 | 视觉风格 | 沿用现有 / 全新设计 | 沿用现有 | 视觉一致性，与 `项目管理AI增强方案/` 形成"系列感" |

---

> **维护者**：Sisyphus · 2026-06-09
> **下一步**：用户审阅本 spec → 确认后调用 `writing-plans` skill 制定实现计划

# MyWord 内容聚合平台 · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 `D:\code\MyWord\` 根目录的主索引页，把仓库内"有读者价值的资产"聚合成一个可双击打开、可搜索、可筛选的卡片网格，配合 `scripts/scan-index.js` 自动维护资产清单。

**Architecture:** 单文件 HTML SPA（继承 `项目管理AI增强方案/index.html` 的 Industrial Editorial 视觉系统） + 预生成 `data.json` + Node 扫描脚本。三文件结构，零构建、零运行时依赖、file:// 兼容。

**Tech Stack:**
- HTML5 + CSS3 (Grid, CSS Variables) + Vanilla JavaScript (ES2022)
- Node.js v18+ 内置 `node --test`（用于扫描脚本 TDD）
- Google Fonts CDN（渐进增强，断网 fallback）

**前置条件：**
- Node.js v18+（本机已验证 v24.5.0）
- 已阅读 spec：`docs/superpowers/specs/2026-06-09-content-aggregation-platform-design.md`
- 工作目录：`D:\code\MyWord\`

**测试策略：**
- 扫描脚本：`node --test`（TDD）
- HTML/JS：手动验证（单文件 SPA 无构建链，引入测试框架会破坏"双击即用"原则）

---

## 文件结构

| 文件 | 角色 | 状态 |
|---|---|---|
| `D:\code\MyWord\index.html` | 主索引页（单文件 SPA） | 新建 |
| `D:\code\MyWord\data.json` | 资产清单（脚本生成） | 新建（Task 13 首次生成） |
| `D:\code\MyWord\scripts\scan-index.js` | 扫描脚本 | 新建 |
| `D:\code\MyWord\scripts\scan-index.test.js` | 扫描脚本测试 | 新建 |
| `D:\code\MyWord\package.json` | Node 项目配置（仅 scripts + name） | 新建 |
| `D:\code\MyWord\README.md` | 项目说明 | 新建 |
| `D:\code\MyWord\.gitignore` | 忽略配置 | 修改（追加 data.json watch 临时文件等） |

**文件职责边界：**
- `scan-index.js` 只关心"扫描 + 输出 JSON"，不涉及任何 HTML
- `index.html` 只关心"读 JSON + 渲染 + 交互"，不写文件
- `data.json` 是唯一数据源，由脚本生成，由 HTML 消费

---

# Task 0 · 初始化项目结构

**Files:**
- Create: `D:\code\MyWord\package.json`
- Modify: `D:\code\MyWord\.gitignore`（如存在）

- [ ] **Step 1: 检查 .gitignore**

```powershell
Test-Path -LiteralPath "D:\code\MyWord\.gitignore"
```

如果存在，读取内容；如果不存在，跳到 Step 3。

- [ ] **Step 2: 追加忽略规则（如 .gitignore 存在）**

在 `.gitignore` 末尾追加：

```
# 内容聚合平台
node_modules/
data.local.json
*.scan-tmp
```

- [ ] **Step 3: 创建 package.json**

文件路径：`D:\code\MyWord\package.json`

```json
{
  "name": "myword-content-hub",
  "version": "1.0.0",
  "private": true,
  "description": "MyWord 内容聚合平台主索引",
  "scripts": {
    "scan": "node scripts/scan-index.js",
    "scan:watch": "node scripts/scan-index.js --watch",
    "test": "node --test scripts/"
  }
}
```

- [ ] **Step 4: 验证 package.json 合法**

```powershell
Get-Content "D:\code\MyWord\package.json" | ConvertFrom-Json
```

Expected: 输出对象无错误（看到 name, version, scripts 字段）。

---

# Task 1 · 编写扫描脚本骨架

**Files:**
- Create: `D:\code\MyWord\scripts\scan-index.js`

- [ ] **Step 1: 创建脚本文件**

文件路径：`D:\code\MyWord\scripts\scan-index.js`

```javascript
#!/usr/bin/env node
/**
 * scan-index.js
 * 扫描 D:\code\MyWord\ 仓库，生成 D:\code\MyWord\data.json
 * 用法：node scripts/scan-index.js [--output PATH] [--watch] [--dry-run]
 */

'use strict';

const fs = require('fs').promises;
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_OUTPUT = path.join(ROOT, 'data.json');

/**
 * 主入口
 */
async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outputPath = args.output || DEFAULT_OUTPUT;
  const dryRun = !!args['dry-run'];
  const watch = !!args.watch;

  if (watch) {
    await runWatch(outputPath);
  } else {
    await runOnce(outputPath, dryRun);
  }
}

/**
 * 解析 CLI 参数
 */
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    }
  }
  return args;
}

/**
 * 扫描并输出一次
 */
async function runOnce(outputPath, dryRun) {
  console.log('[scan] scanning', ROOT);
  const data = await scanRepository(ROOT);
  const json = JSON.stringify(data, null, 2);
  if (dryRun) {
    console.log('[scan] DRY RUN — 不写文件');
    console.log(json.slice(0, 500) + (json.length > 500 ? '...' : ''));
  } else {
    await fs.writeFile(outputPath, json + '\n', 'utf8');
    console.log('[scan] wrote', outputPath, `(${json.length} bytes)`);
  }
}

/**
 * watch 模式：每 5 秒扫一次
 */
async function runWatch(outputPath) {
  console.log('[scan] watch mode — Ctrl+C to stop');
  let lastJson = '';
  const tick = async () => {
    try {
      const data = await scanRepository(ROOT);
      const json = JSON.stringify(data, null, 2);
      if (json !== lastJson) {
        await fs.writeFile(outputPath, json + '\n', 'utf8');
        lastJson = json;
        console.log(`[scan] ${new Date().toISOString()} — ${data.totals.items} items`);
      }
    } catch (err) {
      console.error('[scan] error:', err.message);
    }
  };
  await tick();
  setInterval(tick, 5000);
}

/**
 * 扫描仓库主函数（Task 2-11 逐步实现）
 */
async function scanRepository(rootDir) {
  // 占位 — Task 11 完成
  return {
    version: '1.0.0',
    generatedAt: new Date().toISOString(),
    totals: { items: 0, groups: 0, files: 0 },
    groups: [],
  };
}

main().catch((err) => {
  console.error('[scan] fatal:', err);
  process.exit(1);
});
```

- [ ] **Step 2: 验证脚本能运行（dry-run）**

```powershell
cd D:\code\MyWord
node scripts/scan-index.js --dry-run
```

Expected: 输出 `[scan] DRY RUN — 不写文件`，后跟空 `groups: []` 的 JSON 片段。无 fatal error。

- [ ] **Step 3: 验证 --help（隐式测试 parseArgs）**

```powershell
node scripts/scan-index.js --output test.json
```

Expected: 写入 `D:\code\MyWord\test.json`（含 `groups: []`）。删除该临时文件：

```powershell
Remove-Item "D:\code\MyWord\test.json" -Force
```

- [ ] **Step 4: Commit**

```bash
cd D:\code\MyWord
git add package.json scripts/scan-index.js .gitignore
git commit -m "feat(scan): 初始化扫描脚本骨架 + package.json"
```

---

# Task 2 · 编写第一个测试 + 目录扫描辅助函数

**Files:**
- Create: `D:\code\MyWord\scripts\scan-index.test.js`
- Modify: `D:\code\MyWord\scripts\scan-index.js`

- [ ] **Step 1: 编写失败测试**

文件路径：`D:\code\MyWord\scripts\scan-index.test.js`

```javascript
const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { walkTopLevel, isExcludedDir } = require('./scan-index');

test('walkTopLevel 列出 ROOT 下非排除目录', async () => {
  const root = path.resolve(__dirname, '..');
  const dirs = await walkTopLevel(root);
  // 应包含已知的粒子动画目录
  assert.ok(dirs.some((d) => d.name.startsWith('4.')), '应包含 4.x 编号目录');
  // 应排除 .claude
  assert.ok(!dirs.some((d) => d.name === '.claude'), '不应包含 .claude');
});

test('isExcludedDir 排除隐藏目录与已知工程目录', () => {
  assert.equal(isExcludedDir('.git'), true);
  assert.equal(isExcludedDir('.claude'), true);
  assert.equal(isExcludedDir('node_modules'), true);
  assert.equal(isExcludedDir('项目管理AI增强方案'), false);
  assert.equal(isExcludedDir('小红书笔记'), false);
});
```

- [ ] **Step 2: 运行测试确认失败**

```powershell
cd D:\code\MyWord
npm test
```

Expected: FAIL — `Cannot find module './scan-index'` 或 `walkTopLevel is not a function`。

- [ ] **Step 3: 实现 walkTopLevel + isExcludedDir**

在 `D:\code\MyWord\scripts\scan-index.js` 中，将 `scanRepository` 函数替换为：

```javascript
const EXCLUDED_TOP_LEVEL = new Set([
  '.git', '.claude', '.sisyphus', '.clauge-worktrees',
  '.playwright-mcp', '.antigravitycli', '.vscode',
  'node_modules', 'scripts', 'mlruns', 'cors-proxy',
  'browser-use-test', 'research', 'work', 'skills', 'docs',
  '内容', // 发布流程工作流
]);

/**
 * 判定目录是否在排除清单
 */
function isExcludedDir(name) {
  if (name.startsWith('.')) return true;
  return EXCLUDED_TOP_LEVEL.has(name);
}

/**
 * 列出 ROOT 顶层非排除的目录
 */
async function walkTopLevel(rootDir) {
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  const dirs = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (isExcludedDir(e.name)) continue;
    dirs.push({
      name: e.name,
      fullPath: path.join(rootDir, e.name),
    });
  }
  return dirs;
}

/**
 * 扫描仓库主函数（Task 11 完成版本）
 */
async function scanRepository(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  // TODO Task 3-11: 分类 + 提取 + 输出
  return {
    version: '1.0.0',
    generatedAt: new Date().toISOString(),
    totals: { items: 0, groups: 0, files: 0 },
    groups: [],
    _topDirs: topDirs.map((d) => d.name), // 临时供 Task 3 验证
  };
}

module.exports = {
  walkTopLevel,
  isExcludedDir,
  scanRepository,
};
```

并在文件顶部 `const fs = require('fs').promises;` 后添加：

```javascript
const fsSync = require('fs');
```

修改 `walkTopLevel` 实现使用 `fsSync.readdirSync` 还是 `fs.readdir`？用 `fs.readdir`：

```javascript
async function walkTopLevel(rootDir) {
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  // ... (上面已写)
}
```

- [ ] **Step 4: 运行测试确认通过**

```powershell
cd D:\code\MyWord
npm test
```

Expected: 2 个 test 全部 PASS。

- [ ] **Step 5: Commit**

```bash
cd D:\code\MyWord
git add scripts/scan-index.js scripts/scan-index.test.js
git commit -m "feat(scan): 顶层目录扫描 + 排除清单"
```

---

# Task 3 · 实现 particles 分组扫描

**Files:**
- Modify: `D:\code\MyWord\scripts\scan-index.js`
- Modify: `D:\code\MyWord\scripts\scan-index.test.js`

- [ ] **Step 1: 添加测试**

在 `D:\code\MyWord\scripts\scan-index.test.js` 末尾追加：

```javascript
const { scanParticles } = require('./scan-index');

test('scanParticles 匹配 4.x ~ 10.x 编号目录', async () => {
  const root = path.resolve(__dirname, '..');
  const group = await scanParticles(root);
  assert.ok(group, '应返回 group 对象');
  assert.equal(group.id, 'particles');
  assert.ok(group.items.length >= 1, '应至少扫描到 1 个粒子项目');
  // 第一个 item 应有 path 指向 index.html
  const first = group.items[0];
  assert.match(first.path, /^[0-9]+\..+\/index\.html$/);
  assert.ok(first.id, 'id 非空');
  assert.ok(first.title, 'title 非空');
});
```

- [ ] **Step 2: 跑测试确认失败**

```powershell
cd D:\code\MyWord
npm test
```

Expected: FAIL — `scanParticles is not a function`。

- [ ] **Step 3: 实现 scanParticles + 通用工具**

在 `D:\code\MyWord\scripts\scan-index.js` 中添加（在 `isExcludedDir` 之前或合适位置）：

```javascript
/**
 * 编号目录粒子项目：4.x ~ 10.x
 */
async function scanParticles(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const items = [];
  for (const d of topDirs) {
    if (!/^[0-9]+\..+/.test(d.name)) continue;
    const indexPath = path.join(d.fullPath, 'index.html');
    if (!(await fileExists(indexPath))) continue;
    const title = await readHtmlTitle(indexPath) || d.name;
    const desc = await readHtmlDescription(indexPath) || '';
    const fileCount = await countFiles(d.fullPath);
    const lastModified = await latestMtime(d.fullPath);
    items.push({
      id: toKebabCase(d.name),
      title,
      desc,
      path: `${d.name}/index.html`,
      fileCount,
      lastModified,
      tags: extractTags(`${d.name} ${title} ${desc}`),
    });
  }
  return {
    id: 'particles',
    label: '粒子动画作品',
    color: '#06B6D4',
    description: 'GSAP / Three.js 粒子动画视频作品',
    items,
  };
}

// ============ 工具函数（其他 Task 也会用到，先在此引入） ============

/**
 * 文件是否存在
 */
async function fileExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

/**
 * 读取 HTML 的 <title>
 */
async function readHtmlTitle(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}

/**
 * 读取 HTML 的 <meta name="description">
 */
async function readHtmlDescription(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}

/**
 * 递归统计文件数（排除常见目录）
 */
async function countFiles(dir) {
  let count = 0;
  const stack = [dir];
  while (stack.length) {
    const cur = stack.pop();
    let entries;
    try {
      entries = await fs.readdir(cur, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const e of entries) {
      if (e.name === 'node_modules' || e.name === '.git' || e.name === 'renders') continue;
      const full = path.join(cur, e.name);
      if (e.isDirectory()) {
        stack.push(full);
      } else if (/\.(html|md|mp4|json)$/i.test(e.name)) {
        count++;
      }
    }
  }
  return count;
}

/**
 * 取目录下所有文件最新的 mtime
 */
async function latestMtime(dir) {
  let latest = 0;
  const stack = [dir];
  while (stack.length) {
    const cur = stack.pop();
    let entries;
    try {
      entries = await fs.readdir(cur, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const e of entries) {
      if (e.name === 'node_modules' || e.name === '.git' || e.name === 'renders') continue;
      const full = path.join(cur, e.name);
      if (e.isDirectory()) {
        stack.push(full);
      } else {
        try {
          const stat = await fs.stat(full);
          if (stat.mtimeMs > latest) latest = stat.mtimeMs;
        } catch {}
      }
    }
  }
  return latest ? new Date(latest).toISOString() : '';
}

/**
 * 中文 + 符号字符串转 kebab-case id
 */
function toKebabCase(s) {
  return s
    .replace(/^[0-9]+\./, '')
    .replace(/[·・\s]+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5-]/g, '')
    .toLowerCase()
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * 标签启发式
 */
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

function extractTags(text) {
  const tags = [];
  for (const [tag, regex] of Object.entries(TAG_KEYWORDS)) {
    if (regex.test(text)) tags.push(tag);
  }
  return tags;
}
```

并在 `module.exports` 中追加：

```javascript
module.exports = {
  walkTopLevel,
  isExcludedDir,
  scanParticles,
  scanRepository,
  // 工具（供后续 Task 复用）
  readHtmlTitle,
  readHtmlDescription,
  countFiles,
  latestMtime,
  toKebabCase,
  extractTags,
};
```

- [ ] **Step 4: 跑测试确认通过**

```powershell
cd D:\code\MyWord
npm test
```

Expected: 3 个 test 全部 PASS。

- [ ] **Step 5: Commit**

```bash
cd D:\code\MyWord
git add scripts/scan-index.js scripts/scan-index.test.js
git commit -m "feat(scan): particles 分组 + 通用工具（title/desc/count/mtime/tags）"
```

---

# Task 4 · 实现 project-plan / xhs-notes / specs / videos 分组

**Files:**
- Modify: `D:\code\MyWord\scripts\scan-index.js`
- Modify: `D:\code\MyWord\scripts\scan-index.test.js`

- [ ] **Step 1: 添加 4 个测试**

在 `D:\code\MyWord\scripts\scan-index.test.js` 末尾追加：

```javascript
const {
  scanProjectPlan,
  scanXhsNotes,
  scanSpecs,
  scanVideos,
} = require('./scan-index');

test('scanProjectPlan 扫描 项目管理AI增强方案', async () => {
  const root = path.resolve(__dirname, '..');
  const group = await scanProjectPlan(root);
  assert.equal(group.id, 'project-plan');
  assert.ok(group.items.length >= 1);
  assert.match(group.items[0].path, /项目管理AI增强方案/);
});

test('scanXhsNotes 扫描 小红书笔记 下的 .md', async () => {
  const root = path.resolve(__dirname, '..');
  const group = await scanXhsNotes(root);
  assert.equal(group.id, 'xhs-notes');
  assert.ok(group.items.length >= 1);
  for (const item of group.items) {
    assert.ok(item.path.endsWith('.md') || item.path.endsWith('.html'));
  }
});

test('scanSpecs 扫描 项目文档 下 iWork 系列 + specs/ 子目录', async () => {
  const root = path.resolve(__dirname, '..');
  const group = await scanSpecs(root);
  assert.equal(group.id, 'specs');
  // iWork 系列应有 5 个文件
  const iworkCount = group.items.filter((i) => /iWork/.test(i.title)).length;
  assert.ok(iworkCount >= 1, '应至少 1 个 iWork 文档');
});

test('scanVideos 扫描 xhs-output 下一级目录（排除 renders）', async () => {
  const root = path.resolve(__dirname, '..');
  const group = await scanVideos(root);
  assert.equal(group.id, 'videos');
  assert.ok(group.items.length >= 1);
  // 不应包含 renders 子目录（虽然在 xhs-output 内）
  assert.ok(!group.items.some((i) => /renders/.test(i.path)));
});
```

- [ ] **Step 2: 跑测试确认失败**

```powershell
cd D:\code\MyWord
npm test
```

Expected: FAIL — `scanProjectPlan is not a function` 等。

- [ ] **Step 3: 实现 4 个 scan 函数**

在 `D:\code\MyWord\scripts\scan-index.js` 中 `scanParticles` 后追加：

```javascript
/**
 * 项目方案分组：项目管理AI增强方案
 */
async function scanProjectPlan(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '项目管理AI增强方案');
  if (!dir) return emptyGroup('project-plan', '项目方案', '#3B82F6', '项目管理方案文档');

  const indexPath = path.join(dir.fullPath, 'index.html');
  const title = (await readHtmlTitle(indexPath)) || dir.name;
  const desc = (await readHtmlDescription(indexPath)) || '基于 Excel 整理的项目管理方案';
  return {
    id: 'project-plan',
    label: '项目方案',
    color: '#3B82F6',
    description: '项目管理方案与决策框架',
    items: [
      {
        id: 'pm-ai-enhancement',
        title,
        desc,
        path: `${dir.name}/index.html`,
        fileCount: await countFiles(dir.fullPath),
        lastModified: await latestMtime(dir.fullPath),
        tags: extractTags(`${title} ${desc}`),
      },
    ],
  };
}

/**
 * 小红书笔记分组：小红书笔记/*.md
 */
async function scanXhsNotes(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '小红书笔记');
  if (!dir) return emptyGroup('xhs-notes', '小红书笔记', '#F59E0B', '小红书内容草稿');

  const items = [];
  const entries = await fs.readdir(dir.fullPath, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isFile() || !/\.md$/i.test(e.name)) continue;
    const filePath = path.join(dir.fullPath, e.name);
    const title = await readMdTitle(filePath) || e.name.replace(/\.md$/i, '');
    const desc = await readMdFirstParagraph(filePath);
    items.push({
      id: toKebabCase(e.name.replace(/\.md$/i, '')),
      title,
      desc,
      path: `${dir.name}/${e.name}`,
      fileCount: 1,
      lastModified: (await fs.stat(filePath)).mtime.toISOString(),
      tags: extractTags(`${title} ${desc} ${e.name}`),
    });
  }
  return {
    id: 'xhs-notes',
    label: '小红书笔记',
    color: '#F59E0B',
    description: '小红书内容草稿与发布笔记',
    items,
  };
}

/**
 * 项目文档 / Specs 分组：项目文档/*.md + 项目文档/ specs/*.md
 */
async function scanSpecs(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '项目文档');
  if (!dir) return emptyGroup('specs', '项目文档 / Specs', '#10B981', 'iWork 系列 + 技术规范');

  const items = [];
  // 顶层 .md
  const topEntries = await fs.readdir(dir.fullPath, { withFileTypes: true });
  for (const e of topEntries) {
    if (e.isFile() && /\.md$/i.test(e.name)) {
      const fp = path.join(dir.fullPath, e.name);
      items.push(await makeMdItem(fp, e.name, dir.name));
    }
  }
  // ' specs' 子目录（含前导空格）
  const specsSub = topEntries.find((e) => e.isDirectory() && e.name === ' specs');
  if (specsSub) {
    const subEntries = await fs.readdir(path.join(dir.fullPath, specsSub.name), { withFileTypes: true });
    for (const e of subEntries) {
      if (e.isFile() && /\.md$/i.test(e.name)) {
        const fp = path.join(dir.fullPath, specsSub.name, e.name);
        items.push(await makeMdItem(fp, e.name, `${dir.name}/${specsSub.name}`));
      }
    }
  }
  return {
    id: 'specs',
    label: '项目文档 / Specs',
    color: '#10B981',
    description: 'iWork 系列与技术规范',
    items,
  };
}

/**
 * 视频作品分组：xhs-output 下一级目录（排除 renders/ 与隐藏）
 */
async function scanVideos(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === 'xhs-output');
  if (!dir) return emptyGroup('videos', '视频作品', '#EF4444', '小红书视频输出');

  const items = [];
  const entries = await fs.readdir(dir.fullPath, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (e.name === 'renders' || e.name.startsWith('.')) continue;
    const sub = path.join(dir.fullPath, e.name);
    const indexPath = path.join(sub, 'index.html');
    const hasIndex = await fileExists(indexPath);
    const title = hasIndex ? (await readHtmlTitle(indexPath)) || e.name : e.name;
    const desc = hasIndex ? await readHtmlDescription(indexPath) : '视频作品输出';
    items.push({
      id: toKebabCase(e.name),
      title,
      desc,
      path: `${dir.name}/${e.name}${hasIndex ? '/index.html' : ''}`,
      fileCount: await countFiles(sub),
      lastModified: await latestMtime(sub),
      tags: extractTags(`${title} ${desc} ${e.name}`),
    });
  }
  return {
    id: 'videos',
    label: '视频作品',
    color: '#EF4444',
    description: '小红书视频输出',
    items,
  };
}

// ============ MD 相关工具 ============

async function readMdTitle(mdPath) {
  try {
    const content = await fs.readFile(mdPath, 'utf8');
    // 优先 frontmatter title
    const fm = content.match(/^---\n[\s\S]*?title:\s*["']?(.+?)["']?\n[\s\S]*?---/);
    if (fm) return fm[1].trim();
    // 否则第一行 # 标题
    const h1 = content.match(/^#\s+(.+?)$/m);
    return h1 ? h1[1].trim() : '';
  } catch {
    return '';
  }
}

async function readMdFirstParagraph(mdPath) {
  try {
    const content = await fs.readFile(mdPath, 'utf8');
    // 跳过 frontmatter 和标题
    const lines = content.split('\n');
    let started = false;
    const buf = [];
    for (const line of lines) {
      if (!started) {
        if (line.startsWith('#') || line.startsWith('---') || line.trim() === '') continue;
        started = true;
      }
      if (started) {
        if (line.trim() === '' && buf.length) break;
        buf.push(line);
      }
      if (buf.join(' ').length > 100) break;
    }
    return buf.join(' ').slice(0, 100);
  } catch {
    return '';
  }
}

async function makeMdItem(filePath, fileName, parentPath) {
  const title = (await readMdTitle(filePath)) || fileName.replace(/\.md$/i, '');
  const desc = await readMdFirstParagraph(filePath);
  const stat = await fs.stat(filePath);
  return {
    id: toKebabCase(fileName.replace(/\.md$/i, '')),
    title,
    desc,
    path: `${parentPath}/${fileName}`,
    fileCount: 1,
    lastModified: stat.mtime.toISOString(),
    tags: extractTags(`${title} ${desc} ${fileName}`),
  };
}

function emptyGroup(id, label, color, description) {
  return { id, label, color, description, items: [] };
}
```

更新 `module.exports`：

```javascript
module.exports = {
  walkTopLevel,
  isExcludedDir,
  scanParticles,
  scanProjectPlan,
  scanXhsNotes,
  scanSpecs,
  scanVideos,
  scanRepository,
  readHtmlTitle,
  readHtmlDescription,
  countFiles,
  latestMtime,
  toKebabCase,
  extractTags,
  readMdTitle,
  readMdFirstParagraph,
};
```

- [ ] **Step 4: 跑测试确认通过**

```powershell
cd D:\code\MyWord
npm test
```

Expected: 7 个 test 全部 PASS。

- [ ] **Step 5: Commit**

```bash
cd D:\code\MyWord
git add scripts/scan-index.js scripts/scan-index.test.js
git commit -m "feat(scan): 4 个剩余分组（project-plan/xhs-notes/specs/videos）"
```

---

# Task 5 · 整合 5 个分组 + 计算 totals

**Files:**
- Modify: `D:\code\MyWord\scripts\scan-index.js`
- Modify: `D:\code\MyWord\scripts\scan-index.test.js`

- [ ] **Step 1: 添加测试**

在测试文件末尾追加：

```javascript
test('scanRepository 整合 5 个分组，totals 正确', async () => {
  const root = path.resolve(__dirname, '..');
  const data = await scanRepository(root);
  assert.equal(data.version, '1.0.0');
  assert.equal(data.groups.length, 5);
  assert.ok(data.generatedAt);
  // totals.items = 所有分组 items 累加
  const expected = data.groups.reduce((s, g) => s + g.items.length, 0);
  assert.equal(data.totals.items, expected);
  assert.equal(data.totals.groups, 5);
  assert.ok(data.totals.files > 0);
});
```

- [ ] **Step 2: 跑测试确认失败**

```powershell
cd D:\code\MyWord
npm test
```

Expected: FAIL — `data.groups.length` 不为 5（仍为 0）。

- [ ] **Step 3: 重写 scanRepository**

将 `scanRepository` 替换为：

```javascript
async function scanRepository(rootDir) {
  const groups = await Promise.all([
    scanParticles(rootDir),
    scanProjectPlan(rootDir),
    scanXhsNotes(rootDir),
    scanSpecs(rootDir),
    scanVideos(rootDir),
  ]);
  const items = groups.reduce((s, g) => s + g.items.length, 0);
  const files = groups.reduce((s, g) => s + g.items.reduce((ss, it) => ss + (it.fileCount || 0), 0), 0);
  return {
    version: '1.0.0',
    generatedAt: new Date().toISOString(),
    totals: { items, groups: groups.length, files },
    groups,
  };
}
```

- [ ] **Step 4: 跑测试确认通过**

```powershell
cd D:\code\MyWord
npm test
```

Expected: 8 个 test 全部 PASS。

- [ ] **Step 5: 真实运行 + 检查 data.json 形状**

```powershell
cd D:\code\MyWord
node scripts/scan-index.js
Get-Content "D:\code\MyWord\data.json" | Select-Object -First 30
```

Expected: 看到 `data.json` 写入，第一行 `"version": "1.0.0"`，groups 数组 5 项，totals 数字合理（基于实际扫描结果）。

- [ ] **Step 6: Commit**

```bash
cd D:\code\MyWord
git add scripts/scan-index.js scripts/scan-index.test.js data.json
git commit -m "feat(scan): 整合 5 分组 + totals + 首版 data.json"
```

---

# Task 6 · HTML 骨架 + 设计 tokens

**Files:**
- Create: `D:\code\MyWord\index.html`

- [ ] **Step 1: 创建 index.html 骨架**

文件路径：`D:\code\MyWord\index.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MyWord · 内容管理中枢</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@400;700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0A0E1A;
    --bg-elev: #131825;
    --bg-elev-2: #1A2236;
    --border: #1F2940;
    --border-strong: #2D3A5C;
    --text: #E8ECF1;
    --text-mute: #94A3B8;
    --text-faint: #64748B;

    --waterfall: #3B82F6;
    --agile: #F59E0B;
    --ai: #06B6D4;
    --success: #10B981;
    --danger: #EF4444;

    --grid-line: rgba(148,163,184,.05);

    --r-sm: 4px;
    --r-md: 8px;
    --r-lg: 14px;

    --f-display: 'Anton', 'Noto Serif SC', serif;
    --f-serif: 'Noto Serif SC', serif;
    --f-body: 'IBM Plex Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    --f-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--f-body);
    font-size: 15px;
    line-height: 1.65;
    min-height: 100vh;
    background-image:
      linear-gradient(var(--grid-line) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 48px 48px;
  }

  /* ===== Hero ===== */
  .hero {
    padding: 64px 48px 48px;
    border-bottom: 1px solid var(--border);
  }
  .hero h1 {
    font-family: var(--f-display);
    font-size: 96px;
    font-weight: 400;
    line-height: 1;
    letter-spacing: -0.02em;
    color: var(--text);
  }
  .hero h1 .cn {
    font-family: var(--f-serif);
    font-weight: 900;
  }
  .hero .tagline {
    font-family: var(--f-serif);
    font-size: 18px;
    color: var(--text-mute);
    margin-top: 12px;
  }
  .hero .stats {
    display: flex;
    gap: 32px;
    margin-top: 24px;
    font-family: var(--f-mono);
    font-size: 13px;
    color: var(--text-faint);
  }
  .hero .stats strong {
    color: var(--text);
    font-weight: 500;
    margin-right: 4px;
  }

  /* ===== Search ===== */
  .search-wrap {
    margin-top: 32px;
  }
  .search {
    width: 100%;
    max-width: 480px;
    padding: 12px 16px;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    color: var(--text);
    font-family: var(--f-body);
    font-size: 14px;
    outline: none;
    transition: border-color .15s;
  }
  .search:focus {
    border-color: var(--border-strong);
  }
  .search::placeholder { color: var(--text-faint); }
</style>
</head>
<body>
  <header class="hero">
    <h1><span class="cn">MyWord</span></h1>
    <p class="tagline">内容管理中枢 · 一页通览所有产出</p>
    <div class="stats" id="stats"></div>
    <div class="search-wrap">
      <input type="search" class="search" id="search" placeholder="搜索资产 · 标题、描述、标签" aria-label="搜索资产">
    </div>
  </header>

  <main id="groups" aria-live="polite">
    <p style="padding:48px;color:var(--text-faint);font-family:var(--f-mono);font-size:13px;">加载中...</p>
  </main>

  <script>
    // 任务 7-13 在此填充
  </script>
</body>
</html>
```

- [ ] **Step 2: 浏览器验证骨架**

双击 `D:\code\MyWord\index.html`，预期：
- 看到 "MyWord" 大标题
- 看到"内容管理中枢 · 一页通览所有产出"副标题
- 看到搜索框
- 主区域显示"加载中..."
- 无 console error

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add index.html
git commit -m "feat(html): 骨架 + Hero + 搜索框 + 设计 tokens"
```

---

# Task 7 · HTML 加载 data.json + 渲染分组

**Files:**
- Modify: `D:\code\MyWord\index.html`

- [ ] **Step 1: 在 `<script>` 中添加加载与渲染逻辑**

替换 `<script>...</script>` 块为：

```html
<script>
  (async function main() {
    const groupsEl = document.getElementById('groups');
    const statsEl = document.getElementById('stats');
    let DATA = null;

    try {
      const res = await fetch('./data.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      DATA = await res.json();
    } catch (err) {
      groupsEl.innerHTML = renderFatal(err.message);
      return;
    }

    renderStats(DATA.totals, DATA.generatedAt);
    renderGroups(DATA.groups);
    setupFilter();
  })();

  function renderStats(totals, generatedAt) {
    const el = document.getElementById('stats');
    const ago = timeAgo(generatedAt);
    el.innerHTML = `
      <span><strong>${totals.items}</strong>资产</span>
      <span><strong>${totals.groups}</strong>分组</span>
      <span><strong>${totals.files}</strong>文件</span>
      <span>更新于 ${ago}</span>
    `;
  }

  function renderGroups(groups) {
    const el = document.getElementById('groups');
    el.innerHTML = groups.map(renderGroup).join('');
  }

  function renderGroup(g, idx) {
    if (!g.items.length) return '';
    const itemsHtml = g.items.map((it, i) => renderCard(it, g, idx, i)).join('');
    return `
      <section class="group" id="group-${g.id}" data-group="${g.id}">
        <header class="group-head">
          <span class="group-dot" style="background:${g.color}"></span>
          <h2 class="group-title">
            <span class="group-num">${String(idx + 1).padStart(2, '0')}</span>
            ${escapeHtml(g.label)}
          </h2>
          <span class="group-count">${g.items.length}</span>
        </header>
        <p class="group-desc">${escapeHtml(g.description || '')}</p>
        <div class="grid">${itemsHtml}</div>
      </section>
    `;
  }

  function renderCard(it, g, groupIdx, itemIdx) {
    const num = String(groupIdx * 10 + itemIdx + 1).padStart(2, '0');
    const tagsHtml = (it.tags || []).map(t => `<span class="tag" data-tag="${escapeHtml(t)}">#${escapeHtml(t)}</span>`).join('');
    return `
      <a class="card" href="${escapeAttr(it.path)}" tabindex="0"
         data-title="${escapeAttr(it.title.toLowerCase())}"
         data-desc="${escapeAttr((it.desc || '').toLowerCase())}"
         data-tags="${escapeAttr((it.tags || []).join(',').toLowerCase())}">
        <div class="card-head">
          <span class="card-group" style="color:${g.color}">${escapeHtml(g.label)}</span>
          <span class="card-num">#${num}</span>
        </div>
        <h3 class="card-title">${escapeHtml(it.title)}</h3>
        <p class="card-desc">${escapeHtml(it.desc || '')}</p>
        <div class="card-tags">${tagsHtml}</div>
        <div class="card-meta">
          <span>${it.fileCount} 文件</span>
          <span class="dot">·</span>
          <span>${formatDate(it.lastModified)}</span>
        </div>
      </a>
    `;
  }

  function setupFilter() {
    const searchEl = document.getElementById('search');
    const applyNow = () => {
      applyFilter(searchEl.value.trim().toLowerCase(), getActiveTags());
    };
    searchEl.addEventListener('input', applyNow);
    // 任务 9：在此处追加 .tag click 监听
  }

  function getActiveTags() {
    return Array.from(document.querySelectorAll('.tag.active'))
      .map((t) => t.dataset.tag.toLowerCase());
  }

  function applyFilter(query, activeTags) {
    const cards = document.querySelectorAll('.card');
    let visible = 0;
    cards.forEach((card) => {
      const matchQuery = !query ||
        card.dataset.title.includes(query) ||
        card.dataset.desc.includes(query) ||
        card.dataset.tags.includes(query);
      const cardTags = (card.dataset.tags || '').split(',').filter(Boolean);
      const matchTags = !activeTags.length ||
        activeTags.every((t) => cardTags.includes(t));
      const show = matchQuery && matchTags;
      card.classList.toggle('hidden', !show);
      if (show) visible++;
    });
    document.querySelectorAll('.group').forEach((g) => {
      const anyVisible = g.querySelector('.card:not(.hidden)');
      g.classList.toggle('hidden', !anyVisible);
    });
    renderEmptyState(visible === 0);
  }

  function renderEmptyState(show) {
    let empty = document.getElementById('empty-state');
    if (show) {
      if (!empty) {
        empty = document.createElement('div');
        empty.id = 'empty-state';
        empty.className = 'empty';
        empty.innerHTML = `
          <h2>没有匹配资产</h2>
          <p>尝试清空搜索或标签筛选条件</p>
          <p style="margin-top:16px;"><button id="reset-filter" style="cursor:pointer;padding:8px 16px;background:var(--bg-elev);color:var(--text);border:1px solid var(--border);border-radius:6px;">清空筛选</button></p>
        `;
        document.querySelector('main').appendChild(empty);
        document.getElementById('reset-filter').addEventListener('click', () => {
          document.getElementById('search').value = '';
          document.querySelectorAll('.tag.active').forEach((t) => t.classList.remove('active'));
          applyFilter('', []);
        });
      }
    } else if (empty) {
      empty.remove();
    }
  }

  function renderFatal(msg) {
    return `<div class="fatal">
      <h2>无法加载 data.json</h2>
      <p>${escapeHtml(msg)}</p>
      <p>请在仓库根目录运行：<code>node scripts/scan-index.js</code></p>
    </div>`;
  }

  // ===== 工具 =====
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  function escapeAttr(s) { return escapeHtml(s); }
  function timeAgo(iso) {
    if (!iso) return '未知';
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return '刚刚';
    if (m < 60) return `${m} 分钟前`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h} 小时前`;
    const d = Math.floor(h / 24);
    return `${d} 天前`;
  }
  function formatDate(iso) {
    if (!iso) return '';
    return new Date(iso).toISOString().slice(0, 10);
  }
</script>
```

并在 `<style>` 中追加卡片/分组样式（在 `</style>` 之前）：

```css
  /* ===== Group section ===== */
  .group {
    padding: 48px;
    border-bottom: 1px solid var(--border);
  }
  .group-head {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .group-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }
  .group-num {
    font-family: var(--f-display);
    font-size: 14px;
    color: var(--text-faint);
    letter-spacing: 0.1em;
  }
  .group-title {
    font-family: var(--f-serif);
    font-size: 28px;
    font-weight: 700;
    color: var(--text);
    display: flex;
    align-items: baseline;
    gap: 12px;
  }
  .group-count {
    font-family: var(--f-mono);
    font-size: 13px;
    color: var(--text-faint);
    margin-left: auto;
  }
  .group-desc {
    font-size: 13px;
    color: var(--text-mute);
    margin-top: 8px;
    margin-bottom: 24px;
  }

  /* ===== Card grid ===== */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }

  /* ===== Card ===== */
  .card {
    display: block;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: 20px;
    text-decoration: none;
    color: inherit;
    transition: transform .15s, border-color .15s, box-shadow .15s;
    position: relative;
  }
  .card:hover, .card:focus {
    transform: translateY(-4px);
    border-color: var(--border-strong);
    box-shadow: 0 16px 40px -20px rgba(0,0,0,.6);
    outline: none;
  }
  .card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .card-group {
    font-family: var(--f-mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .card-num {
    font-family: var(--f-display);
    font-size: 20px;
    color: var(--text-faint);
  }
  .card-title {
    font-family: var(--f-serif);
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.3;
  }
  .card-desc {
    font-size: 13px;
    color: var(--text-mute);
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    min-height: 2.6em;
  }
  .card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
  }
  .tag {
    font-family: var(--f-mono);
    font-size: 11px;
    color: var(--text-faint);
    background: var(--bg-elev-2);
    padding: 2px 8px;
    border-radius: var(--r-sm);
    cursor: pointer;
    transition: color .15s, background .15s;
  }
  .tag:hover {
    color: var(--text);
    background: var(--border);
  }
  .tag.active {
    color: var(--ai);
    background: rgba(6,182,212,.15);
  }
  .card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    font-family: var(--f-mono);
    font-size: 11px;
    color: var(--text-faint);
  }
  .card-meta .dot { opacity: .5; }

  /* ===== Empty / Fatal ===== */
  .empty, .fatal {
    padding: 96px 48px;
    text-align: center;
    color: var(--text-mute);
  }
  .empty h2, .fatal h2 {
    font-family: var(--f-serif);
    font-size: 20px;
    margin-bottom: 12px;
  }
  .fatal code {
    font-family: var(--f-mono);
    background: var(--bg-elev);
    padding: 2px 8px;
    border-radius: var(--r-sm);
  }

  /* ===== Hidden state ===== */
  .card.hidden { display: none; }
  .group.hidden { display: none; }
```

- [ ] **Step 2: 浏览器验证**

双击 `D:\code\MyWord\index.html`，预期：
- Hero 显示 "24 资产 · 5 分组 · 187 文件"（具体数字取决于扫描结果）
- 5 个分组依次排开
- 每个分组下卡片正常显示
- 鼠标悬停卡片有上浮效果
- 点击卡片能跳转到对应 index.html
- 无 console error

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add index.html
git commit -m "feat(html): 加载 data.json + 渲染分组与卡片 + 样式系统"
```

---

# Task 8 · 搜索过滤验证

**Files:** 无新增/修改（功能已在 Task 7 一并实现）

- [ ] **Step 1: 浏览器验证搜索**

双击 `D:\code\MyWord\index.html`，逐项验证：

- 在搜索框输入"鲸鱼" → 只显示含"鲸鱼"的卡片，其他隐藏
- 输入"管理" → 只显示管理相关卡片
- 清空搜索框 → 全部恢复显示
- 不匹配的关键词（如"xxxxxx"）→ 显示"没有匹配资产" + "清空筛选"按钮
- 点击"清空筛选"按钮 → 搜索框清空 + 所有标签取消激活

- [ ] **Step 2: 无 commit（仅验证）**

如验证通过，无需 commit。

---

# Task 9 · 标签 chip 过滤

**Files:**
- Modify: `D:\code\MyWord\index.html`

- [ ] **Step 1: 在 setupFilter 中添加 chip 监听**

将 `setupFilter` 函数（当前是 Task 7 写的版本）替换为：

```javascript
  function setupFilter() {
    const searchEl = document.getElementById('search');
    const applyNow = () => {
      applyFilter(searchEl.value.trim().toLowerCase(), getActiveTags());
    };
    searchEl.addEventListener('input', applyNow);
    // 事件委托：监听所有 .tag 点击
    document.addEventListener('click', (e) => {
      const tag = e.target.closest('.tag');
      if (!tag) return;
      e.preventDefault(); // 阻止冒泡到卡片
      tag.classList.toggle('active');
      applyNow();
    });
  }
```

- [ ] **Step 2: 浏览器验证**

- 点击任一卡片上的 #GSAP 标签 → 卡片上的该标签高亮（青色背景），且筛选后只显示含 GSAP 的卡片
- 再点击另一标签（如 #AI）→ 多个标签 AND 关系，两个标签共有的卡片显示
- 再次点击已激活标签 → 取消激活，恢复过滤
- 在搜索框中输入内容时 + 激活标签 → 双重过滤生效

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add index.html
git commit -m "feat(html): 标签 chip 过滤（AND 多选）"
```

---

# Task 10 · 键盘快捷键

**Files:**
- Modify: `D:\code\MyWord\index.html`

- [ ] **Step 1: 添加快捷键处理**

在 `setupFilter()` 函数之后添加：

```javascript
  // ===== 键盘快捷键（Task 10） =====
  let lastG = 0;
  document.addEventListener('keydown', (e) => {
    const tag = (e.target.tagName || '').toLowerCase();
    const inField = tag === 'input' || tag === 'textarea';

    // Esc — 清空搜索
    if (e.key === 'Escape') {
      const s = document.getElementById('search');
      if (s.value) {
        s.value = '';
        applyFilter('', getActiveTags());
        e.preventDefault();
      }
      if (inField) e.target.blur();
      return;
    }
    // / — 聚焦搜索（任何非输入态）
    if (e.key === '/' && !inField) {
      e.preventDefault();
      document.getElementById('search').focus();
      return;
    }
    // gg — 跳顶（200ms 内连按两次 g）
    if (e.key === 'g' && !inField) {
      const now = Date.now();
      if (now - lastG < 200) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        lastG = 0;
      } else {
        lastG = now;
      }
    }
  });
```

- [ ] **Step 2: 浏览器验证**

- 按 `/` → 搜索框聚焦（光标在搜索框中）
- 在搜索框中按 `Esc` → 清空内容 + 失焦
- 不在搜索框时按 `g g`（200ms 内连按两次）→ 页面平滑滚动到顶部
- 在搜索框中输入时按 `g` → 不会触发跳顶（因 `inField` 判断）

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add index.html
git commit -m "feat(html): 键盘快捷键（/ 搜索、Esc 清空、gg 跳顶）"
```

---

# Task 11 · 响应式 + 移动端适配

**Files:**
- Modify: `D:\code\MyWord\index.html`

- [ ] **Step 1: 在 `<style>` 中追加响应式断点**

在 `</style>` 之前添加：

```css
  /* ===== Responsive ===== */
  @media (max-width: 720px) {
    .hero { padding: 40px 24px 32px; }
    .hero h1 { font-size: 56px; }
    .hero .tagline { font-size: 16px; }
    .hero .stats { flex-wrap: wrap; gap: 16px; font-size: 12px; }
    .group { padding: 32px 24px; }
    .group-title { font-size: 22px; }
    .grid { grid-template-columns: 1fr; }
  }
  @media (max-width: 480px) {
    .hero h1 { font-size: 40px; }
  }
```

- [ ] **Step 2: 浏览器验证（移动端模拟）**

- Chrome DevTools → Toggle Device Toolbar（Ctrl+Shift+M）
- iPhone 12 Pro 视口：标题缩小、卡片单列、间距紧凑
- iPad 视口：卡片 2 列
- 桌面端：恢复正常布局

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add index.html
git commit -m "feat(html): 响应式（移动端单列、紧凑间距）"
```

---

# Task 12 · README

**Files:**
- Create: `D:\code\MyWord\README.md`

- [ ] **Step 1: 检查 README 是否已存在**

```powershell
Test-Path -LiteralPath "D:\code\MyWord\README.md"
```

如果存在，备份为 `README.md.bak` 并删除原文件（避免覆盖用户已有内容）：

```powershell
Move-Item "D:\code\MyWord\README.md" "D:\code\MyWord\README.md.bak" -Force
```

如果不存在，直接创建。

- [ ] **Step 2: 写入 README.md**

```markdown
# MyWord · 内容管理中枢

> **一页通览所有产出** · 双击 `index.html` 即可打开

## 一、这是什么

`MyWord` 是一个内容仓库索引页。把仓库里散落在各子目录的"有读者价值的资产"——粒子动画项目、项目方案、小红书笔记、技术规范、视频作品——聚合成一个可搜索、可筛选的卡片网格。

**特点**：
- 单文件 HTML SPA + 预生成 JSON，**零构建、零运行时依赖**
- 双击 `index.html` 即可在浏览器打开（**file:// 兼容**）
- 视觉风格与 `项目管理AI增强方案/` 一致（深色 Industrial Editorial）

## 二、目录结构

```
MyWord/
├── index.html              ← 主索引页（核心交付物）
├── data.json               ← 资产清单（脚本生成）
├── scripts/
│   ├── scan-index.js       ← 扫描脚本
│   └── scan-index.test.js  ← 脚本测试
├── package.json            ← Node 项目配置
├── README.md               ← 本文件
└── （其他子目录：粒子动画、方案、笔记、视频 等）
```

## 三、如何使用

### 方式 1：直接打开（最简单）
双击 `D:\code\MyWord\index.html`，默认浏览器打开即可。

### 方式 2：本地 HTTP（推荐用于演示）
部分浏览器对 `file://` 协议下的字体加载有限制。如遇字体回退问题，启动本地 HTTP：

```powershell
cd 'D:\code\MyWord'
python -m http.server 8080
# 然后访问 http://localhost:8080
```

## 四、如何维护

### 1. 新增资产
1. 把新资产放到对应分组目录下（如新建 `11.新动画/` → 自动归入"粒子动画作品"分组）
2. 在仓库根目录运行：
   ```powershell
   node scripts/scan-index.js
   ```
3. 浏览器刷新 `index.html` 即可看到新内容

### 2. 修改资产
- 仅修改文件内容：直接刷新浏览器即可（`data.json` 未变）
- 想看新 `lastModified`：重新跑 `node scripts/scan-index.js`

### 3. 删除资产
1. 删目录
2. 跑 `node scripts/scan-index.js`
3. 刷新浏览器

### 4. 开发模式（watch）
```powershell
node scripts/scan-index.js --watch
# 每 5 秒扫描一次，输出文件变化时自动重写 data.json
```

## 五、扫描脚本

`scripts/scan-index.js` 按以下规则分类资产：

| 分组 ID | 匹配规则 | 颜色 |
|---|---|---|
| `particles` | 顶层匹配 `^[0-9]+\..+` 的目录（4-10 编号项目） | AI 青 `#06B6D4` |
| `project-plan` | `项目管理AI增强方案/` | 瀑布蓝 `#3B82F6` |
| `xhs-notes` | `小红书笔记/*.md` | 敏捷橙 `#F59E0B` |
| `specs` | `项目文档/*.md` + `项目文档/ specs/*.md` | 成功绿 `#10B981` |
| `videos` | `xhs-output/` 下一级目录（排除 `renders/`） | 风险红 `#EF4444` |

CLI 参数：
```bash
node scripts/scan-index.js                  # 默认输出到 data.json
node scripts/scan-index.js --output foo.json  # 自定义输出
node scripts/scan-index.js --dry-run          # 只打印不写文件
node scripts/scan-index.js --watch            # 5s 间隔 watch
```

## 六、测试

```powershell
npm test
```

使用 Node 内置 `node --test` 运行扫描脚本测试（8 个 test）。

## 七、键盘快捷键

| 快捷键 | 作用 |
|---|---|
| `/` | 聚焦搜索框 |
| `Esc` | 清空搜索 + 失焦 |
| `g g` | 跳回顶部 |

## 八、浏览器兼容

| 浏览器 | 状态 |
|---|---|
| Chrome / Edge 90+ | ✅ 完整支持 |
| Firefox 88+ | ✅ 完整支持 |
| Safari 14+ | ✅ 完整支持 |
| IE 11 | ❌ 不支持 |

## 九、版本

- **v1.0.0** · 2026-06-09 · 初始版本
- 设计文档：`docs/superpowers/specs/2026-06-09-content-aggregation-platform-design.md`
- 实现计划：`docs/superpowers/plans/2026-06-09-content-aggregation-platform.md`

---

> 维护者：Mige / Migeking
```

- [ ] **Step 3: Commit**

```bash
cd D:\code\MyWord
git add README.md
git commit -m "docs: README — 使用与维护指南"
```

---

# Task 13 · 最终手动验证清单

**Files:** 无（验证任务）

- [ ] **Step 1: 跑测试 + 重新生成 data.json**

```powershell
cd D:\code\MyWord
npm test
node scripts/scan-index.js
```

Expected: 8 个测试 PASS；data.json 成功更新。

- [ ] **Step 2: 浏览器打开 + 逐项验证**

打开 `D:\code\MyWord\index.html`，逐项验证：

- [ ] Hero 显示正确的统计数字（资产数、分组数、文件数、更新于 X 分钟前）
- [ ] 5 个分组（粒子动画、项目方案、小红书笔记、Specs、视频作品）按顺序展示
- [ ] 每个分组色与 README 表格一致
- [ ] 至少 1 张卡片在每个分组下
- [ ] 鼠标悬停卡片：上浮 4px、边框变亮
- [ ] 点击卡片：在新窗口/同窗口跳转到目标 index.html
- [ ] 搜索框输入"鲸鱼"：只剩含鲸鱼的卡片
- [ ] 搜索框输入"xxxx"：显示"没有匹配资产"空状态
- [ ] 点击 #GSAP 标签：高亮 + 只显示含 GSAP 的卡片
- [ ] 再点 #AI：多个标签 AND 关系
- [ ] 取消激活标签：恢复正常
- [ ] 按 `/`：搜索框聚焦
- [ ] 按 `Esc`：搜索清空
- [ ] 连按 `g g`：跳回顶部
- [ ] Chrome DevTools 移动端模拟：响应式布局生效
- [ ] F12 → Console：无任何 error

- [ ] **Step 3: 关闭 console 警告**

如有 console warning（如 Google Fonts 加载失败），记录但不阻塞。如有 error，先修复再继续。

- [ ] **Step 4: 全部通过 — 标记完成**

在 PR / 报告中说明所有项通过。

---

# Task 14 · 初次 commit（如果此前未 commit）

**Files:** 无（git 操作任务）

> **注**：仓库当前处于早期阶段（无 commit）。如果 Task 1-12 过程中已逐 task commit，本任务跳过。否则补一次基础 commit。

- [ ] **Step 1: 检查 git 状态**

```powershell
cd D:\code\MyWord
git log --oneline -5 2>&1
```

如果已有 5+ commit（如 Task 1-12 的提交），跳过本任务。

- [ ] **Step 2: 如果无 commit，做首次提交**

```bash
cd D:\code\MyWord
git add .gitignore package.json scripts/ index.html data.json README.md docs/
git commit -m "feat: 初始版本 — MyWord 内容聚合平台 v1.0.0

- 单文件 HTML SPA + 预生成 JSON
- Node 扫描脚本 + 8 个测试
- 5 个内容分组（粒子/方案/笔记/Specs/视频）
- 搜索 + 标签过滤 + 键盘快捷键
- 响应式布局 + file:// 兼容"
```

---

# 完成 ✅

所有任务完成后：
- ✅ 8 个测试通过
- ✅ 双击 `index.html` 即可使用
- ✅ `node scripts/scan-index.js` 一键维护
- ✅ 5 个分组 + 卡片 + 搜索 + 标签 + 快捷键 + 响应式
- ✅ README + 设计文档 + 实现计划 三件套齐全

下一步可以做的（YAGNI · 不在 v1.0 范围）：
- 全文搜索（lunr.js / fuse.js）
- 缩略图自动截图（puppeteer）
- 暗/亮主题切换
- 部署到 GitHub Pages

---

> **Plan author**: Sisyphus · 2026-06-09
> **Spec reference**: `docs/superpowers/specs/2026-06-09-content-aggregation-platform-design.md`

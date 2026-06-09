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

// ============================================================================
// 顶层目录排除清单
// ============================================================================
const EXCLUDED_TOP_LEVEL = new Set([
  '.git', '.claude', '.sisyphus', '.clauge-worktrees',
  '.playwright-mcp', '.antigravitycli', '.vscode',
  'node_modules', 'scripts', 'mlruns', 'cors-proxy',
  'browser-use-test', 'research', 'work', 'skills', 'docs',
  '内容', // 发布流程工作流（流程文档，非产出）
]);

// ============================================================================
// 标签启发式
// ============================================================================
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

// ============================================================================
// 工具函数
// ============================================================================
function isExcludedDir(name) {
  if (name.startsWith('.')) return true;
  return EXCLUDED_TOP_LEVEL.has(name);
}

async function walkTopLevel(rootDir) {
  const entries = await fs.readdir(rootDir, { withFileTypes: true });
  const dirs = [];
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (isExcludedDir(e.name)) continue;
    dirs.push({ name: e.name, fullPath: path.join(rootDir, e.name) });
  }
  return dirs;
}

async function fileExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function readHtmlTitle(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}

async function readHtmlDescription(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}

async function readMdTitle(mdPath) {
  try {
    const content = await fs.readFile(mdPath, 'utf8');
    const fm = content.match(/^---\n[\s\S]*?title:\s*["']?(.+?)["']?\n[\s\S]*?---/);
    if (fm) return fm[1].trim();
    const h1 = content.match(/^#\s+(.+?)$/m);
    return h1 ? h1[1].trim() : '';
  } catch {
    return '';
  }
}

async function readMdFirstParagraph(mdPath) {
  try {
    const content = await fs.readFile(mdPath, 'utf8');
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

function toKebabCase(s) {
  return s
    .replace(/^[0-9]+\./, '')
    .replace(/[·・\s]+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5-]/g, '')
    .toLowerCase()
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

function emptyGroup(id, label, color, description) {
  return { id, label, color, description, items: [] };
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

// ============================================================================
// 5 个分组扫描
// ============================================================================
async function scanParticles(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const items = [];
  for (const d of topDirs) {
    if (!/^[0-9]+\..+/.test(d.name)) continue;
    const indexPath = path.join(d.fullPath, 'index.html');
    if (!(await fileExists(indexPath))) continue;
    const title = (await readHtmlTitle(indexPath)) || d.name;
    const desc = (await readHtmlDescription(indexPath)) || '';
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

async function scanXhsNotes(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '小红书笔记');
  if (!dir) return emptyGroup('xhs-notes', '小红书笔记', '#F59E0B', '小红书内容草稿');

  const items = [];
  const entries = await fs.readdir(dir.fullPath, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isFile() || !/\.md$/i.test(e.name)) continue;
    const filePath = path.join(dir.fullPath, e.name);
    const title = (await readMdTitle(filePath)) || e.name.replace(/\.md$/i, '');
    const desc = await readMdFirstParagraph(filePath);
    const stat = await fs.stat(filePath);
    items.push({
      id: toKebabCase(e.name.replace(/\.md$/i, '')),
      title,
      desc,
      path: `${dir.name}/${e.name}`,
      fileCount: 1,
      lastModified: stat.mtime.toISOString(),
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

async function scanSpecs(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '项目文档');
  if (!dir) return emptyGroup('specs', '项目文档 / Specs', '#10B981', 'iWork 系列 + 技术规范');

  const items = [];
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
    const title = hasIndex ? ((await readHtmlTitle(indexPath)) || e.name) : e.name;
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

// ============================================================================
// 主入口
// ============================================================================
async function scanRepository(rootDir) {
  const groups = await Promise.all([
    scanParticles(rootDir),
    scanProjectPlan(rootDir),
    scanXhsNotes(rootDir),
    scanSpecs(rootDir),
    scanVideos(rootDir),
  ]);
  const items = groups.reduce((s, g) => s + g.items.length, 0);
  const files = groups.reduce(
    (s, g) => s + g.items.reduce((ss, it) => ss + (it.fileCount || 0), 0),
    0
  );
  return {
    version: '1.0.0',
    generatedAt: new Date().toISOString(),
    totals: { items, groups: groups.length, files },
    groups,
  };
}

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

async function runOnce(outputPath, dryRun) {
  console.log('[scan] scanning', ROOT);
  const data = await scanRepository(ROOT);
  const json = JSON.stringify(data, null, 2);
  if (dryRun) {
    console.log('[scan] DRY RUN — 不写文件');
    console.log(json.slice(0, 500) + (json.length > 500 ? '...' : ''));
  } else {
    await fs.writeFile(outputPath, json + '\n', 'utf8');
    console.log('[scan] wrote', outputPath, `(${json.length} bytes, ${data.totals.items} items)`);
  }
}

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

// 仅当作为主模块运行时执行
if (require.main === module) {
  main().catch((err) => {
    console.error('[scan] fatal:', err);
    process.exit(1);
  });
}

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
  readMdTitle,
  readMdFirstParagraph,
  countFiles,
  latestMtime,
  toKebabCase,
  extractTags,
  makeMdItem,
  emptyGroup,
};

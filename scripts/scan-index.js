#!/usr/bin/env node
/**
 * scan-index.js
 * 扫描 D:\code\MyWord\ 仓库，生成 D:\code\MyWord\data.json
 * 用法：node scripts/scan-index.js [--output PATH] [--watch] [--dry-run]
 *
 * 扫描维度：
 *   - 5 个内容分组（particles / project-plan / xhs-notes / specs / videos）
 *   - 媒体类型统计：html / md / video / audio / image / json / other
 *   - 总字节数
 *   - 自动找 poster 缩略图
 *   - 额外：xhs-output/videos/ 下的孤儿 mp4 → media-renders 分组
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
  '内容',
]);

// ============================================================================
// 媒体扩展名分类
// ============================================================================
const EXT = {
  html: ['.html', '.htm'],
  md:   ['.md', '.markdown'],
  video:['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv', '.m4v'],
  audio:['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'],
  image:['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.bmp'],
  json: ['.json'],
};

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
  'TTS': /tts|配音|语音/i,
  '视频': /video|视频/i,
  'BGM': /bgm|配乐/i,
};

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
  try { await fs.access(p); return true; } catch { return false; }
}

async function dirExists(p) {
  try { const stat = await fs.stat(p); return stat.isDirectory(); } catch { return false; }
}

async function readHtmlTitle(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    return m ? m[1].trim() : '';
  } catch { return ''; }
}

async function readHtmlDescription(htmlPath) {
  try {
    const content = await fs.readFile(htmlPath, 'utf8');
    const m = content.match(/<meta\s+name=["']description["']\s+content=["']([^"']+)["']/i);
    return m ? m[1].trim() : '';
  } catch { return ''; }
}

async function readMdTitle(mdPath) {
  try {
    const content = await fs.readFile(mdPath, 'utf8');
    const fm = content.match(/^---\n[\s\S]*?title:\s*["']?(.+?)["']?\n[\s\S]*?---/);
    if (fm) return fm[1].trim();
    const h1 = content.match(/^#\s+(.+?)$/m);
    return h1 ? h1[1].trim() : '';
  } catch { return ''; }
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
  } catch { return ''; }
}

function extractTags(text) {
  const tags = [];
  for (const [tag, regex] of Object.entries(TAG_KEYWORDS)) {
    if (regex.test(text)) tags.push(tag);
  }
  return tags;
}

function classifyExt(name) {
  const ext = path.extname(name).toLowerCase();
  for (const [type, exts] of Object.entries(EXT)) {
    if (exts.includes(ext)) return type;
  }
  return 'other';
}

/**
 * 递归统计目录中的文件，按媒体类型分类 + 总字节数
 * 排除：node_modules / .git / renders / 任何 dotfile 目录
 */
async function countMedia(dir) {
  const counts = { html: 0, md: 0, video: 0, audio: 0, image: 0, json: 0, other: 0, total: 0, size: 0 };
  const stack = [dir];
  const seen = new Set();
  while (stack.length) {
    const cur = stack.pop();
    if (seen.has(cur)) continue;
    seen.add(cur);
    let entries;
    try { entries = await fs.readdir(cur, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (e.name === 'node_modules' || e.name === '.git') continue;
      const full = path.join(cur, e.name);
      if (e.isDirectory()) {
        stack.push(full);
      } else if (e.isFile()) {
        const type = classifyExt(e.name);
        counts[type]++;
        counts.total++;
        try {
          const stat = await fs.stat(full);
          counts.size += stat.size;
        } catch {}
      }
    }
  }
  return counts;
}

/**
 * 找目录里的 poster 缩略图
 * 优先级：cover → frames 目录首图 → screenshots 目录首图 → 递归首张图
 */
async function findPoster(dir) {
  for (const prefix of ['cover', 'poster', 'thumbnail', 'thumb', 'preview']) {
    for (const ext of ['.jpg', '.jpeg', '.png', '.webp', '.gif']) {
      const p = path.join(dir, prefix + ext);
      if (await fileExists(p)) return p;
    }
  }
  for (const sub of ['frames', 'screenshots', 'slides']) {
    const subDir = path.join(dir, sub);
    if (await dirExists(subDir)) {
      const post = await findFirstImage(subDir);
      if (post) return post;
    }
  }
  return findFirstImage(dir);
}

async function findFirstImage(dir) {
  let entries;
  try { entries = await fs.readdir(dir, { withFileTypes: true }); } catch { return null; }
  for (const e of entries) {
    if (e.isFile() && EXT.image.includes(path.extname(e.name).toLowerCase())) {
      return path.join(dir, e.name);
    }
  }
  for (const e of entries) {
    if (e.isDirectory() && !e.name.startsWith('.')) {
      const sub = await findFirstImage(path.join(dir, e.name));
      if (sub) return sub;
    }
  }
  return null;
}

async function latestMtime(dir) {
  let latest = 0;
  const stack = [dir];
  const seen = new Set();
  while (stack.length) {
    const cur = stack.pop();
    if (seen.has(cur)) continue;
    seen.add(cur);
    let entries;
    try { entries = await fs.readdir(cur, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (e.name === 'node_modules' || e.name === '.git') continue;
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
  return { id, label, color, description, items: [], subGroups: [] };
}

function formatSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n < 10 ? 1 : 0)} ${units[i]}`;
}

async function makeMdItem(filePath, fileName, parentPath) {
  const title = (await readMdTitle(filePath)) || fileName.replace(/\.md$/i, '');
  const desc = await readMdFirstParagraph(filePath);
  const stat = await fs.stat(filePath);
  const size = stat.size;
  return {
    id: toKebabCase(fileName.replace(/\.md$/i, '')),
    title,
    desc,
    path: `${parentPath}/${fileName}`,
    fileCount: 1,
    lastModified: stat.mtime.toISOString(),
    tags: extractTags(`${title} ${desc} ${fileName}`),
    media: { html: 0, md: 1, video: 0, audio: 0, image: 0, json: 0, other: 0, total: 1, size },
    size,
    sizeFormatted: formatSize(size),
    poster: null,
  };
}

async function makeDirItem(dir) {
  const title = path.basename(dir.fullPath);
  const media = await countMedia(dir.fullPath);
  const lastModified = await latestMtime(dir.fullPath);
  const indexPath = path.join(dir.fullPath, 'index.html');
  const hasIndex = await fileExists(indexPath);
  const linkPath = hasIndex ? `${dir.name}/index.html` : `${dir.name}/`;
  const realTitle = hasIndex ? ((await readHtmlTitle(indexPath)) || title) : title;
  const desc = hasIndex ? (await readHtmlDescription(indexPath)) : '';
  const posterAbs = await findPoster(dir.fullPath);
  const poster = posterAbs ? path.relative(ROOT, posterAbs).replace(/\\/g, '/') : null;
  return {
    id: toKebabCase(dir.name),
    title: realTitle,
    desc,
    path: linkPath,
    fileCount: media.total,
    lastModified,
    tags: extractTags(`${dir.name} ${realTitle} ${desc}`),
    media,
    size: media.size,
    sizeFormatted: formatSize(media.size),
    poster,
  };
}

async function hasFileWithExt(dir, exts) {
  let entries;
  try { entries = await fs.readdir(dir, { withFileTypes: true }); } catch { return false; }
  for (const e of entries) {
    if (e.isFile() && exts.includes(path.extname(e.name).toLowerCase())) return true;
    if (e.isDirectory() && !e.name.startsWith('.') && e.name !== 'renders') {
      if (await hasFileWithExt(path.join(dir, e.name), exts)) return true;
    }
  }
  return false;
}

// ============================================================================
// 5 个内容分组扫描
// ============================================================================
async function scanParticles(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const items = [];
  for (const d of topDirs) {
    if (!/^[0-9]+\..+/.test(d.name)) continue;
    const indexPath = path.join(d.fullPath, 'index.html');
    if (!(await fileExists(indexPath))) continue;
    items.push(await makeDirItem(d));
  }
  return {
    id: 'particles',
    label: '粒子动画作品',
    color: '#06B6D4',
    description: 'GSAP / Three.js 粒子动画视频作品',
    items,
    subGroups: [],
  };
}

async function scanProjectPlan(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === '项目管理AI增强方案');
  if (!dir) return emptyGroup('project-plan', '项目方案', '#3B82F6', '项目管理方案文档');

  return {
    id: 'project-plan',
    label: '项目方案',
    color: '#3B82F6',
    description: '项目管理方案与决策框架',
    items: [await makeDirItem(dir)],
    subGroups: [],
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
    items.push(await makeMdItem(filePath, e.name, dir.name));
  }
  return {
    id: 'xhs-notes',
    label: '小红书笔记',
    color: '#F59E0B',
    description: '小红书内容草稿与发布笔记',
    items,
    subGroups: [],
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
    subGroups: [],
  };
}

/**
 * 视频项目：xhs-output 下除辅助目录外的子目录
 * 区分：
 *   - 含视频文件 → 视频项目（item）
 *   - 纯资源池（frames/screenshots/slides 等）→ media-renders 分组
 */
async function scanVideos(rootDir) {
  const topDirs = await walkTopLevel(rootDir);
  const dir = topDirs.find((d) => d.name === 'xhs-output');
  if (!dir) {
    return emptyGroup('videos', '视频作品', '#EF4444', '小红书视频输出');
  }

  const videoProjects = [];
  const mediaRenders = [];

  const entries = await fs.readdir(dir.fullPath, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    if (e.name === 'scripts' || e.name === 'work-94c53cea-150e-4375-b3ed-8283ef672319') continue;
    if (e.name.startsWith('.')) continue;

    const sub = path.join(dir.fullPath, e.name);
    const hasVideo = await hasFileWithExt(sub, EXT.video);
    if (hasVideo) {
      videoProjects.push({ name: e.name, fullPath: sub });
    } else {
      const media = await countMedia(sub);
      if (media.total > 0) {
        const posterAbs = await findPoster(sub);
        mediaRenders.push({
          id: toKebabCase('media-' + e.name),
          title: e.name,
          desc: `${media.image} 张图 · ${media.audio} 个音频 · ${media.sizeFormatted}`,
          path: `${dir.name}/${e.name}/`,
          fileCount: media.total,
          lastModified: await latestMtime(sub),
          tags: extractTags(e.name + ' media pool'),
          media,
          size: media.size,
          sizeFormatted: formatSize(media.size),
          poster: posterAbs ? path.relative(ROOT, posterAbs).replace(/\\/g, '/') : null,
        });
      }
    }
  }

  const projectItems = [];
  for (const p of videoProjects) {
    projectItems.push(await makeDirItem(p));
  }

  return {
    id: 'videos',
    label: '视频作品',
    color: '#EF4444',
    description: '小红书视频输出',
    items: projectItems,
    subGroups: [
      {
        id: 'media-renders',
        label: '媒体资源池',
        color: '#DC2626',
        description: '无最终视频的纯资源目录（frames / 音频库 / 草稿）',
        items: mediaRenders,
      },
    ],
  };
}

// ============================================================================
// 整合
// ============================================================================
async function scanRepository(rootDir) {
  const groups = await Promise.all([
    scanParticles(rootDir),
    scanProjectPlan(rootDir),
    scanXhsNotes(rootDir),
    scanSpecs(rootDir),
    scanVideos(rootDir),
  ]);

  const totals = {
    items: 0,
    groups: groups.length,
    files: 0,
    size: 0,
    byType: { html: 0, md: 0, video: 0, audio: 0, image: 0, json: 0, other: 0 },
    withPoster: 0,
  };
  for (const g of groups) {
    totals.items += g.items.length;
    for (const it of g.items) accumulateItem(totals, it);
    if (g.subGroups) for (const sg of g.subGroups) {
      totals.items += sg.items.length;
      for (const it of sg.items) accumulateItem(totals, it);
    }
  }
  totals.sizeFormatted = formatSize(totals.size);

  return {
    version: '2.0.0',
    generatedAt: new Date().toISOString(),
    totals,
    groups,
  };
}

function accumulateItem(totals, it) {
  if (it.media) {
    for (const k of Object.keys(totals.byType)) totals.byType[k] += it.media[k] || 0;
    totals.files += it.media.total || 0;
    totals.size += it.size || 0;
    if (it.poster) totals.withPoster++;
  }
}

// ============================================================================
// CLI
// ============================================================================
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) { args[key] = next; i++; }
      else { args[key] = true; }
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
    console.log(`items: ${data.totals.items}, files: ${data.totals.files}, size: ${data.totals.sizeFormatted}`);
    console.log(`byType: html=${data.totals.byType.html} md=${data.totals.byType.md} video=${data.totals.byType.video} audio=${data.totals.byType.audio} image=${data.totals.byType.image} json=${data.totals.byType.json} other=${data.totals.byType.other}`);
    console.log(`withPoster: ${data.totals.withPoster}`);
  } else {
    await fs.writeFile(outputPath, json + '\n', 'utf8');
    console.log(`[scan] wrote ${outputPath} (${json.length} bytes)`);
    console.log(`[scan] stats: ${data.totals.items} items, ${data.totals.files} files, ${data.totals.sizeFormatted}, ${data.totals.withPoster} with posters`);
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
        console.log(`[scan] ${new Date().toISOString()} — ${data.totals.items} items, ${data.totals.sizeFormatted}`);
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

  if (watch) await runWatch(outputPath);
  else await runOnce(outputPath, dryRun);
}

if (require.main === module) {
  main().catch((err) => { console.error('[scan] fatal:', err); process.exit(1); });
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
  countMedia,
  countFiles: countMedia, // 兼容
  latestMtime,
  toKebabCase,
  extractTags,
  makeDirItem,
  makeMdItem,
  findPoster,
  findFirstImage,
  classifyExt,
  formatSize,
  hasFileWithExt,
  emptyGroup,
  ROOT,
  EXT,
};

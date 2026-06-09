'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const {
  walkTopLevel,
  isExcludedDir,
  scanParticles,
  scanProjectPlan,
  scanXhsNotes,
  scanSpecs,
  scanVideos,
  scanRepository,
  toKebabCase,
  extractTags,
  readHtmlTitle,
  readMdTitle,
  emptyGroup,
  countMedia,
  formatSize,
  classifyExt,
  findPoster,
  makeDirItem,
} = require('./scan-index');

const ROOT = path.resolve(__dirname, '..');

test('walkTopLevel 列出 ROOT 下非排除目录', async () => {
  const dirs = await walkTopLevel(ROOT);
  assert.ok(dirs.some((d) => d.name.startsWith('4.')), '应包含 4.x 编号目录');
  assert.ok(!dirs.some((d) => d.name === '.claude'), '不应包含 .claude');
  assert.ok(!dirs.some((d) => d.name === 'scripts'), '不应包含 scripts');
  assert.ok(!dirs.some((d) => d.name === 'docs'), '不应包含 docs');
});

test('isExcludedDir 排除隐藏目录与已知工程目录', () => {
  assert.equal(isExcludedDir('.git'), true);
  assert.equal(isExcludedDir('.claude'), true);
  assert.equal(isExcludedDir('node_modules'), true);
  assert.equal(isExcludedDir('scripts'), true);
  assert.equal(isExcludedDir('项目管理AI增强方案'), false);
  assert.equal(isExcludedDir('小红书笔记'), false);
});

test('classifyExt 正确分类扩展名', () => {
  assert.equal(classifyExt('foo.html'), 'html');
  assert.equal(classifyExt('foo.md'), 'md');
  assert.equal(classifyExt('foo.mp4'), 'video');
  assert.equal(classifyExt('foo.WEBM'), 'video');
  assert.equal(classifyExt('foo.mp3'), 'audio');
  assert.equal(classifyExt('foo.wav'), 'audio');
  assert.equal(classifyExt('foo.png'), 'image');
  assert.equal(classifyExt('foo.jpg'), 'image');
  assert.equal(classifyExt('foo.json'), 'json');
  assert.equal(classifyExt('foo.xyz'), 'other');
});

test('formatSize 正确格式化字节数', () => {
  assert.equal(formatSize(0), '0 B');
  assert.equal(formatSize(512), '512 B');
  assert.equal(formatSize(1024), '1.0 KB');
  assert.equal(formatSize(1024 * 1024), '1.0 MB');
  assert.equal(formatSize(1024 * 1024 * 1024), '1.0 GB');
  assert.equal(formatSize(Math.round(1024 * 1024 * 7.5)), '7.5 MB');
});

test('toKebabCase 转中文 + 数字为 id', () => {
  assert.equal(toKebabCase('4.鲸鱼粒子-自由自在'), '鲸鱼粒子-自由自在');
  assert.equal(toKebabCase('10.治愈水母'), '治愈水母');
  assert.equal(toKebabCase('AI · 落地'), 'ai-落地');
});

test('extractTags 匹配关键词', () => {
  assert.ok(extractTags('鲸鱼粒子 GSAP 动画').includes('GSAP'));
  assert.ok(extractTags('鲸鱼粒子 GSAP 动画').includes('粒子'));
  assert.ok(extractTags('鲸鱼粒子 GSAP 动画').includes('海洋'));
  assert.ok(extractTags('工业物联网 AI 落地').includes('工业'));
  assert.ok(extractTags('工业物联网 AI 落地').includes('AI'));
  assert.ok(extractTags('TTS 配音视频').includes('TTS'));
  assert.ok(extractTags('TTS 配音视频').includes('视频'));
});

test('readHtmlTitle 解析 <title> 标签', () => {
  return readHtmlTitle(path.join(ROOT, '项目管理AI增强方案/index.html')).then((t) => {
    assert.ok(t.length > 0, 'title 非空');
    assert.match(t, /无人机|项目管理|AI/i);
  });
});

test('countMedia 真实统计 xhs-output 媒体', async () => {
  const m = await countMedia(path.join(ROOT, 'xhs-output'), { version: 2, dirs: {} });
  assert.ok(m.total > 1000, 'xhs-output 应有大量文件');
  assert.ok(m.video > 0, '应有视频');
  assert.ok(m.audio > 0, '应有音频');
  assert.ok(m.image > 1000, '应有大量图片');
  assert.ok(m.size > 0, '应有字节数');
  assert.equal(typeof m.html, 'number');
  assert.equal(typeof m.md, 'number');
  assert.equal(typeof m.json, 'number');
  assert.equal(typeof m.other, 'number');
});

test('countMedia 排除 node_modules 与 renders 子树', async () => {
  const m = await countMedia(path.join(ROOT, '7.粒子章鱼'), { version: 2, dirs: {} });
  assert.ok(m.image > 100, '粒子章鱼应有大量图片');
});

test('makeDirItem 产物字段完整性', async () => {
  const it = await makeDirItem({ name: '4.鲸鱼粒子-自由自在', fullPath: path.join(ROOT, '4.鲸鱼粒子-自由自在') }, { version: 2, dirs: {} });
  assert.ok(it.id);
  assert.ok(it.title);
  assert.ok(it.path.endsWith('index.html'));
  assert.ok(it.media);
  assert.equal(typeof it.size, 'number');
  assert.equal(typeof it.sizeFormatted, 'string');
  assert.ok(typeof it.poster === 'string' || it.poster === null);
  assert.ok(Array.isArray(it.tags));
});

test('findPoster 找 frames 目录首图或返回 null', async () => {
  const poster = await findPoster(path.join(ROOT, '7.粒子章鱼'));
  if (poster) {
    assert.ok(poster.includes('7.粒子章鱼'), 'poster 路径应在 7.粒子章鱼 下');
  }
  const noPoster = await findPoster(path.join(ROOT, '.git'));
  assert.equal(noPoster, null);
});

test('scanParticles 匹配 4.x ~ 10.x 编号目录', async () => {
  const group = await scanParticles(ROOT, { version: 2, dirs: {} });
  assert.equal(group.id, 'particles');
  assert.equal(group.color, '#06B6D4');
  assert.ok(group.items.length >= 1, '应至少扫描到 1 个粒子项目');
  const first = group.items[0];
  assert.match(first.path, /^[0-9]+\..+\/index\.html$/);
  assert.ok(first.id, 'id 非空');
  assert.ok(first.title, 'title 非空');
  assert.ok(first.media, 'media 字段存在');
  assert.equal(typeof first.sizeFormatted, 'string', 'sizeFormatted 存在');
});

test('scanProjectPlan 扫描 项目管理AI增强方案', async () => {
  const group = await scanProjectPlan(ROOT, { version: 2, dirs: {} });
  assert.equal(group.id, 'project-plan');
  assert.equal(group.color, '#3B82F6');
  assert.ok(group.items.length >= 1);
  assert.match(group.items[0].path, /项目管理AI增强方案/);
});

test('scanXhsNotes 扫描 小红书笔记 下的 .md', async () => {
  const group = await scanXhsNotes(ROOT);
  assert.equal(group.id, 'xhs-notes');
  assert.equal(group.color, '#F59E0B');
  assert.ok(group.items.length >= 1);
  for (const item of group.items) {
    assert.ok(item.path.endsWith('.md') || item.path.endsWith('.html'));
  }
});

test('scanSpecs 扫描 项目文档 下 iWork 系列 + specs/ 子目录', async () => {
  const group = await scanSpecs(ROOT);
  assert.equal(group.id, 'specs');
  assert.equal(group.color, '#10B981');
  const iworkCount = group.items.filter((i) => /iWork/.test(i.title)).length;
  assert.ok(iworkCount >= 1, '应至少 1 个 iWork 文档');
});

test('scanVideos 扫描 xhs-output 视频项目 + media-renders 子组', async () => {
  const group = await scanVideos(ROOT, { version: 2, dirs: {} });
  assert.equal(group.id, 'videos');
  assert.equal(group.color, '#EF4444');
  assert.ok(group.items.length >= 1, '应至少 1 个视频项目');
  assert.ok(Array.isArray(group.subGroups), '应包含 subGroups 数组');
  assert.ok(group.subGroups.length >= 1, '应至少 1 个子组');
  assert.equal(group.subGroups[0].id, 'media-renders');
});

test('scanRepository 整合 5 个分组 + 子组 + 媒体统计', async () => {
  const data = await scanRepository(ROOT, { version: 2, dirs: {} });
  assert.equal(data.version, '2.0.0');
  assert.equal(data.groups.length, 5);
  assert.ok(data.generatedAt);
  const expected = data.groups.reduce((s, g) => {
    let c = g.items.length;
    if (g.subGroups) c += g.subGroups.reduce((s2, sg) => s2 + sg.items.length, 0);
    return s + c;
  }, 0);
  assert.equal(data.totals.items, expected);
  assert.equal(data.totals.groups, 5);
  assert.ok(data.totals.files > 0);
  assert.ok(data.totals.size > 0);
  assert.ok(data.totals.byType);
  assert.ok(data.totals.sizeFormatted);
  assert.ok(data.totals.withPoster >= 0);
  // 视频/音频/图片总数应 > 0
  assert.ok(data.totals.byType.video > 0, '项目里有视频');
  assert.ok(data.totals.byType.audio > 0, '项目里有音频');
  assert.ok(data.totals.byType.image > 0, '项目里有图片');
});

test('emptyGroup 返回正确结构', () => {
  const g = emptyGroup('test', 'Test', '#FFF', 'desc');
  assert.equal(g.id, 'test');
  assert.equal(g.label, 'Test');
  assert.equal(g.items.length, 0);
  assert.ok(Array.isArray(g.subGroups));
});

test('real data.json 合法 + 含 media 字段', async () => {
  const data = await scanRepository(ROOT, { version: 2, dirs: {} });
  const json = JSON.stringify(data, null, 2);
  assert.ok(json.length > 10000);
  const groupIds = data.groups.map((g) => g.id);
  assert.deepEqual(groupIds, ['particles', 'project-plan', 'xhs-notes', 'specs', 'videos']);
  for (const g of data.groups) {
    for (const it of g.items) {
      assert.ok(it.media, `${g.id}/${it.id} 应有 media 字段`);
      assert.equal(typeof it.sizeFormatted, 'string');
    }
  }
});

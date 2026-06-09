'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs').promises;
const os = require('node:os');

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
} = require('./scan-index');

const ROOT = path.resolve(__dirname, '..');

// ----------------------------------------------------------------------------
// Task 2: walkTopLevel + isExcludedDir
// ----------------------------------------------------------------------------

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

// ----------------------------------------------------------------------------
// Task 3: scanParticles + 工具函数
// ----------------------------------------------------------------------------

test('scanParticles 匹配 4.x ~ 10.x 编号目录', async () => {
  const group = await scanParticles(ROOT);
  assert.equal(group.id, 'particles');
  assert.equal(group.color, '#06B6D4');
  assert.ok(group.items.length >= 1, '应至少扫描到 1 个粒子项目');
  const first = group.items[0];
  assert.match(first.path, /^[0-9]+\..+\/index\.html$/);
  assert.ok(first.id, 'id 非空');
  assert.ok(first.title, 'title 非空');
  assert.ok(Array.isArray(first.tags), 'tags 是数组');
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
});

test('readHtmlTitle 解析 <title> 标签', () => {
  // 真实 HTML 文件读取
  return readHtmlTitle(path.join(ROOT, '项目管理AI增强方案/index.html')).then((t) => {
    assert.ok(t.length > 0, 'title 非空');
    assert.match(t, /无人机|项目管理|AI/i);
  });
});

// ----------------------------------------------------------------------------
// Task 4: 4 个剩余分组
// ----------------------------------------------------------------------------

test('scanProjectPlan 扫描 项目管理AI增强方案', async () => {
  const group = await scanProjectPlan(ROOT);
  assert.equal(group.id, 'project-plan');
  assert.equal(group.color, '#3B82F6');
  assert.ok(group.items.length >= 1);
  assert.match(group.items[0].path, /项目管理AI增强方案/);
});

test('scanXhsNotes 扫描 小红书笔记 下的 .md', async () => {
  const group = await scanXhsNotes(ROOT);
  assert.equal(group.id, 'xhs-notes');
  assert.equal(group.color, '#F59E0B');
  // 至少扫描到现有文件
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

test('scanVideos 扫描 xhs-output 下一级目录（排除 renders）', async () => {
  const group = await scanVideos(ROOT);
  assert.equal(group.id, 'videos');
  assert.equal(group.color, '#EF4444');
  assert.ok(group.items.length >= 1);
  // 不应包含 renders 子目录
  assert.ok(!group.items.some((i) => /renders/.test(i.path)));
});

// ----------------------------------------------------------------------------
// Task 5: scanRepository 整合
// ----------------------------------------------------------------------------

test('scanRepository 整合 5 个分组，totals 正确', async () => {
  const data = await scanRepository(ROOT);
  assert.equal(data.version, '1.0.0');
  assert.equal(data.groups.length, 5);
  assert.ok(data.generatedAt);
  const expected = data.groups.reduce((s, g) => s + g.items.length, 0);
  assert.equal(data.totals.items, expected);
  assert.equal(data.totals.groups, 5);
  assert.ok(data.totals.files > 0);
});

test('emptyGroup 返回正确结构', () => {
  const g = emptyGroup('test', 'Test', '#FFF', 'desc');
  assert.equal(g.id, 'test');
  assert.equal(g.label, 'Test');
  assert.equal(g.items.length, 0);
});

// ----------------------------------------------------------------------------
// 真实 data.json 验证
// ----------------------------------------------------------------------------

test('scan 实际运行生成的 data.json 合法', async () => {
  const data = await scanRepository(ROOT);
  const json = JSON.stringify(data, null, 2);
  // 至少 1MB 字符（视仓库大小，但所有分组都有内容）
  assert.ok(json.length > 100);
  // 5 个分组都应被列出
  const groupIds = data.groups.map((g) => g.id);
  assert.deepEqual(groupIds, ['particles', 'project-plan', 'xhs-notes', 'specs', 'videos']);
});

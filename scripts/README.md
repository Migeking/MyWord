# scripts/

构建/维护工具集。

## 文件

| 文件 | 行数 | 作用 |
|---|---|---|
| `scan-index.js` | ~440 | 扫描仓库根目录，生成 `data.json` |
| `scan-index.test.js` | ~140 | 13 个单元测试，覆盖 5 个分组扫描 + 工具函数 |

## scan-index.js 详解

### CLI

```bash
node scripts/scan-index.js                  # 默认：扫描 → 写入 data.json
node scripts/scan-index.js --output FILE   # 自定义输出路径
node scripts/scan-index.js --dry-run       # 扫描但不写文件
node scripts/scan-index.js --watch         # 每 5 秒扫一次
```

### 5 个分组扫描规则

| ID | 匹配 |
|---|---|
| `particles` | 顶层匹配 `^[0-9]+\..+` 的目录（4-10 编号项目） |
| `project-plan` | `项目管理AI增强方案/` |
| `xhs-notes` | `小红书笔记/*.md` |
| `specs` | `项目文档/*.md` + `项目文档/ specs/*.md`（注意 specs 目录有前导空格） |
| `videos` | `xhs-output/` 下一级目录（排除 `renders/`） |

### 输出格式

`data.json` 结构：

```json
{
  "version": "1.0.0",
  "generatedAt": "2026-06-09T...",
  "totals": { "items": 50, "groups": 5, "files": 110 },
  "groups": [
    {
      "id": "particles",
      "label": "粒子动画作品",
      "color": "#06B6D4",
      "description": "GSAP / Three.js 粒子动画视频作品",
      "items": [
        {
          "id": "鲸鱼粒子-自由自在",
          "title": "鲸鱼粒子 · 自由自在",
          "desc": "鲸鱼造型的 GSAP 粒子动画",
          "path": "4.鲸鱼粒子-自由自在/index.html",
          "fileCount": 12,
          "lastModified": "2026-06-06T22:53:58.000Z",
          "tags": ["gsap", "粒子", "海洋"]
        }
      ]
    }
  ]
}
```

### 排除清单

EXCLUDED_TOP_LEVEL 包含：
- 工程化：`.claude/`、`.git/`、`.sisyphus/`、`.clauge-worktrees/`、`.playwright-mcp/`、`.antigravitycli/`、`.vscode/`、`node_modules/`、`scripts/`、`mlruns/`、`cors-proxy/`、`browser-use-test/`、`research/`、`work/`、`skills/`、`docs/`
- 工作流：`内容/`

## 测试

```bash
npm test
```

使用 Node 内置 `node --test`。13 个测试全部通过。

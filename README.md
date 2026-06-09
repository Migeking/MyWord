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

使用 Node 内置 `node --test` 运行扫描脚本测试（13 个 test）。

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

# MyWord · 内容管理中枢

> **一页通览所有产出** · 双击 `index.html` 即可打开

## 一、这是什么

`MyWord` 是一个内容仓库索引页。把仓库里散落在各子目录的"有读者价值的资产"——粒子动画项目、项目方案、小红书笔记、技术规范、视频作品——聚合成一个可搜索、可筛选、可监控的卡片仪表盘。

**特点**：
- 单文件 HTML SPA + 预生成 JSON，**零构建、零运行时依赖**
- 双击 `index.html` 即可在浏览器打开（**file:// 兼容**）
- 现代 SaaS Dashboard 视觉：白底卡片 + 5 个 KPI 指标 + 实时 LIVE 指示器
- 与 `项目管理AI增强方案/` 的深色杂志感形成对比，避免视觉雷同

## 二、目录结构

```
MyWord/
├── index.html                              ← 主索引页（双击打开的核心交付物）
├── data.json                               ← 资产清单（脚本生成，已 commit）
├── package.json                            ← Node 项目配置（npm scripts + name）
├── README.md                               ← 本文件
├── .gitignore                              ← 忽略规则
│
├── scripts/                                ← 构建工具
│   ├── scan-index.js                       ← 扫描脚本（CLI + 模块）
│   ├── scan-index.test.js                  ← 13 个单元测试
│   └── README.md                           ← 脚本使用文档
│
├── docs/                                   ← 文档
│   ├── design/                             ← 设计探索档案
│   │   ├── README.md                       ← 6 个 mockup 决策记录
│   │   ├── mockups/                        ← 6 个独立 HTML 风格原型
│   │   └── screenshots/                    ← 对应 PNG 预览 + 实施截图
│   └── superpowers/                        ← 设计与计划元文档
│       ├── specs/                          ← 1 个 spec 文档（440 行）
│       └── plans/                          ← 1 个实现计划（1975 行）
│
├── .claude/                                ← Claude 配置（保留原有）
│
└── （其他原有子目录：）
    ├── 4.鲸鱼粒子-自由自在/   5.HyperFrames品牌模板/   6.李子蝴蝶-粒子动画/
    ├── 7.粒子章鱼/             8.离子雄鹰/               9.AI重构工业/
    ├── 10.治愈水母/
    ├── 11.沙漠琉璃/            人生/                      小红书笔记/
    ├── 项目管理AI增强方案/    项目文档/                 xhs-output/
    └── …
```

## 三、快速开始

### 1. 直接打开（最简单）
双击 `D:\code\MyWord\index.html`，默认浏览器打开即可。

### 2. 本地 HTTP（推荐用于演示字体）
```powershell
cd 'D:\code\MyWord'
python -m http.server 8080
# 然后访问 http://localhost:8080
```

### 3. 运行测试
```powershell
cd 'D:\code\MyWord'
npm test
```

## 四、键盘快捷键

| 快捷键 | 作用 |
|---|---|
| `/` | 聚焦搜索框 |
| `Esc` | 清空搜索 + 失焦 |
| `g g` | 跳回顶部 |

## 五、浏览器兼容

| 浏览器 | 状态 |
|---|---|
| Chrome / Edge 90+ | ✅ 完整支持 |
| Firefox 88+ | ✅ 完整支持 |
| Safari 14+ | ✅ 完整支持 |
| IE 11 | ❌ 不支持 |

## 六、维护

详见 [`scripts/README.md`](./scripts/README.md) — 包含：
- 5 个分组扫描规则
- CLI 参数
- data.json 输出格式
- 排除清单

## 七、设计历史

本项目的视觉风格经历了**两轮探索**（共 6 个 mockup），最终选用 Dashboard 仪表盘风。详细过程与决策记录见：

📁 **[`docs/design/README.md`](./docs/design/README.md)** — 6 个变体的对比 + 为何选 F

## 八、版本

- **v1.0.0** · 2026-06-09
  - 初始版本：终端 `ls -lah` 风
  - 视觉迭代：替换为 Dashboard 浅色现代风
- 设计文档：[`docs/superpowers/specs/2026-06-09-content-aggregation-platform-design.md`](./docs/superpowers/specs/2026-06-09-content-aggregation-platform-design.md)
- 实现计划：[`docs/superpowers/plans/2026-06-09-content-aggregation-platform.md`](./docs/superpowers/plans/2026-06-09-content-aggregation-platform.md)

---

> 维护者：Mige / Migeking

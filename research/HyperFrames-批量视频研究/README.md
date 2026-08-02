# HyperFrames 批量视频研究

## 核心发现

用 HyperFrames 批量做视频，最大的感受是：**第一条视频最费时间，之后每多一条，成本几乎为零。**

因为一旦有了第一个模板，后面只需要告诉 AI：「参考上一条的 HTML，把标题和图片换成新的」，AI 就能在几分钟内生成一条新视频。

## 项目概述

HyperFrames 是 HeyGen 推出的视频批量生成工具，核心原理：

1. **AI 自动生成 HTML 模板**：描述需求，AI 生成第一个视频的 `index.html`
2. **模板复用**：后续视频只需替换内容（标题、图片、配乐），保留原有排版和动画
3. **边际成本趋零**：3-5 分钟生成一条新视频

## 技术栈

- **核心**：HTML + GSAP 动画
- **CLI 工具**：`npx hyperframes`
- **输出**：MP4 视频（1080x1920 竖版）

## 工作流程

```
1. 环境准备 → npm install -g @heygen/hyperframes
2. 创建项目 → mkdir e-magazine-video && cd e-magazine-video && mkdir pic
3. 准备资源 → 背景图 bj.jpg + 截图 pic/1-4.png + 音乐 music.mp3
4. 生成第一个视频 → 描述需求给 AI → AI 生成 index.html
5. 预览渲染 → npx hyperframes lint . && npx hyperframes preview . && npx hyperframes render . --output ./output.mp4
6. 批量生成 → 复制 index.html，告知 AI 替换内容
```

## 批量制作指令示例

| 修改内容 | 告诉 AI |
|---------|---------|
| 改标题 | 把主标题改成 "新品上市"，副标题改成 "限时优惠" |
| 改图片 | 把轮播图换成 ./pic/new-1.png ~ ./pic/new-4.png |
| 改配色 | 把主色调从深色改成浅色系 |
| 改时长 | 把视频总时长延长到 10 秒 |
| 改音乐 | 把背景音乐换成 ./music/new.mp3 |

## 文件结构

```
e-magazine-video/
├── index.html          # AI 自动生成的视频 composition
├── bj.jpg              # 背景图 (1080x1920)
├── music.mp3           # 背景音乐 (可选)
└── pic/
    ├── 1.png           # 截图1
    ├── 2.png           # 截图2
    ├── 3.png           # 截图3
    └── 4.png           # 截图4
```

## 与现有项目的结合点

### 现有工具分析
- `xhs-animated.html` / `xhs-slides.html` - 小红书动画/幻灯片
- `capture_xhs_video.py` - 视频捕获
- `capture_xhs_frames.py` - 帧捕获

### 结合可能
1. **模板生成**：用 AI 生成 HyperFrames HTML 替代手动编辑
2. **批量内容**：复用现有小红书内容生成模板
3. **工作流整合**：capture → HyperFrames → 发布

## 待研究问题

- [ ] HyperFrames CLI 的具体能力边界
- [ ] 与现有 capture 工具的整合方案
- [ ] 适合 HyperFrames 的内容类型（产品展示？教程？）
- [ ] 实际测试：生成一条视频需要多少时间

## 参考资料

- 微信文章：https://mp.weixin.qq.com/s/8Y6_VIb9BeLCr22kKglZ3g
- HyperFrames CLI：npm install -g @heygen/hyperframes

## 初步结论

HyperFrames 的核心价值在于**模板复用**和**批量生成**，非常适合：
- 产品宣传视频批量生成
- 小红书图文转视频
- 风格统一的系列视频制作

与我们现有的 `xhs-animated.html` 有相似之处，但 HyperFrames 更侧重于 CLI 批量化和 AI 辅助生成。

---

*创建时间：2026-05-20*
*最后更新：2026-05-20*

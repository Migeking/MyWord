# Page-Agent CORS 代理服务器

> 让浏览器里的 Page-Agent SDK 能够调用**讯飞星火 MaaS**（`maas-coding-api.cn-huabei-1.xf-yun.com`）等**不支持 CORS** 的 API。

## 为什么需要这个？

讯飞 MaaS 的 API 端点没有 `Access-Control-Allow-Origin` 头，浏览器从 `file://` 或 `http://localhost` 发请求会被 CORS 策略拦截：

```
Access to fetch at 'https://maas-coding-api.cn-huabei-1.xf-yun.com/v2/chat/completions' 
from origin 'null' has been blocked by CORS policy
```

这个代理服务器：
- 接收浏览器请求 → 加上 CORS 头转发给讯飞 API
- 接收讯飞 API 响应 → 透传给浏览器

## 启动

```powershell
# 1. 进入目录
cd D:\code\MyWord\cors-proxy

# 2. 安装依赖
npm install

# 3. 启动
npm start
```

启动后控制台会显示：

```
================================================================
  Page-Agent CORS 代理已启动
================================================================
  监听地址:  http://127.0.0.1:5503
  上游 API:  https://maas-coding-api.cn-huabei-1.xf-yun.com
  健康检查:  http://127.0.0.1:5503/health

  在 page-agent-demo.html 中配置:
    baseURL: 'http://127.0.0.1:5503/v1'
    apiKey:  '<你的讯飞 MaaS API Key>'
================================================================
```

## 配置 page-agent-demo.html

打开 `D:\code\MyWord\page-agent-demo.html`，找到 `initPageAgent()` 函数（约 1213 行），把：

```javascript
const config = {
  model: 'deepseek-chat',
  baseURL: 'https://api.deepseek.com/v1',     // ← 改成下方
  apiKey: 'YOUR_DEEPSEEK_API_KEY',            // ← 改成你的讯飞 API Key
  ...
};
```

改为：

```javascript
const config = {
  model: 'xopgpt',                            // 讯飞模型名
  baseURL: 'http://127.0.0.1:5503/v1',         // 走本地代理
  apiKey: '你的讯飞 MaaS API Key',             // 完整 Key 即可（带不带 Bearer 都行）
  ...
};
```

## 测试

```powershell
# 健康检查
curl http://127.0.0.1:5503/health

# 真实调用测试
curl -X POST http://127.0.0.1:5503/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <你的 API Key>" `
  -d '{\"model\":\"xopgpt\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'
```

## 支持的路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/v1/models` | 模型列表（占位） |
| POST | `/v1/chat/completions` | 核心代理，支持 SSE 流式 |
| OPTIONS | `*` | 显式 CORS 预检 |

## 文件结构

```
cors-proxy/
├── server.js      # 主程序
├── package.json   # 依赖声明
└── README.md      # 本文件
```

## 技术栈

- Node.js >= 18（使用原生 `fetch`）
- Express 4
- CORS 中间件

## 安全说明

⚠️ **演示用配置**：`ALLOWED_ORIGINS` 当前放行所有来源（含 `null` 即 `file://`），方便本地调试。  
生产环境请收紧来源白名单，并加上：

- API Key 校验（避免被滥用为开放代理）
- 速率限制（`express-rate-limit`）
- 请求日志持久化

---

## 自然语言测试提示词

以下提示词用于测试 `page-agent-demo.html` 的 NLP 指令理解与 ActionEngine 执行链路。

### 采购模块

```
帮我填一张采购申请单，买不锈钢板材，找 XX 钢铁公司，数量 100 吨，单价 500，下周五交货，备注写急用
```

```
我要申请采购无缝钢管 50 米，供应商选 AB 管道集团，单价 200 元
```

### 生产日报

```
查一下今天一车间的生产日报
```

```
帮我查生产数据，三车间和全部车间各查一次
```

```
导出今天的生产日报
```

### 库存查询

```
查一下不锈钢板材的库存
```

```
无缝钢管还有多少库存
```

```
阀门 DN100 的库存水位怎么样
```

### 边界情况（容错测试）

```
帮我买点东西
```

```
查一下库存
```

```
看看生产情况
```

---

## 7 项排查 & 问题记录

### ① 延时过低导致操作被跳过

**现象：** `sleep(30~50)` 时，部分 DOM 操作在面板未完全就绪前执行，`querySelector` 可能找不到目标元素。

**结论：** 已调整为 `sleep(60~100ms)`，在速度与可靠性之间取得平衡。总耗时仍比初始版本（1.8s）快约 10 倍。

### ② DOM 空值保护

**现象：** `_highlight(el)`、`selectOption(id)` 中 `document.getElementById(id)` 可能返回 `null`。

**状态：** 已有 `if (!el) return false` 保护，安全。

### ③ 事件触发兼容性

**现象：** `nativeInputValueSetter` 方案仅对原生 HTML 元素有效。若框架（如 React/Vue）接管了 input，`dispatchEvent(Event('input'))` 可能不被框架识别。

**状态：** 当前页面为纯原生 HTML，无框架绑定，此场景不受影响。若迁移到 SPA 框架需改用 `new Event('input', { bubbles: true })` + 框架特定 setter。

### ④ 并发调用冲突

**现象：** 快速连点时，多个 `sendChat()` 可能叠加执行，`sendBtn.disabled` 在 await 期间被绕过。

**状态：** 有 `sendBtn.disabled = true/false` 保护，但 `async` 函数内 await 返回前若被重新进入仍可能并发。建议加排他锁。

### ⑤ ai-target 样式泄漏

**现象：** `_highlight` 切换时 `document.querySelectorAll('.ai-target')` 清除所有高亮，若页面中其他区域也使用了 `ai-target` 类会冲突。

**状态：** 当前页面全局唯一使用，无冲突。

### ⑥ 日志内存堆积

**现象：** `addLog` 持续追加 DOM 节点，长时间使用后 `#logContent` 可能包含数千条条目。

**状态：** Demo 场景下不构成问题。生产使用需加最大条数限制（如超过 200 条自动截断）。

### ⑦ 错误处理盲区

**现象：** `ActionEngine` 各方法内部无 try/catch，若 `selectOption` 等操作失败（如元素被删除），错误会冒泡到 `executeInstruction` 导致整条指令中断。

**状态：** 当前 Demo 可控，暂无异常路径触发。建议后续增加兜底处理。

---

## 延时配置参考

| 阶段 | 当前值 | 说明 |
|---|---|---|
| 面板切换 | 100ms | 等待 CSS `display` 切换完成 |
| 批量高亮展示 | 80ms | 让用户能看见高亮反馈 |
| 指令预处理 | 60ms | 等待聊天消息渲染 |
| 初始版本 | 200~400ms | 旧版单步串行等待 |

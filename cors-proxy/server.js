/**
 * ============================================================================
 * Page-Agent CORS 代理服务器（零依赖版本）
 * ============================================================================
 *
 * 使用 Node.js 内置 http + https 模块，无需 npm install。
 *
 * 作用：
 *   浏览器中的 Page-Agent SDK 调用 CORS-restricted API（如讯飞 MaaS）时，
 *   本地代理负责加上 CORS 头透传请求。
 *
 * API Key 安全策略（三选一，优先级递减）：
 *   1. 浏览器发送的 Authorization 头（SDK config.apiKey）
 *   2. 环境变量 XFYUN_API_KEY
 *   3. 启动时提示输入
 *
 * 启动：
 *   cd cors-proxy
 *   node server.js
 *
 * ============================================================================
 */

import http from 'node:http';
import https from 'node:https';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createInterface } from 'node:readline';
import path from 'node:path';

// ---------------------------------------------------------------------------
// 配置
// ---------------------------------------------------------------------------
const PORT = 5503;
const UPSTREAM_BASE = 'https://maas-coding-api.cn-huabei-1.xf-yun.com';
const ALLOWED_ORIGINS = [
  'http://127.0.0.1:5500', 'http://127.0.0.1:5501',
  'http://127.0.0.1:5502', 'http://127.0.0.1:5503',
  'http://localhost:5500', 'http://localhost:5501',
  'http://localhost:5502', 'http://localhost:5503',
  'null',
];

// ---------------------------------------------------------------------------
// API Key 安全加载
// ---------------------------------------------------------------------------
function loadApiKey() {
  // 优先级 1：环境变量
  if (process.env.XFYUN_API_KEY) {
    console.log('  → 使用环境变量 XFYUN_API_KEY');
    return process.env.XFYUN_API_KEY;
  }

  // 优先级 2：本地 .env 文件
  const envPath = path.join(import.meta.dirname || '.', '.env');
  if (existsSync(envPath)) {
    try {
      const lines = readFileSync(envPath, 'utf-8').split('\n');
      for (const line of lines) {
        const [k, ...v] = line.split('=');
        if (k.trim() === 'XFYUN_API_KEY' && v.length) {
          const val = v.join('=').trim().replace(/^['"]|['"]$/g, '');
          if (val) {
            console.log('  → 从 .env 文件读取 API Key');
            return val;
          }
        }
      }
    } catch { /* 忽略读取错误 */ }
  }

  return '';
}

const FALLBACK_KEY = loadApiKey();

// ============================================================================
// HTTP 服务器
// ============================================================================
const app = http.createServer(async (req, res) => {
  const t = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  const origin = req.headers.origin || 'null';
  const method = req.method;
  const url = req.url;

  // CORS 头（每次响应都加）
  const setCors = () => {
    if (ALLOWED_ORIGINS.includes(origin) || !origin) {
      res.setHeader('Access-Control-Allow-Origin', origin || '*');
    } else {
      res.setHeader('Access-Control-Allow-Origin', '*');
    }
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
    res.setHeader('Access-Control-Max-Age', '86400');
  };

  // 统一 JSON 响应
  const json = (code, data) => {
    setCors();
    res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(data));
  };

  // 日志
  console.log(`[${t}] ${method} ${url}  (Origin: ${origin})`);

  // ===== OPTIONS 预检 =====
  if (method === 'OPTIONS') {
    setCors();
    res.writeHead(204);
    res.end();
    return;
  }

  // ===== GET /health =====
  if (method === 'GET' && url === '/health') {
    json(200, {
      status: 'ok',
      upstream: UPSTREAM_BASE,
      port: PORT,
      hasKey: !!FALLBACK_KEY,
      keySource: FALLBACK_KEY ? (process.env.XFYUN_API_KEY ? 'env' : '.env') : 'none',
      time: new Date().toISOString(),
    });
    return;
  }

  // ===== GET /v1/models =====
  if (method === 'GET' && url === '/v1/models') {
    json(200, {
      object: 'list',
      data: [
        { id: 'astron-code-latest', object: 'model', owned_by: 'xfyun' },
        { id: 'deepseek-chat', object: 'model', owned_by: 'deepseek' },
        { id: 'xopgpt', object: 'model', owned_by: 'xfyun' },
      ],
    });
    return;
  }

  // ===== POST /v1/chat/completions（核心代理） =====
  if (method === 'POST' && url === '/v1/chat/completions') {
    return proxyChat(req, res);
  }

  // ===== 404 兜底 =====
  json(404, {
    error: {
      message: `代理不支持此路由: ${method} ${url}`,
      hint: '请使用 POST /v1/chat/completions',
    },
  });
});

// ---------------------------------------------------------------------------
// 核心代理逻辑（独立函数便于阅读）
// ---------------------------------------------------------------------------
async function proxyChat(clientReq, clientRes) {
  // 1) 读取 body
  const body = await new Promise((resolve) => {
    const chunks = [];
    clientReq.on('data', (c) => chunks.push(c));
    clientReq.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });

  // 2) 解析 API Key（浏览器 header > FALLBACK_KEY）
  let apiKey = clientReq.headers.authorization || '';
  if (apiKey.toLowerCase().startsWith('bearer ')) apiKey = apiKey.slice(7).trim();
  if (!apiKey) apiKey = FALLBACK_KEY;

  if (!apiKey) {
    const setCors = () => {
      const o = clientReq.headers.origin || 'null';
      clientRes.setHeader('Access-Control-Allow-Origin', o === 'null' ? '*' : o);
    };
    setCors();
    clientRes.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
    clientRes.end(JSON.stringify({
      error: {
        message: '缺少 API Key。请配置：\n  方式 1: 在页面弹出框中输入 Key（推荐）\n  方式 2: 在 .env 文件中设置 XFYUN_API_KEY（重启代理生效）',
      },
    }));
    return;
  }

  // 3) 检查请求体
  let parsed;
  try { parsed = JSON.parse(body); } catch { parsed = {}; }

  const upstreamUrl = `${UPSTREAM_BASE}/v2/chat/completions`;
  const model = parsed.model || 'astron-code-latest';
  console.log(`  → 转发: model=${model}  body=${body.slice(0, 120)}…`);

  // 4) 构造上游请求
  const upstreamReq = https.request(upstreamUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
  });

  upstreamReq.on('response', (upstreamRes) => {
    const ct = upstreamRes.headers['content-type'] || '';
    const isStream = ct.includes('text/event-stream');

    // CORS 头回写
    const o = clientReq.headers.origin || 'null';
    clientRes.setHeader('Access-Control-Allow-Origin', o === 'null' ? '*' : o);
    clientRes.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    clientRes.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (isStream) {
      // SSE 流式透传
      clientRes.writeHead(upstreamRes.statusCode, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      });
      upstreamRes.pipe(clientRes);
      upstreamRes.on('end', () => {
        console.log('  ← SSE 流结束');
        clientRes.end();
      });
    } else {
      // JSON 响应
      let data = '';
      upstreamRes.on('data', (c) => data += c);
      upstreamRes.on('end', () => {
        console.log(`  ← 状态 ${upstreamRes.statusCode}  ${data.slice(0, 120)}…`);
        clientRes.writeHead(upstreamRes.statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
        clientRes.end(data);
      });
    }
  });

  upstreamReq.on('error', (err) => {
    console.error('  ✕ 上游请求失败:', err.message);
    const o = clientReq.headers.origin || 'null';
    clientRes.setHeader('Access-Control-Allow-Origin', o === 'null' ? '*' : o);
    clientRes.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
    clientRes.end(JSON.stringify({
      error: { message: '代理连接上游失败: ' + err.message, type: 'proxy_error' },
    }));
  });

  // 5) 发送 body
  upstreamReq.write(body);
  upstreamReq.end();
}

// ---------------------------------------------------------------------------
// 启动
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log('='.repeat(60));
  console.log('  Page-Agent CORS 代理（零依赖）');
  console.log('='.repeat(60));
  console.log(`  监听端口:  ${PORT}`);
  console.log(`  上游 API:  ${UPSTREAM_BASE}`);
  console.log(`  API Key:   ${FALLBACK_KEY ? '✅ 已配置' : '❌ 未配置（浏览器传入或 .env 文件）'}`);
  console.log(`  健康检查:   http://127.0.0.1:${PORT}/health`);
  console.log('');
  console.log('  页面中配置:');
  console.log(`    baseURL: http://127.0.0.1:${PORT}/v1`);
  console.log('  刷新浏览器后打开 AI 面板输入 Key 即可');
  console.log('='.repeat(60));
});

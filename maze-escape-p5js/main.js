'use strict';

// ============================================================================
// DETERMINISTIC PRNG: mulberry32 + seed 42
// ============================================================================
function mulberry32(a) {
  return function() {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    var t = a;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

var rng = mulberry32(42);

// ============================================================================
// PERLIN NOISE 2D (seeded permutation table from mulberry32(12345))
// ============================================================================
var _perm = new Uint8Array(512);
var _grad2 = [[1,1],[-1,1],[1,-1],[-1,-1],[1,0],[-1,0],[0,1],[0,-1]];
(function initNoise() {
  var noiseRng = mulberry32(12345);
  var p = new Uint8Array(256);
  for (var i = 0; i < 256; i++) p[i] = i;
  for (var i = 255; i > 0; i--) {
    var j = Math.floor(noiseRng() * (i + 1));
    var tmp = p[i]; p[i] = p[j]; p[j] = tmp;
  }
  for (var i = 0; i < 512; i++) _perm[i] = p[i & 255];
})();

function fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
function lerp(a, b, t) { return a + t * (b - a); }
function grad2(hash, x, y) {
  var g = _grad2[hash & 7];
  return g[0] * x + g[1] * y;
}

function noise2D(x, y) {
  var X = Math.floor(x) & 255;
  var Y = Math.floor(y) & 255;
  var xf = x - Math.floor(x);
  var yf = y - Math.floor(y);
  var u = fade(xf);
  var v = fade(yf);
  var aa = _perm[_perm[X] + Y];
  var ab = _perm[_perm[X] + Y + 1];
  var ba = _perm[_perm[X + 1] + Y];
  var bb = _perm[_perm[X + 1] + Y + 1];
  return lerp(
    lerp(grad2(aa, xf, yf), grad2(ba, xf - 1, yf), u),
    lerp(grad2(ab, xf, yf - 1), grad2(bb, xf - 1, yf - 1), u),
    v
  );
}

// ============================================================================
// CANVAS & CONSTANTS
// ============================================================================
var canvas = document.getElementById('mazeCanvas');
var ctx = canvas.getContext('2d');
var W = 1080, H = 1440;

var MAZE_COLS = 24;
var MAZE_ROWS = 32;
var CELL_SIZE = Math.floor(Math.min((W - 80) / MAZE_COLS, (H - 200) / MAZE_ROWS));
var MAZE_OFFSET_X = (W - MAZE_COLS * CELL_SIZE) / 2;
var MAZE_OFFSET_Y = 120;

var PAL = {
  bg: '#050508', wall: '#1a1a2e', wallHi: '#2a2a4e', path: '#0d0d1a',
  accent: '#00ffaa', bfs: '#00ccff', bfsPink: '#ff79c6', exit: '#ffd866',
  crash: '#ff3b30', pink: '#ff79c6', cyan: '#00ffcc', white: '#ffffff',
  gridLine: '#0a0a14', genCell: '#ff3b30'
};

// ============================================================================
// MAZE CELL
// ============================================================================
function MazeCell(col, row) {
  this.col = col; this.row = row;
  this.walls = { top: true, right: true, bottom: true, left: true };
  this.visited = false; this.isPath = false; this.distance = -1;
}

// ============================================================================
// MAZE DATA
// ============================================================================
var grid1 = [], grid2 = [];
var genSteps1 = [], genSteps2 = [];
var deadEndCount1 = 0, deadEndCount2 = 0;
var bfsPath1 = [], bfsVisited1 = [];
var bfsPath2 = [], bfsVisited2 = [];

// ============================================================================
// MAZE GENERATION (full pre-computation, deterministic)
// ============================================================================
function buildMaze(targetGrid, rngSeed) {
  var localRng = mulberry32(rngSeed);
  targetGrid.length = 0;
  for (var r = 0; r < MAZE_ROWS; r++)
    for (var c = 0; c < MAZE_COLS; c++)
      targetGrid.push(new MazeCell(c, r));

  var stack = [], steps = [], deadEnds = 0;
  var vis = new Set(); vis.add('0,0');
  var start = targetGrid[0];
  start.visited = true; stack.push(start);
  var current = start;
  var wallDirs = [
    { dc: 0, dr: -1, wall: 'top', opp: 'bottom' },
    { dc: 1, dr: 0, wall: 'right', opp: 'left' },
    { dc: 0, dr: 1, wall: 'bottom', opp: 'top' },
    { dc: -1, dr: 0, wall: 'left', opp: 'right' }
  ];

  while (stack.length > 0) {
    var neighbors = [];
    for (var d = 0; d < wallDirs.length; d++) {
      var nc = current.col + wallDirs[d].dc;
      var nr = current.row + wallDirs[d].dr;
      if (nc >= 0 && nc < MAZE_COLS && nr >= 0 && nr < MAZE_ROWS) {
        var n = targetGrid[nr * MAZE_COLS + nc];
        if (!n.visited) neighbors.push({ cell: n, wall: wallDirs[d].wall, opp: wallDirs[d].opp });
      }
    }
    if (neighbors.length > 0) {
      var idx = Math.floor(localRng() * neighbors.length);
      var chosen = neighbors[idx];
      current.walls[chosen.wall] = false;
      chosen.cell.walls[chosen.opp] = false;
      chosen.cell.visited = true;
      stack.push(chosen.cell);
      current = chosen.cell;
      vis.add(current.col + ',' + current.row);
    } else {
      if (stack.length > 1) deadEnds++;
      stack.pop();
      current = stack.length > 0 ? stack[stack.length - 1] : null;
    }
    steps.push({
      current: current ? { col: current.col, row: current.row } : null,
      deadEnds: deadEnds,
      visible: new Set(vis)
    });
  }
  return { steps: steps, deadEnds: deadEnds };
}

// ============================================================================
// BFS PATHFINDING
// ============================================================================
function solveMazeBFS(targetGrid) {
  var visited = [], path = [];
  var start = targetGrid[0];
  var end = targetGrid[(MAZE_ROWS - 1) * MAZE_COLS + (MAZE_COLS - 1)];
  var queue = [start], visSet = new Set(), parent = new Map();
  visSet.add(start); start.distance = 0;
  var dirs = [
    { dc: 0, dr: -1, wall: 'top' }, { dc: 1, dr: 0, wall: 'right' },
    { dc: 0, dr: 1, wall: 'bottom' }, { dc: -1, dr: 0, wall: 'left' }
  ];
  while (queue.length > 0) {
    var cell = queue.shift(); visited.push(cell);
    if (cell === end) break;
    for (var d = 0; d < dirs.length; d++) {
      if (!cell.walls[dirs[d].wall]) {
        var nc = cell.col + dirs[d].dc, nr = cell.row + dirs[d].dr;
        if (nc >= 0 && nc < MAZE_COLS && nr >= 0 && nr < MAZE_ROWS) {
          var neighbor = targetGrid[nr * MAZE_COLS + nc];
          if (!visSet.has(neighbor)) {
            visSet.add(neighbor); neighbor.distance = cell.distance + 1;
            parent.set(neighbor, cell); queue.push(neighbor);
          }
        }
      }
    }
  }
  var cur = end;
  while (cur) { cur.isPath = true; path.unshift(cur); cur = parent.get(cur); }
  return { visited: visited, path: path };
}
// ============================================================================
// PARTICLE SYSTEM (600 particles, Perlin flow field)
// ============================================================================
var PARTICLE_COUNT = 600;
var particles = [];
var pRng = mulberry32(555);

function createParticle(initial) {
  var p = {
    x: pRng() * W, y: pRng() * H,
    size: 1.5 + pRng() * 2.5,
    maxLife: 120 + Math.floor(pRng() * 180),
    speed: 0.3 + pRng() * 0.8,
    hue: pRng() > 0.5 ? 'cyan' : 'pink',
    prevX: 0, prevY: 0, life: 0
  };
  p.life = initial ? Math.floor(pRng() * p.maxLife) : p.maxLife;
  p.prevX = p.x; p.prevY = p.y;
  return p;
}

function resetParticle(p, initial) {
  var np = createParticle(initial);
  p.x = np.x; p.y = np.y; p.size = np.size;
  p.maxLife = np.maxLife; p.speed = np.speed;
  p.hue = np.hue; p.life = np.life;
  p.prevX = np.prevX; p.prevY = np.prevY;
}

function initParticles() {
  particles = [];
  for (var i = 0; i < PARTICLE_COUNT; i++) particles.push(createParticle(true));
}

function updateParticle(p, time) {
  p.prevX = p.x; p.prevY = p.y;
  var scale = 0.003;
  var n = noise2D(p.x * scale, p.y * scale + time * 0.1);
  var angle = n * Math.PI * 4;
  p.x += Math.cos(angle) * p.speed;
  p.y += Math.sin(angle) * p.speed;
  p.life--;
  if (p.life <= 0 || p.x < -20 || p.x > W + 20 || p.y < -20 || p.y > H + 20)
    resetParticle(p, false);
}

function drawParticle(p, opacity) {
  var alpha = Math.min(1, p.life / 30) * opacity;
  if (alpha <= 0) return;
  var color = p.hue === 'cyan'
    ? 'rgba(0,255,204,' + (alpha * 0.7) + ')'
    : 'rgba(255,121,198,' + (alpha * 0.7) + ')';
  ctx.beginPath(); ctx.moveTo(p.prevX, p.prevY); ctx.lineTo(p.x, p.y);
  ctx.strokeStyle = color; ctx.lineWidth = p.size; ctx.lineCap = 'round'; ctx.stroke();
}

// ============================================================================
// EXPLOSION DATA
// ============================================================================
var explosionDebris = [];

function initExplosion() {
  explosionDebris = [];
  var expRng = mulberry32(999);
  for (var i = 0; i < 200; i++) {
    var angle = expRng() * Math.PI * 2;
    var speed = 2 + expRng() * 12;
    var size = 2 + expRng() * 6;
    var ml = 40 + Math.floor(expRng() * 40);
    explosionDebris.push({
      vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
      size: size, life: ml, maxLife: ml,
      hue: expRng() > 0.3 ? 'red' : 'yellow'
    });
  }
}

// ============================================================================
// PRE-COMPUTE ALL DATA
// ============================================================================
function precomputeAll() {
  var m1 = buildMaze(grid1, 100);
  genSteps1 = m1.steps; deadEndCount1 = m1.deadEnds;
  var b1 = solveMazeBFS(grid1);
  bfsVisited1 = b1.visited; bfsPath1 = b1.path;
  var m2 = buildMaze(grid2, 200);
  genSteps2 = m2.steps; deadEndCount2 = m2.deadEnds;
  var b2 = solveMazeBFS(grid2);
  bfsVisited2 = b2.visited; bfsPath2 = b2.path;
  initParticles(); initExplosion();
}

// ============================================================================
// DRAW: BACKGROUND
// ============================================================================
function drawBackground(time) {
  var grd = ctx.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, H);
  grd.addColorStop(0, '#0a0a1a'); grd.addColorStop(1, '#050508');
  ctx.fillStyle = grd; ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = PAL.gridLine; ctx.lineWidth = 0.5;
  for (var x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (var y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

  var ga = 0.03 + Math.sin(time * 0.5) * 0.01;
  var glow = ctx.createRadialGradient(W / 2, H * 0.4, 50, W / 2, H * 0.4, 400);
  glow.addColorStop(0, 'rgba(0,255,170,' + ga + ')'); glow.addColorStop(1, 'rgba(0,255,170,0)');
  ctx.fillStyle = glow; ctx.fillRect(0, 0, W, H);
}

// ============================================================================
// DRAW: MAZE
// ============================================================================
function drawMaze(targetGrid, stepsArr, revealProgress, time) {
  if (revealProgress <= 0) return;
  var stepsToShow = Math.max(1, Math.floor(revealProgress * stepsArr.length));
  var stepIdx = Math.min(stepsToShow - 1, stepsArr.length - 1);
  var visible = stepsArr[stepIdx].visible;

  // Cell backgrounds
  for (var i = 0; i < targetGrid.length; i++) {
    var cell = targetGrid[i];
    if (!cell.visited) continue;
    if (!visible.has(cell.col + ',' + cell.row)) continue;
    var x = MAZE_OFFSET_X + cell.col * CELL_SIZE;
    var y = MAZE_OFFSET_Y + cell.row * CELL_SIZE;
    ctx.fillStyle = cell.isPath ? 'rgba(0,204,255,0.08)' : PAL.path;
    ctx.fillRect(x, y, CELL_SIZE, CELL_SIZE);
  }

  // Walls
  ctx.strokeStyle = PAL.wall; ctx.lineWidth = 2; ctx.lineCap = 'round';
  for (var i = 0; i < targetGrid.length; i++) {
    var cell = targetGrid[i];
    if (!cell.visited || !visible.has(cell.col + ',' + cell.row)) continue;
    var x = MAZE_OFFSET_X + cell.col * CELL_SIZE;
    var y = MAZE_OFFSET_Y + cell.row * CELL_SIZE;
    if (cell.walls.top) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + CELL_SIZE, y); ctx.stroke(); }
    if (cell.walls.right) { ctx.beginPath(); ctx.moveTo(x + CELL_SIZE, y); ctx.lineTo(x + CELL_SIZE, y + CELL_SIZE); ctx.stroke(); }
    if (cell.walls.bottom) { ctx.beginPath(); ctx.moveTo(x, y + CELL_SIZE); ctx.lineTo(x + CELL_SIZE, y + CELL_SIZE); ctx.stroke(); }
    if (cell.walls.left) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + CELL_SIZE); ctx.stroke(); }
  }

  // Current gen cell highlight
  if (stepsToShow > 0) {
    var cur = stepsArr[Math.min(stepsToShow - 1, stepsArr.length - 1)].current;
    if (cur) {
      var cx = MAZE_OFFSET_X + cur.col * CELL_SIZE;
      var cy = MAZE_OFFSET_Y + cur.row * CELL_SIZE;
      ctx.fillStyle = 'rgba(255,59,48,0.3)'; ctx.fillRect(cx - 4, cy - 4, CELL_SIZE + 8, CELL_SIZE + 8);
      ctx.fillStyle = PAL.genCell; ctx.fillRect(cx + 2, cy + 2, CELL_SIZE - 4, CELL_SIZE - 4);
    }
  }

  // Start marker
  ctx.fillStyle = PAL.accent;
  ctx.beginPath(); ctx.arc(MAZE_OFFSET_X + CELL_SIZE / 2, MAZE_OFFSET_Y + CELL_SIZE / 2, CELL_SIZE * 0.3, 0, Math.PI * 2); ctx.fill();

  // End marker
  var ex = MAZE_OFFSET_X + (MAZE_COLS - 0.5) * CELL_SIZE;
  var ey = MAZE_OFFSET_Y + (MAZE_ROWS - 0.5) * CELL_SIZE;
  ctx.fillStyle = PAL.exit;
  ctx.beginPath(); ctx.arc(ex, ey, CELL_SIZE * 0.3, 0, Math.PI * 2); ctx.fill();
  var pulse = 0.3 + Math.sin(time * 3) * 0.15;
  ctx.strokeStyle = 'rgba(255,216,102,' + pulse + ')'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(ex, ey, CELL_SIZE * 0.4 + Math.sin(time * 2) * 3, 0, Math.PI * 2); ctx.stroke();
}
// ============================================================================
// DRAW: FLOW FIELD
// ============================================================================
function drawFlowField(time, opacity) {
  if (opacity <= 0) return;
  ctx.globalAlpha = opacity;
  var spacing = 45, arrowLen = 14;
  var mazeBottom = MAZE_OFFSET_Y + MAZE_ROWS * CELL_SIZE;
  var mazeHeight = MAZE_ROWS * CELL_SIZE;
  for (var x = spacing; x < W; x += spacing) {
    for (var y = MAZE_OFFSET_Y; y < mazeBottom; y += spacing) {
      var n = noise2D(x * 0.005 + time * 0.2, y * 0.005);
      var angle = n * Math.PI * 2;
      var dx = Math.cos(angle) * arrowLen, dy = Math.sin(angle) * arrowLen;
      var t = (y - MAZE_OFFSET_Y) / mazeHeight;
      var r = Math.floor(lerp(0, 255, t));
      var g = Math.floor(lerp(255, 121, t));
      var b = Math.floor(lerp(204, 198, t));
      ctx.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.4)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x - dx * 0.5, y - dy * 0.5); ctx.lineTo(x + dx * 0.5, y + dy * 0.5); ctx.stroke();

    }
  }
  ctx.globalAlpha = 1;
}

// ============================================================================
// DRAW: BFS PATH
// ============================================================================
function drawBFSPath(targetBfsVisited, targetBfsPath, time, bfsReveal) {
  if (bfsReveal <= 0 || targetBfsVisited.length === 0) return;
  var visitedCount = Math.floor(bfsReveal * 2 * targetBfsVisited.length);
  for (var i = 0; i < Math.min(visitedCount, targetBfsVisited.length); i++) {
    var cell = targetBfsVisited[i];
    var x = MAZE_OFFSET_X + cell.col * CELL_SIZE;
    var y = MAZE_OFFSET_Y + cell.row * CELL_SIZE;
    var alpha = 0.05 + 0.05 * Math.sin(time * 2 + i * 0.1);
    ctx.fillStyle = 'rgba(0,204,255,' + alpha + ')';
    ctx.fillRect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2);
  }
  if (bfsReveal > 0.3 && targetBfsPath.length > 0) {
    var pathReveal = Math.min(1, (bfsReveal - 0.3) / 0.7);
    var pathCount = Math.floor(pathReveal * targetBfsPath.length);
    if (pathCount > 1) {
      ctx.lineWidth = CELL_SIZE * 0.35; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      for (var i = 1; i < pathCount; i++) {
        var prev = targetBfsPath[i - 1], curr = targetBfsPath[i];
        var t = i / targetBfsPath.length;
        var r = Math.floor(lerp(0, 255, t));
        var g = Math.floor(lerp(204, 121, t));
        var b = Math.floor(lerp(255, 198, t));
        ctx.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.8)';
        ctx.beginPath();
        ctx.moveTo(MAZE_OFFSET_X + prev.col * CELL_SIZE + CELL_SIZE / 2, MAZE_OFFSET_Y + prev.row * CELL_SIZE + CELL_SIZE / 2);
        ctx.lineTo(MAZE_OFFSET_X + curr.col * CELL_SIZE + CELL_SIZE / 2, MAZE_OFFSET_Y + curr.row * CELL_SIZE + CELL_SIZE / 2);
        ctx.stroke();
      }
      // Pulsing head cursor
      if (pathCount > 0) {
        var head = targetBfsPath[pathCount - 1];
        var hx = MAZE_OFFSET_X + head.col * CELL_SIZE + CELL_SIZE / 2;
        var hy = MAZE_OFFSET_Y + head.row * CELL_SIZE + CELL_SIZE / 2;
        var pulse = 4 + Math.sin(time * 6) * 2;
        ctx.fillStyle = PAL.white;
        ctx.beginPath(); ctx.arc(hx, hy, pulse, 0, Math.PI * 2); ctx.fill();
        var headGlow = ctx.createRadialGradient(hx, hy, 0, hx, hy, CELL_SIZE);
        headGlow.addColorStop(0, 'rgba(0,255,170,0.3)'); headGlow.addColorStop(1, 'rgba(0,255,170,0)');
        ctx.fillStyle = headGlow;
        ctx.fillRect(hx - CELL_SIZE, hy - CELL_SIZE, CELL_SIZE * 2, CELL_SIZE * 2);
      }
    }
  }
}

// ============================================================================
// DRAW: EXPLOSION
// ============================================================================
function drawExplosion(time, progress) {
  if (progress <= 0) return;
  var cx = W / 2, cy = H / 2, p = Math.min(1, progress);
  // Screen flash
  if (p < 0.3) {
    ctx.fillStyle = 'rgba(255,59,48,' + ((1 - p / 0.3) * 0.6) + ')';
    ctx.fillRect(0, 0, W, H);
  }
  // Shockwave ring 1
  var ringA = Math.max(0, 1 - p);
  ctx.strokeStyle = 'rgba(255,59,48,' + ringA + ')'; ctx.lineWidth = 4 + (1 - p) * 8;
  ctx.beginPath(); ctx.arc(cx, cy, p * 600, 0, Math.PI * 2); ctx.stroke();
  // Shockwave ring 2
  ctx.strokeStyle = 'rgba(255,216,102,' + (ringA * 0.5) + ')'; ctx.lineWidth = 2 + (1 - p) * 4;
  ctx.beginPath(); ctx.arc(cx, cy, p * 400, 0, Math.PI * 2); ctx.stroke();
  // Center flash
  if (p < 0.5) {
    var fs = (1 - p * 2) * 200;
    if (fs > 1) {
      var fg = ctx.createRadialGradient(cx, cy, 0, cx, cy, fs);
      fg.addColorStop(0, 'rgba(255,255,255,' + ((1 - p * 2) * 0.8) + ')');
      fg.addColorStop(0.5, 'rgba(255,59,48,' + ((1 - p * 2) * 0.4) + ')');
      fg.addColorStop(1, 'rgba(255,59,48,0)');
      ctx.fillStyle = fg; ctx.fillRect(cx - fs, cy - fs, fs * 2, fs * 2);
    }
  }
  // Debris
  for (var i = 0; i < explosionDebris.length; i++) {
    var dp = explosionDebris[i];
    var dpp = Math.min(1, p * 1.5);
    var px = cx + dp.vx * dpp * 30, py = cy + dp.vy * dpp * 30;
    var alpha = Math.max(0, 1 - dpp * 1.2) * (dp.life / dp.maxLife);
    if (alpha <= 0) continue;
    ctx.fillStyle = dp.hue === 'red' ? 'rgba(255,59,48,' + alpha + ')' : 'rgba(255,216,102,' + alpha + ')';
    ctx.fillRect(px - dp.size / 2, py - dp.size / 2, dp.size, dp.size);
  }
  // Glitch lines
  if (p < 0.7) {
    var glitchRng = mulberry32(777);
    ctx.fillStyle = 'rgba(255,59,48,' + ((1 - p / 0.7) * 0.3) + ')';
    for (var i = 0; i < 15; i++) {
      var gy = glitchRng() * H, gw = 50 + glitchRng() * 300, gx = glitchRng() * W;
      ctx.fillRect(gx, gy, gw, 2 + glitchRng() * 4);
    }
  }
}
// ============================================================================
// DRAW: MOBIUS STRIP
// ============================================================================
function drawMobiusStrip(time, opacity) {
  if (opacity <= 0) return;
  ctx.globalAlpha = opacity;
  var cx = W / 2, cy = H * 0.55, R = 200, halfW = 60;
  var rotation = time * 0.5, tilt = 0.4;
  var segments = 120, strips = 6;

  for (var s = 0; s < strips; s++) {
    var v = (s / strips - 0.5) * 2;
    ctx.beginPath();
    var first = true;
    for (var i = 0; i <= segments; i++) {
      var u = (i / segments) * Math.PI * 2;
      var ht = u / 2;
      var xp = R * Math.cos(u + rotation) + v * halfW * Math.cos(ht) * Math.cos(u + rotation) * 0.3;
      var yp = R * Math.sin(u + rotation) * Math.cos(tilt) + v * halfW * (Math.sin(ht) * 0.7 + Math.cos(ht) * Math.sin(u + rotation) * Math.sin(tilt) * 0.3);
      if (first) { ctx.moveTo(cx + xp, cy + yp); first = false; }
      else { ctx.lineTo(cx + xp, cy + yp); }
    }
    var t = s / strips;
    var r = Math.floor(lerp(0, 255, t)), g = Math.floor(lerp(255, 121, t)), b = Math.floor(lerp(170, 198, t));
    ctx.strokeStyle = 'rgba(' + r + ',' + g + ',' + b + ',0.6)'; ctx.lineWidth = 2; ctx.stroke();
  }

  // Flow particles on strip
  var mobiusRng = mulberry32(888);
  for (var i = 0; i < 40; i++) {
    var baseU = mobiusRng() * Math.PI * 2, baseV = (mobiusRng() - 0.5) * 2;
    var speed = 0.3 + mobiusRng() * 0.7;
    var u = baseU + time * speed, v = baseV, ht = u / 2;
    var xp = R * Math.cos(u + rotation) + v * halfW * Math.cos(ht) * Math.cos(u + rotation) * 0.3;
    var yp = R * Math.sin(u + rotation) * Math.cos(tilt) + v * halfW * (Math.sin(ht) * 0.7 + Math.cos(ht) * Math.sin(u + rotation) * Math.sin(tilt) * 0.3);
    var depth = (Math.sin(u + rotation) * Math.sin(tilt) + 1) / 2;
    var alpha = 0.3 + depth * 0.5, sz = 1.5 + depth * 2;
    var pt = (Math.sin(u) + 1) / 2;
    var pr = Math.floor(lerp(0, 255, pt)), pg = Math.floor(lerp(255, 121, pt)), pb = Math.floor(lerp(170, 198, pt));
    ctx.fillStyle = 'rgba(' + pr + ',' + pg + ',' + pb + ',' + alpha + ')';
    ctx.beginPath(); ctx.arc(cx + xp, cy + yp, sz, 0, Math.PI * 2); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// ============================================================================
// DRAW: PARTICLES
// ============================================================================
function drawParticles(time, opacity) {
  if (opacity <= 0) return;
  ctx.globalAlpha = opacity;
  for (var i = 0; i < particles.length; i++) {
    updateParticle(particles[i], time);
    drawParticle(particles[i], opacity);
  }
  ctx.globalAlpha = 1;
}

// ============================================================================
// CODE PANEL CONTENT PER PHASE
// ============================================================================
function getCodePanelHTML(progress) {
  if (progress < 0.02) {
    return '<span class="code-comment">// initialize maze escape</span>\n' +
      '<span class="code-keyword">const</span> seed = <span class="code-num">42</span>;\n' +
      '<span class="code-keyword">const</span> rng = <span class="code-func">mulberry32</span>(seed);';
  } else if (progress < 0.18) {
    return '<span class="code-comment">// recursive backtracker</span>\n' +
      '<span class="code-keyword">while</span> (stack.length > <span class="code-num">0</span>) {\n' +
      '  <span class="code-keyword">var</span> next = <span class="code-func">pickNeighbor</span>(rng);\n' +
      '  <span class="code-func">removeWall</span>(current, next);\n' +
      '  deadEnds++; <span class="code-comment">// backtrack</span>\n}';
  } else if (progress < 0.28) {
    return '<span class="code-comment">// perlin noise flow</span>\n' +
      '<span class="code-keyword">var</span> n = <span class="code-func">noise2D</span>(x*<span class="code-num">0.005</span>, y*<span class="code-num">0.005</span>);\n' +
      '<span class="code-keyword">var</span> angle = n * Math.PI * <span class="code-num">4</span>;\n' +
      '<span class="code-func">particle</span>.x += <span class="code-func">cos</span>(angle) * speed;';
  } else if (progress < 0.48) {
    return '<span class="code-comment">// BFS pathfinding</span>\n' +
      '<span class="code-keyword">var</span> queue = [<span class="code-func">start</span>];\n' +
      '<span class="code-keyword">while</span> (queue.length > <span class="code-num">0</span>) {\n' +
      '  <span class="code-keyword">var</span> cell = queue.<span class="code-func">shift</span>();\n' +
      '  <span class="code-keyword">for</span> (neighbor <span class="code-keyword">of</span> cell) {\n' +
      '    <span class="code-func">explore</span>(neighbor);\n' +
      '  }\n}';
  } else if (progress < 0.52) {
    return '<span class="code-keyword">Uncaught TypeError</span>:\n' +
      '  Cannot read property <span class="code-num">\'path\'</span>\n' +
      '  of undefined at <span class="code-func">solveMaze</span>\n' +
      '  <span class="code-comment">// stack overflow detected</span>';
  } else if (progress < 0.68) {
    return '<span class="code-comment">// rebuild from scratch</span>\n' +
      '<span class="code-func">resetAll</span>();\n' +
      '<span class="code-keyword">var</span> m2 = <span class="code-func">buildMaze</span>(grid, <span class="code-num">200</span>);\n' +
      '<span class="code-keyword">var</span> b2 = <span class="code-func">solveMaze</span>(grid2);\n' +
      'vote += <span class="code-num">32</span>; <span class="code-comment">// recovered</span>';
  } else if (progress < 0.90) {
    return '<span class="code-comment">// mobius strip transform</span>\n' +
      '<span class="code-keyword">var</span> ht = u / <span class="code-num">2</span>;\n' +
      '<span class="code-keyword">var</span> x = R*<span class="code-func">cos</span>(u) + v*w*<span class="code-func">cos</span>(ht);\n' +
      '<span class="code-keyword">var</span> y = R*<span class="code-func">sin</span>(u) + v*w*<span class="code-func">sin</span>(ht);\n' +
      '<span class="code-comment">// topology: non-orientable</span>';
  } else {
    return '<span class="code-comment">// vote passed!</span>\n' +
      '<span class="code-keyword">if</span> (vote >= <span class="code-num">72</span>) {\n' +
      '  <span class="code-func">escape</span>(maze);\n' +
      '  <span class="code-keyword">return</span> <span class="code-num">true</span>;\n' +
      '}\n<span class="code-comment">// 72% VOTE PASSED</span>';
  }
}
// ============================================================================
// HUD UPDATE
// ============================================================================
function updateHUD(progress, time) {
  // Countdown: 30:00 counting down (1800s total)
  var totalSec = 1800 - Math.floor(progress * 1800);
  var min = Math.floor(totalSec / 60);
  var sec = totalSec % 60;
  var countdownEl = document.getElementById('countdown');
  if (countdownEl) countdownEl.textContent = (min < 10 ? '0' : '') + min + ':' + (sec < 10 ? '0' : '') + sec;

  // Vote percent
  var votePct = 0;
  if (progress < 0.02) votePct = 0;
  else if (progress < 0.18) votePct = Math.floor(((progress - 0.02) / 0.16) * 12);
  else if (progress < 0.28) votePct = 12 + Math.floor(((progress - 0.18) / 0.10) * 20);
  else if (progress < 0.48) votePct = 32 + Math.floor(((progress - 0.28) / 0.20) * 35);
  else if (progress < 0.52) votePct = 67 - Math.floor(((progress - 0.48) / 0.04) * 29);
  else if (progress < 0.54) votePct = 38;
  else if (progress < 0.68) votePct = 38 + Math.floor(((progress - 0.54) / 0.14) * 32);
  else if (progress < 0.90) votePct = 70 + Math.floor(((progress - 0.68) / 0.22) * 2);
  else votePct = 72;

  var voteEl = document.getElementById('votePercent');
  if (voteEl) voteEl.textContent = votePct + '%';

  // Vote label
  var voteLabelEl = document.getElementById('voteLabel');
  if (voteLabelEl) {
    if (progress >= 0.90) voteLabelEl.textContent = 'PASSED / 通过';
    else if (progress >= 0.48 && progress < 0.54) voteLabelEl.textContent = 'CRASH / 崩溃';
    else voteLabelEl.textContent = 'VOTE';
  }

  // Dead ends
  var deadEnds = 0;
  if (progress >= 0.02 && progress < 0.52) {
    deadEnds = progress < 0.18 ? Math.floor(((progress - 0.02) / 0.16) * deadEndCount1) : deadEndCount1;
  } else if (progress >= 0.54 && progress < 0.68) {
    deadEnds = Math.floor(((progress - 0.54) / 0.14) * deadEndCount2);
  } else if (progress >= 0.72) {
    deadEnds = deadEndCount2;
  }
  var deadEl = document.getElementById('deadEnds');
  if (deadEl) deadEl.textContent = 'DEAD ENDS / 死胡同: ' + deadEnds;

  // Progress bar
  var pf = document.getElementById('progressFill');
  if (pf) pf.style.width = (progress * 100) + '%';

  // Status text
  var statusEl = document.getElementById('statusText');
  if (statusEl) {
    var statusText = '', statusColor = PAL.accent;
    var statusSub = '';
    if (progress < 0.02) { statusText = 'MAZE ESCAPE'; statusSub = '迷宫逃生'; }
    else if (progress < 0.18) { statusText = 'GENERATING...'; statusSub = '生成中...'; }
    else if (progress < 0.28) { statusText = 'FLOW FIELD'; statusSub = '流场'; statusColor = PAL.cyan; }
    else if (progress < 0.48) { statusText = 'PATHFINDING'; statusSub = '路径搜索'; statusColor = PAL.bfs; }
    else if (progress < 0.52) { statusText = 'CRASH!'; statusSub = '崩溃!'; statusColor = PAL.crash; }
    else if (progress < 0.54) { statusText = ''; statusSub = ''; }
    else if (progress < 0.68) { statusText = 'REBUILD'; statusSub = '重建'; statusColor = PAL.cyan; }
    else if (progress < 0.90) { statusText = 'TRANSCEND'; statusSub = '超越'; statusColor = PAL.pink; }
    else { statusText = '72% VOTE PASSED'; statusSub = '72% 投票通过'; statusColor = PAL.accent; }

    statusEl.textContent = statusText;
    statusEl.style.color = statusColor;
    statusEl.style.opacity = statusText ? '1' : '0';

    var subEl = document.getElementById('statusSub');
    if (subEl) {
      subEl.textContent = statusSub;
      subEl.style.color = statusColor;
      subEl.style.opacity = statusSub ? '0.7' : '0';
    }

    // Fade in/out for transitions
    if (progress < 0.02) {
      statusEl.style.opacity = String(Math.min(1, progress / 0.01));
      if (subEl) subEl.style.opacity = String(Math.min(0.7, progress / 0.01 * 0.7));
    } else if (progress > 0.95) {
      statusEl.style.opacity = String(Math.max(0, (1 - progress) / 0.05));
      if (subEl) subEl.style.opacity = String(Math.max(0, (1 - progress) / 0.05 * 0.7));
    }
  }

  // Code panel
  var codeEl = document.getElementById('codeContent');
  if (codeEl) codeEl.innerHTML = getCodePanelHTML(progress);
}

// ============================================================================
// INTRO OVERLAY
// ============================================================================
function drawIntro(progress) {
  if (progress >= 0.02) return;
  var alpha = Math.min(1, progress / 0.01);
  if (progress > 0.013) alpha = Math.max(0, (0.02 - progress) / 0.007);

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = PAL.accent;
  ctx.font = 'bold 72px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('MAZE ESCAPE / 迷宫逃生', W / 2, H / 2 - 50);

  ctx.fillStyle = 'rgba(255,255,255,0.5)';
  ctx.font = '24px monospace';
  ctx.fillText('确定性生成艺术 / Deterministic Generative Art', W / 2, H / 2 + 10);
  ctx.fillText('seed = 42', W / 2, H / 2 + 55);
  ctx.restore();
}

// ============================================================================
// FADE OUT
// ============================================================================
function drawFadeOut(progress) {
  if (progress < 0.95) return;
  var alpha = (progress - 0.95) / 0.05;
  ctx.fillStyle = 'rgba(5,5,8,' + alpha + ')';
  ctx.fillRect(0, 0, W, H);
}

// ============================================================================
// MAIN RENDER FUNCTION
// ============================================================================
var _initialized = false;

window.__renderFrameAt = function(progress) {
  // Clamp
  progress = Math.max(0, Math.min(1, progress));
  var time = progress * 60.0;

  // Initialize on first call
  if (!_initialized) {
    precomputeAll();
    _initialized = true;
  }

  // Warm-up at frame 0
  if (time === 0) {
    for (var i = 0; i < 150; i++) {
      for (var j = 0; j < particles.length; j++) {
        updateParticle(particles[j], 0.01 * i);
      }
    }
  }

  // ===== PHASE COMPUTATION =====
  var mazeReveal1 = 0, flowOpacity = 0, bfsReveal1 = 0;
  var explosionProgress = 0, blackoutAlpha = 0;
  var mazeReveal2 = 0, bfsReveal2 = 0;
  var mobiusOpacity = 0, particleOpacity = 0;

  if (progress < 0.02) {
    // Intro (1.2s - faster)
    particleOpacity = 0;
  } else if (progress < 0.18) {
    // MazeGen: 0.02-0.18 (9.6s)
    mazeReveal1 = (progress - 0.02) / 0.16;
    particleOpacity = 0;
  } else if (progress < 0.28) {
    // FlowField: 0.18-0.28 (6s)
    mazeReveal1 = 1;
    flowOpacity = (progress - 0.18) / 0.10;
    particleOpacity = flowOpacity * 0.5;
  } else if (progress < 0.48) {
    // BFS: 0.28-0.48 (12s)
    mazeReveal1 = 1;
    flowOpacity = 1;
    bfsReveal1 = (progress - 0.28) / 0.20;
    particleOpacity = 0.5 + bfsReveal1 * 0.3;
  } else if (progress < 0.52) {
    // CRASH: 0.48-0.52 (2.4s)
    mazeReveal1 = 1;
    flowOpacity = 1 - (progress - 0.48) / 0.04;
    bfsReveal1 = 1;
    explosionProgress = (progress - 0.48) / 0.04;
    particleOpacity = 0;
  } else if (progress < 0.54) {
    // Blackout: 0.52-0.54 (1.2s - shorter)
    blackoutAlpha = 1;
    particleOpacity = 0;
  } else if (progress < 0.68) {
    // Rebuild: 0.54-0.68 (8.4s)
    var rebuildProg = (progress - 0.54) / 0.14;
    mazeReveal2 = rebuildProg;
    flowOpacity = rebuildProg > 0.3 ? (rebuildProg - 0.3) / 0.3 : 0;
    bfsReveal2 = rebuildProg > 0.5 ? (rebuildProg - 0.5) / 0.5 : 0;
    particleOpacity = rebuildProg * 0.6;
  } else if (progress < 0.90) {
    // Mobius: 0.68-0.90 (13.2s - more time)
    mazeReveal2 = 1;
    flowOpacity = Math.max(0, 1 - (progress - 0.68) / 0.10);
    bfsReveal2 = 1;
    mobiusOpacity = Math.min(1, (progress - 0.68) / 0.08);
    particleOpacity = 0.6 + (progress - 0.68) / 0.22 * 0.4;
  } else {
    // Final: 0.90-1.00 (6s)
    mazeReveal2 = 1;
    bfsReveal2 = 1;
    mobiusOpacity = 1;
    particleOpacity = 1;
  }

  // ===== UPDATE BGM =====
  updateBGM(progress);

  // ===== DRAW LAYERS =====
  // 1. Background (always)
  drawBackground(time);

  // 2. Intro overlay
  drawIntro(progress);

  // 3. Flow field (behind maze)
  drawFlowField(time, flowOpacity);

  // 4. Maze
  if (progress < 0.55) {
    drawMaze(grid1, genSteps1, mazeReveal1, time);
  } else if (progress >= 0.58) {
    drawMaze(grid2, genSteps2, mazeReveal2, time);
  }

  // 5. BFS path
  if (progress < 0.55) {
    drawBFSPath(bfsVisited1, bfsPath1, time, bfsReveal1);
  } else if (progress >= 0.58) {
    drawBFSPath(bfsVisited2, bfsPath2, time, bfsReveal2);
  }

  // 6. Particles
  drawParticles(time, particleOpacity);

  // 7. Explosion
  drawExplosion(time, explosionProgress);

  // 8. Mobius strip
  drawMobiusStrip(time, mobiusOpacity);

  // 9. Blackout overlay
  if (blackoutAlpha > 0) {
    ctx.fillStyle = 'rgba(5,5,8,' + blackoutAlpha + ')';
    ctx.fillRect(0, 0, W, H);
    // Countdown still visible during blackout
    ctx.fillStyle = 'rgba(0,255,170,0.3)';
    ctx.font = 'bold 48px monospace';
    ctx.textAlign = 'center';
    var totalSec = 1800 - Math.floor(progress * 1800);
    var min = Math.floor(totalSec / 60);
    var sec = totalSec % 60;
    ctx.fillText((min < 10 ? '0' : '') + min + ':' + (sec < 10 ? '0' : '') + sec, W / 2, H / 2);
  }

  // 10. Final glow
  if (progress >= 0.90) {
    var glowP = (progress - 0.90) / 0.10;
    var glowAlpha = 0.1 + Math.sin(time * 2) * 0.05;
    var finalGlow = ctx.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 500);
    finalGlow.addColorStop(0, 'rgba(0,255,170,' + (glowAlpha * glowP) + ')');
    finalGlow.addColorStop(0.5, 'rgba(255,121,198,' + (glowAlpha * 0.3 * glowP) + ')');
    finalGlow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = finalGlow;
    ctx.fillRect(0, 0, W, H);
  }

  // 11. Fade out
  drawFadeOut(progress);

  // ===== UPDATE HUD =====
  updateHUD(progress, time);
};

// ============================================================================
// BGM: Procedural Ambient Music (Web Audio API)
// ============================================================================
var bgmCtx = null, bgmStarted = false;
var bgmPadNodes = [], bgmBassNode = null, bgmArpNode = null;
var bgmChordNotes = [
  [261.63, 329.63, 392.00, 523.25], // C major
  [220.00, 277.18, 329.63, 440.00], // A minor
  [246.94, 311.13, 369.99, 493.88], // B dim
  [196.00, 246.94, 293.66, 392.00], // G major
  [261.63, 311.13, 392.00, 466.16], // F# dim  (crash)
  [220.00, 261.63, 329.63, 392.00]  // A minor 7
];
var bgmChordSchedule = [
  [0.00, 0], [0.04, 1], [0.18, 2], [0.28, 3],
  [0.36, 1], [0.48, 4], [0.54, 5], [0.68, 0],
  [0.78, 3], [0.90, 0]
];

function initBGM() {
  if (bgmCtx) return;
  try {
    bgmCtx = new (window.AudioContext || window.webkitAudioContext)();
    var resumeHandler = function() {
      if (bgmCtx && bgmCtx.state === 'suspended') bgmCtx.resume();
      if (!bgmStarted) { bgmStarted = true; startBGM(); }
      document.removeEventListener('click', resumeHandler);
      document.removeEventListener('touchstart', resumeHandler);
    };
    document.addEventListener('click', resumeHandler);
    document.addEventListener('touchstart', resumeHandler);
  } catch(e) { console.log('BGM unavailable'); }
}

function getBGMChordIdx(progress) {
  for (var i = bgmChordSchedule.length - 1; i >= 0; i--) {
    if (progress >= bgmChordSchedule[i][0]) return i;
  }
  return 0;
}

function startBGM() {
  if (!bgmCtx) return;
  var now = bgmCtx.currentTime;

  bgmCtx._masterGain = bgmCtx.createGain();
  bgmCtx._masterGain.gain.value = 0.25;
  bgmCtx._masterGain.connect(bgmCtx.destination);

  // 3 pad voices (saw, triangle, sine) → lowpass filter → master
  bgmPadNodes = [];
  for (var v = 0; v < 3; v++) {
    var osc = bgmCtx.createOscillator();
    var gain = bgmCtx.createGain();
    var filter = bgmCtx.createBiquadFilter();
    osc.type = v === 0 ? 'sawtooth' : v === 1 ? 'triangle' : 'sine';
    osc.frequency.value = 220;
    gain.gain.value = 0;
    filter.type = 'lowpass';
    filter.frequency.value = 800 + v * 400;
    filter.Q.value = 1;
    osc.connect(gain);
    gain.connect(filter);
    filter.connect(bgmCtx._masterGain);
    osc.start();
    bgmPadNodes.push({ osc: osc, gain: gain, filter: filter });
  }

  // Bass drone
  bgmBassNode = { osc: null, gain: null };
  bgmBassNode.osc = bgmCtx.createOscillator();
  bgmBassNode.gain = bgmCtx.createGain();
  bgmBassNode.osc.type = 'sine';
  bgmBassNode.osc.frequency.value = 110;
  bgmBassNode.gain.gain.value = 0.12;
  bgmBassNode.osc.connect(bgmBassNode.gain);
  bgmBassNode.gain.connect(bgmCtx._masterGain);
  bgmBassNode.osc.start();

  // Arpeggiator
  bgmArpNode = { osc: null, gain: null };
  bgmArpNode.osc = bgmCtx.createOscillator();
  bgmArpNode.gain = bgmCtx.createGain();
  bgmArpNode.osc.type = 'sine';
  bgmArpNode.gain.gain.value = 0;
  bgmArpNode.osc.connect(bgmArpNode.gain);
  bgmArpNode.gain.connect(bgmCtx._masterGain);
  bgmArpNode.osc.start();

  bgmCtx._lastChord = -1;
  bgmCtx._arpStep = 0;
  bgmCtx._arpTime = now;
}

function updateBGM(progress) {
  if (!bgmCtx || bgmPadNodes.length === 0) return;
  var now = bgmCtx.currentTime;

  // Chord selection
  var ci = getBGMChordIdx(progress);
  var notes = bgmChordNotes[bgmChordSchedule[ci][1]];

  // Smooth chord transition
  if (ci !== bgmCtx._lastChord) {
    bgmCtx._lastChord = ci;
    for (var i = 0; i < bgmPadNodes.length; i++) {
      var freq = i < notes.length ? notes[i] : notes[notes.length - 1];
      bgmPadNodes[i].osc.frequency.setTargetAtTime(freq, now, 0.3);
      bgmPadNodes[i].gain.gain.setTargetAtTime(0.08 - i * 0.02, now, 0.1);
      bgmPadNodes[i].filter.frequency.setTargetAtTime(
        600 + i * 500 + (progress >= 0.68 ? 400 : 0), now, 0.3);
    }
    // Bass follows root note
    if (bgmBassNode) {
      bgmBassNode.osc.frequency.setTargetAtTime(notes[0] / 2, now, 0.3);
    }
    bgmCtx._arpStep = 0;
    bgmCtx._arpTime = now;
  }

  // Arpeggiator: active during BFS (0.28-0.48) and Mobius (0.68+)
  if (bgmArpNode) {
    if ((progress >= 0.28 && progress < 0.52) || progress >= 0.68) {
      var arpPeriod = progress >= 0.68 ? 0.15 : 0.3;
      if (now - bgmCtx._arpTime > arpPeriod) {
        bgmCtx._arpTime = now;
        bgmCtx._arpStep = (bgmCtx._arpStep + 1) % (notes.length * (progress >= 0.68 ? 2 : 1));
        var ni = bgmCtx._arpStep % notes.length;
        var oct = progress >= 0.68 && bgmCtx._arpStep >= notes.length ? 2 : 1;
        bgmArpNode.osc.frequency.setValueAtTime(notes[ni] * oct, now);
        bgmArpNode.gain.gain.setValueAtTime(0.05, now);
        bgmArpNode.gain.gain.exponentialRampToValueAtTime(0.001, now + arpPeriod * 0.6);
      }
    } else {
      bgmArpNode.gain.gain.setTargetAtTime(0, now, 0.05);
    }
  }

  // Volume envelope
  var vol = 0.25;
  if (progress < 0.02) vol = 0.08;
  else if (progress >= 0.48 && progress < 0.54) vol = 0.35;
  else if (progress >= 0.90) vol = lerp(0.25, 0, (progress - 0.90) / 0.10);
  else if (progress >= 0.02 && progress < 0.04) vol = lerp(0.08, 0.25, (progress - 0.02) / 0.02);
  bgmCtx._masterGain.gain.setTargetAtTime(vol, now, 0.2);
}

// ============================================================================
// INITIALIZATION TRIGGER (called when script loads)
// ============================================================================
// Pre-compute immediately so data is ready for first frame
precomputeAll();

// Initialize BGM on load (requires user click to fully start)
setTimeout(initBGM, 100);

// ============================================================================
// INITIALIZATION TRIGGER (called when script loads)
// ============================================================================
// Pre-compute immediately so data is ready for first frame
precomputeAll();

// Initialize BGM on load (requires user click to fully start)
setTimeout(initBGM, 100);
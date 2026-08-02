# -*- coding: utf-8 -*-
import os, shutil

# Write to a temp ASCII-named file first
tmp = r'D:\code\MyWord\_temp_moat.html'
final_src = r'D:\code\MyWord\小红书笔记\AI时代护城河_完整精读版.html'
final_dst_desk = os.path.expanduser('~') + '\Desktop\AI时代护城河_完整精读版.html'

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Microsoft YaHei,PingFang SC,sans-serif;background:#faf8f5;color:#2d2926;line-height:2;font-size:16px}
.wrap{max-width:860px;margin:0 auto;padding:40px 24px 80px}
.hero{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);border-radius:28px;padding:64px 56px;margin-bottom:48px;color:#fff;text-align:center;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(ellipse at center,rgba(255,107,107,0.08) 0%,transparent 70%);pointer-events:none}
.hero .source{font-size:12px;letter-spacing:3px;color:rgba(255,255,255,0.5);text-transform:uppercase;margin-bottom:20px}
.hero h1{font-size:46px;font-weight:800;line-height:1.15;margin-bottom:20px;background:linear-gradient(135deg,#ff6b6b,#ffa07a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px}
.hero .subtitle{font-size:18px;color:rgba(255,255,255,0.75);margin-bottom:32px;line-height:1.6}
.hero .meta{display:flex;justify-content:center;gap:32px;flex-wrap:wrap;margin-top:8px}
.hero .meta span{font-size:13px;color:rgba(255,255,255,0.45)}
.hero .meta strong{color:#ffa07a;font-weight:600}
.tags{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:28px}
.tag{background:rgba(255,107,107,0.15);border:1px solid rgba(255,107,107,0.3);color:#ff8c8c;border-radius:20px;padding:5px 16px;font-size:12px}
.section{background:#fff;border-radius:24px;padding:40px 48px;margin-bottom:28px;box-shadow:0 1px 3px rgba(0,0,0,0.04),0 4px 16px rgba(0,0,0,0.03)}
h2{font-size:24px;font-weight:700;color:#1a1a2e;margin-bottom:28px;padding-bottom:16px;border-bottom:2px solid #f0ebe5}
h2 .num{color:#ff6b6b;font-size:14px;font-weight:600;margin-right:10px}
h3{font-size:18px;font-weight:700;color:#2d2926;margin:28px 0 16px}
h4{font-size:15px;font-weight:600;color:#444;margin:20px 0 12px}
p{color:#555;margin-bottom:16px;font-size:15px;line-height:1.9}
.lead{font-size:17px;color:#333;line-height:2;margin-bottom:24px}
.lead strong{color:#ff6b6b}
.quote{background:linear-gradient(135deg,#fff8f7,#fff5f2);border-left:5px solid #ff6b6b;padding:28px 32px;margin:28px 0;border-radius:0 20px 20px 0;font-size:18px;font-weight:600;color:#2d2926;line-height:1.8}
.quote-author{font-size:13px;color:#999;font-weight:400;margin-top:12px;font-style:normal}
.key-point{background:#fff;border:1px solid #f0e8e3;border-radius:18px;padding:24px 28px;margin:16px 0}
.key-point h4{font-size:15px;font-weight:700;color:#ff6b6b;margin:0 0 10px}
.key-point p{font-size:14px;color:#666;margin:0;line-height:1.8}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:24px 0}
.card{background:#faf9f7;border:1px solid #ede8e0;border-radius:20px;padding:28px;text-align:center;transition:transform 0.2s}
.card:hover{transform:translateY(-3px)}
.card .icon{font-size:36px;margin-bottom:14px}
.card h4{font-size:16px;font-weight:700;color:#1a1a2e;margin:0 0 10px}
.card p{font-size:13px;color:#777;margin:0;line-height:1.7}
.cards5{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:24px 0}
.card5{background:#fff;border:1px solid #ede8e0;border-radius:16px;padding:20px;text-align:center}
.card5 .num{font-size:32px;font-weight:800;color:#ff6b6b;margin-bottom:6px}
.card5 .label{font-size:13px;font-weight:600;color:#333;margin-bottom:4px}
.card5 .sub{font-size:11px;color:#999}
.step-item{display:flex;gap:24px;padding:24px 0;border-bottom:1px solid #f5f0eb}
.step-item:last-child{border-bottom:none}
.step-num{width:44px;height:44px;background:linear-gradient(135deg,#ff6b6b,#ffa07a);border-radius:50%;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px}
.step-body h4{font-size:16px;font-weight:700;color:#1a1a2e;margin:0 0 8px}
.step-body p{font-size:14px;color:#777;margin:0;line-height:1.8}
.tbl{width:100%;border-collapse:collapse;font-size:14px;margin:16px 0}
.tbl th{background:#1a1a2e;color:#fff;font-weight:600;text-align:left;padding:14px 20px;font-size:13px;letter-spacing:0.5px}
.tbl td{padding:14px 20px;border-bottom:1px solid #f0ebe5;vertical-align:top;color:#555}
.tbl .维度{font-weight:700;color:#1a1a2e;white-space:nowrap}
.tbl .新时代{background:#fff5f3;color:#ff6b6b;font-weight:600}
.highlight-box{background:linear-gradient(135deg,#fff5f3,#fff);border:2px solid #ff6b6b;border-radius:20px;padding:32px;margin:28px 0}
.highlight-box h3{font-size:18px;font-weight:700;color:#ff6b6b;margin:0 0 16px}
.highlight-box p{font-size:15px;color:#555;margin:0;line-height:1.9}
.warning-box{background:#fffbe6;border:1px solid #ffe066;border-radius:16px;padding:24px;margin:20px 0}
.warning-box h4{font-size:14px;font-weight:700;color:#b8860b;margin:0 0 10px}
.warning-box p{font-size:13px;color:#888;margin:0}
.info-box{background:#f0f7ff;border:1px solid #cce0ff;border-radius:16px;padding:24px;margin:20px 0}
.info-box h4{font-size:14px;font-weight:700;color:#2d5fc8;margin:0 0 10px}
.info-box p{font-size:13px;color:#666;margin:0}
.金句{background:#fff;border:2px solid #ff6b6b;border-radius:16px;padding:24px;margin:20px 0;font-size:16px;font-weight:600;color:#333;text-align:center;line-height:1.8}
.总结大框{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;border-radius:24px;padding:48px;text-align:center}
.总结大框 h2{color:#fff;border:none;padding:0;margin-bottom:24px;font-size:28px}
.总结大框 p{color:rgba(255,255,255,0.8);font-size:16px;line-height:2;margin:0 auto;max-width:600px}
.footer{text-align:center;padding:40px;color:#bbb;font-size:13px;line-height:2}
.flex-row{display:flex;gap:20px;align-items:flex-start;margin:20px 0}
.flex-row .item{flex:1;background:#fff;border:1px solid #ede8e0;border-radius:16px;padding:24px}
.flex-row .item h4{font-size:14px;font-weight:700;color:#1a1a2e;margin:0 0 10px}
.flex-row .item p{font-size:13px;color:#777;margin:0;line-height:1.7}
.四宫格{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}
.quad{background:#fff;border:1px solid #ede8e0;border-radius:18px;padding:24px}
.quad h4{font-size:14px;font-weight:700;color:#1a1a2e;margin:0 0 10px}
.quad p{font-size:13px;color:#666;margin:0;line-height:1.7}
@media(max-width:700px){
.cards3,.cards5,.四宫格,.flex-row{display:block}
.cards3 .card,.cards5>div,.四宫格 .quad,.flex-row .item{margin-bottom:12px}
.step-item{gap:16px}
.hero{padding:40px 24px}
.hero h1{font-size:32px}
.section{padding:28px 24px}
}
"""

body = """
<div class="wrap">
<div class="hero">
<div class="source">NFX Research &nbsp;|&nbsp; 原版深度解读</div>
<h1>AI时代最宽的护城河</h1>
<p class="subtitle">不是技术，不是产品，不是数据<br>是组织形态——一家公司如何吸引人才、如何集中判断力、如何分配权力</p>
<div class="meta">
<span>作者 <strong>James Currier</strong></span>
<span>来源 <strong>NFX</strong></span>
<span>领域 <strong>VC / 创业投资</strong></span>
<span>整理 <strong>QClaw AI</strong></span>
</div>
<div class="tags">
<span class="tag">AI时代</span><span class="tag">护城河</span><span class="tag">组织能力</span>
<span class="tag">超级个体</span><span class="tag">超级团队</span><span class="tag">人才密度</span>
<span class="tag">判断力集中</span><span class="tag">战略管理</span>
</div>
</div>

<div class="section">
<h2><span class="num">00</span>开篇：一个反直觉的命题</h2>
<p class="lead">很多人以为，AI时代最宽的护城河是<strong>数据</strong>、是<strong>算法</strong>、是<strong>技术</strong>。但真正穿越过多个技术周期的投资人知道，这些都不是。</p>
<p>NFX 合伙人 James Currier 在这篇文章中给出了一个让很多人没想到的答案：</p>
<div class="quote">AI时代最宽的护城河，是<strong>组织形态</strong>。<span class="quote-author">—— James Currier, NFX</span></div>
<p>这个结论来自一个简单但深刻的观察：当技术变得民主化（每个人都能用API调用同样的模型），<strong>唯一不能被复制的是组织的独特性</strong>。技术可以被买走，人才可以被挖走，数据可以被爬取——但一个组织通过多年沉淀形成的做事方式、决策风格、文化惯性，无法在短期内被复制。</p>
<p>这就是护城河的本质：不是你知道什么，而是你是什么，以及你能做什么别人做不到的事。</p>
</div>

<div class="section">
<h2><span class="num">01</span>为什么传统护城河在AI时代正在被削弱？</h2>
<p class="lead">在进入组织形态之前，我们需要先理解为什么旧的那套护城河正在失效。</p>
<div class="cards3">
<div class="card"><div class="icon">🔢</div><h4>数据壁垒瓦解</h4><p>AI让数据更容易被采集、分析、合成。OpenAI、Anthropic、DeepSeek的模型可以用公开数据训练出接近专有数据效果的模型。数据作为护城河的价值正在快速蒸发。</p></div>
<div class="card"><div class="icon">⚙️</div><h4>算法开源化</h4><p>Meta开源LLaMA、Google开源Gemma、DeepSeek开源V4。算法壁垒在12-18个月内几乎必然被追平。这是技术进步规律，不是例外。</p></div>
<div class="card"><div class="icon">💰</div><h4>资本不再稀缺</h4><p>AI基础设施成本下降，云计算按需付费，GPU不再是稀缺资源。钱能买到的东西，无法成为长期壁垒。</p></div>
</div>
<div class="warning-box">
<h4>⚠️ 重要提醒</h4>
<p>不是说数据、技术、资本不再重要——它们仍然是入场券。但它们不再能形成<strong>长期的、难以复制</strong>的竞争优势。当所有人都能拿到同样的工具，差异化就转向了"谁用得更好"——而这本质上是组织问题。</p>
</div>
</div>

<div class="section">
<h2><span class="num">02</span>AI时代的新护城河框架</h2>
<p>James Currier 提出，AI时代的护城河有五个层次，从易到难排列：</p>
<div class="cards5">
<div class="card5"><div class="num">1</div><div class="label">技术壁垒</div><div class="sub">会被开源追平</div></div>
<div class="card5"><div class="num">2</div><div class="label">数据壁垒</div><div class="sub">正在被合成数据瓦解</div></div>
<div class="card5"><div class="num">3</div><div class="label">产品壁垒</div><div class="sub">可以被copy</div></div>
<div class="card5"><div class="num">4</div><div class="label">分发壁垒</div><div class="sub">网络效应最强</div></div>
<div class="card5"><div class="num">5</div><div class="label">组织壁垒</div><div class="sub">最难被复制 ★</div></div>
</div>
<div class="quote">"如果移动互联网时代的最强护城河是网络效应，那么AI时代的最强护城河是组织能力。"<span class="quote-author">—— James Currier</span></div>
</div>

<div class="section">
<h2><span class="num">03</span>组织护城河的三要素</h2>
<p class="lead">什么是"组织形态"？James Currier 用三个维度来定义它：</p>

<div class="key-point">
<h4>要素一：吸引杰出人才的能力</h4>
<p>AI时代最稀缺的资源是什么？不是GPU，是<strong>既懂AI又懂业务</strong>的复合型人才。这类人极其稀有，他们的判断力可以直接决定一个产品、一个公司、甚至一个市场的走向。</p>
</div>
<div class="flex-row">
<div class="item"><h4>为什么人才是最宽的护城河？</h4><p>优秀的人才会吸引更多优秀的人（A-player吸引A-player）。他们自带网络效应，而且这种效应是自我强化、不可逆的——一旦形成，很难被打破。</p></div>
<div class="item"><h4>什么样的人才最难找？</h4><p>既会训练模型、又会定义产品、还能和客户对话的"T型人才"。这种人在全球范围内屈指可数，而且他们的选择极多，不会被困在一个组织里。</p></div>
</div>

<div class="key-point">
<h4>要素二：集中判断力（Centralize Judgment）</h4>
<p>这里的"集中"不是传统意义上的"中央集权"或"老板一言堂"，而是<strong>战略级判断的集中</strong>。在一个充满不确定性的AI时代，哪些方向值得投入、哪些市场值得进入、哪些技术路线值得押注——这些决策的质量直接决定公司的命运。</p>
</div>
<div class="flex-row">
<div class="item"><h4>好的集中判断</h4><p>CEO和核心团队花80%的时间思考战略方向，确保每一个大方向的选择是经过深度推演的。这是"高质量的集中"。</p></div>
<div class="item"><h4>坏的集中判断</h4><p>老板审批所有费用、签字所有决定、决定每个人用什么工具。这是"低质量的集中"——它只会让组织僵化。</p></div>
</div>

<div class="key-point">
<h4>要素三：分配权力（Distribute Authority）</h4>
<p>在战略方向被集中判断之后，执行权必须充分下放。一线的人离客户最近、离问题最近，他们应该拥有足够的决策权来快速响应市场变化。</p>
</div>

<div class="highlight-box">
<h3>三要素的动态关系</h3>
<p>吸引人才 → 让组织拥有更多高质量的判断力来源<br>集中判断力 → 让关键决策由最有可能做对的人来做<br>分配权力 → 让一线的人能够快速行动，不被流程拖慢</p>
<p style="margin-top:12px"><strong>三者缺一不可：</strong>只吸引人才但不让其发挥，等于没有；只集中判断但不授权，等于僵化；只授权不集中判断，等于混乱。</p>
</div>
</div>

<div class="section">
<h2><span class="num">04</span>连接点：从超级个体到超级团队</h2>
<p class="lead">这篇文章的核心洞察，和我们正在推进的「从超级个体到超级团队」项目高度相关。</p>
<div class="quote">超级个体 = 少数有AI判断力的人<br>超级团队 = 能放大超级个体能力的组织架构<br><strong>AI不是护城河本身，用AI的组织能力才是护城河。</strong></div>

<h3>什么是"超级个体"？</h3>
<p>超级个体不是"全能的人"，而是"有AI放大的特定能力"的人。他们可能是：一个能用AI同时做产品、运营、代码三件事的产品经理；一个能把10年行业经验转化为AI辅助决策的销售；一个能借助AI工具独立完成以前需要整个团队才能完成的架构师。</p>
<p>超级个体的核心特征：<strong>判断力强 + AI工具熟练 + 执行效率高</strong>。他们不是更好的工具，而是用AI重新定义了"一个人能做的事的边界"。</p>

<h3>什么是"超级团队"？</h3>
<p>超级团队不是"人多"，而是"能把超级个体的能力放大"的结构。它的核心是：让一群超级个体在正确的组织结构下工作，让1+1远远大于2。</p>
<div class="cards3">
<div class="card"><div class="icon">🔗</div><h4>能力互补而非重叠</h4><p>每个成员带来不同维度的判断力，形成覆盖完整的能力矩阵</p></div>
<div class="card"><div class="icon">⚡</div><h4>决策链路短</h4><p>一线的人有决策权，不需要层层汇报，响应速度接近市场变化的速度</p></div>
<div class="card"><div class="icon">🔄</div><h4>反馈闭环快</h4><p>每个项目的复盘经验被自动沉淀为组织记忆，团队持续进化</p></div>
</div>

<h3>从超级个体到超级团队的四个步骤</h3>
<div class="step-item"><div class="step-num">1</div><div class="step-body"><h4>换招聘逻辑</h4><p>以前招"能干活的人"，现在招"能判断的人"。技能可以教，判断力教不了。这个转变是整个路径的起点。</p></div></div>
<div class="step-item"><div class="step-num">2</div><div class="step-body"><h4>重新设计决策流</h4><p>不要等上级批准才能行动。让听到炮声的人做决定。决策链条从5层压到2层，让授权真正落地。</p></div></div>
<div class="step-item"><div class="step-num">3</div><div class="step-body"><h4>统一AI工具链</h4><p>全团队用同一套工具链，能力下沉。避免某个人成了"AI依赖症"而其他人完全无法参与的撕裂。</p></div></div>
<div class="step-item"><div class="step-num">4</div><div class="step-body"><h4>建立反馈闭环</h4><p>每个项目的复盘要自动化，经验要数字化。让团队在"事上练"而不是在"汇报上耗"，在实战中积累组织记忆。</p></div></div>

<div class="金句">超级个体决定团队的天花板<br>超级团队决定个体能走多远<br>两者不是替代关系，是乘积关系</div>
</div>

<div class="section">
<h2><span class="num">05</span>时代对比：移动互联网时代 vs AI时代</h2>
<p class="lead">理解AI时代护城河的本质，需要把它和上一个时代做个对比。</p>
<table class="tbl">
<tr><th class="维度">维度</th><th>移动互联网时代</th><th class="新时代">AI时代</th></tr>
<tr><td class="维度">护城河形态</td><td>技术 / 产品 / 品牌 / 叙事能力</td><td class="新时代">组织能力 / 文化 / 人才密度</td></tr>
<tr><td class="维度">核心资源</td><td>数据 / 用户量 / 资本</td><td class="新时代">人才密度 / 判断力集中度 / AI应用能力</td></tr>
<tr><td class="维度">决策模式</td><td>层级制 / 长汇报链 / 审批文化</td><td class="新时代">集中判断 + 分布式执行 / 短链路决策</td></tr>
<tr><td class="维度">复制难度</td><td>中等（钱能买技术/挖人）</td><td class="新时代">极难（组织文化无法被短期复制）</td></tr>
<tr><td class="维度">护城河有效期</td><td>3-5年</td><td class="新时代">更长（组织能力建立需要的时间远长于技术追赶）</td></tr>
<tr><td class="维度">增长曲线</td><td>线性增长（人多力量大）</td><td class="新时代">指数增长（AI×组织产生复利效应）</td></tr>
<tr><td class="维度">决策者角色</td><td>资源分配者 / 审批者</td><td class="新时代">战略判断者 + 赋能者</td></tr>
<tr><td class="维度">核心竞争力</td><td>执行速度 / 产品迭代</td><td class="新时代">判断质量 + 适应速度</td></tr>
</table>
<div class="info-box">
<h4>💡 关键观察</h4>
<p>移动互联网时代的竞争核心是"执行速度"——谁能更快地推出产品、获取用户、复制对手的模式。AI时代的竞争核心是"判断质量"——在正确的时间做正确的事，这要求组织有更深度的思考能力和更快的适应能力。</p>
</div>
</div>

<div class="section">
<h2><span class="num">06</span>复利系统：为什么组织能力是最深的护城河？</h2>
<p class="lead">这篇文章最核心的一个隐喻是：好的组织能把工作变成<strong>复利系统</strong>。</p>
<p>什么是复利系统？简单说就是：你做的每一件事，不仅在当下产生价值，还在为未来积累更多产生价值的能力。这就是复利的本质——产出不只是线性增长，而是会自我加速。</p>

<div class="四宫格">
<div class="quad"><h4>技术复利</h4><p>用AI写代码 → 代码质量提升 → 开发速度加快 → 有更多时间用AI → 循环强化</p></div>
<div class="quad"><h4>经验复利</h4><p>每个项目的复盘 → 经验数字化 → 新人能快速上手 → 组织整体能力提升 → 循环</p></div>
<div class="quad"><h4>人才复利</h4><p>吸引顶级人才 → 环境变好 → 吸引更多顶级人才 → 能力密度指数上升 → 循环</p></div>
<div class="quad"><h4>文化复利</h4><p>正确的决策文化 → 更多正确决策 → 文化被强化 → 做决策越来越准 → 循环</p></div>
</div>

<div class="quote">"一家公司如何让工作变成复利系统？答案是：通过正确的组织结构，让每一次成功的判断都在为下一次更好的判断积累素材。"<span class="quote-author">—— James Currier</span></div>
<p>这就是为什么组织能力是最深的护城河。技术可以被复制，产品可以被抄袭，但一个组织在多年实战中积累的"判断质量循环"是无法被购买的。每一次成功或失败的决策都在强化这个循环，让组织的判断力像滚雪球一样越滚越大。</p>
</div>

<div class="section">
<h2><span class="num">07</span>实践框架：如何在组织中建立这三要素</h2>

<h3>一、建立吸引人才的能力</h3>
<div class="flex-row">
<div class="item"><h4>让人才做有意义的事</h4><p>顶级人才不在乎钱，在乎"这件事值不值得做"。给他们足够难的问题和足够的自主权。</p></div>
<div class="item"><h4>创造A吸引A的环境</h4><p>一旦有了一个A-player，下一步是确保他能帮助你吸引下一个A-player。内推奖励、文化塑造、快速晋升通道。</p></div>
</div>

<h3>二、建立集中判断力的机制</h3>
<div class="flex-row">
<div class="item"><h4>战略日/战略周</h4><p>核心团队定期（比如每季度）花整块时间讨论最重要的战略判断。形式不重要，关键是形成规律。</p></div>
<div class="item"><h4>决策质量复盘</h4><p>不只是复盘结果，也要复盘决策过程——当时的假设是什么？判断依据是什么？有什么信息我们没考虑到？</p></div>
</div>

<h3>三、建立分配权力的文化</h3>
<div class="flex-row">
<div class="item"><h4>最小化审批层级</h4><p>如果一个决定可以由2个人做，就不要让它经过5个人。让决策者在自己的层级承担完整的责任。</p></div>
<div class="item"><h4>容错机制</h4><p>授权的代价是错误。关键是要有快速纠正的机制，而不是通过收回权力来"防止错误"。</p></div>
</div>

<div class="info-box">
<h4>📌 三要素的检查清单</h4>
<p>你现在的组织：<br>
• 能持续吸引比你当前水平更高的人才吗？<br>
• 最重要的战略判断是由最有判断力的人做出的吗？<br>
• 一线员工有没有足够的权力快速响应客户需求？<br>
如果以上任何一个答案是"不太确定"，这就是你需要重点改进的方向。</p>
</div>
</div>

<div class="section">
<h2><span class="num">08</span>关于组织护城河的常见误解</h2>

<h4>误解一：组织护城河 = 大公司</h4>
<p>不是的。组织护城河和规模无关——一个10人的团队如果建立了正确的判断力集中+授权机制，它的组织护城河可能比一个1000人但决策链条冗长的公司要强得多。关键在于组织形态的质量，而不是人数。</p>

<h4>误解二：集中判断 = 老板说了算</h4>
<p>不是的。James Currier 强调的"集中判断力"是指把关键战略决策权交给最有判断力的人，而不是交给"最高职位的人"。在一些正确的组织里，最有判断力的人可能并不是CEO。</p>

<h4>误解三：分配权力 = 放任不管</h4>
<p>不是的。授权的前提是有清晰的战略方向和明确的决策原则。没有判断力基础的授权是混乱，不是敏捷。</p>

<h4>误解四：AI会替代组织</h4>
<p>不是的。AI是放大器——它放大好的组织能力，也放大坏的组织能力。一个决策质量低的组织引入AI只会让错误发生得更快。AI时代最需要的不是更多的AI，而是更好的组织。</p>
</div>

<div class="总结大框">
<h2>最终结论</h2>
<p>技术不是护城河。<br>用技术的<strong>组织能力</strong>，才是护城河。</p>
<p style="margin-top:24px">AI时代，最强的个体，会被组织形态<strong>放大或削弱</strong>。<br>强的组织 = <strong>吸引人才</strong> + <strong>集中判断</strong> + <strong>分配权力</strong><br>这个框架你认同吗？</p>
</div>

<div class="footer">
内容来源：《The Next Biggest Moat in AI》by James Currier @ NFX<br>
整理：QClaw AI &nbsp;|&nbsp; 2026-05-18<br>
相关文章：《从超级个体到超级团队》报告
</div>
</div>
"""

html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>AI时代最宽的护城河：完整精读版</title>\n<style>' + CSS + '</style>\n</head>\n<body>\n' + body + '\n</body>\n</html>'

with open(tmp, 'w', encoding='utf-8') as f:
    f.write(html)

sz = os.path.getsize(tmp)
print(f'Written {sz} bytes to temp file')

# Copy to final destinations
shutil.copy2(tmp, final_src)
shutil.copy2(tmp, final_dst_desk)
print(f'Saved to:')
print(f'  {final_src}')
print(f'  {final_dst_desk}')
print(f'Size: {sz} bytes')
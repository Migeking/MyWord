#!/usr/bin/env python3
"""Regenerate index.html cleanly from timing.json"""
import json

with open('timing.json', 'r', encoding='utf-8') as f:
    timings = json.load(f)

# Calculate timings with 0.5s gap between slides
slides = []
cum_audio = 0.0
prev_slide_end = 0.0

for i, t in enumerate(timings):
    num = t['slide']
    audio_dur = t['duration']
    audio_file = t['file']

    if i == 0:
        slide_start = 0.0
        audio_start = 0.3
    else:
        slide_start = round(prev_slide_end, 1)
        audio_start = round(cum_audio + 0.3, 1)

    slide_dur = round(audio_dur + 0.5, 1)  # 0.5s gap after audio ends

    slides.append({
        'num': num, 'audio_dur': audio_dur, 'audio_file': audio_file,
        'slide_start': slide_start, 'slide_dur': slide_dur, 'audio_start': audio_start
    })

    cum_audio += audio_dur
    prev_slide_end = slide_start + slide_dur

total_dur = slides[-1]['slide_start'] + slides[-1]['slide_dur']
bgm_dur = round(total_dur) + 2

# ============================================================
CSS = r"""    * { margin: 0; padding: 0; box-sizing: border-box; }

    html, body {
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
      color: #ffffff;
    }

    .clip { position: absolute; opacity: 0; will-change: transform, opacity; }

    .slide {
      position: absolute; top: 0; left: 0;
      width: 1080px; height: 1920px;
      display: flex; flex-direction: column;
      justify-content: center; align-items: center; padding: 80px;
    }

    .bg-hero { background: linear-gradient(135deg, #0a0e17 0%, #1a1a2e 40%, #16213e 100%); }
    .bg-1 { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a3e 100%); }
    .bg-2 { background: linear-gradient(135deg, #0a0e17 0%, #2d1b69 100%); }
    .bg-3 { background: linear-gradient(180deg, #1a1a2e 0%, #0f3460 100%); }
    .bg-4 { background: linear-gradient(135deg, #16213e 0%, #0a0e17 100%); }
    .bg-dark { background: #0a0a0f; }
    .bg-conclusion { background: linear-gradient(180deg, #1a1a2e 0%, #0a0e17 100%); }

    .title-main { font-size: 88px; font-weight: 900; line-height: 1.2; text-align: center; letter-spacing: -1px; }
    .title-gradient { background: linear-gradient(135deg, #ff6b35, #ff8c5a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .subtitle { font-size: 34px; color: rgba(255,255,255,0.7); text-align: center; margin-top: 36px; line-height: 1.6; max-width: 850px; }
    .section-title { font-size: 56px; font-weight: 800; text-align: center; margin-bottom: 12px; }
    .highlight { color: #ff6b35; }
    .accent-orange { color: #ff8c5a; font-weight: 700; }
    .accent-line { width: 60px; height: 4px; background: #ff6b35; border-radius: 2px; margin: 16px auto 32px; }
    .body-text { font-size: 32px; text-align: center; line-height: 1.6; max-width: 900px; }
    .quote-text { font-size: 32px; text-align: center; line-height: 1.5; color: rgba(255,255,255,0.85); max-width: 850px; }
    .small-quote { font-size: 24px; text-align: center; color: rgba(255,255,255,0.5); max-width: 800px; line-height: 1.5; }
    .formula-text { font-size: 48px; font-weight: 800; text-align: center; color: #ff6b35; }
    .tag-container { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-top: 32px; }
    .tag { padding: 8px 24px; background: rgba(255,107,53,0.15); border: 1px solid rgba(255,107,53,0.3); border-radius: 20px; font-size: 20px; color: #ff8c5a; }
    .meta-info { font-size: 18px; text-align: center; color: rgba(255,255,255,0.3); margin-top: 48px; }

    .cards-row { display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; max-width: 960px; }
    .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px 20px; width: 280px; text-align: center; }
    .card-icon { font-size: 40px; margin-bottom: 8px; }
    .card-num { font-size: 28px; font-weight: 800; color: #ff6b35; margin-bottom: 8px; }
    .card-title { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
    .card-text { font-size: 20px; color: rgba(255,255,255,0.6); line-height: 1.4; }

    .grid-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 900px; }
    .grid-item { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; text-align: center; }
    .grid-item-title { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
    .grid-item-text { font-size: 18px; color: rgba(255,255,255,0.6); line-height: 1.4; }

    .steps { display: flex; flex-direction: column; gap: 16px; width: 100%; max-width: 860px; }
    .step { display: flex; align-items: flex-start; gap: 16px; }
    .step-num { width: 40px; height: 40px; border-radius: 50%; background: #ff6b35; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; flex-shrink: 0; }
    .step-content { flex: 1; }
    .step-title { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
    .step-text { font-size: 20px; color: rgba(255,255,255,0.6); line-height: 1.4; }

    .conclusion-box { background: rgba(255,107,53,0.08); border: 2px solid rgba(255,107,53,0.2); border-radius: 20px; padding: 32px 48px; text-align: center; min-width: 500px; }
    .conclusion-main { font-size: 48px; font-weight: 800; }"""

# ============================================================
SCRIPTS_CONTENT = """  <script>
  document.addEventListener("DOMContentLoaded", () => {
    const clips = document.querySelectorAll(".clip");
    const tl = gsap.timeline({ paused: true });

    clips.forEach(clip => {
      const start = parseFloat(clip.dataset.start) || 0;
      const duration = parseFloat(clip.dataset.duration) || 0;
      if (duration <= 0) return;

      tl.to(clip, { opacity: 1, duration: 0.4, ease: "power2.in" }, start);
      tl.to(clip, { opacity: 0, duration: 0.4, ease: "power2.out" }, start + duration - 0.4);
    });

    const audioClips = document.querySelectorAll("audio.clip");
    audioClips.forEach(audio => {
      const start = parseFloat(audio.dataset.start) || 0;
      tl.call(() => {
        audio.currentTime = 0;
        audio.play().catch(e => console.warn("Audio play failed:", e));
      }, [], start);
    });

    tl.play();
  });
  </script>"""

# ============================================================
SLIDE_HTML = {
1: """    <!-- ====== SLIDE 1: Title ====== -->
    <div id="slide-1" class="clip slide bg-hero" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="title-main title-gradient">AI时代</div>
      <div class="title-main">最宽的护城河</div>
      <div class="subtitle">不是技术，不是产品<br>是<span style="color:#ff6b35;font-weight:700">组织形态</span></div>
      <div class="tag-container"><span class="tag">组织能力</span><span class="tag">人才密度</span><span class="tag">判断力</span><span class="tag">权力分配</span></div>
      <div class="meta-info">基于 NFX · James Currier 的研究</div>
    </div>
    <audio id="audio-1" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

2: """    <!-- ====== SLIDE 2: Hook ====== -->
    <div id="slide-2" class="clip slide bg-1" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">反直觉的<span class="highlight">命题</span></div>
      <div class="accent-line"></div>
      <div class="quote-text">很多人以为AI时代最宽的护城河<br>是数据、是算法、是技术……</div>
      <div class="small-quote" style="margin-top:32px">但纽曼在《The Next Biggest Moat in AI》里说：</div>
      <div class="formula-text" style="font-size:40px;margin-top:24px">「组织形态」</div>
      <div class="body-text" style="font-size:28px">才是真正的护城河</div>
    </div>
    <audio id="audio-2" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

3: """    <!-- ====== SLIDE 3: 要素1 ====== -->
    <div id="slide-3" class="clip slide bg-2" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">要素一：<span class="highlight">吸引杰出人才</span></div>
      <div class="accent-line"></div>
      <div class="body-text" style="margin-bottom:40px">AI时代最稀缺的资源，不是算法，<br>而是<span class="accent-orange">既懂AI又懂业务</span>的人</div>
      <div class="cards-row">
        <div class="card"><div class="card-num">❶</div><div class="card-title">识别人才</div><div class="card-text">找到跨领域复合型人才</div></div>
        <div class="card"><div class="card-num">❷</div><div class="card-title">吸引人才</div><div class="card-text">A-player吸引A-player<br>自我强化网络效应</div></div>
        <div class="card"><div class="card-num">❸</div><div class="card-title">留住人才</div><div class="card-text">给足够的空间和决策权</div></div>
      </div>
      <div class="small-quote" style="margin-top:20px;font-size:24px">能持续吸引这类人才的组织，才有可能在AI时代胜出</div>
    </div>
    <audio id="audio-3" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

4: """    <!-- ====== SLIDE 4: 要素2 ====== -->
    <div id="slide-4" class="clip slide bg-3" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">要素二：<span class="highlight">集中判断力</span></div>
      <div class="accent-line"></div>
      <div class="body-text" style="margin-bottom:32px">关键决策要集中在<br><span class="accent-orange">少数真正有洞察力</span>的人手里</div>
      <div class="grid-2x2">
        <div class="grid-item"><div class="grid-item-title">✅ 集中判断</div><div class="grid-item-text">战略方向不跑偏<br>重大决策不犯错</div></div>
        <div class="grid-item"><div class="grid-item-title">❌ 不是中央集权</div><div class="grid-item-text">只在战略层面收权<br>执行层面充分放权</div></div>
        <div class="grid-item"><div class="grid-item-title">🎯 目标对齐</div><div class="grid-item-text">所有人知道方向<br>但怎么做自己决定</div></div>
        <div class="grid-item"><div class="grid-item-title">📈 效率提升</div><div class="grid-item-text">决策链条缩短<br>市场响应速度翻倍</div></div>
      </div>
    </div>
    <audio id="audio-4" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

5: """    <!-- ====== SLIDE 5: 要素3 ====== -->
    <div id="slide-5" class="clip slide bg-4" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">要素三：<span class="highlight">分配权力</span></div>
      <div class="accent-line"></div>
      <div class="body-text" style="margin-bottom:32px">在判断力集中的基础上<br><span class="accent-orange">把执行权充分下放</span></div>
      <div class="cards-row">
        <div class="card"><div class="card-icon">⚡</div><div class="card-title">一线决策</div><div class="card-text">让听得见炮火的人做决定</div></div>
        <div class="card"><div class="card-icon">🔄</div><div class="card-title">快速响应</div><div class="card-text">从5层审批缩到2层<br>速度就是竞争力</div></div>
        <div class="card"><div class="card-icon">🌱</div><div class="card-title">人才成长</div><div class="card-text">在实战中锻炼判断力<br>人才密度指数上升</div></div>
      </div>
    </div>
    <audio id="audio-5" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

6: """    <!-- ====== SLIDE 6: 实践 ====== -->
    <div id="slide-6" class="clip slide bg-hero" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">从<span class="highlight">超级个体</span>到<span class="highlight">超级团队</span></div>
      <div class="accent-line"></div>
      <div class="body-text" style="font-size:28px;margin-bottom:20px">见过太多「AI工具很强，团队跟不上」的情况<br>我们在推一个内部项目，核心四步：</div>
      <div class="steps">
        <div class="step"><div class="step-num">1</div><div class="step-content"><div class="step-title">换招聘逻辑</div><div class="step-text">招"能判断的人"而不是"能干活的人"</div></div></div>
        <div class="step"><div class="step-num">2</div><div class="step-content"><div class="step-title">重新设计决策流</div><div class="step-text">听到炮声的人做决定，决策层从5压到2</div></div></div>
        <div class="step"><div class="step-num">3</div><div class="step-content"><div class="step-title">统一AI工具</div><div class="step-text">全团队同一套工具链，能力下沉到每个人</div></div></div>
        <div class="step"><div class="step-num">4</div><div class="step-content"><div class="step-title">建立反馈闭环</div><div class="step-text">复盘自动化，经验数字化，在事上练</div></div></div>
      </div>
    </div>
    <audio id="audio-6" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

7: """    <!-- ====== SLIDE 7: 核心观点 ====== -->
    <div id="slide-7" class="clip slide bg-dark" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">核心<span class="highlight">观点</span></div>
      <div class="accent-line"></div>
      <div class="quote-text" style="margin-bottom:24px">技术<span style="color:rgba(255,255,255,0.4)">不是</span>护城河</div>
      <div class="formula-text" style="font-size:48px;margin-bottom:24px">用技术的组织能力</div>
      <div class="body-text" style="font-size:28px">才是真正的护城河</div>
      <div class="tag-container"><span class="tag">无法靠买</span><span class="tag">只能靠建</span><span class="tag">一旦建成很难复制</span></div>
    </div>
    <audio id="audio-7" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",

8: """    <!-- ====== SLIDE 8: 总结 ====== -->
    <div id="slide-8" class="clip slide bg-conclusion" data-start="{ss}" data-duration="{sd}" data-track-index="1">
      <div class="section-title">总结</div>
      <div class="accent-line"></div>
      <div class="conclusion-box">
        <div class="conclusion-main"><span style="color:#ff6b35">吸引人才</span> + <span style="color:#ff8c5a">集中判断</span> + <span style="color:#ff6b35">分配权力</span></div>
        <div class="quote-text" style="font-size:36px;margin-top:16px">= <span style="color:#ff6b35;font-weight:900">强组织</span></div>
      </div>
      <div class="body-text" style="margin-top:48px;font-size:30px">AI时代，最强的个体<br>会被组织形态<span class="accent-orange">放大或削弱</span></div>
      <div class="small-quote" style="margin-top:32px;font-size:24px">你认同这个框架吗？欢迎分享你的看法</div>
      <div class="meta-info" style="margin-top:20px">#AI时代 #组织能力 #护城河 #超级个体 #超级团队</div>
    </div>
    <audio id="audio-8" class="clip" data-start="{astart}" data-duration="{adur}" data-track-index="2" src="{afile}"></audio>""",
}

# ============================================================
lines = [
    '<!DOCTYPE html>',
    '<html lang="zh-CN" data-composition-id="main" data-width="1080" data-height="1920">',
    '<head>',
    '  <meta charset="UTF-8">',
    '  <meta name="viewport" content="width=1080, height=1920, initial-scale=1.0">',
    '  <title>AI时代最宽的护城河</title>',
    '  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>',
    '  <style>',
    CSS,
    '  </style>',
    '</head>',
    '<body>',
    '  <div data-composition-id="main" data-width="1080" data-height="1920" data-start="0">',
    '',
]

for s in slides:
    html = SLIDE_HTML[s['num']].format(
        ss=s['slide_start'], sd=s['slide_dur'],
        astart=s['audio_start'], adur=s['audio_dur'],
        afile=s['audio_file']
    )
    lines.append(html)
    lines.append('')

lines.append('    <!-- BGM -->')
lines.append(f'    <audio id="bgm-music" class="clip" data-start="0" data-duration="{bgm_dur}" data-track-index="3" src="assets/bgm.wav"></audio>')
lines.append('')
lines.append('  </div>')
lines.append('')
lines.append(SCRIPTS_CONTENT)
lines.append('</body>')
lines.append('</html>')

content = '\n'.join(lines)
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"=== Done ===")
print(f"Size: {len(content):,} bytes")
print(f"Total duration: {bgm_dur}s")
for s in slides:
    print(f"  Slide {s['num']}: slide=[{s['slide_start']}->{round(s['slide_start']+s['slide_dur'],1)}]s audio=[{s['audio_start']}->{round(s['audio_start']+s['audio_dur'],1)}]s")

"""
BGM 背景音乐下载脚本
==============================
从 Kevin MacLeod (incompetech.com) 下载 CC BY 4.0 免费音乐，
用作 AI 视频的背景音。

许可: Creative Commons: By Attribution 4.0
署名要求: "Kevin MacLeod (incompetech.com)"
建议在视频简介中添加上述署名。

下载保存到: assets/bgm/

用法:
    python download_bgm.py              # 下载精选的 65 首氛围/环境 BGM
    python download_bgm.py --count 5    # 只下载前 5 首
    python download_bgm.py --list       # 只列出曲目
    python download_bgm.py --fetch-all  # 从 pieces.json 自动发现并下载所有 BGM 适配曲目
    python download_bgm.py --all        # 下载全部 1441 首（谨慎！大流量）

依赖:
    pip install requests
"""

import os
import sys
import time
import argparse
import json
from urllib.parse import quote

try:
    import requests as req
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BGM_DIR = os.path.join(SCRIPT_DIR, "assets", "bgm")
os.makedirs(BGM_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 精选 BGM 曲目 - 仅包含适合做视频背景的氛围/环境/轻音乐
# 全部来自 Kevin MacLeod (incompetech.com) - CC BY 4.0
# ---------------------------------------------------------------------------
CURATED_TRACKS = [
    # === B/Ambient - 纯氛围音乐 ===
    "Fluidscape", "Ambiment", "Lightless Dawn", "Chill Wave",
    "Magic Forest", "Organic Meditations One", "Organic Meditations Two",
    "Organic Meditations Three", "Perspectives", "Silver Blue Light",
    "Spacial Harvest", "Tranquility Base", "Wisps of Whorles",
    "Almost in F", "New Direction",
    # === A/Contemporary - 当代舒缓 ===
    "Carefree", "Clean Soul", "Dream Culture", "Ebbs and Flows",
    "Immersed", "Inner Light", "Montauk Point", "Brittle Rille",
    "Almost Bliss", "Autumn Day", "Blue Feather", "Windswept", "Winter Chimes",
    # === E/New Age - 新世纪/冥想 ===
    "At Rest", "Blue Paint", "Clear Waters", "Concentration",
    "Continue Life", "Deep Relaxation", "Dewdrop Fantasy",
    "Dreams Become Real", "Elf Meditation", "Garden Music",
    "Healing", "Heartwarming", "Infinite Perspective",
    "Luminous Rain", "Midsummer Sky", "Moonstone",
    "Numinous Shine", "Peace of Mind", "Relaxing Piano Music",
    "Sapphire Isle", "Simple Duet", "Soaring", "Sovereign",
    "Starry", "Stoic Morning", "Touching Moments One - Pulse",
    "Touching Moments Two - Higher", "Touching Moments Three - Deeper",
    "Touching Story", "Universal", "White Lotus", "White",
    "With the Sea", "Aretes",
    # === D/Everything Else - 舒缓配乐 ===
    "Long Note One", "Long Note Two", "Long Note Three", "Long Note Four",
    "Very Low Note",
]

BASE_URL = "https://incompetech.com/music/royalty-free/mp3-royaltyfree"


def make_url(title):
    """由曲目名生成下载 URL"""
    fn = f"{title}.mp3"
    return f"{BASE_URL}/{quote(fn)}"


def make_filename(title):
    """由曲目名生成安全的本地文件名"""
    safe = title.replace("/", "-").replace("\\", "-").replace(":", "-")
    safe = "".join(c for c in safe if c.isalnum() or c in "._- ")
    return f"{safe}.mp3"


def download_file(url, dest_path, timeout=60):
    """下载文件，返回 (成功, 消息)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "audio/mpeg,*/*",
    }
    try:
        r = req.get(url, headers=headers, timeout=timeout, stream=True)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        ct = r.headers.get("Content-Type", "")
        if "text/html" in ct:
            return False, "返回 HTML（链接可能已过期）"

        total = int(r.headers.get("Content-Length", 0))
        if total < 5000:
            return False, f"文件太小 ({total} bytes)"

        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        actual = os.path.getsize(dest_path)
        return True, f"{actual / 1000000:.1f}MB"
    except Exception as e:
        return False, str(e)


def fetch_tracks_from_catalog():
    """从 pieces.json 自动获取所有曲目信息"""
    url = "https://incompetech.com/music/royalty-free/pieces.json"
    try:
        r = req.get(url, timeout=30)
        if r.status_code != 200:
            print(f"  ! pieces.json 获取失败: HTTP {r.status_code}")
            return None
        data = r.json()
        print(f"  pieces.json: {len(data)} 首曲目")
        return data
    except Exception as e:
        print(f"  ! pieces.json 请求失败: {e}")
        return None


def find_bgm_from_catalog(data):
    """从完整曲目中智能筛选适合做 BGM 的曲子"""
    bgm_keywords = [
        "ambient", "meditation", "relax", "calm", "peace", "dream",
        "chill", "soft", "smooth", "floating", "gentle", "quiet",
        "serene", "tranquil", "ethereal", "mellow", "slow",
        "atmospheric", "deep relaxation",
    ]
    results = []
    for p in data:
        title = p.get("title", "").lower()
        genre = (p.get("genre") or "").lower()
        tags = (p.get("tags") or "").lower() if p.get("tags") else ""

        matched = False
        for kw in bgm_keywords:
            if kw in title or kw in genre or kw in tags:
                matched = True
                break
        if matched:
            results.append(p)

    results.sort(key=lambda x: x.get("title", ""))
    return results


def main():
    parser = argparse.ArgumentParser(description="下载 CC BY 4.0 BGM 背景音乐")
    parser.add_argument("--list", action="store_true", help="只列出曲目，不下载")
    parser.add_argument("--count", type=int, default=0, help="只下载前 N 首")
    parser.add_argument("--all", action="store_true", help="下载全部 1441 首")
    parser.add_argument("--fetch-all", action="store_true",
                        help="从 pieces.json 自动发现并下载所有 BGM 适配曲目")
    args = parser.parse_args()

    # 确定要下载的曲目
    tracks = []

    if args.all:
        print("正在获取全部曲目列表...")
        data = fetch_tracks_from_catalog()
        if data:
            tracks = [p.get("filename", "").replace(".mp3", "") for p in data]
            tracks.sort()
            print(f"将从 {len(tracks)} 首全部曲目中下载")
        else:
            print("无法获取曲目列表，使用精选列表代替")
            tracks = CURATED_TRACKS
    elif args.fetch_all:
        print("正在从 pieces.json 筛选 BGM 适配曲目...")
        data = fetch_tracks_from_catalog()
        if data:
            bgm = find_bgm_from_catalog(data)
            tracks = [p.get("filename", "").replace(".mp3", "") for p in bgm]
            print(f"自动筛选到 {len(tracks)} 首 BGM 适配曲目")
        else:
            print("无法获取曲目列表，使用精选列表代替")
            tracks = CURATED_TRACKS
    else:
        tracks = CURATED_TRACKS

    if args.count > 0:
        tracks = tracks[:args.count]

    # 提示信息
    print(f"\n{'='*60}")
    print(f"  BGM 音乐下载器")
    print(f"  来源: incompetech.com (Kevin MacLeod)")
    print(f"  许可: CC BY 4.0")
    print(f"  署名: Kevin MacLeod (incompetech.com)")
    print(f"  保存: {BGM_DIR}")
    print(f"{'='*60}")
    print(f"\n共 {len(tracks)} 首曲目\n")

    if args.list:
        for i, t in enumerate(tracks, 1):
            url = make_url(t)
            print(f"  {i:3d}. {t}")
            print(f"       {url}")
        print("\n（仅列表示例，无实际下载）")
        return

    # 开始下载
    success = 0
    skipped = 0
    failed = 0

    for i, title in enumerate(tracks, 1):
        url = make_url(title)
        dest_path = os.path.join(BGM_DIR, make_filename(title))

        if os.path.exists(dest_path):
            fsize = os.path.getsize(dest_path)
            print(f"  [{i:3d}/{len(tracks)}] {title:40s}  已存在 ({fsize/1000000:.1f}MB)")
            skipped += 1
            continue

        print(f"  [{i:3d}/{len(tracks)}] {title:40s}  ", end="", flush=True)
        ok, msg = download_file(url, dest_path)
        if ok:
            print(f"OK {msg}")
            success += 1
        else:
            print(f"FAIL {msg}")
            failed += 1

        if i < len(tracks):
            time.sleep(0.3)

    # 汇总
    print(f"\n{'='*60}")
    print(f"  完成!")
    print(f"  新下载: {success} 首")
    print(f"  已存在: {skipped} 首")
    if failed:
        print(f"  失败:   {failed} 首")
    print(f"  保存位置: {BGM_DIR}")
    print(f"{'='*60}")

    print(f"\n署名要求:")
    print(f"  所有曲目来自 Kevin MacLeod (incompetech.com)")
    print(f"  许可: Creative Commons: By Attribution 4.0")
    print(f"  请在视频简介中添加:")
    print(f'    "Music: Kevin MacLeod (incompetech.com) - Licensed under CC BY 4.0"')


if __name__ == "__main__":
    main()

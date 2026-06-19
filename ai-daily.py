#!/usr/bin/env python3
"""AI HOT 日报 — 拉数据 → 生成HTML → 推GitHub Pages → 输出解读"""
import json, os, shutil, subprocess, sys, datetime, urllib.request

# ── 配置 ──
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_URL = f"https://AHH20250507:{GITHUB_TOKEN}@github.com/AHH20250507/ai-daily.git"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-daily-deploy")
WORK_DIR = os.path.join(os.environ.get("TEMP", "/tmp"), "ai-daily-repo")
API_DAILY = "https://aihot.virxact.com/api/public/daily"
API_LATEST = "https://aihot.virxact.com/api/public/dailies?take=1"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# ── 1. 拉取数据 ──
def fetch_data():
    req = urllib.request.Request(API_DAILY, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        req2 = urllib.request.Request(API_LATEST, headers={"User-Agent": UA})
        with urllib.request.urlopen(req2, timeout=30) as resp:
            latest = json.loads(resp.read())
            date_str = latest["data"][0]["date"]
            req3 = urllib.request.Request(
                f"https://aihot.virxact.com/api/public/daily?date={date_str}",
                headers={"User-Agent": UA}
            )
            with urllib.request.urlopen(req3, timeout=30) as resp:
                data = json.loads(resp.read())
    return data


# ── 2. 生成 HTML ──
def generate_html(data):
    date_str = data["date"]
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    weekday = weekdays[dt.weekday()]
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_day = f"{months[dt.month-1]} {dt.day}"

    sections = data.get("sections", [])
    total = sum(len(s["items"]) for s in sections)

    # stat bar
    stat_items = ""
    for s in sections:
        label_short = s["label"].replace("发布/更新","").replace("发布","").replace("更新","")
        stat_items += f'<div class="stat-item"><div class="stat-num">{len(s["items"])}</div><div class="stat-label">{label_short}</div></div>\n'

    # card list
    sections_html = ""
    global_idx = 0
    for s in sections:
        items = s["items"]
        sections_html += f'<section class="section">\n'
        sections_html += f'<div class="section-head"><h2 class="section-title">{s["label"]}</h2><span class="section-count">{len(items)} 条</span></div>\n'
        if not items:
            sections_html += f'<p class="empty-section">今日暂无{s["label"]}条目</p>\n'
        else:
            sections_html += '<div class="card-list">\n'
            for item in items:
                global_idx += 1
                title = item["title"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                summary = item["summary"][:120].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                src = item.get("sourceName","")[:20]
                url = item["sourceUrl"]
                sections_html += f'''<a class="card" href="{url}" target="_blank" rel="noopener">
<span class="card-num">{global_idx:02d}</span>
<div class="card-body"><div class="card-title">{title}</div><p class="card-summary">{summary}</p></div>
<div class="card-meta"><span class="card-source">{src}</span><span class="card-arrow">→</span></div>
</a>\n'''
            sections_html += '</div>\n'
        sections_html += '</section>\n'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI HOT 日报 · {date_str}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-font-smoothing:antialiased}}
body{{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC",sans-serif;background:#fbfbfd;color:#1d1d1f;line-height:1.5}}
body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:-1;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.015'/%3E%3C/svg%3E");opacity:.6}}
.hero{{padding:120px 0 100px;text-align:center}}
.hero-tag{{display:inline-flex;align-items:center;gap:8px;font-size:11px;font-weight:600;color:#86868b;letter-spacing:.18em;text-transform:uppercase;margin-bottom:28px;padding:5px 16px;border-radius:12px;background:rgba(0,113,227,.04);border:1px solid rgba(0,113,227,.06)}}
.hero-tag-dot{{width:5px;height:5px;border-radius:50%;background:#0071e3}}
.hero-weekday{{font-size:14px;color:#86868b;letter-spacing:.12em;text-transform:uppercase;font-weight:500;margin-bottom:8px}}
.hero-date{{font-size:64px;font-weight:700;letter-spacing:-.03em;line-height:1.05;margin-bottom:48px}}
.hero-total-num{{font-size:200px;font-weight:800;line-height:.9;letter-spacing:-.05em;background:linear-gradient(175deg,#0059b3,#0071e3 30%,#39f 60%,#0071e3);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:16px}}
.hero-total-label{{font-size:17px;color:#86868b;font-weight:500;letter-spacing:.04em}}
.stat-bar{{display:flex;justify-content:center;gap:1px;margin:56px auto 0;max-width:720px;background:rgba(0,0,0,.04);border-radius:14px;overflow:hidden}}
.stat-item{{flex:1;text-align:center;padding:18px 12px 16px;background:#fbfbfd}}
.stat-num{{font-size:28px;font-weight:700;color:#0071e3;line-height:1}}
.stat-label{{font-size:11px;color:#86868b;margin-top:6px;letter-spacing:.03em}}
.container{{max-width:1000px;margin:0 auto;padding:0 32px}}
.section{{margin-bottom:100px}}
.section-head{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:36px;padding-bottom:18px;border-bottom:1px solid rgba(0,0,0,.05)}}
.section-title{{font-size:22px;font-weight:700;letter-spacing:-.01em}}
.section-count{{font-size:13px;color:#86868b;font-weight:500}}
.empty-section{{color:#aeaeb2;font-size:14px;padding:48px 0;text-align:center}}
.card-list{{display:flex;flex-direction:column;gap:1px}}
.card{{display:flex;align-items:flex-start;gap:24px;padding:28px 0;text-decoration:none;color:inherit;border-bottom:1px solid rgba(0,0,0,.04)}}
.card:first-child{{border-top:1px solid rgba(0,0,0,.04)}}
.card-num{{font-size:28px;font-weight:700;flex-shrink:0;width:48px;text-align:right;color:#d2d2d7;letter-spacing:-.02em;line-height:1;padding-top:2px}}
.card-body{{flex:1;min-width:0}}
.card-title{{font-size:16px;font-weight:600;line-height:1.5;letter-spacing:-.01em;margin-bottom:6px}}
.card-summary{{font-size:13.5px;color:#86868b;line-height:1.75}}
.card-meta{{flex-shrink:0;text-align:right;padding-top:2px;display:flex;flex-direction:column;align-items:flex-end;gap:8px}}
.card-source{{font-size:11px;color:#aeaeb2;font-weight:500;white-space:nowrap}}
.card-arrow{{font-size:14px;color:#d2d2d7}}
.footer{{text-align:center;padding:80px 0 100px;border-top:1px solid rgba(0,0,0,.04);margin-top:40px}}
.footer-divider{{width:1px;height:32px;background:rgba(0,0,0,.08);margin:0 auto 32px}}
.footer-total{{font-size:14px;color:#86868b;font-weight:500}}
.footer-source{{font-size:12px;color:#aeaeb2;margin-top:10px}}
.footer-source a{{color:#0071e3;text-decoration:none;font-weight:540}}
@media(max-width:768px){{.hero{{padding:64px 0 56px}}.hero-date{{font-size:38px}}.hero-total-num{{font-size:120px}}.stat-bar{{flex-wrap:wrap;border-radius:12px}}.stat-item{{flex:1 1 33%;min-width:90px;padding:14px 8px 12px}}.stat-num{{font-size:22px}}.container{{padding:0 20px}}.section{{margin-bottom:64px}}.card{{gap:14px;padding:20px 0}}.card-num{{font-size:22px;width:36px}}.card-meta{{display:none}}.footer{{padding:48px 0 64px}}}}
</style></head>
<body>
<header class="hero">
<div class="hero-tag"><span class="hero-tag-dot"></span>AI HOT</div>
<div class="hero-weekday">{weekday}</div>
<div class="hero-date">{month_day}, {dt.year}</div>
<div class="hero-total-num">{total}</div>
<div class="hero-total-label">今日 AI 动态</div>
<div class="stat-bar">{stat_items}</div>
</header>
<div class="container">{sections_html}</div>
<footer class="footer"><div class="footer-divider"></div><div class="footer-total">共计 {total} 条 AI 动态 · {date_str}</div><div class="footer-source">数据来源 <a href="https://aihot.virxact.com" target="_blank">AI HOT</a></div></footer>
</body></html>'''

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return total, date_str


# ── 3. 推送到 GitHub ──
def git_push(date_str):
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
    subprocess.run(["git", "clone", REPO_URL, WORK_DIR], capture_output=True, text=True, timeout=60)
    src = os.path.join(OUTPUT_DIR, "index.html")
    dst = os.path.join(WORK_DIR, "index.html")
    with open(src, "rb") as f:
        content = f.read()
    with open(dst, "wb") as f:
        f.write(content)
    subprocess.run(["git", "-C", WORK_DIR, "config", "user.email", "ahh20250507@users.noreply.github.com"], capture_output=True)
    subprocess.run(["git", "-C", WORK_DIR, "config", "user.name", "AHH20250507"], capture_output=True)
    subprocess.run(["git", "-C", WORK_DIR, "add", "index.html"], capture_output=True)
    subprocess.run(["git", "-C", WORK_DIR, "commit", "-m", f"{date_str} 日报"], capture_output=True)
    result = subprocess.run(["git", "-C", WORK_DIR, "push"], capture_output=True, text=True, timeout=60)
    return result.returncode == 0


# ── 4. 选重点 + 写解读 ──
def pick_highlights(data):
    all_items = []
    for s in data.get("sections", []):
        for item in s["items"]:
            all_items.append({"title": item["title"], "summary": item["summary"], "section": s["label"]})

    # 优先选 行业动态 + 有金额/收购/重大发布的
    def score(item):
        s = 0
        t = item["title"] + item["summary"]
        if item["section"] == "行业动态": s += 3
        if item["section"] == "模型发布/更新": s += 2
        if any(kw in t for kw in ["收购","亿美元","上市","开源","裁员"]): s += 3
        if any(kw in t for kw in ["发布","发布","首","第一"]): s += 1
        return s

    ranked = sorted(all_items, key=score, reverse=True)
    return ranked[:2]


def write_analysis(items, total, date_str):
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📰 AI HOT 日报 · {date_str}")
    lines.append(f"链接：https://ahh20250507.github.io/ai-daily/")
    lines.append("")

    emojis = ["🔴", "🔵"]
    for i, item in enumerate(items):
        title = item["title"]
        summary = item["summary"]
        lines.append(f"{emojis[i]} {title}")
        # 写 3-4 句解读
        lines.append(f"[解读] {summary[:200]}……")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"共计 {total} 条 | 链接：https://ahh20250507.github.io/ai-daily/")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ── 主流程 ──
def main():
    print("⏳ 拉取 AI HOT 数据...")
    data = fetch_data()
    date_str = data["date"]
    print(f"✅ 数据日期: {date_str}")

    print("📄 生成 HTML...")
    total, _ = generate_html(data)
    print(f"✅ 已生成 {total} 条动态")

    print("🚀 推送到 GitHub Pages...")
    ok = git_push(date_str)
    print(f"{'✅' if ok else '❌'} GitHub推送{'成功' if ok else '失败'}")

    print("\n📋 重点解读:")
    highlights = pick_highlights(data)
    msg = write_analysis(highlights, total, date_str)
    print(msg)
    return msg

if __name__ == "__main__":
    main()

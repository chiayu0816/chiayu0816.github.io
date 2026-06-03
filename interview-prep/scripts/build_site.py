#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a static study site from the interview-prep markdown files.

Parses the 13 tech `.md` files into structured Q&A data and writes a
self-contained static site under `interview-prep/site/`:

    site/index.html
    site/assets/style.css
    site/assets/app.js
    site/assets/data.js   (generated content; window.__IP_DATA__)

Data is embedded as a JS global (not JSON+fetch) so the site works when
opened directly via file:// with no server.

Regenerate:  python3 scripts/build_site.py
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ASSETS = SITE / "assets"

# (filename, key, display name, short nav label, priority 2|3)
TECHS = [
    ("go.md", "go", "Go", "Go", 3),
    ("redis.md", "redis", "Redis", "Redis", 3),
    ("mysql.md", "mysql", "MySQL", "MySQL", 3),
    ("system-design.md", "system-design", "System Design", "System Design", 3),
    ("performance-pprof.md", "performance-pprof", "Performance / pprof", "pprof", 3),
    ("kafka.md", "kafka", "Kafka", "Kafka", 3),
    ("rocketmq.md", "rocketmq", "RocketMQ", "RocketMQ", 3),
    ("grpc.md", "grpc", "gRPC", "gRPC", 2),
    ("websocket.md", "websocket", "WebSocket", "WebSocket", 2),
    ("mongodb.md", "mongodb", "MongoDB", "MongoDB", 2),
    ("rabbitmq.md", "rabbitmq", "RabbitMQ", "RabbitMQ", 2),
    ("java-spring-boot.md", "java-spring-boot", "Java / Spring Boot", "Java", 2),
    ("docker-aws.md", "docker-aws", "Docker / AWS", "Docker/AWS", 2),
]

SECTION_MARKERS = [
    ("**核心回答：**", "core"),
    ("**深入原理：**", "dive"),
    ("**考官可能追問：**", "followups"),
    ("**常見陷阱 / 易錯點：**", "pitfalls"),
    ("**實務場景：**", "scenario"),
    ("**結合履歷：**", "resume_legacy"),
]

INCLUDE_PERSONAL = os.environ.get("INCLUDE_PERSONAL", "0") == "1"


def load_personal_overlay() -> dict[str, str]:
    """Load PERSONAL_OVERLAY from private repo via RESUME_OVERLAY_PATH."""
    if not INCLUDE_PERSONAL:
        return {}
    path = os.environ.get("RESUME_OVERLAY_PATH", "").strip()
    if not path:
        return {}
    overlay_path = Path(path).expanduser().resolve()
    if not overlay_path.is_file():
        return {}
    spec = importlib.util.spec_from_file_location("resume_overlay_private", overlay_path)
    if spec is None or spec.loader is None:
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = getattr(mod, "PERSONAL_OVERLAY", {})
    return data if isinstance(data, dict) else {}

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)
SVG_FENCE_RE = re.compile(r"```svg\n(.*?)```", re.S)


def inline_md(escaped: str) -> str:
    """Apply inline markdown (code, bold) to already HTML-escaped text."""
    escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    return escaped


def render_rich(text: str) -> str:
    """Render a free-text section (paragraphs + fenced code blocks)."""
    out: list[str] = []
    idx = 0
    pieces: list[tuple] = []
    for m in FENCE_RE.finditer(text):
        pieces.append(("text", text[idx:m.start()]))
        pieces.append(("code", m.group(1), m.group(2)))
        idx = m.end()
    pieces.append(("text", text[idx:]))
    for p in pieces:
        if p[0] == "text":
            chunk = p[1].strip()
            if not chunk:
                continue
            for para in re.split(r"\n\s*\n", chunk):
                para = para.strip()
                if not para:
                    continue
                esc = html.escape(para).replace("\n", "<br>")
                out.append(f"<p>{inline_md(esc)}</p>")
        else:
            lang = p[1] or "text"
            if lang == "svg":
                # Inline SVG diagrams are emitted as raw html (not escaped),
                # so the hand-authored markup renders as an actual diagram.
                out.append(f'<div class="diagram">{p[2].strip()}</div>')
                continue
            code = html.escape(p[2].rstrip("\n"))
            out.append(
                f'<pre class="code"><span class="code-lang">{lang}</span>'
                f"<code>{code}</code></pre>"
            )
    return "".join(out)


def bullets(text: str) -> list[str]:
    items = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("- "):
            items.append(inline_md(html.escape(s[2:].strip())))
    return items


def bullets_and_diagram(text: str) -> tuple[list[str], str]:
    """Split a dive section into bullet items + raw inline-SVG diagram html."""
    svgs: list[str] = []

    def grab(m: re.Match) -> str:
        svgs.append(m.group(1).strip())
        return ""

    rest = SVG_FENCE_RE.sub(grab, text)
    diagram = "".join(f'<div class="diagram">{s}</div>' for s in svgs)
    return bullets(rest), diagram


def parse_followups(text: str) -> list[dict]:
    pairs = []
    cur_q = None
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("- Q:"):
            cur_q = s[4:].strip()
        elif s.startswith("- A:") and cur_q is not None:
            pairs.append({
                "q": inline_md(html.escape(cur_q)),
                "a": inline_md(html.escape(s[4:].strip())),
            })
            cur_q = None
    return pairs


def plain(text: str) -> str:
    t = re.sub(r"```\w*\n.*?```", " ", text, flags=re.S)
    t = re.sub(r"[`*#>\-]", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def parse_topic(block: str) -> dict | None:
    lines = block.strip().split("\n")
    q = None
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("### Q:"):
            q = line[len("### Q:"):].strip()
            body_start = i + 1
            break
    if q is None:
        return None
    body = "\n".join(lines[body_start:])

    positions = []
    for marker, key in SECTION_MARKERS:
        idx = body.find(marker)
        if idx != -1:
            positions.append((idx, marker, key))
    positions.sort()

    raw = {}
    for i, (idx, marker, key) in enumerate(positions):
        start = idx + len(marker)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        raw[key] = body[start:end].strip()

    search_src = q + " " + " ".join(raw.values())
    dive_items, dive_diagram = bullets_and_diagram(raw.get("dive", ""))
    scenario_raw = raw.get("scenario") or raw.get("resume_legacy", "")
    return {
        "q": q,
        "core": render_rich(raw.get("core", "")),
        "dive": dive_items,
        "diagram": dive_diagram,
        "followups": parse_followups(raw.get("followups", "")),
        "pitfalls": bullets(raw.get("pitfalls", "")),
        "scenario": render_rich(scenario_raw) if scenario_raw else "",
        "personal": "",
        "text": plain(search_src),
    }


def parse_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    chunks = text.split("\n---\n")
    topics = []
    for chunk in chunks:
        if "### Q:" in chunk:
            t = parse_topic(chunk)
            if t:
                topics.append(t)
    return topics


def build_data() -> dict:
    overlay = load_personal_overlay()
    techs = []
    total = 0
    personal_count = 0
    for fname, key, name, short, prio in TECHS:
        topics = parse_file(ROOT / fname)
        for idx, topic in enumerate(topics):
            tid = f"{key}-{idx}"
            topic["id"] = tid
            if INCLUDE_PERSONAL:
                topic["personal"] = overlay.get(tid, "")
            else:
                topic["personal"] = ""
            if topic["personal"]:
                personal_count += 1
            topic["text"] = plain(
                topic["q"] + " " + topic.get("core", "")
                + " " + " ".join(topic.get("dive", []))
                + " " + topic.get("scenario", "")
                + (" " + topic["personal"] if INCLUDE_PERSONAL else "")
            )
        total += len(topics)
        techs.append({
            "key": key, "name": name, "short": short,
            "prio": prio, "count": len(topics), "topics": topics,
        })
    return {
        "techs": techs,
        "total": total,
        "hasPersonal": personal_count > 0,
        "personalCount": personal_count,
    }


# ---------------------------------------------------------------------------
# Static assets (authored once, written verbatim so the build is self-contained)
# ---------------------------------------------------------------------------

STYLE_CSS = r"""/* Interview Prep — technical-editorial dark study console */
:root{
  --bg:#0a0c11; --bg2:#0d1017; --surface:#13161f; --surface2:#171b25;
  --border:#242a36; --border2:#2f3645;
  --text:#e7eaf2; --muted:#9aa3b5; --faint:#6b7385;
  --accent:#ffb454; --accent-dim:#7a5a26;
  --c-core:#ffb454; --c-dive:#56c2ff; --c-ask:#c79cff; --c-trap:#ff6b6b; --c-resume:#54dd9b;
  --radius:14px; --radius-sm:9px;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;
  --maxw:1180px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; font-family:var(--sans); color:var(--text); background:var(--bg);
  line-height:1.6; -webkit-font-smoothing:antialiased; letter-spacing:.01em;
  background-image:
    radial-gradient(900px 600px at 12% -8%, rgba(255,180,84,.10), transparent 60%),
    radial-gradient(800px 700px at 100% 0%, rgba(86,194,255,.07), transparent 55%),
    linear-gradient(180deg,#0a0c11,#0a0c11);
  background-attachment:fixed;
}
body::before{ /* faint engineering grid */
  content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.4;
  background-image:linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);
  background-size:46px 46px; mask-image:radial-gradient(circle at 50% 0%,#000,transparent 85%);
}
a{color:var(--accent);text-decoration:none}
::selection{background:rgba(255,180,84,.28)}

/* Topbar */
.topbar{position:sticky;top:0;z-index:50;backdrop-filter:blur(14px);
  background:rgba(10,12,17,.72);border-bottom:1px solid var(--border)}
.topbar-in{max-width:var(--maxw);margin:0 auto;padding:14px 22px;display:flex;align-items:center;gap:18px}
.brand{display:flex;align-items:baseline;gap:10px;flex-shrink:0}
.brand .logo{font-family:var(--mono);font-weight:700;font-size:17px;color:var(--text);letter-spacing:-.02em}
.brand .logo .pin{color:var(--accent)}
.brand .sub{font-family:var(--mono);font-size:11px;color:var(--faint);letter-spacing:.06em}
.search{position:relative;flex:1;max-width:460px}
.search input{width:100%;padding:9px 36px 9px 36px;border-radius:999px;border:1px solid var(--border2);
  background:var(--surface);color:var(--text);font-family:var(--mono);font-size:13px;outline:none;transition:.18s}
.search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(255,180,84,.12)}
.search .si{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:13px}
.search .kbd{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-family:var(--mono);
  font-size:10px;color:var(--faint);border:1px solid var(--border2);border-radius:5px;padding:1px 6px}
.topbar .progress-wrap{margin-left:auto;display:flex;align-items:center;gap:10px;flex-shrink:0}
.progress-num{font-family:var(--mono);font-size:12px;color:var(--muted)}
.progress-num b{color:var(--accent)}
.ring{--p:0;width:34px;height:34px;border-radius:50%;flex-shrink:0;
  background:conic-gradient(var(--accent) calc(var(--p)*1%), var(--border) 0);
  display:grid;place-items:center}
.ring::after{content:"";width:24px;height:24px;border-radius:50%;background:var(--bg2)}

/* Layout */
.layout{max-width:var(--maxw);margin:0 auto;display:grid;grid-template-columns:248px 1fr;gap:34px;
  padding:26px 22px 90px;position:relative;z-index:1}
.sidebar{position:sticky;top:78px;align-self:start;max-height:calc(100vh - 96px);overflow:auto;padding-right:4px}
.side-title{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--faint);
  text-transform:uppercase;margin:4px 0 12px 10px}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:var(--radius-sm);
  cursor:pointer;color:var(--muted);font-size:13.5px;border:1px solid transparent;transition:.14s;width:100%;text-align:left;background:none}
.nav-item:hover{background:var(--surface);color:var(--text)}
.nav-item.active{background:var(--surface2);color:var(--text);border-color:var(--border2)}
.nav-item.active .dot{box-shadow:0 0 0 4px rgba(255,180,84,.12)}
.nav-item .dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;background:var(--c-dive)}
.nav-item.p3 .dot{background:var(--accent)}
.nav-item .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-item .ct{font-family:var(--mono);font-size:11px;color:var(--faint)}
.nav-item.done .ct{color:var(--c-resume)}
.side-foot{margin:16px 8px 0;font-family:var(--mono);font-size:11px;color:var(--faint);line-height:1.7}
.side-foot button{background:none;border:1px solid var(--border2);color:var(--muted);border-radius:6px;
  font-family:var(--mono);font-size:11px;padding:4px 8px;cursor:pointer;margin-top:8px}
.side-foot button:hover{border-color:var(--c-trap);color:var(--c-trap)}

/* Hero */
.hero{margin-bottom:30px}
.hero h1{font-family:var(--mono);font-weight:700;font-size:clamp(26px,4vw,38px);margin:0 0 6px;
  letter-spacing:-.02em;line-height:1.15}
.hero h1 .em{color:var(--accent)}
.hero p{color:var(--muted);max-width:680px;margin:6px 0 0;font-size:14.5px}
.hero .meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.chip{font-family:var(--mono);font-size:11.5px;color:var(--muted);background:var(--surface);
  border:1px solid var(--border);border-radius:999px;padding:5px 12px}
.chip b{color:var(--text)}

/* Tech section */
.tech{margin:0 0 14px;scroll-margin-top:90px}
.tech-head{display:flex;align-items:flex-end;gap:14px;padding:26px 0 14px;border-bottom:1px solid var(--border);margin-bottom:18px}
.tech-head .idx{font-family:var(--mono);font-size:13px;color:var(--accent);opacity:.8}
.tech-head h2{font-family:var(--mono);font-size:23px;margin:0;letter-spacing:-.01em}
.tech-head .meta{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--faint)}
.tech-head .bar{height:4px;width:90px;border-radius:3px;background:var(--border);overflow:hidden;margin-left:14px}
.tech-head .bar i{display:block;height:100%;background:var(--accent);width:0;transition:width .4s}

/* Cards */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  margin-bottom:12px;overflow:hidden;transition:border-color .16s, transform .16s;
  opacity:0;transform:translateY(8px);animation:rise .4s forwards}
@keyframes rise{to{opacity:1;transform:none}}
.card:hover{border-color:var(--border2)}
.card.reviewed{border-color:var(--accent-dim)}
.card.reviewed .q-num{color:var(--c-resume)}
.q-row{display:flex;align-items:center;gap:14px;padding:15px 18px;cursor:pointer;width:100%;
  background:none;border:none;text-align:left;color:var(--text);font-family:inherit}
.q-num{font-family:var(--mono);font-size:12px;color:var(--accent);flex-shrink:0;min-width:34px}
.q-text{flex:1;font-size:15.5px;font-weight:600;letter-spacing:.005em}
.q-row .chev{flex-shrink:0;color:var(--faint);transition:transform .22s;font-size:13px}
.card.open .chev{transform:rotate(90deg)}
.rev{flex-shrink:0;display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--faint)}
.rev input{appearance:none;width:16px;height:16px;border:1.5px solid var(--border2);border-radius:5px;cursor:pointer;
  position:relative;transition:.15s;background:var(--bg2)}
.rev input:checked{background:var(--c-resume);border-color:var(--c-resume)}
.rev input:checked::after{content:"✓";position:absolute;inset:0;display:grid;place-items:center;color:#06140d;font-size:11px;font-weight:700}

.answer{display:none;padding:2px 18px 18px;border-top:1px solid var(--border)}
.card.open .answer{display:block}
.sec{margin-top:16px;padding-left:14px;border-left:2px solid var(--border2)}
.sec-core{border-color:var(--c-core)} .sec-dive{border-color:var(--c-dive)}
.sec-ask{border-color:var(--c-ask)} .sec-trap{border-color:var(--c-trap)} .sec-resume{border-color:var(--c-resume)}
.sec-label{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  display:inline-block;margin-bottom:7px;font-weight:600}
.sec-core .sec-label{color:var(--c-core)} .sec-dive .sec-label{color:var(--c-dive)}
.sec-ask .sec-label{color:var(--c-ask)} .sec-trap .sec-label{color:var(--c-trap)} .sec-resume .sec-label{color:var(--c-resume)}
.sec p{margin:0 0 8px;font-size:14.5px;color:#d8dce8}
.sec ul{margin:0;padding-left:18px}
.sec li{margin:5px 0;font-size:14px;color:#cdd3e0}
.sec code{font-family:var(--mono);font-size:.86em;background:#0c0f16;border:1px solid var(--border);
  border-radius:5px;padding:1px 5px;color:#ffce8a}
pre.code{position:relative;background:#0b0e15;border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:14px 14px 13px;overflow:auto;margin:10px 0}
pre.code code{font-family:var(--mono);font-size:12.8px;line-height:1.65;color:#cfe3ff;background:none;border:none;padding:0;white-space:pre}
.code-lang{position:absolute;top:7px;right:10px;font-family:var(--mono);font-size:10px;color:var(--faint);text-transform:uppercase;letter-spacing:.1em}
.diagram{
  margin:12px 0 4px;padding:16px 14px;background:#0b0e15;border:1px solid var(--border);
  border-radius:var(--radius-sm);overflow-x:auto;-webkit-overflow-scrolling:touch;text-align:center;
}
.diagram svg{display:block;max-width:100%;height:auto;margin:0 auto;font-family:var(--mono)}
.fu{margin:8px 0;padding:10px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-sm)}
.fu .fq{font-size:13.5px;color:var(--text);font-weight:600}
.fu .fq::before{content:"Q ";font-family:var(--mono);color:var(--c-ask);font-weight:700}
.fu .fa{font-size:13.5px;color:var(--muted);margin-top:4px}
.fu .fa::before{content:"A ";font-family:var(--mono);color:var(--c-resume);font-weight:700}

mark{background:rgba(255,180,84,.30);color:#fff;border-radius:3px;padding:0 1px}
.empty{text-align:center;color:var(--faint);font-family:var(--mono);padding:60px 0;font-size:14px}
.hidden{display:none !important}

/* Responsive */
@media (max-width:900px){
  .layout{grid-template-columns:1fr;gap:0;padding:16px 14px 80px}
  .sidebar{position:static;max-height:none;overflow:visible;margin-bottom:8px}
  .side-title{display:none}
  .nav-scroll{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px}
  .nav-item{width:auto;white-space:nowrap;border-color:var(--border)}
  .nav-item .ct{display:none}
  .side-foot{display:none}
  .topbar .progress-wrap .progress-num{display:none}
  .topbar-in{flex-wrap:wrap;gap:10px;padding:12px 14px}
  .search{order:3;max-width:none;flex-basis:100%}
}
"""

APP_JS = r"""(function(){
  "use strict";
  var DATA = window.__IP_DATA__ || {techs:[],total:0};
  var LS = "ipv1:";
  var $ = function(s,r){return (r||document).querySelector(s);};
  var ce = function(t,c){var e=document.createElement(t); if(c) e.className=c; return e;};

  // ---- progress store ----
  function isDone(id){ return localStorage.getItem(LS+id)==="1"; }
  function setDone(id,v){ v?localStorage.setItem(LS+id,"1"):localStorage.removeItem(LS+id); }

  var sideNav = $("#side-nav"), content = $("#content");
  var navItems = {};

  // ---- render ----
  DATA.techs.forEach(function(tech, ti){
    // nav
    var n = ce("button","nav-item p"+tech.prio);
    n.dataset.key = tech.key;
    n.innerHTML = '<span class="dot"></span><span class="nm">'+tech.name+
      '</span><span class="ct" data-ct>0/'+tech.count+'</span>';
    n.addEventListener("click",function(){ scrollToTech(tech.key); });
    sideNav.appendChild(n);
    navItems[tech.key] = n;

    // section
    var sec = ce("section","tech");
    sec.id = "tech-"+tech.key;
    var head = ce("div","tech-head");
    head.innerHTML = '<span class="idx">'+String(ti+1).padStart(2,"0")+'</span>'+
      '<h2>'+tech.name+'</h2>'+
      '<span class="meta" data-meta>0 / '+tech.count+' 已複習</span>'+
      '<span class="bar"><i data-prog></i></span>';
    sec.appendChild(head);

    tech.topics.forEach(function(t, idx){
      sec.appendChild(buildCard(tech, t, idx));
    });
    content.appendChild(sec);
  });

  function buildCard(tech, t, idx){
    var id = tech.key+"-"+idx;
    var card = ce("article","card");
    card.id = "c-"+id;
    card.style.animationDelay = Math.min(idx,12)*22 + "ms";
    if(isDone(id)) card.classList.add("reviewed");

    var row = ce("button","q-row");
    row.innerHTML = '<span class="q-num">'+String(idx+1).padStart(2,"0")+'</span>'+
      '<span class="q-text"></span>'+
      '<label class="rev" title="標記為已複習"><input type="checkbox"'+
      (isDone(id)?" checked":"")+'><span>已複習</span></label>'+
      '<span class="chev">▶</span>';
    $(".q-text",row).textContent = t.q;
    row.addEventListener("click",function(e){
      if(e.target.closest(".rev")) return;
      card.classList.toggle("open");
    });

    var chk = $(".rev input",row);
    chk.addEventListener("click",function(e){ e.stopPropagation(); });
    chk.addEventListener("change",function(){
      setDone(id, chk.checked);
      card.classList.toggle("reviewed", chk.checked);
      updateProgress();
    });
    card.appendChild(row);

    var ans = ce("div","answer");
    ans.innerHTML = renderAnswer(t);
    card.appendChild(ans);
    card._text = t.text;
    card._q = t.q;
    return card;
  }

  function sec(cls,label,inner){
    return '<div class="sec sec-'+cls+'"><span class="sec-label">'+label+'</span>'+inner+'</div>';
  }
  function list(arr){ return "<ul>"+arr.map(function(x){return "<li>"+x+"</li>";}).join("")+"</ul>"; }

  function renderAnswer(t){
    var h = "";
    if(t.core) h += sec("core","核心回答",t.core);
    if((t.dive&&t.dive.length) || t.diagram)
      h += sec("dive","深入原理",(t.dive&&t.dive.length?list(t.dive):"")+(t.diagram||""));
    if(t.followups&&t.followups.length){
      var fu = t.followups.map(function(f){
        return '<div class="fu"><div class="fq">'+f.q+'</div><div class="fa">'+f.a+'</div></div>';
      }).join("");
      h += sec("ask","考官可能追問",fu);
    }
    if(t.pitfalls&&t.pitfalls.length) h += sec("trap","常見陷阱 / 易錯點",list(t.pitfalls));
    if(t.resume) h += sec("resume","結合履歷",t.resume);
    return h;
  }

  // ---- progress ----
  function updateProgress(){
    var totalDone = 0;
    DATA.techs.forEach(function(tech){
      var done = 0;
      tech.topics.forEach(function(_,idx){ if(isDone(tech.key+"-"+idx)) done++; });
      totalDone += done;
      var nav = navItems[tech.key];
      $("[data-ct]",nav).textContent = done+"/"+tech.count;
      nav.classList.toggle("done", done===tech.count && tech.count>0);
      var s = $("#tech-"+tech.key);
      $("[data-meta]",s).textContent = done+" / "+tech.count+" 已複習";
      $("[data-prog]",s).style.width = (tech.count? (done/tech.count*100):0)+"%";
    });
    var pct = DATA.total? Math.round(totalDone/DATA.total*100):0;
    $("#p-done").textContent = totalDone;
    $("#p-total").textContent = DATA.total;
    $("#p-pct").textContent = pct+"%";
    $("#ring").style.setProperty("--p", pct);
  }

  // ---- scrollspy ----
  function scrollToTech(key){
    var el = $("#tech-"+key);
    if(el) window.scrollTo({top: el.getBoundingClientRect().top + window.pageYOffset - 74, behavior:"smooth"});
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        var key = en.target.id.replace("tech-","");
        Object.keys(navItems).forEach(function(k){ navItems[k].classList.toggle("active", k===key); });
      }
    });
  },{rootMargin:"-45% 0px -50% 0px"});
  DATA.techs.forEach(function(t){ io.observe($("#tech-"+t.key)); });

  // ---- search ----
  var box = $("#search");
  var timer=null;
  box.addEventListener("input",function(){ clearTimeout(timer); timer=setTimeout(runSearch,120); });
  box.addEventListener("keydown",function(e){ if(e.key==="Escape"){ box.value=""; runSearch(); box.blur(); } });
  document.addEventListener("keydown",function(e){
    if(e.key==="/" && document.activeElement!==box){ e.preventDefault(); box.focus(); }
  });

  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"); }
  function runSearch(){
    var q = box.value.trim().toLowerCase();
    var any = false;
    DATA.techs.forEach(function(tech){
      var s = $("#tech-"+tech.key);
      var shown = 0;
      Array.prototype.forEach.call(s.querySelectorAll(".card"),function(card){
        var match = !q || card._text.indexOf(q) !== -1;
        card.classList.toggle("hidden", !match);
        if(match){
          shown++; any=true;
          var qt = $(".q-text",card);
          if(q){
            qt.innerHTML = card._q.replace(new RegExp("("+esc(box.value.trim())+")","ig"),"<mark>$1</mark>");
            card.classList.add("open");
          } else {
            qt.textContent = card._q;
            card.classList.remove("open");
          }
        }
      });
      s.classList.toggle("hidden", shown===0 && !!q);
    });
    $("#empty").classList.toggle("hidden", any || !q);
  }

  // reset progress
  $("#reset").addEventListener("click",function(){
    if(confirm("清除所有「已複習」紀錄？")){
      Object.keys(localStorage).forEach(function(k){ if(k.indexOf(LS)===0) localStorage.removeItem(k); });
      Array.prototype.forEach.call(document.querySelectorAll(".rev input"),function(i){ i.checked=false; });
      Array.prototype.forEach.call(document.querySelectorAll(".card"),function(c){ c.classList.remove("reviewed"); });
      updateProgress();
    }
  });

  updateProgress();
})();
"""


def build_index_html(data: dict) -> str:
    total = data["total"]
    nstars3 = sum(1 for t in data["techs"] if t["prio"] == 3)
    first_tech = data["techs"][0]["name"] if data["techs"] else "—"
    toggle_hidden = "" if data.get("hasPersonal") else " hidden"
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Senior 後端面試題庫 · Go/Java</title>
<meta name="description" content="Senior Go/Java 後端面試題庫 · {total} 題五段式 Q&A，含原理追問與實務場景，可離線瀏覽">
<meta name="theme-color" content="#0a0c11">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="topbar-in">
    <button type="button" class="nav-toggle" id="nav-toggle" aria-label="開啟技術分類" aria-controls="sidebar" aria-expanded="false">
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
    </button>
    <div class="brand">
      <span class="logo">interview<span class="pin">_</span>prep</span>
      <span class="sub">SENIOR BACKEND · GO/JAVA</span>
    </div>
    <div class="search">
      <span class="si" aria-hidden="true">⌕</span>
      <input id="search" type="search" placeholder="搜尋題目與答案…  (按 / 聚焦)" autocomplete="off" aria-label="搜尋">
      <span class="kbd" aria-hidden="true">/</span>
    </div>
    <div class="progress-wrap">
      <span class="progress-num"><b id="p-done">0</b>/<span id="p-total">{total}</span> · <span id="p-pct">0%</span></span>
      <div class="ring" id="ring" title="整體複習進度" role="img" aria-label="整體複習進度"></div>
    </div>
    <label class="personal-toggle" id="personal-toggle-wrap"{toggle_hidden}>
      <input type="checkbox" id="personal-toggle" aria-label="顯示個人實戰對照">
      <span class="pt-label">個人對照</span>
    </label>
    <a href="https://www.linkedin.com/in/cylee-19830816/" class="topbar-linkedin" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn 個人檔案">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 114.126 0 2.063 2.063 0 01-2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
    </a>
  </div>
</header>

<div class="nav-backdrop" id="nav-backdrop" hidden></div>

<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="side-title">技術分類</div>
    <div id="side-nav" class="nav-scroll"></div>
    <div class="side-foot">
      進度自動存於此瀏覽器<br>localStorage
      <br><button type="button" id="reset">清除複習紀錄</button>
    </div>
  </aside>

  <main id="content">
    <section class="hero">
      <h1>Senior 後端<span class="em">面試題庫</span></h1>
      <p class="hero-lead">Go / Java · {total} 題 · 五段式可開口作答</p>
      <p>每題依「核心回答 → 深入原理 → 考官追問 → 常見陷阱 → 實務場景」整理，目標是<strong>聽得懂追問、講得出原理</strong>。
         涵蓋交易所（撮合、行情、對沖）與高吞吐數據管線等 Senior 常見脈絡。
         展開題卡練口述，勾選「已複習」在本機追蹤進度；歡迎在 GitHub 討論與共筆。</p>
      <div class="meta">
        <span class="chip"><b>{total}</b> 題</span>
        <span class="chip"><b>{len(data['techs'])}</b> 項技術</span>
        <span class="chip"><b>{nstars3}</b> 個核心領域</span>
        <span class="chip">繁體中文 · 可離線</span>
        <a class="chip chip-link" href="https://github.com/chiayu0816/chiayu0816.github.io/discussions" target="_blank" rel="noopener noreferrer">GitHub 討論</a>
        <a class="chip chip-link" href="https://github.com/chiayu0816/chiayu0816.github.io/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">貢獻題庫</a>
      </div>
    </section>
    <div id="empty" class="empty hidden">沒有符合的題目，試試其他關鍵字。</div>
  </main>
</div>

<nav class="bottom-nav" id="bottom-nav" aria-label="快速導覽">
  <button type="button" class="bn-btn" id="bn-menu"><span class="bn-ico" aria-hidden="true">☰</span><span>分類</span></button>
  <span class="bn-current" id="bn-current">{first_tech}</span>
  <button type="button" class="bn-btn" id="bn-search"><span class="bn-ico" aria-hidden="true">⌕</span><span>搜尋</span></button>
</nav>

<script src="assets/data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    data = build_data()
    (ASSETS / "data.js").write_text(
        "window.__IP_DATA__ = " + json.dumps(data, ensure_ascii=False) + ";",
        encoding="utf-8",
    )
    # style.css and app.js are authored under site/assets/ (mobile RWD, etc.)
    if not (ASSETS / "style.css").is_file():
        (ASSETS / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    if not (ASSETS / "app.js").is_file():
        (ASSETS / "app.js").write_text(APP_JS, encoding="utf-8")
    (SITE / "index.html").write_text(build_index_html(data), encoding="utf-8")
    print(f"Site built: {SITE/'index.html'}")
    print(f"Techs: {len(data['techs'])} | Total topics: {data['total']}")
    for t in data["techs"]:
        print(f"  {t['key']:18s} {t['count']:3d}")


if __name__ == "__main__":
    main()

---
name: interview-study-builder
description: Build senior-level backend interview study notes (繁體中文, 5-section Q&A) and a polished offline study site for Roy Lee's resume project. Use when the user wants to add a new technology's interview knowledge, mentions "interview notes", "面試筆記", "新增技術知識", "面試題庫", "study site", "interview prep", or wants to reproduce the structured Q&A + study-console workflow under interview-prep/.
---

# Interview Study Builder

Reproducible workflow for Roy Lee's backend interview prep. Adding a new technology means: research → author a `topics_<tech>.py` module in the 5-section schema → register it → run the generator (with 繁→繁 normalization) → rebuild the static study site. The design system is fixed so new content looks identical to existing content.

**Project root:** `interview-prep/` · **Scripts:** `interview-prep/scripts/` · **Site:** `interview-prep/site/`

## Workflow checklist

Copy and track:

```
- [ ] 1. Research the tech (source repos + web, prioritize high-freq senior Qs)
- [ ] 2. Author topics_<tech>.py in the 5-section schema (繁體中文)
- [ ] 3. Register in generate_comprehensive.py (import + write_file call)
- [ ] 4. Register in build_site.py TECHS list (with priority)
- [ ] 5. python3 scripts/generate_comprehensive.py   (writes <tech>.md, normalized)
- [ ] 6. python3 scripts/build_site.py               (rebuilds site + data.js)
- [ ] 7. Update README.md index table + 讀書順序
- [ ] 8. (optional) sync to Notion
```

Run scripts from `interview-prep/` (e.g. `cd interview-prep && python3 scripts/generate_comprehensive.py`). Requires `opencc` (`pip install opencc`).

## 1. Research method

Source repos are cloned under `interview-prep-source/` (read locally, do not re-clone):

| Repo | Path | Best for |
|------|------|----------|
| go-questions | `go-questions/content/` | Go internals: GMP, GC, channel, map, slice, interface, context, compile |
| interview-go | `interview-go/{redis,mysql,architecture,question,base}/` | Redis/MySQL/system-design Q&A, Go basics |
| tech-vault | `tech-vault/README.md` | DevOps, System Design, messaging, infra breadth |
| go-interview-practice | `go-interview-practice/` | Coding exercises, hands-on patterns |

For libraries/frameworks not covered, use the **user-context7** MCP for current official docs, and web search for high-frequency interview questions. Web sources already used: tech-vault, go-interview-practice.

**Selection rules (keep it senior-level, non-redundant):**
- Prioritize high-frequency, senior-depth questions that survive interviewer follow-ups — not trivia.
- Every answer must reach the WHY/底層原理 level, not just the WHAT.
- Tie at least the high-value topics back to Roy's real experience (see `interview-prep/README.md` 履歷亮點: crypto exchange matching/market-data/liquidity/hedging, sports data Betradar/Kafka/LMAX Disruptor, K-line pprof tuning, Spring Boot refactor, Docker/AWS).
- Deduplicate against existing `.md` files — don't repeat a concept already covered under another tech.
- Frontend is explicitly excluded (Vue/Pinia/Vite/Naive UI).

## 2. Content schema (the 5-section format)

Each topic is a Python dict. Output is **繁體中文 (台灣用語)**. The five sections, in order:

| Section | Key | Purpose | Site accent |
|---------|-----|---------|-------------|
| 核心回答 | `core` | 面試開場 3–5 句，直接可講 | amber `#ffb454` |
| 深入原理 | `dive` | 實作/底層 WHY，bullet list | cyan `#56c2ff` |
| 考官可能追問 | `followups` | `(問, 答)` tuples, anticipate follow-ups | purple `#c79cff` |
| 常見陷阱 / 易錯點 | `pitfalls` | bullet list of mistakes | red `#ff6b6b` |
| 結合履歷 | `resume` | Roy's relevant experience (optional) | green `#54dd9b` |

Target: **a candidate can survive a 45–60 min senior backend interview (with follow-ups) using only these notes.**

Topic dict shape (see [topic-module-template.py](topic-module-template.py) for a copy-paste template):

```python
{
    "q": "問題（繁體中文）",
    "core": "核心回答，3–5 句。",
    "dive": ["原理 bullet 1", "原理 bullet 2"],
    "followups": [("追問問題", "簡答"), ("追問 2", "答 2")],
    "pitfalls": ["易錯點 1", "易錯點 2"],
    "resume": "Roy 相關經驗（可省略此 key）。",
}
```

- Use markdown inline `` `code` `` and `**bold**`; fenced code blocks (```go) are supported and rendered with syntax-styled `<pre>`.
- It's fine to author in 简体 then let OpenCC normalize — the generator converts everything to 繁體 (step 5).

## 3. Add & register a new topic module

1. Create `interview-prep/scripts/topics_<tech>.py` exporting an uppercase list, e.g. `KOTLIN_TOPICS = [ ... ]`. (One file may export several lists, like `topics_redis_mysql.py` → `REDIS_TOPICS, MYSQL_TOPICS`.)
2. In `generate_comprehensive.py`: add the import near the other `from topics_* import ...` lines, then add a `write_file(...)` call:

```python
from topics_kotlin import KOTLIN_TOPICS

COUNTS["kotlin"] = write_file(
    "kotlin.md", "Kotlin 面試 Q&A",
    "來源描述（哪些 repo / 實務）",
    KOTLIN_TOPICS,
)
```

3. In `build_site.py`: add a tuple to the `TECHS` list — `(filename, key, display name, short nav label, priority)` where priority is `3` (⭐⭐⭐ core) or `2` (⭐⭐ secondary). Order in this list = order on the site.

```python
("kotlin.md", "kotlin", "Kotlin", "Kotlin", 2),
```

## 4. Generate + 繁體 normalization

Run `python3 scripts/generate_comprehensive.py`. It writes each `<tech>.md` using the header/`fmt()` format and normalizes all CJK text to 繁體 via OpenCC `s2twp`.

The s2twp config + over-conversion correction map live in `generate_comprehensive.py` and must be preserved. OpenCC only touches CJK characters, so Go code in fenced blocks is safe. Known over-conversions corrected:

```python
_CC = opencc.OpenCC("s2twp")
_FIX = {
    "擴充套件": "擴展",   # 扩展 → 不應變成「擴充套件(plugin)」
    "跳錶": "跳表",       # skip list 的「表」誤轉成「錶(watch)」
    "例項": "實例",       # instance 台灣慣用「實例」
    "全域性": "全域",     # 全局 → 不應加上「性」
    "掛瞭": "掛了",       # 了 作語助詞誤轉成「瞭」
}
```

If a new over-conversion appears in output, add a `原誤轉: 正確` pair to `_FIX` (with a comment explaining why) and regenerate.

## 5. Rebuild the site

Run `python3 scripts/build_site.py`. It parses the 5 section markers from each `.md`, embeds all data into `site/assets/data.js` as `window.__IP_DATA__` (so the site works offline via `file://` — no server, no fetch), and rewrites `index.html` (counts/chips auto-update). Then open `site/index.html`.

The CSS and JS in `build_site.py` (`STYLE_CSS`, `APP_JS`) are authored verbatim and self-contained. **Do not change the design system** when adding content — only edit it intentionally per the design spec. See [design-tokens.md](design-tokens.md) for the exact tokens, colors, fonts, and UI features.

## 6. Notion sync (optional)

`prepare_notion_sync.py` maps each `<tech>.md` to a Notion page id and copies content to `/tmp/notion_sync/`. To add a new tech, add its `page_id: "<tech>.md"` entry to the `PAGES` dict, then push via the **user-Notion** MCP. The parent page is linked in `interview-prep/README.md`.

## 7. Update README

Add a row to the 技術分類索引 table in `interview-prep/README.md` (priority stars, name, file link, count), update the total count, and slot the tech into the 讀書順序 if it's a core (⭐⭐⭐) topic.

## Quality gate

- All output is 繁體中文 (台灣用語), normalized — no stray 简体 or over-converted terms.
- Every topic has `core` + `dive` + `followups` + `pitfalls`; high-value topics also have `resume`.
- Answers reach senior depth (原理/WHY), survive follow-ups, and don't duplicate other techs.
- Generator + site build run clean; `site/index.html` opens offline and the new tech appears in the sidebar with the right priority dot and count.
- The design system is unchanged — new content is visually consistent with existing content.

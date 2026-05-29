# Cursor Agent Skills — Resume & Career

This folder contains Cursor agent skills for resume writing, LinkedIn profile optimization, job application workflows, and building backend interview study material. Skills are automatically picked up by Cursor when you're working in this repo.

---

## Skills

### `resume-toolkit`

Resume writing and optimization. Just describe what you need — the agent will auto-load your resume from this repo.

| Task | Example prompt |
|---|---|
| Build resume from scratch | `幫我針對這個 JD 從頭寫一份履歷` |
| Optimize existing resume | `幫我優化履歷，針對這個職缺` |
| Rewrite bullets into achievements | `把這些工作內容改成成就導向的條目` |
| ATS keyword boost | `從這份 JD 提取關鍵字，補強我的履歷` |
| Skill gap analysis | `對比這份 JD，分析我的技能落差` |
| Cover letter | `幫我寫一封求職信` |
| Per-job customization | `針對這個職位客製化我的履歷` |

---

### `linkedin-career-writer`

LinkedIn profile writing and career outreach. Auto-loads your resume for context.

| Task | Example prompt |
|---|---|
| LinkedIn headline | `幫我生成 5 個 LinkedIn 標題` |
| About section | `幫我寫 LinkedIn 的 About 區段` |
| Experience entries | `把我的工作經歷改寫成 LinkedIn 格式` |
| Cold recruiter message | `幫我寫一封冷連絡招募人員的 LinkedIn 訊息` |
| Interview preparation | `針對這份 JD 和我的履歷，幫我準備面試題目和答案` |

---

### `interview-study-builder`

Build senior-level backend interview study notes (繁體中文, 5-section Q&A) and the polished offline "study console" site under `interview-prep/`. Codifies the research → author → generate → build workflow and the fixed design system, so new technologies look identical to existing content.

| Task | Example prompt |
|---|---|
| Add a new technology's interview prep | `幫我新增 Kotlin 的面試筆記` |
| Author topics in the 5-section schema | `幫我把這些 Redis 題目整理成面試筆記格式` |
| Regenerate notes + rebuild study site | `重新生成題庫並重建學習網站` |
| Match the study site design | `用 study site 的設計風格呈現這些內容` |

Supporting files: `design-tokens.md` (exact design system), `topic-module-template.py` (new topic module template).

---

## Resume files in this repo

Skills will auto-detect and load the appropriate file:

- `Roy-Resume-EN.md` — English version
- `Roy-Resume-中文.md` — Chinese version

You can also paste your resume directly in the chat to override.

---

## How skills work

Skills are loaded by Cursor when their trigger keywords appear in the conversation. You don't need to reference them by name — just describe what you want in plain language and Cursor will apply the right skill automatically.

To explicitly invoke a skill, mention it by name: `use resume-toolkit to...`

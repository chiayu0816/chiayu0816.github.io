# Study Site Design Tokens

The exact design system used by `interview-prep/site/` (authored as `STYLE_CSS` / `APP_JS` in `build_site.py`). Reuse these verbatim so new content stays consistent.

## Direction

Technical-editorial **dark "study console"** — near-black canvas, monospace headings, one amber signal accent, atmospheric engineering grid. Commit to it; do not mix in other aesthetics.

## Fonts

- **Headings / brand / code:** `JetBrains Mono` (`--mono`)
- **Body:** `Inter` (`--sans`), with `PingFang TC` / `Microsoft JhengHei` fallbacks for 繁體中文
- Loaded from Google Fonts: `Inter:wght@400;500;600;700` + `JetBrains+Mono:wght@400;500;700`

## CSS variables (`:root`)

```css
--bg:#0a0c11; --bg2:#0d1017; --surface:#13161f; --surface2:#171b25;
--border:#242a36; --border2:#2f3645;
--text:#e7eaf2; --muted:#9aa3b5; --faint:#6b7385;
--accent:#ffb454; --accent-dim:#7a5a26;        /* amber signal accent */
/* 5 answer-section color codes */
--c-core:#ffb454;    /* 核心回答 — amber  */
--c-dive:#56c2ff;    /* 深入原理 — cyan   */
--c-ask:#c79cff;     /* 考官追問 — purple */
--c-trap:#ff6b6b;    /* 常見陷阱 — red    */
--c-resume:#54dd9b;  /* 結合履歷 — green  */
--radius:14px; --radius-sm:9px;
--maxw:1180px;
```

Each answer section is a left-border `.sec sec-<key>` block whose border + label use the matching `--c-*` color.

## Background atmosphere

- Two fixed radial gradients (amber top-left, cyan top-right) over a near-black base.
- `body::before`: faint engineering grid — 46px white lines at ~2.2% opacity, radial-masked so it fades downward. `opacity:.4`.

## Spacing rhythm

- Layout grid: `248px` sidebar + `1fr` content, `34px` gap, `--maxw` 1180px, page padding `26px 22px 90px`.
- Cards: `12px` vertical gap, `radius:14px`. Sections inside answers: `16px` top margin, `14px` left padding.
- Sticky topbar (blur 14px) at top; sidebar sticky at `top:78px`.

## UI features (in `APP_JS`)

- **Sidebar nav by tech** with priority dots (⭐⭐⭐ amber `.p3` / ⭐⭐ cyan) + `done/total` counts; turns green when complete.
- **Live search** with 120ms debounce, query highlight via `<mark>`, auto-expands matching cards; `/` keyboard shortcut focuses the box, `Esc` clears.
- **Collapsible Q&A cards** — click row to expand the 5-section answer; staggered rise-in animation.
- **localStorage progress tracking** (`ipv1:` prefix) — per-question "已複習" checkbox, per-tech progress bar, global progress ring (conic-gradient) in the topbar, reset button.
- **Scrollspy** (IntersectionObserver) highlights the active tech in the sidebar.
- **Responsive** — under 900px the sidebar becomes a horizontal scroll strip, search goes full-width.
- **Accessible** — semantic `<button>`/`<label>`, `aria-label` on search.
- **No framework, fully offline** — data embedded as `data.js` (`window.__IP_DATA__`), opens via `file://`.

## Code blocks

`pre.code` on `#0b0e15`, mono 12.8px `#cfe3ff`, with a small uppercase language tag (`.code-lang`) in the top-right corner. Inline `code` is amber-tinted (`#ffce8a`) on a dark chip.

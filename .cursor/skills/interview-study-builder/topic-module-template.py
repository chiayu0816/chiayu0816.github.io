# -*- coding: utf-8 -*-
"""<Tech> interview topics — N comprehensive Q&A.

Copy to interview-prep/scripts/topics_<tech>.py, rename the list, fill in topics.
Then register in generate_comprehensive.py (import + write_file) and in
build_site.py (TECHS list). Authoring in 简体 is fine — the generator runs
OpenCC s2twp to normalize everything to 繁體中文.

Each topic dict:
  q         (str)   required — 問題
  core      (str)   required — 核心回答，3–5 句
  dive      (list)  required — 深入原理 bullets
  followups (list)  required — [(問, 答), ...] 考官可能追問
  pitfalls  (list)  required — 常見陷阱 / 易錯點 bullets
  resume    (str)   optional — 結合履歷（high-value topics only）
"""

TECH_TOPICS = [
    {
        "q": "範例問題：X 的底層原理是什麼？",
        "core": "面試開場 3–5 句，直接可講的核心回答。先給結論，再點出關鍵機制。",
        "dive": [
            "底層/實作細節 1（WHY，不只是 WHAT）",
            "底層/實作細節 2，可用 `inline code` 與 **粗體**",
        ],
        "followups": [
            ("考官追問 1？", "簡答 1，展現 senior 深度。"),
            ("考官追問 2？", "簡答 2。"),
        ],
        "pitfalls": [
            "常見誤解或易錯點 1",
            "常見誤解或易錯點 2",
        ],
        "resume": "Roy 在某專案的相關實務（撮合/行情/K線/Disruptor 等），可省略整個 key。",
    },
    # ... more topics; aim for high-frequency, senior-level, non-redundant questions.
]

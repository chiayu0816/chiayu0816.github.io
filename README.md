# 後端面試準備 · Senior Backend Interview Prep

繁體中文 Senior Go / Java 後端面試題庫（五段式 Q&A），開源共筆、持續更新。

**線上學習站：** [https://chiayu0816.github.io/](https://chiayu0816.github.io/)

---

## 內容概要

- **223+ 題**，涵蓋 Go、Redis、MySQL、Kafka、RocketMQ、System Design、pprof 等
- 每題：**核心回答 → 深入原理 → 考官追問 → 常見陷阱 → 實務場景**（可選）
- 詳細索引與讀書順序見 [interview-prep/README.md](interview-prep/README.md)

---

## 資料參考來源

編寫與整理時曾參考或受啟發的開源資源（排名不分先後）：

- [golang-design/go-questions](https://github.com/golang-design/go-questions) — [Go 程序员面试笔试宝典](https://golang.design/go-questions)
- [lifei6671/interview-go](https://github.com/lifei6671/interview-go) — Golang 面试题搜集
- [RezaSi/go-interview-practice](https://github.com/RezaSi/go-interview-practice)
- [moabukar/tech-vault](https://github.com/moabukar/tech-vault)

---

## 本機預覽

```bash
pip install -r requirements.txt
cd interview-prep
python3 scripts/generate_comprehensive.py   # 可選：從 topics_*.py 重產 .md
python3 scripts/build_site.py
open site/index.html
```

---

## 更新與部署

1. 編輯 `interview-prep/scripts/topics_*.py`（或對應 `.md`）
2. 執行 `generate_comprehensive.py` → `build_site.py`
3. Push 至 `main` → [GitHub Actions](.github/workflows/deploy-pages.yml) 自動部署至 Pages

---

## 參與貢獻

歡迎透過 Issue / Pull Request 新增題目、勘誤或討論面試經驗。請先閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。

也可使用 [GitHub Discussions](https://github.com/chiayu0816/chiayu0816.github.io/discussions) 交流。

# 後端面試準備 · Senior Backend Interview Prep

繁體中文 Senior Go / Java 後端面試題庫（五段式 Q&A），開源共筆、持續更新。

**線上學習站：** [https://chiayu0816.github.io/](https://chiayu0816.github.io/)

> **站點說明：** 本網址已改為面試準備題庫。舊「CodeLife Chronicles」程式筆記已封存於 [codelife-chronicles-archive](https://github.com/chiayu0816/codelife-chronicles-archive)（tag：`archive/codelife-chronicles-2025`）。

---

## 內容概要

- **223+ 題**，涵蓋 Go、Redis、MySQL、Kafka、RocketMQ、System Design、pprof 等
- 每題：**核心回答 → 深入原理 → 考官追問 → 常見陷阱 → 實務場景**（可選）
- 詳細索引與讀書順序見 [interview-prep/README.md](interview-prep/README.md)

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

更新紀錄見 [CHANGELOG.md](CHANGELOG.md)。

---

## 參與貢獻

歡迎透過 Issue / Pull Request 新增題目、勘誤或討論面試經驗。請先閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。

也可使用 [GitHub Discussions](https://github.com/chiayu0816/chiayu0816.github.io/discussions) 交流。

---

## 倉庫可見性

本倉庫為 **public**（GitHub Free 需公開倉庫才能使用 Pages）。對外只部署 `interview-prep/site/` 靜態學習站。

履歷與個人化面試筆記不在此倉庫；請使用你的 **private** `chiayu0816/resume` 倉庫（若尚未建立，見該 repo 的 README）。

---

## 授權

- 本倉庫腳本：MIT（見 [LICENSE](LICENSE)）
- 題庫內容：CC BY-SA 4.0；彙整來源見 [interview-prep/README.md](interview-prep/README.md)

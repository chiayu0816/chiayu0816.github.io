# 後端面試準備 · Senior Backend Interview Prep

繁體中文 Senior Go / Java 後端面試題庫（五段式 Q&A），含交易所與體育數據實戰脈絡。

**線上學習站：** [https://chiayu0816.github.io/](https://chiayu0816.github.io/)

> **站點說明：** 本網址已改為面試準備題庫。舊「CodeLife Chronicles」程式學習筆記已封存於 [codelife-chronicles-archive](https://github.com/chiayu0816/codelife-chronicles-archive)（tag：`archive/codelife-chronicles-2025`）。

---

## 內容概要

- **223+ 題**，涵蓋 Go、Redis、MySQL、Kafka、RocketMQ、System Design、pprof 等
- 每題：**核心回答 → 深入原理 → 考官追問 → 常見陷阱 → 實務場景**（個人對照可選，預設隱藏）
- 詳細索引與讀書順序見 [interview-prep/README.md](interview-prep/README.md)

---

## 本機預覽

```bash
pip install -r requirements.txt
cd interview-prep
python3 scripts/generate_comprehensive.py   # 可選：從 topics_*.py 重產 .md
INCLUDE_PERSONAL=1 python3 scripts/build_site.py   # 含個人對照；公開站 CI 為 0
open site/index.html
```

學習站頂欄可開啟 **「個人對照」**，顯示 `resume_overlay.py` 中的個人化筆記（僅本機完整 build 時有資料）。

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

本倉庫為 **public**（GitHub Free 方案需公開倉庫才能使用 Pages）。對外網站只部署 `interview-prep/site/`，不會把根目錄的履歷 `.docx` 當靜態檔提供下載；若介意履歷出現在 Git 歷史，可改放私人 fork。

## 授權

- 本倉庫腳本：MIT（見 [LICENSE](LICENSE)）
- 題庫內容：CC BY-SA 4.0；彙整來源見 [interview-prep/README.md](interview-prep/README.md)

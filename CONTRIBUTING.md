# 貢獻指南

感謝願意一起完善後端面試題庫！請以 **Pull Request** 為主（避免直接改 `site/assets/data.js`，會被 `build_site.py` 覆寫）。

---

## 貢獻方式

| 方式 | 適用情境 |
|------|----------|
| [Issue：新增技術/題目](https://github.com/chiayu0816/chiayu0816.github.io/issues/new?template=content-request.md) | 想加新技術領域、但尚未準備 PR |
| [Issue：勘誤](https://github.com/chiayu0816/chiayu0816.github.io/issues/new?template=correction.md) | 答案錯誤、過時、用語問題 |
| [Discussions](https://github.com/chiayu0816/chiayu0816.github.io/discussions) | 面試經驗、讀書順序、非程式變更的討論 |
| Pull Request | 已準備好題目內容或腳本修正 |

---

## 新增或修改題目（建議流程）

1. 在 `interview-prep/scripts/` 新增或編輯 `topics_<tech>.py`，匯出 `TECH_TOPICS` 列表。
2. 每題使用五段式 dict（繁體中文）：

   - `q`：問題
   - `core`：核心回答（3–5 句）
   - `dive`：深入原理（字串列表）
   - `followups`：`[(追問, 答), ...]`
   - `pitfalls`：常見陷阱（字串列表）
   - `resume`：**可選**；實務場景範例即可，請勿寫入可識別個資

3. 在 `generate_comprehensive.py` 加入 `import` 與 `write_file(...)`。
4. 在 `build_site.py` 的 `TECHS` 列表註冊新技術（含 priority 2 或 3）。
5. 本機執行：

   ```bash
   pip install -r requirements.txt
   cd interview-prep
   python3 scripts/generate_comprehensive.py
   python3 scripts/build_site.py
   ```

6. 更新 `interview-prep/README.md` 題數表；若有重大變更，更新根目錄 `CHANGELOG.md`。
7. 開 PR，說明新增/修改範圍與來源（官方文件、書籍、面試回饋等）。

---

## PR 檢查清單

- [ ] 五段式欄位齊全（`resume` 可省略）
- [ ] 繁體中文（台灣用語）；若用簡體撰寫，請跑過 `generate_comprehensive.py` 的 OpenCC 正規化
- [ ] 不與其他技術檔重複同一概念
- [ ] 答案達 Senior 深度（原理與追問），非死記定義
- [ ] 未直接編輯 `site/assets/data.js`
- [ ] `build_site.py` 可成功執行

---

## 行為準則

請遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)：尊重、就事論事、歡迎新手提問。

---

## 維護者

高頻核心技術（Go、Redis、MySQL、System Design 等）由倉庫維護者審閱合併；歡迎社群補充次要技術與勘誤。

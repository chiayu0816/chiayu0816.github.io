# 履歷改進對照與 ATS 建議

## 本次主要變更

| 項目 | 改前 | 改後 | 為何有利 ATS / 面試 |
|------|------|------|---------------------|
| 時間線 | 雷速標示至 Present | 雷速 2023.03–2024.07；克拉 2024.11–至今 | 避免誠信疑慮，時間線可驗證 |
| 克拉科技 | 無 | 完整 6 條量化/關鍵字 bullet | 最新 Go/交易所經歷可被搜到 |
| K 線優化 | 無 | 3–5s → 300–500ms + SP + Redis ZSET | 量化成果，技術深度明確 |
| HRM 系統 | 無 | 全端上線 + Cursor AI + MCP/RAG 等 | 差異化：全端交付 + AI 實戰 |
| 專業摘要 | 無 | 6 行關鍵字摘要 | ATS 首屏匹配率提升 |
| 技能區 | 散落在職稱行 | 獨立 Technical Skills 分類 | 解析器易抓取 Go/Kafka/RocketMQ 等 |
| Goland | 誤拼 | Go (Golang) | 標準關鍵字 |
| 分頁殘留 | 正文出現「1」 | 已移除 | 專業度 |
| 學歷 | 英文缺資策會 | 中英文皆含 III 養成班 | 兩版一致 |
| Team Leader | 英文用 Leader | Tech Lead / 技術負責人 | 常見 JD 搜尋詞 |

---

## ATS 關鍵字清單（已寫入履歷）

**語言與框架：** Go, Golang, Java, Gin, GORM, Spring Boot, Vue 3, Pinia, Vite

**資料與快取：** MySQL, Oracle, Microsoft SQL Server, SQLite, Redis, ZSET, MongoDB, stored procedures

**訊息與 API：** Apache Kafka, Apache RocketMQ, RabbitMQ, gRPC, WebSocket, RESTful API

**領域：** cryptocurrency exchange, order matching, market data, K-line, OHLC, candlestick, liquidity, hedging, sports data, Betradar, HRM

**效能與維運：** pprof, flame graph, high concurrency, low latency, microservices, event-driven, Docker Compose, AWS, CI/CD, Jenkins

**AI（差異化）：** Cursor, MCP, AI agent, hooks, RAG, skills, LLM application

---

## 投遞建議

1. **檔案格式：** 優先送 `.docx` 或依 JD 要求轉 PDF（由 Word 另存，避免排版跑版）。
2. **LinkedIn：** 同步更新任職時間（克拉 2024/11–、雷速至 2024/07）與摘要前 3 行關鍵字。
3. **客製化：** 投交易所職缺時，摘要與克拉區塊置頂；投 Java 體育數據職缺時，強調伊諾/雷速與 Disruptor/Kafka。
4. **AI 職缺：** 可強調 HRM 專案與 MCP/RAG 實作；若 JD 偏純研究崗，避免過度強調 Cursor 而弱化後端核心。

---

## 建議後續可補數字（有則更強）

- 伊諾/雷速：延遲優化後的實際 ms（若可公開）
- 克拉：整體交易服務 QPS、可用性 SLA
- HRM：使用者數、模組數、上線後節省工時（若可量化）

---

## 面試準備（未寫入履歷的內容）

- 2024/08–10 空檔：準備簡短誠實說明（求職/轉換），履歷不必主動寫。
- 部門僅一人維運：可說明 ownership、穩定交付、與 CTO/PM 協作模式；避免在履歷寫資遣或財務原因。
- K 線 / ZSET：準備清洗規則與 score 設計的高層說明（不洩漏內部 schema）。
- HRM：準備架構圖、模組清單、AI 如何加速（MCP/RAG 用在哪些場景）。

---

## 產出檔案

| 檔案 | 說明 |
|------|------|
| `Roy's Resume (中文).docx` | 中文履歷（ATS 版） |
| `Roy's Resume.docx` | 英文履歷（ATS 版） |
| `Roy-Resume-中文.md` | 中文 Markdown 草稿 |
| `Roy-Resume-EN.md` | 英文 Markdown 草稿 |
| `generate_resumes.py` | 可重複產生 docx 的腳本 |
| `RESUME_IMPROVEMENTS.md` | 本對照與建議 |

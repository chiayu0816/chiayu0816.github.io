# 後端面試準備（Senior 深度版）

> Senior Backend Engineer | Go & Java  
> 最後更新：2026-05-29

---

## 使用方式

每題格式（繁體中文）：

```
### Q: [問題]
**核心回答：** （面試開場 3–5 句）
**深入原理：** （實作/底層 WHY）
**考官可能追問：** Q→A
**常見陷阱 / 易錯點：**
**實務場景：** （通用實務脈絡，可選）
```

**目標：** 僅憑此筆記可撐過 45–60 分鐘 Senior Backend 技術面試（含原理追問）。

**已排除前端：** Vue 3、Pinia、Vite、Naive UI

**重新生成題庫（含簡→繁正規化）：** `python3 scripts/generate_comprehensive.py`

**重新生成靜態學習網站：** `python3 scripts/build_site.py` → 開啟 `site/index.html`

---

## 技術分類索引（223 題）

| 優先順序 | 技術 | 檔案 | 題數 |
|--------|------|------|------|
| ⭐⭐⭐ | Go | [go.md](./go.md) | 38 |
| ⭐⭐⭐ | Redis | [redis.md](./redis.md) | 20 |
| ⭐⭐⭐ | MySQL | [mysql.md](./mysql.md) | 21 |
| ⭐⭐⭐ | Kafka | [kafka.md](./kafka.md) | 15 |
| ⭐⭐⭐ | RocketMQ | [rocketmq.md](./rocketmq.md) | 12 |
| ⭐⭐ | gRPC | [grpc.md](./grpc.md) | 12 |
| ⭐⭐ | WebSocket | [websocket.md](./websocket.md) | 12 |
| ⭐⭐ | MongoDB | [mongodb.md](./mongodb.md) | 12 |
| ⭐⭐ | RabbitMQ | [rabbitmq.md](./rabbitmq.md) | 12 |
| ⭐⭐⭐ | System Design | [system-design.md](./system-design.md) | 23 |
| ⭐⭐⭐ | Performance / pprof | [performance-pprof.md](./performance-pprof.md) | 15 |
| ⭐⭐ | Java / Spring Boot | [java-spring-boot.md](./java-spring-boot.md) | 16 |
| ⭐⭐ | Docker / AWS | [docker-aws.md](./docker-aws.md) | 15 |

**合計：223 題 · 約 143 KB 正文**

**最近補充（Senior 重點）：** Go loopvar 捕獲、worker pool / fan-in 手寫題；MySQL 線上 DDL（gh-ost/pt-osc）；System Design 撮合引擎、分散式事務選型、流動性/對沖系統；Java JVM 類載入與雙親委派。

---

## 建議讀書順序（2–3 週）

### 第 1 週：語言 + 資料層（面試核心）

| 天 | 主題 | 題數 | 目標 |
|----|------|------|------|
| 1–2 | Go（GMP/GC/channel/map/sync） | 35 | 能白板講 GMP、GC 三色、channel 關閉語義 |
| 3 | Redis（結構/持久化/叢集/快取問題） | 20 | 能設計 K 線 ZSET + 穿透/擊穿方案 |
| 4 | MySQL（InnoDB/MVCC/索引/日誌） | 20 | 能 EXPLAIN + 講 redo/undo/binlog |
| 5 | Performance / pprof | 15 | 能說 K 線最佳化案例 + 讀 flame graph |
| 6–7 | 複習 + 模擬：每技術抽 5 題口述 | — | 每題 3 分鐘核心回答 + 2 分鐘追問 |

### 第 2 週：訊息 + 協議 + 設計

| 天 | 主題 | 題數 | 目標 |
|----|------|------|------|
| 8 | RocketMQ（交易所實務）+ Kafka 對比 | 12+5 | 講 Tag/事務訊息/ vs Kafka |
| 9 | Kafka（partition/offset/rebalance） | 10 | 補完剩餘 Kafka 題 |
| 10 | gRPC + WebSocket | 24 | 講 streaming、WS 水平擴展 |
| 11 | System Design（交易所/K線/秒殺/一致性） | 20 | 準備 2 個 whiteboard design |
| 12 | RabbitMQ + MongoDB | 24 | 體育資料/legacy 場景 |
| 13–14 | 全真模擬 60 分鐘：Go+Redis+MySQL+Design | — | 錄音自評 |

### 第 3 週（選修/衝刺）

| 天 | 主題 | 題數 | 目標 |
|----|------|------|------|
| 15 | Java / Spring Boot | 15 | Spring Boot 重構 + 事務/AOP 追問 |
| 16 | Docker / AWS | 15 | Docker Compose + RDS/ElastiCache |
| 17–21 | 弱項重讀 + 履歷 STAR 每亮點 5 分鐘 | — | K線/Disruptor/Betradar/notification |

---

## 履歷亮點速記（面試開場）

1. **K 線延遲最佳化**：MySQL SP + index rebuild + Redis ZSET 重構 → 3–5s → 300–500ms  
2. **交易所 sole Go owner**：matching、market data、liquidity、hedging、gRPC/WS/RocketMQ  
3. **體育資料**：Betradar 接入、Kafka、LMAX Disruptor 並行、>1000ms → 亞秒  
4. **生產調優**：pprof、flame graph、Redis 快取穿透修復  
5. **Spring Boot 重構**：Struts → Spring Boot + Jenkins CI/CD  
6. **AI 輔助交付**：Cursor、MCP、agents、RAG（全棧專案）

---

## Notion

同步副本：[面試技術準備](https://www.notion.so/36781d1e116e803c891aed65a942119f) 頁面下各技術子頁。

---

## 參考來源

整理題庫時參考的上游開源專案（自行 clone 即可，無需放進本倉庫）：

- https://github.com/golang-design/go-questions
- https://github.com/lifei6671/interview-go
- https://github.com/moabukar/tech-vault
- https://github.com/RezaSi/go-interview-practice

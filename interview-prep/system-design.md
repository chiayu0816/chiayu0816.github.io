# System Design 面試 Q&A

> 來源：interview-go（architecture/）、tech-vault
> 題數：23 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: 設計高併發加密貨幣交易所後端要考慮什麼？

**核心回答：**
核心：撮合（記憶體 order book）、market data 推送、資產/account 一致性、風控 hedging。架構：gRPC 內部、WS 行情、RocketMQ 事件、MySQL 權威賬本、Redis 熱資料/K線。CAP：分割槽時寧可停 trade 保一致。

**深入原理：**
- matching engine 單執行緒 per symbol
- sequencer 全域序
- idempotent 出入金
- audit trail

**考官可能追問：**
- Q: 撮合延遲？
  - A: 記憶體+無鎖結構
- Q: 峰值？
  - A: MQ 削峰

**常見陷阱 / 易錯點：**
- 雙寫不一致
- 無冪等充值

**結合履歷：**
實務經驗（交易所 Go 主要負責人）：matching、market data、liquidity、hedging、K線最佳化。

---
### Q: K 線（OHLC）系統如何設計？

**核心回答：**
Tick/trade→聚合 candle（1m/5m/1h）；MySQL 權威儲存+SP 聚合；Redis ZSET 熱窗；WS 推 update；duplicate 清洗與 index (symbol,time)。

**深入原理：**
- 滑動視窗聚合
- late tick 修正 candle
- partition by symbol
- read path cache-first

**考官可能追問：**
- Q: 3-5s→300ms？
  - A: SP+index+ZSET
- Q: 歷史查詢？
  - A: MySQL range+分頁

**常見陷阱 / 易錯點：**
- 單 ZSET 全歷史
- 無 unique constraint

**結合履歷：**
實際最佳化案例：SP+index rebuild+Redis ZSET。

---
### Q: 快取與資料庫一致性方案？

**核心回答：**
Cache-Aside 主流：讀 miss 載入寫 cache；寫 DB 刪 cache。強一致：分散式事務、Canal 訂閱 binlog 更新 cache、延遲雙刪。接受最終一致+TTL 兜底。

**深入原理：**
- version stamp
- write-through 寫穿
- read-your-writes 會話粘滯

**考官可能追問：**
- Q: Redis MySQL 不一致視窗？
  - A: 毫秒~秒
- Q: Canal 架構？
  - A: binlog→MQ→cache updater

**常見陷阱 / 易錯點：**
- 先刪 cache 後寫 DB 併發髒讀
- 無 TTL

**結合履歷：**
architecture/0004 類場景：Redis+MySQL K線一致。

---
### Q: 秒殺/突發流量庫存扣減如何設計？

**核心回答：**
Redis 預減庫存+Lua 原子；非同步 MQ 下單；DB 最終扣減；限流熔斷；防超賣：DB WHERE stock>=n + 唯一訂單號冪等。

**深入原理：**
- 分段庫存 hot key 拆分
- queue 排隊
- 靜態化頁面 CDN

**考官可能追問：**
- Q: Redis 扣了 DB 失敗？
  - A: 補償+對賬
- Q: 黃牛？
  - A: 驗證碼+風控

**常見陷阱 / 易錯點：**
- 僅 Redis 無 DB 對賬
- 無冪等重複扣

---
### Q: 關注/粉絲系統如何設計？

**核心回答：**
寫擴散 vs 讀擴散：明星使用者讀擴散（fan-out on read）；普通使用者寫擴散 fan-out on write 到 timeline 快取。混合+分層。

**深入原理：**
- push timeline Redis zset
- pull merge K 路
- Bloom 過濾未關注

**考官可能追問：**
- Q: 千萬粉絲？
  - A: 讀擴散+快取
- Q: 一致性？
  - A: 最終一致

**常見陷阱 / 易錯點：**
- 寫擴散風暴
- 熱點 celebrity

---
### Q: 分散式 ID 生成方案？

**核心回答：**
Snowflake：timestamp+machine+sequence；DB號段；UUID 無序不適合索引；Redis INCR。趨勢遞增利於 B+樹。

**深入原理：**
- clock rollback 處理
- sequence 4096/ms
- biz prefix in ID

**考官可能追問：**
- Q: 全域嚴格遞增？
  - A: DB 或 Redis
- Q: Snowflake 衝突？
  - A: workerId 分配

**常見陷阱 / 易錯點：**
- UUID PK 頁分裂
- 無 workerId 管理

---
### Q: 短連結系統 design？

**核心回答：**
Hash(id) 或 base62 編碼；讀多寫少：Redis cache + DB；301/302；防爬蟲 rate limit；唯一 ID→短碼衝突重 hash。

**深入原理：**
- 62^7 萬億
- 布隆預判存在
- analytics 非同步

**考官可能追問：**
- Q: 衝突？
  - A: 加鹽 rehash
- Q: 過期？
  - A: TTL+lazy delete

**常見陷阱 / 易錯點：**
- 短碼可預測被掃
- 無 cache 打穿 DB

---
### Q: 定時排程系統如何保證準時？

**核心回答：**
時間輪/優先佇列（delay queue）；Worker 池；冪等執行；miss fire 策略（立即補跑 vs skip）；分片排程避免單點。

**深入原理：**
- DB 掃表 vs MQ delay
- clock skew NTP
- leader election 單 scheduler

**考官可能追問：**
- Q: 大量任務？
  - A: 分桶+shard
- Q: 失敗重試？
  - A: exponential backoff

**常見陷阱 / 易錯點：**
- 單執行緒掃全表
- 無冪等重複執行

---
### Q: 系統可用性 99.9% 如何保障？

**核心回答：**
冗餘（多 AZ）、無單點、health check、自動 failover、限流降級、多活/主備、演練 chaos。SLI/SLO/error budget。

**深入原理：**
- bulkhead 艙壁
- circuit breaker
- graceful degradation 非核心關

**考官可能追問：**
- Q: 99.99%？
  - A: 跨 region+自動
- Q: 如何驗證？
  - A: game day

**常見陷阱 / 易錯點：**
- 無容量規劃
- 依賴鏈無 timeout

---
### Q: 可觀測性三支柱？

**核心回答：**
Metrics（RED/USE）、Logs（結構化+traceId）、Traces（OpenTelemetry span）。關聯：traceId 貫穿 log/metric。

**深入原理：**
- Span context propagation
-  exemplars
- SLO burn rate alert

**考官可能追問：**
- Q:  vs 監控？
  - A: Observability 可 ad-hoc 問
- Q: 取樣？
  - A: head/tail sampling

**常見陷阱 / 易錯點：**
- 只有 metrics 無 trace
- log 無 correlation id

---
### Q: Trace 資料模型：Span/Trace ID？

**核心回答：**
Trace 一次請求鏈；Span 單步操作；SpanId parent SpanId；Baggage 傳業務上下文。W3C traceparent header。

**深入原理：**
- server/client span kind
- events vs logs in span
- sampling decision

**考官可能追問：**
- Q: 跨 MQ？
  - A: inject headers in message
- Q: 儲存成本？
  - A: 取樣+TTL

**常見陷阱 / 易錯點：**
- broken trace 無 parent
- PII in baggage

---
### Q: IO 多路複用 select/poll/epoll？

**核心回答：**
單執行緒監聽多 fd 就緒事件。select/poll O(n)；epoll O(1) 事件驅動 edge/level trigger。Go netpoller 類似。

**深入原理：**
- Reactor 模式
- ET 需讀盡 LT 簡單
- C10K 問題

**考官可能追問：**
- Q: Go 如何用？
  - A: netpoll+epoll
- Q: 阻塞 API？
  - A: thread pool offload

**常見陷阱 / 易錯點：**
- LT 未讀盡餓死
- fd 上限

---
### Q: LSM-Tree vs B+ Tree 本質區別？

**核心回答：**
B+Tree 讀優、原地更新（InnoDB）；LSM 寫優、append+merge（RocksDB/Cassandra）。讀需多層 merge 可能放大。

**深入原理：**
- memtable+SSTable
- compaction 寫放大
- bloom filter 減讀

**考官可能追問：**
- Q: 何時 LSM？
  - A: 寫密集時序
- Q: MySQL 用？
  - A: InnoDB B+

**常見陷阱 / 易錯點：**
- LSM 讀延遲 tail
- compaction 阻塞

---
### Q: 體育資料即時管道設計？

**核心回答：**
Betradar ingest→validate→LMAX Disruptor 分類→並行 pipeline→Kafka fan-out→下游 API/Redis。延遲從 >1000ms 最佳化亞秒。

**深入原理：**
- ring buffer 無鎖
- event type handler chain
- backpressure Kafka

**考官可能追問：**
- Q: Disruptor vs channel？
  - A: 更低延遲序
- Q: 峰值賽事？
  - A: horizontal consumer

**常見陷阱 / 易錯點：**
- 單執行緒 bottleneck
- 無 schema 校驗

**結合履歷：**
體育資料實務：Betradar、LMAX Disruptor、Kafka、>1000ms→亞秒。

---
### Q: 通知中心（Email/SMS/Telegram）設計？

**核心回答：**
統一 notification hub：模板+渠道 adapter+MQ 非同步+重試+冪等+限流+preference。交易所場景的 notification hub 即採此設計。

**深入原理：**
- provider failover
- rate limit per channel
- delivery status webhook

**考官可能追問：**
- Q: 事務外發？
  - A: Outbox+MQ
- Q: 轟炸使用者？
  - A: 頻控

**常見陷阱 / 易錯點：**
- 同步傳送阻塞交易
- 無 dedup

---
### Q: API 閘道器 vs 服務網格？

**核心回答：**
Gateway：南北向 TLS/路由/限流/auth。Service mesh（Istio）：東西向 mTLS/telemetry/retry。可並存。

**深入原理：**
- Envoy sidecar
- Kong/APISIX
- gRPC transcoding

**考官可能追問：**
- Q: 小團隊？
  - A: gateway 足夠
- Q: 延遲？
  - A: sidecar 開銷 ms

**常見陷阱 / 易錯點：**
- 閘道器過重業務邏輯
- mesh 過早引入

---
### Q: Event-driven vs Request-driven？

**核心回答：**
Request：同步 query/command。Event：非同步 fact 廣播、解耦、最終一致。交易所：下單 sync；成交 event 驅動下游。

**深入原理：**
- CQRS
- event sourcing
- saga 分散式事務

**考官可能追問：**
- Q: 何時 event？
  - A: 多訂閱者+非同步
- Q: 除錯難？
  - A: trace+correlation

**常見陷阱 / 易錯點：**
- 同步鏈路過長
- event 無 schema 版本

---
### Q: 限流演算法：令牌桶 vs 漏桶？

**核心回答：**
令牌桶允許 burst（Token bucket）；漏桶平滑輸出（Leaky bucket）。滑動視窗計數精確限 QPS。Redis+Lua 分散式限流。

**深入原理：**
- GCRA 演算法
- per user/IP/API
- 429+Retry-After

**考官可能追問：**
- Q: 分散式？
  - A: Redis central
- Q: Warm up？
  - A: token 初始滿

**常見陷阱 / 易錯點：**
- 限流無降級
- 時鐘不同步

---
### Q: 資料分片後跨分片查詢？

**核心回答：**
避免 cross-shard join；全域表/索引表；ES 聚合；Scatter-gather 並行+merge；API 層組裝。

**深入原理：**
- duplicate global dim table
- async ES sync
- cursor pagination

**考官可能追問：**
- Q: 排序分頁？
  - A: seek vs offset
- Q: 事務？
  - A: avoid or saga

**常見陷阱 / 易錯點：**
- shard 內 join 假設
- global sort 記憶體爆

---
### Q: Design review 應覆蓋哪些 checklist？

**核心回答：**
需求 QPS/延遲/一致性；資料模型；失敗模式；擴展路徑；安全；成本；migration；monitoring；on-call runbook。

**深入原理：**
- single point analysis
- CAP 顯式選擇
- load test plan

**考官可能追問：**
- Q: 過度設計？
  - A: MVP+擴展點
- Q: 文件？
  - A: ADR

**常見陷阱 / 易錯點：**
- 無 back-of-envelope 容量
- 忽略 ops

---
### Q: 撮合引擎（Matching Engine）如何設計？order book 結構與單執行緒序列化？

**核心回答：**
撮合核心是 order book：買賣兩側各依價格層級排序，依**價格優先、時間優先**撮合。為確定性與低延遲，每個 symbol 用**單執行緒序列化**處理所有訂單（免鎖），輸入用序號定序，記憶體撮合後輸出成交事件。LMAX Disruptor 是經典實作：ring buffer 單寫多讀、無鎖、機械同情（mechanical sympathy）。

**深入原理：**
- order book：每側用 price→FIFO 佇列的有序結構（紅黑樹/跳表/陣列+map），最優價在頂
- 單執行緒只做記憶體運算，持久化/風控/推送透過事件非同步外移
- event sourcing：所有輸入指令落 log，可重放重建狀態做災難復原
- sequencer 給全域單調序號，保證跨副本一致重放

**考官可能追問：**
- Q: 為什麼單執行緒比多執行緒快？
  - A: 撮合是高頻小操作，鎖競爭與 cache miss 成本高於單執行緒記憶體運算；單寫者免鎖、CPU cache 友善
- Q: 撮合掛了如何復原？
  - A: 從 event log/snapshot 重放到最後序號，確定性保證狀態一致
- Q: 如何水平擴展？
  - A: 按 symbol 分片，不同 symbol 跑在不同 engine 實例

**常見陷阱 / 易錯點：**
- 把持久化/風控放進撮合熱路徑拖慢延遲
- 用浮點數做價格/數量（應改用整數最小單位避免精度誤差）
- 跨 symbol 共享狀態破壞單執行緒假設

**結合履歷：**
在交易所擔任 matching/market data 的主要 Go 負責人，撮合與行情低延遲是核心；體育資料用 LMAX Disruptor 把 >1000ms 降到亞秒，思路相通。

---
### Q: 分散式事務如何選型？2PC / TCC / Saga / 本地訊息表？

**核心回答：**
跨服務/跨庫一致性：2PC（XA）強一致但同步阻塞、協調者單點；TCC（Try-Confirm-Cancel）業務層補償、侵入性高；Saga 長事務拆本地事務+補償，最終一致、適合微服務；本地訊息表/Outbox 把業務與訊息寫進同一本地事務，再非同步投遞 MQ，保證「資料庫改了訊息一定發出」。多數網路服務選最終一致（Saga/Outbox）。

**深入原理：**
- Outbox：同事務寫業務表+outbox 表，CDC/輪詢轉發到 MQ，消費端冪等
- TCC：Try 凍結資源、Confirm 提交、Cancel 釋放；需冪等、空回滾、防懸掛
- Saga：orchestration（中央協調）vs choreography（事件驅動）

**考官可能追問：**
- Q: 交易所扣款+發通知如何保證一致？
  - A: Outbox/事務訊息：扣款與訊息同事務落庫再投遞，消費端冪等
- Q: Saga 補償失敗怎辦？
  - A: 重試+告警+人工對帳，補償需冪等可重入

**常見陷阱 / 易錯點：**
- 用 2PC 扛高併發造成阻塞與協調者單點
- 補償/消費未做冪等導致重複扣款
- 忽略空補償、懸掛、亂序問題

**結合履歷：**
交易所場景用 RocketMQ 事務訊息+冪等保證 trading 狀態與下游通知一致。

---
### Q: 交易所流動性 / 對沖（hedging）系統如何設計？

**核心回答：**
做市/流動性系統聚合多個外部交易所或流動性提供者（LP）報價，內部撮合無法消化的部位（風險敞口）需即時對沖到外部市場控制風險。架構：行情聚合 → 內部定價（加點差 spread）→ 風險引擎算淨敞口 → 對沖執行（下單到外部）→ 部位/盈虧記帳。低延遲與一致性是關鍵。

**深入原理：**
- 報價聚合：多 LP 行情經 WS/gRPC 進來，normalize 後合成內部盤口
- 風險引擎即時計算各 symbol 淨部位，超閾值觸發對沖單
- 對沖執行需考慮滑點、外部交易所限流/延遲、失敗重試與部分成交
- 成交/手續費/盈虧冪等入帳，對帳機制兜底

**考官可能追問：**
- Q: 外部對沖下單失敗如何處理？
  - A: 重試+降級（暫停接單/擴大點差）+告警，敞口不可失控
- Q: 如何控制延遲？
  - A: 行情與下單熱路徑記憶體化、gRPC 內部低延遲、避免同步 IO

**常見陷阱 / 易錯點：**
- 對沖延遲過高造成風險敞口擴大虧損
- 重複對沖/重複記帳（缺冪等）
- 外部行情斷線未降級仍按舊價成交

**結合履歷：**
在交易所負責 liquidity/hedging/market data，理解報價聚合、風險敞口與對沖執行的延遲與一致性需求。

---

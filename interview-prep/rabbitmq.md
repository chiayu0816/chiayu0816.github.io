# RabbitMQ 面試 Q&A

> 來源：tech-vault、體育資料實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: RabbitMQ 核心概念：Exchange/Queue/Binding/Routing Key？

**核心回答：**
Producer 發到 Exchange，按型別路由到 Queue；Binding 繫結 routing key 規則。Consumer 從 Queue 拉或推。AMQP 0-9-1 協議。

**深入原理：**
- Virtual host 隔離
- Channel 複用 TCP 連線
- Message properties headers

**考官可能追問：**
- Q:  vs Kafka？
  - A: Rabbit 傳統 MQ 路由靈活；Kafka log
- Q: Exchange 型別？
  - A: direct/topic/fanout/headers

**常見陷阱 / 易錯點：**
- 訊息直接發 queue（預設 exchange）
- 無 binding 訊息丟失

---
### Q: 四種 Exchange 型別與應用？

**核心回答：**
Direct：精確 routing key。Topic：模式 `sport.*`。Fanout：廣播全繫結 queue。Headers：匹配 headers（少用）。

**深入原理：**
- Topic # 多段
- Fanout 忽略 routing key
- Default exchange direct 到同名 queue

**考官可能追問：**
- Q: 體育資料路由？
  - A: Topic `odds.{sport}.{matchId}`
- Q: 廣播配置？
  - A: Fanout+每服務 queue

**常見陷阱 / 易錯點：**
- Topic 模式寫錯無消費
- Fanout 單 queue 瓶頸

---
### Q: 訊息確認機制（ACK）？

**核心回答：**
Consumer manual ack：處理完 basicAck；失敗 basicNack/reject，requeue 或 DLX。Publisher confirm 等 broker 持久化 ack。

**深入原理：**
- auto ack 可能丟
- prefetch 限流
- multiple ack batch

**考官可能追問：**
- Q: 處理中 crash？
  - A: unack 重投
- Q: confirm 模式？
  - A: 非同步 callback

**常見陷阱 / 易錯點：**
- auto ack+處理失敗丟訊息
- 忘記 ack 堆積

---
### Q: 持久化與 durability？

**核心回答：**
要真正不丟訊息需**三者同時成立**：queue 宣告為 durable（重啟仍存在）、訊息 deliveryMode=2（持久化到磁碟）、Publisher Confirm（等 broker 落盤/複製後才確認）。只設其一仍會丟：durable queue 配 transient 訊息，重啟照樣不見。且**單機持久化 ≠ 高可用**——節點掛掉佇列仍不可用，要 HA 需 quorum queue（Raft 多副本）。

**深入原理：**
- Publisher Confirm 是非同步 ack：broker 持久化（或複製到 quorum 多數）後才回 ack，未 ack 的訊息應重送
- Quorum queue（3.8+，基於 Raft）多副本強一致，取代已 deprecated 的 classic mirrored queue
- lazy queue 直接把訊息落盤、減少記憶體佔用，適合大量堆積；代價是吞吐低於純記憶體
- 持久化只保證『落到該節點磁碟』，跨節點可靠性靠 quorum 複製多數派

**考官可能追問：**
- Q: Quorum queue？
  - A: 3.8+ 推薦高可靠，Raft 多副本
- Q: 效能？
  - A: 持久化+confirm 慢於記憶體，吞吐與可靠性需權衡

**常見陷阱 / 易錯點：**
- durable queue 但訊息 transient 仍丟
- 只持久化不 confirm，落盤前 crash 仍丟
- 磁碟慢阻塞 publish

---
### Q: Dead Letter Exchange（DLX）？

**核心回答：**
Queue 設 x-dead-letter-exchange；訊息 reject/expire/queue滿 進 DLQ。用於重試耗盡、 poison message、延遲（TTL+DLX）。

**深入原理：**
- x-message-ttl
- retry 計數 headers
- DLQ 監控告警

**考官可能追問：**
- Q: 延遲佇列？
  - A: TTL+DLX 到實際 queue
- Q: 無限 retry？
  - A: max-length+DLX

**常見陷阱 / 易錯點：**
- DLQ 無消費堆積
- TTL 精度

---
### Q: Prefetch 與 Consumer 公平排程？

**核心回答：**
basicQos(prefetchCount=n) 限制 unack 訊息數，防一 consumer  hoard。Prefetch=1 最公平但吞吐低。

**深入原理：**
- global qos
- 與 concurrency 配合
- channel 級設定

**考官可能追問：**
- Q: 處理慢 consumer？
  - A: prefetch 小
- Q: 高吞吐？
  - A: prefetch 50-100+

**常見陷阱 / 易錯點：**
- prefetch 0 無限
- 單執行緒 consumer 過多 prefetch

---
### Q: RabbitMQ 叢集與 Quorum Queue？

**核心回答：**
Classic 叢集後設資料共享，queue 單 node（映象已棄）。Quorum queue 基於 Raft 多副本強一致，推薦生產。

**深入原理：**
- Stream plugin 大數據
- Federation/Shovel 跨機房
- Khepri 新後設資料

**考官可能追問：**
- Q: 映象佇列遷移？
  - A: 遷 quorum
- Q: 腦裂？
  - A: quorum 多數派

**常見陷阱 / 易錯點：**
- classic 單點 queue node 掛丟服務
- 跨 DC 映象延遲

---
### Q: RabbitMQ vs Kafka/RocketMQ？

**核心回答：**
Rabbit：低延遲、複雜路由、訊息刪除即無；Kafka/RMQ：log 可回溯、高吞吐。體育資料場景曾用 Rabbit 分發部分資料。

**深入原理：**
- Rabbit 適合 task queue RPC
- Kafka 適合 event stream
- RMQ 中間

**考官可能追問：**
- Q: 何時選 Rabbit？
  - A: 路由靈活、中小吞吐、AMQP
- Q: 訊息回溯？
  - A: Rabbit 消費即刪

**常見陷阱 / 易錯點：**
- Rabbit 當 log 平臺
- 大 backlog 記憶體爆

---
### Q: RPC 模式 with RabbitMQ？

**核心回答：**
Client 發 request queue+correlationId+replyTo；Server 消費回 response queue。需 timeout 與 DLQ。

**深入原理：**
- exclusive reply queue
- Direct reply-to 最佳化
- 與 gRPC 對比

**考官可能追問：**
- Q: 生產還用嗎？
  - A: 微服務多用 gRPC
- Q: 臨時 queue 洩漏？
  - A: auto-delete

**常見陷阱 / 易錯點：**
- correlationId 衝突
- 無 timeout 永久等

---
### Q: RabbitMQ 記憶體/磁碟告警與流控？

**核心回答：**
Memory alarm 阻塞 connection publish；disk free 限制。Monitor queue 長度、ready/unack。Lazy queue 落盤。

**深入原理：**
- vm_memory_high_watermark
- paging 訊息到磁碟
- management API 監控

**考官可能追問：**
- Q: 突發堆積？
  - A: 限流+擴 consumer
- Q: 記憶體滿？
  - A: blocking producers

**常見陷阱 / 易錯點：**
- 無告警 OOM
- 單 queue 百萬訊息

---
### Q: 如何保證訊息順序？

**核心回答：**
單 queue 單 consumer 基本順序；多 consumer 亂序。Sharding：同 key 進同 queue+單 active consumer。

**深入原理：**
- Kafka 式用 sharding key
- requeue 可能亂序
- exclusive consumer

**考官可能追問：**
- Q: 失敗重試順序？
  - A: 順序消費需 suspend
- Q: 並行？
  - A: 多 queue 分 key

**常見陷阱 / 易錯點：**
- 多 consumer 要全域順序
- requeue 插入隊首破壞

---
### Q: RabbitMQ 在體育資料專案中的角色？

**核心回答：**
與 Kafka 並用：Betgenius/Betradar 資料經 REST+Kafka+Rabbit 多通道分發下游，Rabbit 適合特定訂閱路由。

**深入原理：**
- Topic exchange 按 sport
- 與 Redis/MySQL 配合
- legacy 系統 AMQP 整合

**考官可能追問：**
- Q: 為何多 MQ？
  - A: 歷史+不同團隊
- Q: 統一？
  - A: 逐步 Kafka/RMQ

**常見陷阱 / 易錯點：**
- 雙寫不一致
- 運維多套 MQ

**結合履歷：**
體育資料實務：multi-vendor sports data via REST/Kafka/RabbitMQ。

---

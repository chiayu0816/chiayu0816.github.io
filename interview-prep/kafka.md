# Kafka 面試 Q&A

> 來源：interview-go（architecture/0002）、tech-vault
> 題數：15 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: Kafka 整體架構？Broker/Topic/Partition/ZooKeeper(KRaft)？

**核心回答：**
Producer 寫入 Topic 的 Partition；Broker 存 log segment；Consumer Group 每 partition 同一時刻僅一 consumer 讀。後設資料曾依賴 ZK，KRaft 3.3+ 用 Raft 內建 quorum。

**深入原理：**
- Leader partition 處理讀寫
- Follower ISR 同步
- Controller 選舉 broker
- Log segment + index 檔案

**考官可能追問：**
- Q: KRaft 好處？
  - A: 去 ZK 運維簡化
- Q: Partition 數能改嗎？
  - A: 可增加不可減

**常見陷阱 / 易錯點：**
- Partition 過少無法並行消費
- 單訊息過大預設 1MB

---
### Q: Partition 與 Consumer Group 機制？

**核心回答：**
訊息按 key hash 或 round-robin 進 partition，分割槽內有序。Consumer group 內 partition 獨佔消費，scale consumer 不超過 partition 數。Rebalance 時 partition 重新分配。

**深入原理：**
- __consumer_offsets 內部 topic
- Static membership 減 rebalance
- Cooperative sticky assignor

**考官可能追問：**
- Q: Consumer 多於 partition？
  - A: 閒置
- Q: 跨 group 消費？
  - A: 各自獨立 offset

**常見陷阱 / 易錯點：**
- Rebalance 期間 stop-the-world 消費
- 處理慢導致 rebalance 迴圈

**結合履歷：**
Roy 在 Luxons/INNO 用 Kafka 分發體育資料到下游。

---
### Q: Offset 提交策略？

**核心回答：**
Auto commit 預設 5s 可能丟或重複；手動 commit 處理完再 commit 至少一次。Exactly-once 需 transactional + idempotent producer。Seek 可重置位點。

**深入原理：**
- enable.auto.commit=false
- commitSync vs commitAsync
- __consumer_offsets compact

**考官可能追問：**
- Q: 重複消費？
  - A: 冪等或去重表
- Q: 丟訊息？
  - A: commit 前 crash

**常見陷阱 / 易錯點：**
- 非同步 commit 失敗未處理
- auto commit 處理中 rebalance

---
### Q: Kafka 如何保證順序？

**核心回答：**
僅分割槽內有序。全域有序需單 partition（吞吐受限）或 key=業務 id 保同實體有序。Consumer 單執行緒 per partition 處理。

**深入原理：**
- max.in.flight.requests 與順序
- 冪等 producer sequence
- retry 可能亂序需配置

**考官可能追問：**
- Q: 多 partition 訂單狀態？
  - A: key=orderId
- Q: 亂序檢測？
  - A: version 欄位

**常見陷阱 / 易錯點：**
- 多執行緒處理同一 partition
- retry 未設 idempotence

---
### Q: Exactly-once 語義如何實現？

**核心回答：**
Idempotent Producer（PID+sequence 防重）+ Transactions（原子寫多 partition + consumer offset）。read-process-write 鏈需 Kafka Streams 或自己協調。

**深入原理：**
- transactional.id
- commitTransaction
- EOS in streams

**考官可能追問：**
- Q: 與 DB 一致？
  - A: Outbox pattern
- Q: 效能代價？
  - A: 事務協調開銷

**常見陷阱 / 易錯點：**
- 以為預設 exactly-once
- transaction timeout 過短

---
### Q: Rebalance 觸發條件與最佳化？

**核心回答：**
Consumer 加入/離開、partition 數變、session 超時（heartbeat 失敗）、processing 超過 max.poll.interval。最佳化：增大 timeout、減 batch、cooperative rebalance、static group.instance.id。

**深入原理：**
- heartbeat 3s session 45s 預設
- GC pause 導致 missed heartbeat
- incremental cooperative

**考官可能追問：**
- Q: Rebalance listener？
  - A: revoke 前 flush
- Q: 為何 stop consumption？
  - A: 舊協議 revoke 全部

**常見陷阱 / 易錯點：**
- 長處理不 poll
- 過多 consumer 頻繁 join

---
### Q: Kafka vs RocketMQ 對比？

**核心回答：**
Kafka：高吞吐 log 流、生態強、延遲 ms 級。RocketMQ：金融級、Tag 過濾、延遲訊息、事務訊息原生、順序+定時成熟。Roy 交易所用 RocketMQ 交易流。

**深入原理：**
- Kafka pull long poll
- RMQ push/pull 混合
- Kafka 適合大數據 pipeline

**考官可能追問：**
- Q: 選型？
  - A: 日誌/analytics→Kafka；交易/訂單→RMQ
- Q: 都支援事務嗎？
  - A: RMQ 半訊息更業務化

**常見陷阱 / 易錯點：**
- 用 Kafka 當 RPC
- 忽視 Topic 規劃

**結合履歷：**
Roy：交易所 RocketMQ 交易/market flow；體育資料 Kafka 高吞吐分發。

---
### Q: Producer acks 與可靠性？

**核心回答：**
acks=0  fire-and-forget；acks=1 leader 寫成功；acks=all/-1 等 ISR 全部 ack。配合 min.insync.replicas=2 防單點。retries 可能重複需冪等。

**深入原理：**
- unclean.leader.election
- replication.factor
- linger.ms batch 吞吐

**考官可能追問：**
- Q: 訊息丟失場景？
  - A: leader 宕未同步
- Q: 延遲 vs 可靠？
  - A: acks=all + sync

**常見陷阱 / 易錯點：**
- acks=1 且 unclean election
- 未開 idempotence 重試重複

---
### Q: Kafka 儲存機制與 retention？

**核心回答：**
Partition log 追加寫 segment 檔案，順序寫磁碟接近記憶體速度。Retention 按時間或大小刪除舊 segment。Compact topic 保留最新 key。

**深入原理：**
- .log .index .timeindex
- zero-copy sendfile
- 頁快取利用

**考官可能追問：**
- Q: 無限保留？
  - A: 磁碟成本+replay 慢
- Q: Compact 用途？
  - A: changelog KV

**常見陷阱 / 易錯點：**
- 磁碟滿 broker 掛
- 單 broker 無 replication

---
### Q: Consumer lag 如何監控與處理？

**核心回答：**
Lag = log end offset - consumer offset。Burrow 或 Kafka exporter 監控。Lag 增：consumer 慢、partition 少、下游阻塞。擴 partition+consumer、最佳化處理、非同步化。

**深入原理：**
- records-lag-max
- 告警閾值
- dead letter queue

**考官可能追問：**
- Q: Lag 突然 0？
  - A: Consumer 掛了或 offset 跳
- Q: 堆積百萬？
  - A: 臨時擴容+限速

**常見陷阱 / 易錯點：**
- 只加 consumer 不加 partition
- 單條 poison pill 阻塞

---
### Q: Kafka 高吞吐設計要點？

**核心回答：**
Batch + compression（lz4/zstd）、適當 partition 數、頁快取、零複製、consumer fetch 批次。Producer linger.ms 湊 batch。

**深入原理：**
- partition 數≈目標吞吐/單 consumer
- broker num.network.threads
- avoid 過大 message

**考官可能追問：**
- Q: 壓縮選哪種？
  - A: lz4 CPU/比平衡
- Q: Too many partitions？
  - A: 檔案控制代碼+選舉開銷

**常見陷阱 / 易錯點：**
- 單條 flush
- partition=1

---
### Q: Kafka Connect 與 MirrorMaker？

**核心回答：**
Connect 框架 source/sink 聯結器同步 DB/ES。MirrorMaker 2 跨叢集複製。用於 CDC、災備、聚合。

**深入原理：**
- Debezium MySQL binlog
- SMT 轉換
- exactly-once connect 配置

**考官可能追問：**
- Q:  vs Canal？
  - A: Canal 更輕量 MySQL
- Q: 延遲？
  - A: 取決於 batch

**常見陷阱 / 易錯點：**
- Schema 變更未處理
- 迴圈複製

---
### Q: Kafka 安全：SASL/SSL/ACL？

**核心回答：**
SSL 加密傳輸；SASL/SCRAM 認證；ACL 控制 topic 讀寫。Enterprise 常 mTLS + RBAC。

**深入原理：**
- authorizer
- super.users
- audit log

**考官可能追問：**
- Q: Plaintext 內網？
  - A: VPC 仍建議 TLS
- Q: ACL 粒度？
  - A: topic+group

**常見陷阱 / 易錯點：**
- ACL 遺漏 consumer group
- 證書過期

---
### Q: Poison message 如何處理？

**核心回答：**
重試 N 次後進 DLQ（dead letter topic），人工/工具修復。Consumer 記錄 error 不 commit 會卡住 partition——應 skip+DLQ 或 quarantine。

**深入原理：**
- Spring Kafka ErrorHandler
- manual offset skip
- metric 告警 DLQ rate

**考官可能追問：**
- Q: Replay DLQ？
  - A: 獨立 consumer
- Q: Schema 錯？
  - A: Schema Registry 相容

**常見陷阱 / 易錯點：**
- 無限 retry 阻塞
- DLQ 無監控

---
### Q: Kafka 在體育資料場景的角色？

**核心回答：**
Betradar 接入後作為 fan-out 匯流排：odds/live events 寫 topic，多下游 REST/gRPC/DB consumer 獨立擴展。

**深入原理：**
- key=matchId 保序
- 多 topic 按 sport/type
- 與 LMAX Disruptor 內部分類配合

**考官可能追問：**
- Q: 延遲要求 sub-second？
  - A: partition 足夠+consumer 並行
- Q: 峰值賽事？
  - A: auto scale consumer

**常見陷阱 / 易錯點：**
- 單 topic 過大
- consumer 同步 HTTP 阻塞

**結合履歷：**
Roy：Betradar onboarding、Kafka 下游分發、LMAX 降延遲 >1000ms。

---

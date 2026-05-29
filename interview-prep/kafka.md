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

```svg
<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kafka partition 與 consumer group 對應關係">
  <text x="330" y="24" fill="#56c2ff" font-size="13" font-weight="700" text-anchor="middle">Topic（3 partitions） → Consumer Group（2 consumers）</text>
  <g>
    <rect x="40" y="46" width="350" height="30" rx="5" fill="#0d1017" stroke="#2f3645"/>
    <text x="62" y="66" fill="#ffb454" font-size="12">P0</text>
    <rect x="92" y="50" width="44" height="22" fill="#ffb454" opacity="0.85"/><rect x="140" y="50" width="44" height="22" fill="#ffb454" opacity="0.6"/><rect x="188" y="50" width="44" height="22" fill="#ffb454" opacity="0.4"/>
    <rect x="40" y="92" width="350" height="30" rx="5" fill="#0d1017" stroke="#2f3645"/>
    <text x="62" y="112" fill="#ffb454" font-size="12">P1</text>
    <rect x="92" y="96" width="44" height="22" fill="#ffb454" opacity="0.85"/><rect x="140" y="96" width="44" height="22" fill="#ffb454" opacity="0.6"/>
    <rect x="40" y="138" width="350" height="30" rx="5" fill="#0d1017" stroke="#2f3645"/>
    <text x="62" y="158" fill="#ffb454" font-size="12">P2</text>
    <rect x="92" y="142" width="44" height="22" fill="#ffb454" opacity="0.85"/><rect x="140" y="142" width="44" height="22" fill="#ffb454" opacity="0.6"/><rect x="188" y="142" width="44" height="22" fill="#ffb454" opacity="0.4"/>
  </g>
  <text x="334" y="64" fill="#6b7385" font-size="10">offset →</text>
  <rect x="452" y="40" width="190" height="138" rx="8" fill="none" stroke="#c79cff" stroke-width="1.3"/>
  <text x="547" y="58" fill="#c79cff" font-size="11" text-anchor="middle">Consumer Group G1</text>
  <rect x="466" y="70" width="162" height="40" rx="6" fill="#13161f" stroke="#56c2ff" stroke-width="1.4"/>
  <text x="547" y="94" fill="#56c2ff" font-size="12" text-anchor="middle">Consumer 1（P0,P1）</text>
  <rect x="466" y="124" width="162" height="40" rx="6" fill="#13161f" stroke="#56c2ff" stroke-width="1.4"/>
  <text x="547" y="148" fill="#56c2ff" font-size="12" text-anchor="middle">Consumer 2（P2）</text>
  <g stroke="#54dd9b" stroke-width="1.5" marker-end="url(#kf)" fill="none">
    <path d="M390 61 L464 84"/>
    <path d="M390 107 L464 94"/>
    <path d="M390 153 L464 144"/>
  </g>
  <text x="330" y="214" fill="#9aa3b5" font-size="11" text-anchor="middle">分割槽內嚴格有序；同 group 內一個 partition 只給一個 consumer；consumer 數 &gt; partition 數則多的閒置</text>
  <defs><marker id="kf" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#54dd9b"/></marker></defs>
</svg>
```

**考官可能追問：**
- Q: Consumer 多於 partition？
  - A: 閒置
- Q: 跨 group 消費？
  - A: 各自獨立 offset

**常見陷阱 / 易錯點：**
- Rebalance 期間 stop-the-world 消費
- 處理慢導致 rebalance 迴圈

**結合履歷：**
實務上用 Kafka 分發體育資料到多個下游。

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
Kafka 的 exactly-once 不是魔法，而是**冪等 Producer + 事務**兩層疊加：冪等 Producer 讓 broker 以 (PID, partition, sequence) 去重，消除『重試造成單分割槽內重複寫』；事務再把『寫多個 partition + 提交 consumer offset』包成一個原子單位，配合 consumer 端 `isolation.level=read_committed` 只讀已提交訊息。完整的 read-process-write（消費→處理→再產出）EOS 需用 Kafka Streams 或自行以同一個 `transactional.id` 協調。

**深入原理：**
- 冪等：Producer 啟動取得 PID + epoch，broker 為每個 (PID, partition) 維護遞增 sequence，重複或亂序的 sequence 直接丟棄
- 事務：`transactional.id` 跨 session 識別同一邏輯 Producer；beginTransaction/commitTransaction 在 log 寫入 transaction marker，未提交訊息對 read_committed consumer 不可見
- 用 `sendOffsetsToTransaction` 把消費位移與輸出寫入放進同一事務，確保『位移與處理結果同生共死』
- epoch 做 fencing：同 transactional.id 但 epoch 較舊的殭屍 Producer 會被 broker 拒絕，避免重複寫

**考官可能追問：**
- Q: 與 DB 一致？
  - A: Kafka 事務無法跨 DB；用 Outbox pattern 讓業務與訊息同事務落庫再投遞
- Q: 效能代價？
  - A: 事務協調與 marker 寫入有開銷，吞吐下降，需權衡

**常見陷阱 / 易錯點：**
- 以為預設 exactly-once（預設是 at-least-once）
- 只開 idempotence 就以為有跨 partition 原子性（需 transaction）
- transaction timeout 過短導致中斷

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
Kafka：高吞吐 log 流、生態強、延遲 ms 級。RocketMQ：金融級、Tag 過濾、延遲訊息、事務訊息原生、順序+定時成熟。交易所場景常用 RocketMQ 承載交易流。

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
實務經驗：交易所用 RocketMQ 承載交易/market flow；體育資料用 Kafka 高吞吐分發。

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
Kafka 把每個 partition 當成**只能追加（append-only）的 log**，訊息順序寫入 segment 檔；順序寫避免隨機 IO 的尋道成本，吞吐接近記憶體。消費時用**零複製（sendfile）**直接把 page cache 的資料送進 socket，省去 user space 來回複製與 GC 壓力。Retention 以時間或大小**刪除整個舊 segment**（非逐筆刪）；compact topic 則只保留每個 key 的最新值，適合 changelog/KV 快照。

**深入原理：**
- 每個 partition 切成多個 segment：`.log`（訊息）、`.index`（offset→實體位置）、`.timeindex`（時間→offset），查詢用二分搜尋
- 順序寫 + OS page cache：寫入先進 page cache 由 OS 批次刷盤，讀取多半命中 cache，broker 幾乎不碰磁碟隨機 IO
- 零複製 sendfile：資料不經 JVM heap，由 DMA 直送網絡卡，大幅降低 CPU 與 GC 壓力
- retention 以 segment 為刪除單位；compact 由 log cleaner 背景合併，保留每 key 最新值（tombstone 代表刪除）

**考官可能追問：**
- Q: 無限保留？
  - A: 磁碟成本高+replay 慢；常配分層儲存或轉 compact
- Q: Compact 用途？
  - A: 保留每 key 最新值，如 changelog KV、狀態快照

**常見陷阱 / 易錯點：**
- 磁碟滿 broker 掛
- 單 broker 無 replication 丟資料
- 誤以為零複製對壓縮訊息仍生效（需解壓則失效）

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
實務經驗：Betradar onboarding、Kafka 下游分發、LMAX Disruptor 降延遲 >1000ms。

---

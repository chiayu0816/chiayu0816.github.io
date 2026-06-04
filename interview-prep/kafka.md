# Kafka 面試 Q&A

> 來源：interview-go（architecture/0002）、tech-vault
> 題數：15 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: Kafka 整體架構？Broker/Topic/Partition/ZooKeeper(KRaft)？

**核心回答：**
Producer 寫入 Topic 的 Partition；Broker 負責儲存 log segment；Consumer Group 內每個 Partition 同一時刻僅能由同一個 Consumer Group 中的一個 Consumer 讀取。元資料管理過去依賴 ZooKeeper，而在 KRaft 模式（3.3+ 穩定，4.0+ 徹底移除 ZooKeeper）下則使用基於 Raft 協定的內建 Quorum 控制器來管理元資料。

**深入原理：**
- Leader Partition 負責處理所有讀寫請求，Follower Partition 僅從 Leader 同步資料
- ISR (In-Sync Replicas) 維護與 Leader 保持同步的副本集合，用於 Leader 選舉
- Controller Broker 由 KRaft 的 Active Controller 選出，負責管理分割槽狀態與分割區 Leader 選舉
- Log Segment 包含 .log（訊息資料）、.index（偏移量索引）與 .timeindex（時間戳記索引）檔案

**考官可能追問：**
- Q: KRaft 相比 ZooKeeper 的優勢？
  - A: 消除 ZooKeeper 外部依賴，簡化運維；Controller 狀態儲存在內建的 Metadata Log 中，元資料變更同步極快，大幅縮短 Broker 故障時 Partition Leader 的選舉時間，支援百萬級 Partition。
- Q: Partition 數量可以修改嗎？
  - A: 只可以增加，不可以減少。因為減少 Partition 會破壞現有的 Key 雜湊路由規則，導致歷史資料與新資料路由不一致，且資料合併與清理難度極高。

**常見陷阱 / 易錯點：**
- Partition 數量過少會限制 Consumer Group 的並行消費能力
- 單一訊息過大（超過預設的 message.max.bytes = 1MB）會導致寫入失敗，需調整 Broker 與 Producer 配置

---
### Q: Partition 與 Consumer Group 機制？

**核心回答：**
訊息寫入時依據 Key 的 Hash 值或 Round-robin 演演算法進入對應 Partition，保證分割區內有序。Consumer Group 內各 Consumer 獨佔消費分配到的 Partition。當 Consumer 數量增加時可提升並行度，但超過 Partition 數量時多餘的 Consumer 將處於閒置狀態。當 Consumer 加入/離開或 Partition 變動時會觸發 Rebalance 重新分配 Partition。

**深入原理：**
- __consumer_offsets 是內建的 Compacted Topic，記錄每個 Consumer Group 對各 Partition 的消費位移 (Offset)
- Static Membership（設定 group.instance.id）可使 Consumer 重啟時保留原有分配，避免觸發不必要的 Rebalance
- Cooperative Sticky Assignor (CoopStickyAssignor) 採漸進式重分配，重平衡期間僅暫停需遷移的 Partition，避免全域暫停

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
- Q: Consumer 數量多於 Partition 數量會如何？
  - A: 多餘的 Consumer 會處於閒置狀態，浪費系統資源。
- Q: 多個 Consumer Group 消費同一個 Topic 會互相干擾嗎？
  - A: 不會，各 Consumer Group 的消費位移 (Offset) 是各自獨立儲存且互不影響的。
- Q: Kafka 4.0 的 Consumer Group Protocol (KIP-848) 有何改進？
  - A: 將 Rebalance 的協調邏輯從 Client 端移至 Broker 端的 Group Coordinator，徹底消除客戶端的 Stop-The-World (STW) 重平衡，實現真正的增量非同步分配。

**常見陷阱 / 易錯點：**
- 傳統 Eager Rebalance 協議在觸發時會導致所有 Consumer 暫停消費 (Stop-The-World)
- Consumer 處理單次 poll 的訊息時間過長，導致未能在 max.poll.interval.ms 內再次呼叫 poll，會被 Coordinator 判定為掛掉並觸發頻繁的 Rebalance 迴圈

**實務場景：**
例如用 Kafka 分發高吞吐量資料管線到多個下游服務

---
### Q: Offset 提交策略？

**核心回答：**
自動提交 (enable.auto.commit=true，預設每 5 秒) 簡單但易導致訊息遺失或重複消費；手動提交則是在業務邏輯處理完畢後呼叫 commitSync()（同步阻塞，支援自動重試）或 commitAsync()（非同步無阻塞，需配合 Callback 處理失敗，不支援重試）。精確一次 (Exactly-once) 需結合冪等 Producer 與事務。Seek 則可用於重置特定消費位移。

**深入原理：**
- enable.auto.commit=false 關閉自動提交，改由手動控制 offset 確保可靠性
- commitSync() 會因網路波動丟擲異常，需在 catch 區塊中進行處理或記錄，以防 Offset 遺失
- __consumer_offsets 使用 Log Compaction 策略，僅保留每個 Group/Partition 對應的最新 Offset 記錄

**考官可能追問：**
- Q: 如何防止重複消費？
  - A: 在 Consumer 端實作業務冪等機制（如資料庫唯一鍵約束、Redis SETNX 去重表，或檢測狀態機的狀態轉移是否合法）。
- Q: 自動提交下訊息遺失的場景？
  - A: Consumer poll 到一批訊息，自動提交時間已過，背景執行緒完成 commit，但隨後業務處理邏輯丟擲異常或當機，重啟後因 Offset 已更新，導致該批訊息被跳過。

**常見陷阱 / 易錯點：**
- 非同步提交 (commitAsync) 失敗時若直接進行重試，可能會因為訊息覆蓋問題導致較新的 Offset 被舊 Offset 覆蓋
- 在 Consumer Rebalance 觸發前，若有部分訊息處理完畢但尚未提交 Offset，重平衡後會被其他 Consumer 重複消費

---
### Q: Kafka 如何保證訊息順序？

**核心回答：**
Kafka 僅保證「分割區 (Partition) 內訊息有序」。若要實現全域有序，需設定單一 Partition（但會嚴重限制吞吐量），或在 Producer 傳送時指定相同的 Key（如 orderId），使同一業務實體的訊息皆路由至同一個 Partition。消費端則需確保單執行緒處理單一 Partition。

**深入原理：**
- max.in.flight.requests.per.connection 設大於 1 時，若發生重試可能導致 Partition 內訊息亂序
- 啟用冪等性 (enable.idempotence=true) 時，Broker 會依據 PID 和 Sequence Number 去重與排序，即使 max.in.flight 達 5 仍能保證順序
- 在 Consumer 內部若使用多執行緒執行緒池並行處理同一個 Partition 的訊息，會破壞 Partition 內的消費順序性

**考官可能追問：**
- Q: 多個 Partition 下如何處理訂單狀態變更？
  - A: 將訂單 ID 作為 Message Key，確保該訂單的所有狀態變更訊息（建立、支付、出貨）皆進入同一 Partition，由同一個 Consumer 執行緒依序處理。
- Q: 消費者端如何做亂序偵測？
  - A: 在訊息中攜帶版本號 (Version) 或時間戳記，在消費時檢查版本號是否遞增，若發現亂序則暫停消費或將訊息送至暫存區。

**常見陷阱 / 易錯點：**
- 在 Consumer 中將 poll 下來的訊息丟給多執行緒非同步處理，卻在主執行緒提交 Offset，這會同時破壞順序性並造成位移提交混亂
- 重試機制 (retries > 0) 開啟但未開啟冪等性，且 max.in.flight.requests.per.connection > 1，會因 Request 失敗重試導致訊息順序顛倒

---
### Q: Exactly-once 語義如何實現？

**核心回答：**
Kafka 的 Exactly-once 語義 (EOS) 是由**冪等 Producer** 與**事務 (Transaction) 機制**疊加實現：冪等性消除「因重試導致的單分割槽重複寫入」；事務機制則將「寫入多個 Partition」與「提交 Consumer Offset」包裝成一個原子單元，配合 Consumer 端的 `isolation.level=read_committed`，確保消費者僅能讀取已提交的訊息。完整的 read-process-write 模式需藉由同一個 `transactional.id` 來協調。

**深入原理：**
- 冪等：Producer 啟動時取得 Producer ID (PID) 與 Epoch，Broker 為每個 (PID, Partition) 維護遞增的 Sequence Number，重複或跳躍的序號會被拒絕
- 事務：`transactional.id` 跨 Session 識別唯一 Producer 實例；beginTransaction/commitTransaction 會在日誌寫入 Control Batch (Transaction Marker)
- 使用 `sendOffsetsToTransaction` 將消費位移與生產訊息繫結在同一個事務中，確保消費進度與處理結果同生共死
- Epoch Fencing：當具有相同 transactional.id 的新 Producer 實例啟動時，會增加 Epoch，舊的 Producer (Zombie) 的任何請求會被 Broker 拒絕

**考官可能追問：**
- Q: Kafka 事務如何與關係型資料庫的一致性結合？
  - A: Kafka 事務無法跨資料庫。通常採用 Outbox Pattern：業務操作與訊息寫入（暫存在資料庫的 Outbox 表）放在同一個 DB 交易中，再由背景服務讀取 Outbox 表並傳送至 Kafka；或者在消費端實作冪等防重。
- Q: Exactly-once 的效能代價？
  - A: 事務協調器 (Transaction Coordinator) 的引入、二階段提交 (2PC) 的 Transaction Marker 寫入，以及 Consumer 端等待事務完成的延遲，都會使吞吐量有所下降，需要權衡可靠性與效能。

**常見陷阱 / 易錯點：**
- 誤以為 Exactly-once 是預設行為（預設為 At-least-once）
- 僅開啟 enable.idempotence=true 就以為能保證跨分割區寫入的原子性（必須使用 Transaction）
- transaction.timeout.ms 設定過短，導致大批次處理時事務超時被 Broker 自動中止

---
### Q: Rebalance 觸發條件與最佳化？

**核心回答：**
Rebalance 觸發於：Consumer Group 內 Consumer 加入或離開、Topic 的 Partition 數量增加、Group Coordinator 檢測到 Consumer 心跳超時（session.timeout.ms 預設 45s），或 Consumer 兩次 poll 間隔超過 max.poll.interval.ms（預設 5 分鐘）。最佳化策略包括：增大超時時間、降低單次 poll 批次大小、使用 Cooperative Sticky 協議，以及配置靜態成員身份。

**深入原理：**
- Group Coordinator 的選擇：依據 group.id 雜湊值對 __consumer_offsets 分割槽數（預設 50）取模，該分割槽 Leader 所在的 Broker 即為 Coordinator
- 靜態成員身份 (Static Membership)：設定 group.instance.id，Consumer 重啟時不會釋放 Partition，只要在 session.timeout.ms 內重連即可避免 Rebalance
- 增量合作重平衡 (Incremental Cooperative Rebalance)：CooperativeStickyAssignor 將大重平衡拆分為多次小重平衡，未受影響的 Partition 無需停止消費

**考官可能追問：**
- Q: Rebalance Listener 的作用？
  - A: 可在 Consumer 被收回 Partition (onPartitionsRevoked) 前，強制執行 commitSync() 以提交當前消費位移，並清理本地快取，防止重複消費。
- Q: 為什麼傳統 Rebalance 需要 Stop-the-World？
  - A: 舊有的 Eager Rebalance 協議要求所有 Consumer 在重新分配前，必須先釋放所持有的所有 Partition，導致整個 Consumer Group 短暫失去消費能力。

**常見陷阱 / 易錯點：**
- 在 poll 後處理訊息過慢（如呼叫外部慢 API 且無超時保護），導致超過 max.poll.interval.ms，使 Consumer 被判定離線而引發 Rebalance 裝態震盪
- JVM 發生 Full GC 停頓時間過長，導致 Heartbeat 執行緒無法向 Broker 傳送心跳，觸發 session.timeout.ms 的 Rebalance

---
### Q: Kafka vs RocketMQ 儲存模型與設計對比？

**核心回答：**
Kafka 採用 Partition-based 儲存，每個 Partition 對應獨立的實體 Log 檔案，Topic/Partition 數量過多時，會因隨機 I/O 增加及大量檔案描述符限制導致效能急劇下降。RocketMQ 採用 CommitLog-based 儲存，所有 Topic 的訊息皆順序寫入單一全域 CommitLog 檔案中，再由背景執行緒建構 ConsumeQueue 索引，因此能支撐海量 Topic 且效能穩定。

**深入原理：**
- Kafka 的 pull 模式採用長輪詢 (Long Polling)，Consumer 批次拉取訊息；RocketMQ 的 push 模式底層亦為長輪詢封裝
- Kafka 適合大資料量、高吞吐的資料管道 (Pipeline) 與日誌收集；RocketMQ 適合高可靠的金融交易、訂單處理與複雜路由場景
- Kafka 的資料清理 (Retention) 預設是刪除整個舊的 Segment 檔案；RocketMQ 也是以 CommitLog 檔案為單位進行過期清理

**考官可能追問：**
- Q: 如何做選型抉擇？
  - A: 如果是大資料、日誌收集、流式處理（Flink/Spark 整合），首選 Kafka；如果是微服務解耦、訂單交易、需要定時/延遲/事務訊息，首選 RocketMQ。
- Q: 兩者都支援事務嗎？有何差別？
  - A: 都支援。Kafka 事務偏向於資料庫式的 2PC原子性寫入（多個 Partition + Offset 同生共死）；RocketMQ 事務則是「半訊息 (Half Message) + 本地事務回查」，更貼近分散式事務中的最終一致性（Saga/TCC）設計。

**常見陷阱 / 易錯點：**
- 在 Kafka 中宣告數千個 Topic，導致 Broker 端 Page Cache 鎖競爭嚴重，I/O 效能崩潰
- 將 Kafka 當作 RPC 系統使用，忽視了高吞吐設計主要是為了非同步緩衝與流式處理

**實務場景：**
例如：交易/行情繫統使用 RocketMQ 承載交易與行情串流；高吞吐量資料管線使用 Kafka 進行大資料 onboarding 與下游分發

---
### Q: 副本同步機制與 ISR、HW、LEO 原理？

**核心回答：**
LEO (Log End Offset) 指向 Partition 副本中下一條即將寫入的訊息位移；HW (High Watermark) 是分割區的高水位線，代表所有處於 ISR 中的副本皆已同步完成的最末位移，Consumer 僅能消費到 HW 之前的訊息。ISR (In-Sync Replicas) 是與 Leader 保持同步的副本集合，若 Follower 同步落後時間超過 `replica.lag.time.max.ms`，會被踢出 ISR。當 `acks=all` 時，Leader 必須等待 ISR 中所有副本皆同步完成（即 HW 更新至該訊息位移）後，才回覆 Producer 寫入成功。

**深入原理：**
- Leader 負責維護所有 Follower 的 LEO，並依據 ISR 中所有副本的最小 LEO 來更新 Leader HW
- Follower 在向 Leader 傳送 Fetch 請求時，會攜帶自己的 LEO，Leader 藉此得知 Follower 的同步進度
- unclean.leader.election.enable 設為 true 允許非 ISR 中的 Follower 被選舉為 Leader，這能保證可用性，但會造成嚴重資料遺失

**考官可能追問：**
- Q: min.insync.replicas 的作用？
  - A: 當 acks=all 時，定義了最少必須有多少個 ISR 副本寫入成功。如果 ISR 副本數小於此值，Producer 的寫入會被拒絕（丟擲 NotEnoughReplicas 異常），以確保資料的高可靠性。
- Q: ISR 副本被踢出與重新加入的依據？
  - A: 依據 `replica.lag.time.max.ms`。若 Follower 超過此時間未傳送 Fetch 請求，或在此時間內其 LEO 未能追上 Leader LEO，則會被踢出；一旦追上，會被自動加回。

**常見陷阱 / 易錯點：**
- 設定 acks=all 卻將 min.insync.replicas 設為 1，當 Leader 寫入成功但隨即當機時，資料仍會遺失（因無其他副本完成同步）
- 設定 unclean.leader.election.enable=true，在叢集發生分割網路時，舊資料被新選舉的 Leader 覆蓋導致嚴重的資料不一致

---
### Q: Kafka 儲存機制與零複製原理？

**核心回答：**
Kafka 將每個 Partition 當作只准追加 (Append-only) 的 Log 檔案。寫入時利用作業系統的 Page Cache 進行順序寫入，避開磁碟隨機定址。讀取時，Broker 使用**零複製 (Zero-Copy) 技術 (sendfile)**，資料直接在核心空間的 Page Cache 與網絡卡 Buffer 間傳輸，不經過 JVM 使用者空間，免去來回複製與 GC 壓力。索引檔案 (.index/.timeindex) 則使用 **mmap (記憶體對映)** 提升讀寫效能。

**深入原理：**
- 傳統 I/O：磁碟 -> Page Cache -> 使用者 Buffer -> Socket Buffer -> 網絡卡 (4次複製，4次上下文切換)
- 零複製 (sendfile)：磁碟 -> Page Cache -> 網絡卡 (利用 DMA，僅 2 次複製與 2 次上下文切換，不經 CPU 複製)
- mmap 用於索引檔案的讀寫，使 Java 程式碼能像操作記憶體一樣操作磁碟檔案，免去 read/write 系統呼叫開銷

**考官可能追問：**
- Q: 什麼情況下零複製會失效？
  - A: 如果 Broker 需要在傳輸前修改訊息內容（例如在 Broker 端解壓縮訊息、過濾訊息，或進行安全加密），資料必須被載入到 JVM 使用者空間，此時零複製失效。
- Q: Log Compaction 運作方式？
  - A: 背景 Cleaner 執行緒會掃描 Segment，針對同一個 Key，僅保留最新值，舊值被覆蓋。若寫入特殊的 tombstone 標記（Null value），代表刪除該 Key。

**常見陷阱 / 易錯點：**
- 未關注 Broker 磁碟 I/O 頻寬，一旦發生大量歷史訊息 Replay，磁碟讀取佔滿 Page Cache，會嚴重影響即時訊息的寫入效能
- 誤以為 Kafka 的順序寫入是直接寫入實體磁碟，實際上是寫入 OS Page Cache，若伺服器突然斷電且未做副本複製，未刷盤的資料將會遺失

---
### Q: Consumer Lag 如何監控與處理？

**核心回答：**
Lag 定義為分割區的最末偏移量 (LEO) 與 Consumer Group 當前提交的偏移量 (Offset) 之差值（Lag = LEO - Offset）。通常使用 Burrow 或 Kafka Exporter 進行監控。當 Lag 持續增加時，代表消費能力不足（如業務程式碼阻塞、下游系統瓶頸、分割區數量過少）。應採取擴充 Partition 數並同步增加 Consumer 數量、最佳化消費端邏輯（如非同步 I/O）等手段。

**深入原理：**
- 監控指標以 records-lag-max（最大分割槽 Lag）為主，避免平均 Lag 掩蓋了單一分割區的堆積問題
- 死信佇列 (Dead Letter Queue, DLQ)：當遇到格式錯誤等無法處理的毒藥訊息 (Poison Message) 時，應丟擲異常並傳送至 DLQ，隨後 commit 該 Offset，防止分割區被卡死

**考官可能追問：**
- Q: 為何 Lag 指標有時會突然變為 0，但實際上訊息並未處理完？
  - A: 這並非 Consumer 掛掉（Consumer 掛掉時，Offset 不變而 LEO 增加，Lag 會上升），而是因為觸發了 Offset 重置（例如找不到 Offset 時 auto.offset.reset 設為 latest，使 Consumer 直接跳到最新位置），或是 Consumer 程式碼在異常處理中盲目 commit 了最新位移，亦或是 Prometheus 監控指標上報因連線斷開而中斷。
- Q: 如何處理百萬級的突發訊息堆積？
  - A: 臨時擴充 Partition 數量並增加對應的 Consumer 實例；若無法擴分割槽，可讓 Consumer 作為中轉站，快速拉取訊息並傳送至一個臨時的新 Topic（具有更多分割槽），再部署大量臨時消費者消費新 Topic。

**常見陷阱 / 易錯點：**
- 只增加 Consumer 實例而不增加 Partition 數量，因為一個 Partition 同時只能分配給同一個 Group 的一個 Consumer，多出來的實例完全無法發揮分流作用
- 無限制地重試處理失敗的訊息，導致單一「毒藥訊息」阻塞整個 Partition 的消費進度

---
### Q: Kafka 高吞吐量設計要點？

**核心回答：**
Kafka 的高吞吐量建立在：1) 批次傳送與壓縮（Producer 端將訊息暫存於快取，湊成 batch 後統一壓縮並傳送，如 lz4/zstd）；2) 順序寫入與 OS Page Cache（避免磁碟隨機定址）；3) 零複製技術 (sendfile)；4) 分割區 (Partition) 併發模型，使讀寫能分散在多臺 Broker 上。

**深入原理：**
- Producer 端 linger.ms 與 batch.size 引數配合：linger.ms 定義了最長等待時間，batch.size 定義了批次大小上限，滿足其一即傳送
- Broker 端調優：調整 num.network.threads（處理網路請求執行緒數）與 num.io.threads（處理磁碟 I/O 執行緒數）
- Consumer 端使用 fetch.min.bytes 與 fetch.max.wait.ms 來累積批次拉取的資料量，提升傳輸效率

**考官可能追問：**
- Q: 壓縮格式選哪種？
  - A: zstd 壓縮比最高，但 CPU 消耗較大；lz4 壓縮速度極快，在 CPU 消耗與壓縮比之間取得了最佳平衡，推薦在超高吞吐場景下使用。
- Q: Partition 數量越多越好嗎？
  - A: 不是。Partition 數量過多會導致 Broker 開啟過多檔案描述符，且在 Controller 故障時需要花費極長的時間進行分割區 Leader 的選舉，還會增加記憶體開銷。建議單個 Broker 的 Partition 總數控制在幾萬以內。

**常見陷阱 / 易錯點：**
- Producer 未設定 batch.size 或 linger.ms=0，導致每條訊息皆觸發一次網路 Request，吞吐量急劇下降
- Partition 數量設為 1，導致整個 Topic 無法進行橫向擴充，完全喪失併發優勢

---
### Q: Kafka Connect 與 MirrorMaker？

**核心回答：**
Kafka Connect 是用於在 Kafka 與其他系統（如 MySQL、Elasticsearch、S3）之間進行資料整合的宣告式框架，提供 Source 與 Sink 聯結器（例如藉由 Debezium 實現 MySQL Binlog 的 CDC 變更捕獲）。MirrorMaker 2 則基於 Connect 框架，用於在不同的 Kafka 叢集之間進行跨地理位置的雙向或單向 Topic 複製，常用於災難備份與資料聚合。

**深入原理：**
- SMT (Single Message Transforms)：在 Connect 傳輸過程中，對訊息進行輕量級的欄位重新命名、過濾或格式轉換
- Kafka Connect 提供分散式運作模式，能自動在多個 Worker 節點間分配 Task，並藉由內建 Topic 實現 State 與 Offset 的持久化

**考官可能追問：**
- Q: Kafka Connect 與 Canal 的區別？
  - A: Canal 專注於 MySQL 的 Binlog 解析，架構較輕量；Kafka Connect 是一個通用的整合框架，支援數百種異構資料來源，且具備分散式橫向擴充能力。
- Q: 跨叢集複製的延遲如何最佳化？
  - A: 最佳化 MirrorMaker 2 的 producer.linger.ms 與 consumer.fetch.min.bytes，在頻寬利用率與即時性之間取得平衡；同時使用專線降低跨機房網路延遲。

**常見陷阱 / 易錯點：**
- 在進行 MirrorMaker 雙向複製時未配置正確的過濾規則，導致訊息在兩個叢集間迴圈複製，撐爆儲存空間
- 下游資料庫 Schema 變更後，Connect 未配置對應的 Schema Registry 相容策略，導致資料寫入 Sink 時解析失敗阻塞

---
### Q: Kafka 安全：SASL/SSL/ACL？

**核心回答：**
Kafka 提供多層次安全防護：1) SSL/TLS 加密傳輸，防範資料被監聽；2) SASL（如 SASL/PLAIN、SASL/SCRAM）或雙向 TLS (mTLS) 進行使用者端身份認證；3) ACL (Access Control Lists) 進行細粒度的許可權控制，限制特定的 Principal 對指定的 Topic 或 Consumer Group 進行 Read/Write 操作。

**深入原理：**
- Broker 端配置 authorizer.class.name 來啟用 ACL 檢查，許可權資訊儲存於 Metadata 中
- 使用 super.users 設定管理員帳號，使其繞過 ACL 限制，方便維運管理
- 審計日誌 (Audit Log) 監控：開啟 Kafka 的安全通道日誌，追蹤未授權的非法存取嘗試

**考官可能追問：**
- Q: 內網環境仍需要開啟 TLS 嗎？
  - A: 建議開啟。雖然內網有 VPC 隔離，但防範內部惡意洩聽與滿足法規合規性要求（如金融 PCI-DSS）仍需傳輸加密。可藉由硬體加速（如 AES-NI）降低加密效能損耗。
- Q: ACL 的最小授權原則？
  - A: 應精確授權到具體的 Topic（例如 Read 許可權）與該消費者所使用的 Consumer Group ID（例如 Read 許可權），避免使用萬用字元 `*` 導致許可權泛濫。

**常見陷阱 / 易錯點：**
- 設定了 Topic ACL 卻遺漏了 Consumer Group ACL，導致 Consumer 認證透過但無法提交 Offset 而報出 GroupAuthorizationException
- 未對 SSL 憑證設定效期監控，憑證過期導致所有使用者端突然中斷連線

---
### Q: 毒藥訊息 (Poison Message) 如何處理？

**核心回答：**
毒藥訊息指因格式錯誤、Schema 不相容或邏輯缺陷，導致 Consumer 處理時必然丟擲異常且無法恢復的訊息。若不處理，Consumer 會因不 commit offset 而反覆重試，卡死分割區。處理策略：設定最大重試次數，超限後藉由 ErrorHandler 將訊息寫入死信佇列 (DLQ / DLT)，隨後提交當前位移以跳過該訊息。

**深入原理：**
- Spring Kafka 中的 DefaultErrorHandler 與 DeadLetterPublishingRecoverer 配合，自動將重試失敗的訊息傳送至 {topic}-dlt 佇列
- 在非同步處理中，若遇到不合法的資料，應直接捕獲異常並記錄日誌，不可讓異常向上丟擲導致整個 poll 批次被重放

**考官可能追問：**
- Q: 如何重放死信佇列中的訊息？
  - A: 通常會部署一個獨立的 Consumer 訂閱 DLT 進行人工修復或使用專用工具修改格式後重送，不可直接與主業務 Consumer 混用。
- Q: 如何從源頭防範 Schema 變更引起的毒藥訊息？
  - A: 引進 Schema Registry（如 Confluent Schema Registry），在 Producer 傳送前進行 Schema 相容性檢查（如 BACKWARD/FORWARD 相容），強制約束訊息格式。

**常見陷阱 / 易錯點：**
- 在 Consumer 中配置無限重試 (Infinite Retry) 且未設定 DLQ，導致單一訊息卡死整個資料管線
- 死信佇列未設定監控與告警，導致大量毒藥訊息堆積卻無人知曉

---
### Q: Kafka 在體育資料場景的角色？

**核心回答：**
體育資料（如 Betradar 賠率、即時賽事資料）具有高頻率、瞬時峰值的特點。Kafka 作為核心的 Fan-out 分散式匯流排：將 odds/live events 寫入對應 Topic，多個下游消費端（如賠率計算引擎、即時看板推播、歷史歸檔資料庫）各自獨立且非同步地消費，實現讀寫分離與高可用擴充。

**深入原理：**
- 使用 key=matchId，確保同一場賽事的所有即時事件順序進入同一個 Partition，保證下游狀態機處理時不會出現「進球在紅牌之後」的順序錯亂
- 多 Topic 規劃：按運動型別（soccer, basketball）或資料頻率（high-frequency odds vs low-frequency match metadata）劃分 Topic
- 與記憶體內佇列（如 LMAX Disruptor）配合：Consumer 執行緒池拉取 Kafka 資料後快速塞入 Disruptor，以極低延遲進行微服務內部的並行分流與撮合

**考官可能追問：**
- Q: 如何應對秒級以下的極致低延遲要求？
  - A: 1) 增加 Partition 數量以提升消費端並行度；2) 最佳化 Consumer，減少單次 poll 訊息的批次大小，並關閉非必要的非同步落庫，主路徑只做記憶體處理與快取推送。
- Q: 如何應對峰值賽事（如世界盃決賽）的突發流量？
  - A: 在賽前預先擴充 Partition 數量並水平擴展 Consumer 實例；利用 Kafka 的磁碟緩衝能力進行削峰填谷，保護下游脆弱的業務資料庫。

**常見陷阱 / 易錯點：**
- 將所有賽事的所有資料塞進同一個單分割區 Topic，導致消費端完全失去擴充性，造成即時資料嚴重積壓與延遲
- Consumer 在消費執行緒中同步進行耗時的 HTTP 呼叫（如向第三方推送賠率），導致 poll 阻塞，觸發 Rebalance 並引發系統雪崩

**實務場景：**
例如：體育賠率與即時事件資料 onboarding，經由 Kafka 進行下游多通道高可用分發，並最佳化拉取引數以降低即時延遲指標

---

# -*- coding: utf-8 -*-
"""Kafka, RocketMQ, RabbitMQ topics."""

KAFKA_TOPICS = [
    {
        "q": "Kafka 整體架構？Broker/Topic/Partition/ZooKeeper(KRaft)？",
        "core": "Producer 寫入 Topic 的 Partition；Broker 負責儲存 log segment；Consumer Group 內每個 Partition 同一時刻僅能由同一個 Consumer Group 中的一個 Consumer 讀取。元資料管理過去依賴 ZooKeeper，而在 KRaft 模式（3.3+ 穩定，4.0+ 徹底移除 ZooKeeper）下則使用基於 Raft 協定的內建 Quorum 控制器來管理元資料。",
        "dive": [
            "Leader Partition 負責處理所有讀寫請求，Follower Partition 僅從 Leader 同步資料",
            "ISR (In-Sync Replicas) 維護與 Leader 保持同步的副本集合，用於 Leader 選舉",
            "Controller Broker 由 KRaft 的 Active Controller 選出，負責管理分區狀態與分割區 Leader 選舉",
            "Log Segment 包含 .log（訊息數據）、.index（偏移量索引）與 .timeindex（時間戳記索引）檔案"
        ],
        "followups": [
            ("KRaft 相比 ZooKeeper 的優勢？", "消除 ZooKeeper 外部依賴，簡化運維；Controller 狀態儲存在內建的 Metadata Log 中，元資料變更同步極快，大幅縮短 Broker 故障時 Partition Leader 的選舉時間，支援百萬級 Partition。"),
            ("Partition 數量可以修改嗎？", "只可以增加，不可以減少。因為減少 Partition 會破壞現有的 Key 哈希路由規則，導致歷史資料與新資料路由不一致，且資料合併與清理難度極高。")
        ],
        "pitfalls": [
            "Partition 數量過少會限制 Consumer Group 的並行消費能力",
            "單一訊息過大（超過預設的 message.max.bytes = 1MB）會導致寫入失敗，需調整 Broker 與 Producer 配置"
        ]
    },
    {
        "q": "Partition 與 Consumer Group 機制？",
        "core": "訊息寫入時依據 Key 的 Hash 值或 Round-robin 演算法進入對應 Partition，保證分割區內有序。Consumer Group 內各 Consumer 獨佔消費分配到的 Partition。當 Consumer 數量增加時可提升並行度，但超過 Partition 數量時多餘的 Consumer 將處於閒置狀態。當 Consumer 加入/離開或 Partition 變動時會觸發 Rebalance 重新分配 Partition。",
        "dive": [
            "__consumer_offsets 是內建的 Compacted Topic，記錄每個 Consumer Group 對各 Partition 的消費位移 (Offset)",
            "Static Membership（設定 group.instance.id）可使 Consumer 重啟時保留原有分配，避免觸發不必要的 Rebalance",
            "Cooperative Sticky Assignor (CoopStickyAssignor) 採漸進式重分配，重平衡期間僅暫停需遷移的 Partition，避免全域暫停"
        ],
        "followups": [
            ("Consumer 數量多於 Partition 數量會如何？", "多餘的 Consumer 會處於閒置狀態，浪費系統資源。"),
            ("多個 Consumer Group 消費同一個 Topic 會互相干擾嗎？", "不會，各 Consumer Group 的消費位移 (Offset) 是各自獨立儲存且互不影響的。"),
            ("Kafka 4.0 的 Consumer Group Protocol (KIP-848) 有何改進？", "將 Rebalance 的協調邏輯從 Client 端移至 Broker 端的 Group Coordinator，徹底消除客戶端的 Stop-The-World (STW) 重平衡，實現真正的增量非同步分配。")
        ],
        "pitfalls": [
            "傳統 Eager Rebalance 協議在觸發時會導致所有 Consumer 暫停消費 (Stop-The-World)",
            "Consumer 處理單次 poll 的訊息時間過長，導致未能在 max.poll.interval.ms 內再次呼叫 poll，會被 Coordinator 判定為掛掉並觸發頻繁的 Rebalance 循環"
        ],
        "svg": """
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
  <text x="330" y="214" fill="#9aa3b5" font-size="11" text-anchor="middle">分區內嚴格有序；同 group 內一個 partition 只給一個 consumer；consumer 數 &gt; partition 數則多的閒置</text>
  <defs><marker id="kf" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#54dd9b"/></marker></defs>
</svg>
""".strip(),
        "scenario": "例如用 Kafka 分發高吞吐量資料管線到多個下游服務"
    },
    {
        "q": "Offset 提交策略？",
        "core": "自動提交 (enable.auto.commit=true，預設每 5 秒) 簡單但易導致訊息遺失或重複消費；手動提交則是在業務邏輯處理完畢後呼叫 commitSync()（同步阻塞，支援自動重試）或 commitAsync()（非同步無阻塞，需配合 Callback 處理失敗，不支援重試）。精確一次 (Exactly-once) 需結合冪等 Producer 與事務。Seek 則可用於重置特定消費位移。",
        "dive": [
            "enable.auto.commit=false 關閉自動提交，改由手動控制 offset 確保可靠性",
            "commitSync() 會因網路波動拋出異常，需在 catch 區塊中進行處理或記錄，以防 Offset 遺失",
            "__consumer_offsets 使用 Log Compaction 策略，僅保留每個 Group/Partition 對應的最新 Offset 記錄"
        ],
        "followups": [
            ("如何防止重複消費？", "在 Consumer 端實作業務冪等機制（如資料庫唯一鍵約束、Redis SETNX 去重表，或檢測狀態機的狀態轉移是否合法）。"),
            ("自動提交下訊息遺失的場景？", "Consumer poll 到一批訊息，自動提交時間已過，背景執行緒完成 commit，但隨後業務處理邏輯拋出異常或當機，重啟後因 Offset 已更新，導致該批訊息被跳過。")
        ],
        "pitfalls": [
            "非同步提交 (commitAsync) 失敗時若直接進行重試，可能會因為訊息覆蓋問題導致較新的 Offset 被舊 Offset 覆蓋",
            "在 Consumer Rebalance 觸發前，若有部分訊息處理完畢但尚未提交 Offset，重平衡後會被其他 Consumer 重複消費"
        ]
    },
    {
        "q": "Kafka 如何保證訊息順序？",
        "core": "Kafka 僅保證「分割區 (Partition) 內訊息有序」。若要實現全域有序，需設定單一 Partition（但會嚴重限制吞吐量），或在 Producer 發送時指定相同的 Key（如 orderId），使同一業務實體的訊息皆路由至同一個 Partition。消費端則需確保單執行緒處理單一 Partition。",
        "dive": [
            "max.in.flight.requests.per.connection 設大於 1 時，若發生重試可能導致 Partition 內訊息亂序",
            "啟用冪等性 (enable.idempotence=true) 時，Broker 會依據 PID 和 Sequence Number 去重與排序，即使 max.in.flight 達 5 仍能保證順序",
            "在 Consumer 內部若使用多執行緒執行緒池並行處理同一個 Partition 的訊息，會破壞 Partition 內的消費順序性"
        ],
        "followups": [
            ("多個 Partition 下如何處理訂單狀態變更？", "將訂單 ID 作為 Message Key，確保該訂單的所有狀態變更訊息（創建、支付、出貨）皆進入同一 Partition，由同一個 Consumer 執行緒依序處理。"),
            ("消費者端如何做亂序偵測？", "在訊息中攜帶版本號 (Version) 或時間戳記，在消費時檢查版本號是否遞增，若發現亂序則暫停消費或將訊息送至暫存區。")
        ],
        "pitfalls": [
            "在 Consumer 中將 poll 下來的訊息丟給多執行緒非同步處理，卻在主執行緒提交 Offset，這會同時破壞順序性並造成位移提交混亂",
            "重試機制 (retries > 0) 開啟但未開啟冪等性，且 max.in.flight.requests.per.connection > 1，會因 Request 失敗重試導致訊息順序顛倒"
        ]
    },
    {
        "q": "Exactly-once 語義如何實現？",
        "core": "Kafka 的 Exactly-once 語義 (EOS) 是由**冪等 Producer** 與**事務 (Transaction) 機制**疊加實現：冪等性消除「因重試導致的單分區重複寫入」；事務機制則將「寫入多個 Partition」與「提交 Consumer Offset」包裝成一個原子單元，配合 Consumer 端的 `isolation.level=read_committed`，確保消費者僅能讀取已提交的訊息。完整的 read-process-write 模式需藉由同一個 `transactional.id` 來協調。",
        "dive": [
            "冪等：Producer 啟動時取得 Producer ID (PID) 與 Epoch，Broker 為每個 (PID, Partition) 維護遞增的 Sequence Number，重複或跳躍的序號會被拒絕",
            "事務：`transactional.id` 跨 Session 識別唯一 Producer 實例；beginTransaction/commitTransaction 會在日誌寫入 Control Batch (Transaction Marker)",
            "使用 `sendOffsetsToTransaction` 將消費位移與生產訊息綁定在同一個事務中，確保消費進度與處理結果同生共死",
            "Epoch Fencing：當具有相同 transactional.id 的新 Producer 實例啟動時，會增加 Epoch，舊的 Producer (Zombie) 的任何請求會被 Broker 拒絕"
        ],
        "followups": [
            ("Kafka 事務如何與關係型資料庫的一致性結合？", "Kafka 事務無法跨資料庫。通常採用 Outbox Pattern：業務操作與訊息寫入（暫存在資料庫的 Outbox 表）放在同一個 DB 交易中，再由背景服務讀取 Outbox 表並發送至 Kafka；或者在消費端實作冪等防重。"),
            ("Exactly-once 的效能代價？", "事務協調器 (Transaction Coordinator) 的引入、二階段提交 (2PC) 的 Transaction Marker 寫入，以及 Consumer 端等待事務完成的延遲，都會使吞吐量有所下降，需要權衡可靠性與效能。")
        ],
        "pitfalls": [
            "誤以為 Exactly-once 是預設行為（預設為 At-least-once）",
            "僅開啟 enable.idempotence=true 就以為能保證跨分割區寫入的原子性（必須使用 Transaction）",
            "transaction.timeout.ms 設定過短，導致大批次處理時事務超時被 Broker 自動中止"
        ]
    },
    {
        "q": "Rebalance 觸發條件與優化？",
        "core": "Rebalance 觸發於：Consumer Group 內 Consumer 加入或離開、Topic 的 Partition 數量增加、Group Coordinator 檢測到 Consumer 心跳超時（session.timeout.ms 預設 45s），或 Consumer 兩次 poll 間隔超過 max.poll.interval.ms（預設 5 分鐘）。優化策略包括：增大超時時間、降低單次 poll 批次大小、使用 Cooperative Sticky 協議，以及配置靜態成員身份。",
        "dive": [
            "Group Coordinator 的選擇：依據 group.id 哈希值對 __consumer_offsets 分區數（預設 50）取模，該分區 Leader 所在的 Broker 即為 Coordinator",
            "靜態成員身份 (Static Membership)：設定 group.instance.id，Consumer 重啟時不會釋放 Partition，只要在 session.timeout.ms 內重連即可避免 Rebalance",
            "增量合作重平衡 (Incremental Cooperative Rebalance)：CooperativeStickyAssignor 將大重平衡拆分為多次小重平衡，未受影響的 Partition 無需停止消費"
        ],
        "followups": [
            ("Rebalance Listener 的作用？", "可在 Consumer 被收回 Partition (onPartitionsRevoked) 前，強制執行 commitSync() 以提交當前消費位移，並清理本地快取，防止重複消費。"),
            ("為什麼傳統 Rebalance 需要 Stop-the-World？", "舊有的 Eager Rebalance 協議要求所有 Consumer 在重新分配前，必須先釋放所持有的所有 Partition，導致整個 Consumer Group 短暫失去消費能力。")
        ],
        "pitfalls": [
            "在 poll 後處理訊息過慢（如呼叫外部慢 API 且無超時保護），導致超過 max.poll.interval.ms，使 Consumer 被判定離線而引發 Rebalance 裝態震盪",
            "JVM 發生 Full GC 停頓時間過長，導致 Heartbeat 執行緒無法向 Broker 發送心跳，觸發 session.timeout.ms 的 Rebalance"
        ]
    },
    {
        "q": "Kafka vs RocketMQ 儲存模型與設計對比？",
        "core": "Kafka 採用 Partition-based 儲存，每個 Partition 對應獨立的實體 Log 檔案，Topic/Partition 數量過多時，會因隨機 I/O 增加及大量檔案描述符限制導致效能急劇下降。RocketMQ 採用 CommitLog-based 儲存，所有 Topic 的訊息皆順序寫入單一全域 CommitLog 檔案中，再由背景執行緒建構 ConsumeQueue 索引，因此能支撐海量 Topic 且效能穩定。",
        "dive": [
            "Kafka 的 pull 模式採用長輪詢 (Long Polling)，Consumer 批次拉取訊息；RocketMQ 的 push 模式底層亦為長輪詢封裝",
            "Kafka 適合大數據量、高吞吐的數據管道 (Pipeline) 與日誌收集；RocketMQ 適合高可靠的金融交易、訂單處理與複雜路由場景",
            "Kafka 的數據清理 (Retention) 預設是刪除整個舊的 Segment 檔案；RocketMQ 也是以 CommitLog 檔案為單位進行過期清理"
        ],
        "followups": [
            ("如何做選型抉擇？", "如果是大數據、日誌收集、流式處理（Flink/Spark 整合），首選 Kafka；如果是微服務解耦、訂單交易、需要定時/延遲/事務訊息，首選 RocketMQ。"),
            ("兩者都支援事務嗎？有何差別？", "都支援。Kafka 事務偏向於資料庫式的 2PC原子性寫入（多個 Partition + Offset 同生共死）；RocketMQ 事務則是「半訊息 (Half Message) + 本地事務回查」，更貼近分散式事務中的最終一致性（Saga/TCC）設計。")
        ],
        "pitfalls": [
            "在 Kafka 中宣告數千個 Topic，導致 Broker 端 Page Cache 鎖競爭嚴重，I/O 效能崩潰",
            "將 Kafka 當作 RPC 系統使用，忽視了高吞吐設計主要是為了非同步緩衝與流式處理"
        ],
        "scenario": "例如：交易/行情系統使用 RocketMQ 承載交易與行情串流；高吞吐量資料管線使用 Kafka 進行大數據 onboarding 與下游分發"
    },
    {
        "q": "副本同步機制與 ISR、HW、LEO 原理？",
        "core": "LEO (Log End Offset) 指向 Partition 副本中下一條即將寫入的訊息位移；HW (High Watermark) 是分割區的高水位線，代表所有處於 ISR 中的副本皆已同步完成的最末位移，Consumer 僅能消費到 HW 之前的訊息。ISR (In-Sync Replicas) 是與 Leader 保持同步的副本集合，若 Follower 同步落後時間超過 `replica.lag.time.max.ms`，會被踢出 ISR。當 `acks=all` 時，Leader 必須等待 ISR 中所有副本皆同步完成（即 HW 更新至該訊息位移）後，才回覆 Producer 寫入成功。",
        "dive": [
            "Leader 負責維護所有 Follower 的 LEO，並依據 ISR 中所有副本的最小 LEO 來更新 Leader HW",
            "Follower 在向 Leader 發送 Fetch 請求時，會攜帶自己的 LEO，Leader 藉此得知 Follower 的同步進度",
            "unclean.leader.election.enable 設為 true 允許非 ISR 中的 Follower 被選舉為 Leader，這能保證可用性，但會造成嚴重資料遺失"
        ],
        "followups": [
            ("min.insync.replicas 的作用？", "當 acks=all 時，定義了最少必須有多少個 ISR 副本寫入成功。如果 ISR 副本數小於此值，Producer 的寫入會被拒絕（拋出 NotEnoughReplicas 異常），以確保資料的高可靠性。"),
            ("ISR 副本被踢出與重新加入的依據？", "依據 `replica.lag.time.max.ms`。若 Follower 超過此時間未發送 Fetch 請求，或在此時間內其 LEO 未能追上 Leader LEO，則會被踢出；一旦追上，會被自動加回。")
        ],
        "pitfalls": [
            "設定 acks=all 卻將 min.insync.replicas 設為 1，當 Leader 寫入成功但隨即當機時，資料仍會遺失（因無其他副本完成同步）",
            "設定 unclean.leader.election.enable=true，在叢集發生分割網路時，舊資料被新選舉的 Leader 覆蓋導致嚴重的資料不一致"
        ]
    },
    {
        "q": "Kafka 儲存機制與零拷貝原理？",
        "core": "Kafka 將每個 Partition 當作只准追加 (Append-only) 的 Log 檔案。寫入時利用作業系統的 Page Cache 進行順序寫入，避開磁碟隨機定址。讀取時，Broker 使用**零拷貝 (Zero-Copy) 技術 (sendfile)**，資料直接在核心空間的 Page Cache 與網卡 Buffer 間傳輸，不經過 JVM 使用者空間，免去來回拷貝與 GC 壓力。索引檔案 (.index/.timeindex) 則使用 **mmap (記憶體映射)** 提升讀寫效能。",
        "dive": [
            "傳統 I/O：磁碟 -> Page Cache -> 使用者 Buffer -> Socket Buffer -> 網卡 (4次拷貝，4次上下文切換)",
            "零拷貝 (sendfile)：磁碟 -> Page Cache -> 網卡 (利用 DMA，僅 2 次拷貝與 2 次上下文切換，不經 CPU 拷貝)",
            "mmap 用於索引檔案的讀寫，使 Java 程式碼能像操作記憶體一樣操作磁碟檔案，免去 read/write 系統呼叫開銷"
        ],
        "followups": [
            ("什麼情況下零拷貝會失效？", "如果 Broker 需要在傳輸前修改訊息內容（例如在 Broker 端解壓縮訊息、過濾訊息，或進行安全加密），資料必須被載入到 JVM 使用者空間，此時零拷貝失效。"),
            ("Log Compaction 運作方式？", "背景 Cleaner 執行緒會掃描 Segment，針對同一個 Key，僅保留最新值，舊值被覆蓋。若寫入特殊的 tombstone 標記（Null value），代表刪除該 Key。")
        ],
        "pitfalls": [
            "未關注 Broker 磁碟 I/O 頻寬，一旦發生大量歷史訊息 Replay，磁碟讀取佔滿 Page Cache，會嚴重影響即時訊息的寫入效能",
            "誤以為 Kafka 的順序寫入是直接寫入實體磁碟，實際上是寫入 OS Page Cache，若伺服器突然斷電且未做副本複製，未刷盤的資料將會遺失"
        ]
    },
    {
        "q": "Consumer Lag 如何監控與處理？",
        "core": "Lag 定義為分割區的最末偏移量 (LEO) 與 Consumer Group 當前提交的偏移量 (Offset) 之差值（Lag = LEO - Offset）。通常使用 Burrow 或 Kafka Exporter 進行監控。當 Lag 持續增加時，代表消費能力不足（如業務代碼阻塞、下游系統瓶頸、分割區數量過少）。應採取擴充 Partition 數並同步增加 Consumer 數量、優化消費端邏輯（如非同步 I/O）等手段。",
        "dive": [
            "監控指標以 records-lag-max（最大分區 Lag）為主，避免平均 Lag 掩蓋了單一分割區的堆積問題",
            "死信佇列 (Dead Letter Queue, DLQ)：當遇到格式錯誤等無法處理的毒藥訊息 (Poison Message) 時，應拋出異常並發送至 DLQ，隨後 commit 該 Offset，防止分割區被卡死"
        ],
        "followups": [
            ("為何 Lag 指標有時會突然變為 0，但實際上訊息並未處理完？", "這並非 Consumer 掛掉（Consumer 掛掉時，Offset 不變而 LEO 增加，Lag 會上升），而是因為觸發了 Offset 重置（例如找不到 Offset 時 auto.offset.reset 設為 latest，使 Consumer 直接跳到最新位置），或是 Consumer 程式碼在異常處理中盲目 commit 了最新位移，亦或是 Prometheus 監控指標上報因連線斷開而中斷。"),
            ("如何處理百萬級的突發訊息堆積？", "臨時擴充 Partition 數量並增加對應的 Consumer 實例；若無法擴分區，可讓 Consumer 作為中轉站，快速拉取訊息並發送至一個臨時的新 Topic（具有更多分區），再部署大量臨時消費者消費新 Topic。")
        ],
        "pitfalls": [
            "只增加 Consumer 實例而不增加 Partition 數量，因為一個 Partition 同時只能分配給同一個 Group 的一個 Consumer，多出來的實例完全無法發揮分流作用",
            "無限制地重試處理失敗的訊息，導致單一「毒藥訊息」阻塞整個 Partition 的消費進度"
        ]
    },
    {
        "q": "Kafka 高吞吐量設計要點？",
        "core": "Kafka 的高吞吐量建立在：1) 批次發送與壓縮（Producer 端將訊息暫存於快取，凑成 batch 後統一壓縮並發送，如 lz4/zstd）；2) 順序寫入與 OS Page Cache（避免磁碟隨機定址）；3) 零拷貝技術 (sendfile)；4) 分割區 (Partition) 併發模型，使讀寫能分散在多台 Broker 上。",
        "dive": [
            "Producer 端 linger.ms 與 batch.size 參數配合：linger.ms 定義了最長等待時間，batch.size 定義了批次大小上限，滿足其一即發送",
            "Broker 端調優：調整 num.network.threads（處理網路請求執行緒數）與 num.io.threads（處理磁碟 I/O 執行緒數）",
            "Consumer 端使用 fetch.min.bytes 與 fetch.max.wait.ms 來累積批次拉取的資料量，提升傳輸效率"
        ],
        "followups": [
            ("壓縮格式選哪種？", "zstd 壓縮比最高，但 CPU 消耗較大；lz4 壓縮速度極快，在 CPU 消耗與壓縮比之間取得了最佳平衡，推薦在超高吞吐場景下使用。"),
            ("Partition 數量越多越好嗎？", "不是。Partition 數量過多會導致 Broker 開啟過多檔案描述符，且在 Controller 故障時需要花費極長的時間進行分割區 Leader 的選舉，還會增加記憶體開銷。建議單個 Broker 的 Partition 總數控制在幾萬以內。")
        ],
        "pitfalls": [
            "Producer 未設定 batch.size 或 linger.ms=0，導致每條訊息皆觸發一次網路 Request，吞吐量急劇下降",
            "Partition 數量設為 1，導致整個 Topic 無法進行橫向擴充，完全喪失併發優勢"
        ]
    },
    {
        "q": "Kafka Connect 與 MirrorMaker？",
        "core": "Kafka Connect 是用於在 Kafka 與其他系統（如 MySQL、Elasticsearch、S3）之間進行資料整合的宣告式框架，提供 Source 與 Sink 連接器（例如藉由 Debezium 實現 MySQL Binlog 的 CDC 變更捕獲）。MirrorMaker 2 則基於 Connect 框架，用於在不同的 Kafka 叢集之間進行跨地理位置的雙向或單向 Topic 複製，常用於災難備份與資料聚合。",
        "dive": [
            "SMT (Single Message Transforms)：在 Connect 傳輸過程中，對訊息進行輕量級的欄位重命名、過濾或格式轉換",
            "Kafka Connect 提供分散式運作模式，能自動在多個 Worker 節點間分配 Task，並藉由內建 Topic 實現 State 與 Offset 的持久化"
        ],
        "followups": [
            ("Kafka Connect 與 Canal 的區別？", "Canal 專注於 MySQL 的 Binlog 解析，架構較輕量；Kafka Connect 是一個通用的整合框架，支援數百種異構資料來源，且具備分散式橫向擴充能力。"),
            ("跨叢集複製的延遲如何優化？", "優化 MirrorMaker 2 的 producer.linger.ms 與 consumer.fetch.min.bytes，在頻寬利用率與即時性之間取得平衡；同時使用專線降低跨機房網路延遲。")
        ],
        "pitfalls": [
            "在進行 MirrorMaker 雙向複製時未配置正確的過濾規則，導致訊息在兩個叢集間循環複製，撐爆儲存空間",
            "下游資料庫 Schema 變更後，Connect 未配置對應的 Schema Registry 兼容策略，導致資料寫入 Sink 時解析失敗阻塞"
        ]
    },
    {
        "q": "Kafka 安全：SASL/SSL/ACL？",
        "core": "Kafka 提供多層次安全防護：1) SSL/TLS 加密傳輸，防範資料被監聽；2) SASL（如 SASL/PLAIN、SASL/SCRAM）或雙向 TLS (mTLS) 進行用戶端身份認證；3) ACL (Access Control Lists) 進行細粒度的權限控制，限制特定的 Principal 對指定的 Topic 或 Consumer Group 進行 Read/Write 操作。",
        "dive": [
            "Broker 端配置 authorizer.class.name 來啟用 ACL 檢查，權限資訊儲存於 Metadata 中",
            "使用 super.users 設定管理員帳號，使其繞過 ACL 限制，方便維運管理",
            "審計日誌 (Audit Log) 監控：開啟 Kafka 的安全通道日誌，追蹤未授權的非法存取嘗試"
        ],
        "followups": [
            ("內網環境仍需要開啟 TLS 嗎？", "建議開啟。雖然內網有 VPC 隔離，但防範內部惡意洩聽與滿足法規合規性要求（如金融 PCI-DSS）仍需傳輸加密。可藉由硬體加速（如 AES-NI）降低加密效能損耗。"),
            ("ACL 的最小授權原則？", "應精確授權到具體的 Topic（例如 Read 權限）與該消費者所使用的 Consumer Group ID（例如 Read 權限），避免使用萬用字元 `*` 導致權限泛濫。")
        ],
        "pitfalls": [
            "設定了 Topic ACL 卻遺漏了 Consumer Group ACL，導致 Consumer 認證通過但無法提交 Offset 而報出 GroupAuthorizationException",
            "未對 SSL 憑證設定效期監控，憑證過期導致所有用戶端突然中斷連接"
        ]
    },
    {
        "q": "毒藥訊息 (Poison Message) 如何處理？",
        "core": "毒藥訊息指因格式錯誤、Schema 不相容或邏輯缺陷，導致 Consumer 處理時必然拋出異常且無法恢復的訊息。若不處理，Consumer 會因不 commit offset 而反覆重試，卡死分割區。處理策略：設定最大重試次數，超限後藉由 ErrorHandler 將訊息寫入死信佇列 (DLQ / DLT)，隨後提交當前位移以跳過該訊息。",
        "dive": [
            "Spring Kafka 中的 DefaultErrorHandler 與 DeadLetterPublishingRecoverer 配合，自動將重試失敗的訊息發送至 {topic}-dlt 佇列",
            "在非同步處理中，若遇到不合法的數據，應直接捕獲異常並記錄日誌，不可讓異常向上拋出導致整個 poll 批次被重放"
        ],
        "followups": [
            ("如何重放死信佇列中的訊息？", "通常會部署一個獨立的 Consumer 訂閱 DLT 進行人工修復或使用專用工具修改格式後重送，不可直接與主業務 Consumer 混用。"),
            ("如何從源頭防範 Schema 變更引起的毒藥訊息？", "引進 Schema Registry（如 Confluent Schema Registry），在 Producer 發送前進行 Schema 相容性檢查（如 BACKWARD/FORWARD 兼容），強制約束訊息格式。")
        ],
        "pitfalls": [
            "在 Consumer 中配置無限重試 (Infinite Retry) 且未設定 DLQ，導致單一訊息卡死整個資料管線",
            "死信佇列未設定監控與告警，導致大量毒藥訊息堆積卻無人知曉"
        ]
    },
    {
        "q": "Kafka 在體育資料場景的角色？",
        "core": "體育資料（如 Betradar 賠率、即時賽事數據）具有高頻率、瞬時峰值的特點。Kafka 作為核心的 Fan-out 分散式總線：將 odds/live events 寫入對應 Topic，多個下游消費端（如賠率計算引擎、即時看板推播、歷史歸檔資料庫）各自獨立且非同步地消費，實現讀寫分離與高可用擴充。",
        "dive": [
            "使用 key=matchId，確保同一場賽事的所有即時事件順序進入同一個 Partition，保證下游狀態機處理時不會出現「進球在紅牌之後」的順序錯亂",
            "多 Topic 規劃：按運動類型（soccer, basketball）或數據頻率（high-frequency odds vs low-frequency match metadata）劃分 Topic",
            "與記憶體內佇列（如 LMAX Disruptor）配合：Consumer 線程池拉取 Kafka 資料後快速塞入 Disruptor，以極低延遲進行微服務內部的並行分流與撮合"
        ],
        "followups": [
            ("如何應對秒級以下的極致低延遲要求？", "1) 增加 Partition 數量以提升消費端並行度；2) 優化 Consumer，減少單次 poll 訊息的批次大小，並關閉非必要的非同步落庫，主路徑只做記憶體處理與快取推送。"),
            ("如何應對峰值賽事（如世界盃決賽）的突發流量？", "在賽前預先擴充 Partition 數量並水平擴展 Consumer 實例；利用 Kafka 的磁碟緩衝能力進行削峰填谷，保護下游脆弱的業務資料庫。")
        ],
        "pitfalls": [
            "將所有賽事的所有數據塞進同一個單分割區 Topic，導致消費端完全失去擴充性，造成即時資料嚴重積壓與延遲",
            "Consumer 在消費執行緒中同步進行耗時的 HTTP 呼叫（如向第三方推送賠率），導致 poll 阻塞，觸發 Rebalance 並引發系統雪崩"
        ],
        "scenario": "例如：體育賠率與即時事件資料 onboarding，經由 Kafka 進行下游多通道高可用分發，並優化拉取參數以降低即時延遲指標"
    }
]

ROCKETMQ_TOPICS = [
    {
        "q": "RocketMQ 架架構：NameServer/Broker/Producer/Consumer？",
        "core": "RocketMQ 採分散式架構：NameServer 是無狀態、輕量級的路由註冊中心（採 AP 模型，不保證強一致，互相獨立）；Broker 負責訊息儲存與分發，支援 Master-Slave 架構；Producer 向指定 Queue 發送訊息；Consumer 依據負載平衡分配 Queue 進行消費，支援群組消費 (Clustering) 與廣播消費 (Broadcasting)。",
        "dive": [
            "Broker 每 30 秒向所有 NameServer 發送心跳，NameServer 每 10 秒掃描一次，若超過 120 秒未收到心跳則剔除該 Broker",
            "Topic 與 Queue 映射關係存於 NameServer，Client（Producer/Consumer）定時從 NameServer 拉取路由資訊",
            "5.x 架構引入 gRPC Proxy 模式，客戶端透過 Proxy 統一入口，大幅簡化容器化部署與網路穿透問題"
        ],
        "followups": [
            ("為何不使用 ZooKeeper 而自研 NameServer？", "ZooKeeper 採 CP 模型，在 Leader 選舉期間服務不可用，且維護複雜。NameServer 各節點互不通訊，無狀態，單台掛掉不影響其他節點運作，極其輕量穩定，非常適合僅需要路由註冊的 MQ 場景。"),
            ("Dledger 模式與 5.x Controller 模式的區別？", "Dledger 基於 Raft 協定，由 Dledger 接管 CommitLog 儲存，寫入效能較差。5.x 引入 Controller 角色（可部署於 NameServer 內），作為元資料中心控制主從切換，Broker 副本間則採更輕量高效的日誌複製協定，效能大幅提升。")
        ],
        "pitfalls": [
            "NameServer 全部宕機時，雖然現有已連線的 Client 仍可憑本地快取發送/消費訊息，但無法更新路由，一旦有 Broker 增減或 Topic 變更將立即失效",
            "未對 Broker 磁碟水位設定警報，磁碟滿時 Broker 會拒絕所有寫入，導致業務中斷"
        ],
        "scenario": "交易/行情系統以 gRPC/WS 整合 RocketMQ，承載即時交易流與行情分發"
    },
    {
        "q": "Topic、Tag、MessageQueue 關係與讀寫佇列？",
        "core": "Topic 代表邏輯訊息分類；Tag 是 Topic 下的子分類，用於輕量級過濾；MessageQueue 是實際的儲存分片與並行單位。RocketMQ 獨創「讀寫佇列分離」設計（writeQueueNums 與 readQueueNums），可在不中斷服務的情況下平滑進行佇列的擴縮容。",
        "dive": [
            "一個 Topic 在一個 Broker 上預設為 4 個寫佇列與 4 個讀佇列，兩者數量通常保持一致",
            "Tag 過濾在 Broker 端先進行 Hash 篩選，最後在 Consumer 端進行精確的字串比對",
            "利用 MessageKey 可以作為訊息的唯一識別碼，並透過 MessageQueueSelector 將相同 Key 的訊息發送至同一個 Queue"
        ],
        "followups": [
            ("讀寫佇列分離的具體應用場景？", "若要縮減佇列，可先將 writeQueueNums 從 8 縮小為 4，此時 Producer 僅會向 0-3 號佇列寫入訊息。待 Consumer 將 4-7 號佇列的存量訊息消費完畢後，再將 readQueueNums 調小為 4，如此可確保平滑縮容且不遺失訊息。"),
            ("Tag 與多 Topic 的選型原則？", "若訊息關聯性強、結構相似，建議使用同一個 Topic 配合不同的 Tag 進行過濾（如 Topic=Order，Tag=Pay/Refund）；若訊息類型截然不同、安全存取控制粒度不同，則應宣告不同的 Topic。")
        ],
        "pitfalls": [
            "在同一個 Consumer Group 內，不同 Consumer 實例訂閱了同一個 Topic 但指定了不同的 Tag，這會破壞訂閱關係一致性（Subscription Relation），導致部分訊息隨機遺失或無法消費",
            "佇列數量設定過少，限制了 Consumer 的並行度，成為系統效能瓶頸"
        ]
    },
    {
        "q": "順序訊息如何實現與底層鎖機制？",
        "core": "RocketMQ 透過將相同 Sharding Key 的訊息發送至同一個 MessageQueue，並在消費端使用 `MessageListenerOrderly` 來保證順序。其實作依賴三層鎖機制：Broker 端的佇列鎖（確保同一時間僅一個 Consumer 執行緒組消費該佇列）、Consumer 本地對應該佇列的 ProcessQueue 鎖，以及消費執行緒內的處理鎖，三者結合實現嚴格順序消費。",
        "dive": [
            "Broker 鎖：Consumer 背景執行緒定時向 Broker 租借該 MessageQueue 的分散式鎖（預設有效期 20 秒），防止 Rebalance 時併發消費",
            "ProcessQueue 鎖：防止同一個 Consumer 實例內多個消費執行緒並行處理同一個佇列的訊息",
            "順序消費失敗時，RocketMQ 不會將訊息送往重試佇列，而是將當前佇列掛起 (suspend)，在本地間隔重試，確保順序不被打亂"
        ],
        "followups": [
            ("順序消費遇到「毒藥訊息」卡死怎麼辦？", "由於順序消費失敗會持續在本地重試，因此必須在業務程式碼中對重試次數進行計數，超限時手動將訊息寫入死信佇列或資料庫，並回傳 CONSUME_SUCCESS 以跳過卡死狀態。"),
            ("全局順序如何實現？", "將 Topic 的 MessageQueue 數量設為 1，且僅部署一個 Consumer 實例。但這會完全失去並行能力，僅適用於低吞吐、對順序有絕對要求的場景。")
        ],
        "pitfalls": [
            "以為將訊息發送到多個 Queue，在 Consumer 端開啟 MessageListenerConcurrently 仍能保證順序",
            "本地事務未完成就發送了順序訊息，或者網路重試導致順序訊息在發送端就已失序"
        ]
    },
    {
        "q": "延遲訊息原理與 5.x 任意精度定時訊息？",
        "core": "在 RocketMQ 4.x 中，僅支援 18 個固定的延遲級別（1s, 5s...2h），訊息先被寫入系統 Topic `SCHEDULE_TOPIC_XXXX`，定時任務到期後再還原至真實 Topic。而自 **RocketMQ 5.0** 起，引進了基於**時間輪 (Timing Wheel) 與 RocksDB** 的內建定時器，原生支援**任意精度（精確到毫秒）**的定時與延遲訊息。",
        "dive": [
            "4.x 延遲原理：Broker 內部為 18 個 Level 建立對應的 ConsumeQueue，並啟動 18 個定時任務定時掃描並還原訊息",
            "5.x 任意精度：定時訊息先寫入系統的 TimerMessageLog，透過時間輪算法進行滾動管理，時間到期後重新投遞",
            "定時訊息的狀態儲存在本地 RocksDB 中，即使 Broker 重啟也能正確恢復定時任務"
        ],
        "followups": [
            ("如何宣告 5.x 的任意精度延遲訊息？", "在發送訊息時設定 Message 的 DeliverTimeMs（預期投遞的時間戳記），而非設定延遲級別。"),
            ("大量定時訊息是否會壓垮 Broker？", "在 5.x 下，定時器有專門的執行緒池與 RocksDB 緩衝，但若在同一個毫秒點有數百萬條訊息到期，仍會造成瞬間的 CPU 與 I/O 尖峰，應盡量將定時時間進行微幅隨機打散（Jitter）。")
        ],
        "pitfalls": [
            "在 4.x 環境中企圖傳入自訂的 delayTimeMs，導致屬性被忽略或訊息發送失敗",
            "使用延遲訊息作為高頻率的定時任務調度器（如秒級輪詢），這會增加 Broker 的磁碟讀寫負擔，應結合專業的調度框架（如 XXL-JOB）"
        ]
    },
    {
        "q": "事務訊息（半訊息）流程與實現原理？",
        "core": "RocketMQ 事務訊息保證了「本地事務執行」與「發送 MQ 訊息」的原子性（最終一致性）。流程：1) Producer 發送 Half Message 至 Broker；2) Broker 將 Topic 改為 `RMQ_SYS_TRANS_HALF_TOPIC` 暫存，對 Consumer 不可見並回傳 ACK；3) Producer 執行本地事務；4) Producer 提交 Commit/Rollback 給 Broker。若第四步失敗，Broker 會定時向 Producer 發送「事務狀態回查」確認狀態。",
        "dive": [
            "Half Message 儲存於 `HALF_TOPIC` 中，因 Consumer 未訂閱該系統 Topic，故無法消費，從而達到隔離效果",
            "Broker 每隔一段時間（預設 6 秒）掃描 `HALF_TOPIC`，若發現無對應 Op 標記（記錄在 `RMQ_SYS_TRANS_OP_HALF_TOPIC` 中），則向 Producer 回查",
            "回查上限為 15 次，若 15 次回查皆未能取得狀態（如服務當機），Broker 將自動 Rollback 該訊息"
        ],
        "followups": [
            ("與 Kafka 事務有何不同？", "Kafka 事務是資料庫式的二階段提交，側重於 read-process-write 的原子性，必須由 Kafka 全權控管。RocketMQ 事務專門設計用來協調外部本地事務（如資料庫操作）與訊息發送的一致性，並具備反向回查機制，更加彈性。"),
            ("如果回查時本地事務尚未提交完畢（如併發鎖延遲）怎麼辦？", "回查 Listener 應返回 UNKNOWN 狀態，讓 Broker 稍後再次回查，不可盲目返回 COMMIT 或 ROLLBACK。")
        ],
        "pitfalls": [
            "本地事務已成功 Commit，但回查邏輯因資料庫主從複製延遲未能查到數據，導致回查返回 ROLLBACK 或 UNKNOWN",
            "回查邏輯中包含耗時的外部服務呼叫，導致回查執行緒池被佔滿，造成事務確認積壓"
        ],
        "scenario": "交易/行情系統使用事務訊息確保「扣減帳戶餘額」與「發送交易完成通知訊息」兩者同生共死"
    },
    {
        "q": "RocketMQ 消費模式 Push vs Pop？",
        "core": "在 RocketMQ 4.x 中，Push 模式（實為 Client 端長輪詢拉取）與 Pull 模式皆依賴 Client 端的 Rebalance 演算法，若某個 Consumer 當機或消費慢，會導致其分配到的 Queue 阻塞。**RocketMQ 5.x 引入了全新的 Pop 模式**，改由 Broker 端無狀態分配訊息，多個 Consumer 可並行消費同一個 Queue，解決了慢消費阻塞的問題。",
        "dive": [
            "Push 模式底層：PullMessageService 執行緒定時拉取，當 Broker 無訊息時掛起請求（長輪詢預設 15 秒）",
            "Pop 模式原理：Consumer 向 Broker 發送 Pop 請求，Broker 從 Queue 中取出訊息並標記為不可見（Lock），Consumer 消費完後發送 Ack 進行確認",
            "若 Pop 訊息消費超時未 Ack，Broker 會自動重新投遞該訊息，類似於 RabbitMQ 的 Ack 機制"
        ],
        "followups": [
            ("廣播模式 (Broadcasting) 的運作與限制？", "廣播模式下，同一個 Consumer Group 內的所有 Consumer 實例都會收到 Topic 的全量訊息。消費進度 (Offset) 儲存在 Consumer 本地而非 Broker，因此不支援消費失敗重試與訊息回溯。"),
            ("消費失敗後的重試機制？", "在群組模式下，消費失敗（拋出異常或返回 RECONSUME_LATER）的訊息會被送往重試佇列 `%RETRY%GroupName`，最多重試 16 次且間隔時間逐次拉長，最後進入死信佇列 (DLQ)。")
        ],
        "pitfalls": [
            "在廣播模式下使用資料庫寫入操作，導致所有實例重複寫入相同資料",
            "併發消費 (ConsumeMessageConcurrentlyService) 時，誤以為消費失敗的訊息會按順序立刻重試，實際上會進入重試佇列導致亂序"
        ]
    },
    {
        "q": "RocketMQ 高吞吐量實踐與暫存池優化？",
        "core": "RocketMQ 高吞吐量基於：1) 批次發送與非同步發送；2) CommitLog 單一檔案順序寫入；3) MappedByteBuffer (mmap) 記憶體映射讀寫。進階優化可啟用 **TransientStorePool (臨時儲存池)**，將寫入與刷盤記憶體隔離，降低 Page Cache 鎖競爭。",
        "dive": [
            "TransientStorePool 原理：開啟後，訊息寫入由 Pool 分配的堆外記憶體 (Direct ByteBuffer)，再由背景執行緒非同步 commit 到 Page Cache，最後由刷盤執行緒 flush 到磁碟",
            "這實現了「讀寫分離」：寫入時往堆外記憶體寫，讀取時從 Page Cache 讀，極大減輕了作業系統 Page Cache 的讀寫鎖衝突",
            "非同步刷盤 (Async Flush) 配合 TransientStorePool 能達到極致寫入效能，但 Broker 異常斷電會遺失 Direct Memory 中未 commit 的資料"
        ],
        "followups": [
            ("何時選擇同步刷盤 (Sync Flush)？", "在金融交易、核心帳務等對可靠性要求極高、不允許遺失任何訊息的場景。此時訊息必須安全寫入磁碟 (fsync) 後才回應 Producer 成功，代價是吞吐量顯著下降。"),
            ("CommitLog 大小為何固定為 1GB？", "因為 RocketMQ 使用 mmap 進行記憶體映射，而在 Java 中，MappedByteBuffer 的單個映射長度限制在 Integer.MAX_VALUE 內，為了便於管理與避免虛擬記憶體碎片化，設定為 1GB。")
        ],
        "pitfalls": [
            "在高併發寫入時未開啟 TransientStorePool，導致 OS Page Cache 頻繁發生髒頁回寫阻塞（Page Cache Busy），造成 Producer 發送延遲尖峰",
            "忽視單一 MessageQueue 的寫入熱點，所有 Producer 皆指定同一個 Key，導致整個 Topic 的吞吐量受限於單一佇列"
        ]
    },
    {
        "q": "RocketMQ 與 Kafka 適用選型對比？",
        "core": "選型核心在於業務屬性。RocketMQ 偏向於**業務整合與金融級可靠性**，提供原生事務訊息、定時/任意精度延遲訊息、Tag SQL92 過濾、消費失敗重試、消費順序掛起等貼近商務邏輯的特性；Kafka 偏向於**高吞吐量數據管道與大數據處理**，生態鏈（Flink/Spark/Connect）極其強大，儲存設計更簡單直覺。",
        "dive": [
            "儲存模型：Kafka 每個 Partition 一個檔案，適合少量 Topic；RocketMQ 所有 Topic 共用 CommitLog，適合海量 Topic（支援幾萬個）",
            "通訊協定：Kafka 使用自訂的 TCP 協定；RocketMQ 5.x 採用 gRPC 協定，提供更好的跨語言支援與雲原生架構相容性",
            "運維成本：Kafka 目前去 ZK 後運維已大幅簡化；RocketMQ 的 NameServer 極其穩定，運維成本同樣很低"
        ],
        "followups": [
            ("是否能用 Kafka 強行實現延遲訊息？", "Kafka 無原生延遲訊息。若強行實作，需建立大量延遲 Topic，並在應用程式中寫定時輪詢，這會產生嚴重的磁碟隨機 I/O 且維護成本極高，不建議。"),
            ("兩者在 Broker 當機時的選主速度？", "KRaft 模式下的 Kafka 選主可在秒級內完成；RocketMQ 5.x 藉由 Controller 進行自動主從切換，同樣能實現秒級切換（通常 < 5s）。")
        ],
        "pitfalls": [
            "將 RocketMQ 當作大數據日誌收集平台，造成 Broker 端 ConsumeQueue 索引檔案建置速度跟不上寫入速度，導致記憶體崩潰",
            "在 Kafka 中為每個用戶建立獨立的 Topic，當 Topic 數量突破數萬時，Broker 會因大量隨機 I/O 導致磁碟寫入卡死"
        ]
    },
    {
        "q": "訊息重複與業務冪等性處理？",
        "core": "由於網路波動、ACK 遺失、Rebalance 觸發等原因，分散式 MQ 僅能保證「至少一次投遞 (At-Least-Once)」，訊息重複在所難免。解決重複消費的核心是**業務冪等性**。RocketMQ 會在客戶端生成唯一的 `MsgId`（在發送時），並在 Broker 儲存時生成 `OffsetMsgId`。建議在業務層使用自訂的業務唯一 Key（如訂單 ID）結合資料庫唯一鍵或 Redis 去重表來實現冪等。",
        "dive": [
            "MsgId：由 Producer 用戶端生成，代表該訊息的邏輯 ID，重試發送時該 ID 保持不變",
            "OffsetMsgId：由 Broker 端生成，代表訊息在 CommitLog 中的實體偏移量，若發送重試或路由到不同佇列，該 ID 會改變",
            "冪等實現手法：DB 唯一鍵（Insert 衝突拒絕）、Redis SETNX（設定過期時間作為分散式鎖去重）、樂觀鎖/狀態機（更新時帶上 status 條件）"
        ],
        "followups": [
            ("能不能依賴 OffsetMsgId 來做消費去重？", "絕對不能。因為同一條訊息在重試投遞或負載平衡重新分配時，其實體偏移量可能會變，導致 OffsetMsgId 發生變化，從而失效。必須使用 MsgId 或訊息內容中的業務唯一 ID。"),
            ("去重表數據無限膨脹如何處理？", "建立帶有 TTL 的去重表，僅保留 7-14 天的資料（依據業務訊息的最大有效期而定），並定期進行物理刪除或歷史歸檔。")
        ],
        "pitfalls": [
            "僅在消費端使用簡單的「印日誌」而未做任何實質去重，導致高併發重試時發生重複扣款等重大資安事故",
            "去重 Key 的粒度過粗，導致不同業務實體的訊息被誤判為重複訊息而丟棄"
        ]
    },
    {
        "q": "Broker 副本複製與高可用？",
        "core": "RocketMQ 支援 Master-Slave 架構。複製方式分為：**同步複製 (Sync Replication)**（Master 收到訊息後，需等待 Slave 複製成功才回應 Producer）與**非同步複製 (Async Replication)**（Master 寫入成功即回應，Slave 非同步同步）。5.x 引入 Controller 角色實現自動主從切換與 Epoch 複製，保證強一致性與高可用性。",
        "dive": [
            "當 Master 掛掉後，Consumer 可以自動切換到其對應的 Slave 進行唯讀消費，保證消費不中斷",
            "5.x Controller 模式下，Controller 監控 Broker 存活狀態。當 Master 故障時，Controller 決定新的 Master，並發布 Epoch 變更，防止腦裂",
            "Epoch 機制：Broker 會記錄每個 Epoch 寫入的日誌起點，在主從切換時進行日誌對齊，防止髒資料被錯誤覆蓋"
        ],
        "followups": [
            ("非同步複製在 Master 當機時會丟資料嗎？", "會。若 Master 收到寫入但尚未同步給 Slave 時突然當機，此時若自動切換 Slave 為 Master，這部分未同步的訊息將會遺失。對資料一致性敏感的場景應強制開啟同步複製。"),
            ("如何防止腦裂 (Split-Brain)？", "在 5.x Controller 模式中，Controller 群組本身使用 Raft 協定，遵循多數決原則（Quorum）。只有獲得多數 Controller 認可的 Broker 才能成為 Master，從根本上避免了雙 Master 腦裂的可能。")
        ],
        "pitfalls": [
            "生產環境僅配置單個 Master 節點而無 Slave 副本，一旦該實體機磁碟損壞或系統崩潰，將導致服務完全中斷且資料面臨永久遺失風險",
            "Slave Broker 的記憶體與 CPU 配置遠低於 Master，當發生主備切換時，Slave 無法承受突發的消費與讀取負載，導致二次崩潰"
        ]
    },
    {
        "q": "RocketMQ 訊息堆積緊急處理方案？",
        "core": "當出現百萬級訊息堆積時，說明消費速度遠低於生產速度。緊急處理策略為：1) 擴充 Consumer 實例數量；2) 增加 Topic 的 MessageQueue 數量（需同時進行）；3) 若無法擴佇列，可部署臨時的「中轉消費服務」，快速將訊息拉取並寫入具有多倍分區的臨時 Topic，再由大量臨時消費者消費新 Topic；4) 暫時關閉非核心業務邏輯以提升下游處理速度。",
        "dive": [
            "只增加 Consumer 實例而不擴充 MessageQueue 數量是無效的，因為一個 Queue 只能被同一個 Group 內的一個 Consumer 實例消費",
            "透過 RocketMQ Admin 工具或 Prometheus 監控 `consume TPS` 與 `produce TPS` 的差值，以及 `accumulated messages` 指標，設定水位線告警",
            "排查堆積源頭：檢查資料庫是否有死鎖、外部 API 呼叫是否超時、Consumer 執行緒是否因拋出異常未捕獲而陷入死循環"
        ],
        "followups": [
            ("如何做臨時中轉分發？", "編寫一個極簡 the Consumer，不進行任何資料庫寫入或業務計算，僅將 poll 到手的訊息發送至臨時 Topic（如 temp_topic，分區數設為 30），隨後立即 Commit。接著部署 30 個臨時 Consumer 實例去消費 temp_topic，實現極速分流。"),
            ("歷史堆積訊息能否直接跳過？", "在非核心業務場景（如非金流通知），可使用 RocketMQ Admin 重置消費位點 (Reset Offset) 到最新位置，將積壓的訊息直接跳過，事後再透過日誌進行補償。")
        ],
        "pitfalls": [
            "在發生大量訊息堆積時，盲目重啟 Consumer 服務，這會觸發頻繁的 Rebalance，導致消費中斷更嚴重，雪上加霜",
            "下游資料庫（如 MySQL）已經達到 I/O 瓶頸，此時盲目擴容 Consumer 只會把壓力轉移到 DB，導致資料庫崩潰"
        ]
    },
    {
        "q": "RocketMQ 在加密貨幣交易所 (Crypto Exchange) 場景的應用？",
        "core": "加密貨幣交易所要求高併發、極致可靠性與精確的狀態變更。RocketMQ 主要用於解耦非核心路徑：1) 撮合引擎 (Matching Engine) 透過記憶體與 gRPC 完成主路徑交易後，將交易事件 (Trade Events) 發送至 RocketMQ；2) 下游的帳戶餘額更新、資產清算、用戶即時推播 (Websocket)、合規審計等模組非同步消費 MQ 訊息，避免影響撮合核心效能。",
        "dive": [
            "使用事務訊息 (Transaction Message) 確保用戶的「鏈上提現/充值操作」與「帳戶系統狀態變更」保持最終一致性",
            "使用訊息軌跡 (MessageTrace) 記錄每一條訂單事件的發送時間、儲存位置與消費狀態，滿足金融監管的審計與回溯要求",
            "使用順序訊息保證特定交易對（如 BTC/USDT）的訂單創建與取消事件在同一個 Queue 中按順序處理，防止撮合狀態機失序"
        ],
        "followups": [
            ("撮合引擎主路徑是否可以直接使用 RocketMQ？", "不行。撮合核心要求微秒級的延遲，任何磁碟 I/O 或網路 MQ 傳輸都會成為瓶頸。撮合引擎應採用 LMAX Disruptor 在記憶體中進行，並以 RocketMQ 作為非同步持久化與下游分發的媒介。"),
            ("如何應對極端行情（如插針、大波動）時的流量暴增？", "利用 RocketMQ 的 CommitLog 順序磁碟寫入能力，充當緩衝墊，吸收暴增的交易與行情訊息；Websocket 推送模組可配置 Pop 模式或 BroadCasting 模式，快速廣播行情資料。")
        ],
        "pitfalls": [
            "將撮合引擎的同步確認邏輯與 RocketMQ 發送綁定，一旦 MQ 發生瞬間網路抖動，會直接拖垮整個交易撮合主鏈",
            "行情廣播訊息未設定過期時間或丟棄策略，導致用戶端接收到幾分鐘前的歷史行情，引發客訴"
        ]
    }
]

RABBITMQ_TOPICS = [
    {
        "q": "RabbitMQ 核心概念：Exchange/Queue/Binding/Routing Key？",
        "core": "RabbitMQ 基於 AMQP 0-9-1 協定。Producer 不直接發送訊息至 Queue，而是發送給 Exchange（交換機），由 Exchange 依據路由規則（Routing Key）將訊息分發至繫結（Binding）的 Queue 中，Consumer 則從 Queue 中拉取 (get) 或訂閱推送 (consume) 訊息。Channel（通道）是複用在 TCP 連線上的虛擬連接，為讀寫的最小單位。",
        "dive": [
            "Virtual Host (vhost)：虛擬主機，提供邏輯上的隔離，擁有獨立的 Exchange, Queue, Binding 與權限控制",
            "Channel 的非執行緒安全特性：多執行緒間共用同一個 Channel 會導致 AMQP 訊框 (Frame) 錯亂，每個執行緒應擁有獨立的 Channel",
            "Message Properties：包含 headers, deliveryMode（2 代表持久化）, priority, correlationId 等豐富的元資料"
        ],
        "followups": [
            ("與 Kafka 的架構區別？", "RabbitMQ 是傳統的訊息佇列，路由功能極其豐富靈活，訊息一經消費確認即會從佇列中刪除，不保留歷史；Kafka 是基於分散式 Commit Log 的流式平台，訊息唯讀且持久化保留，支援多個 Consumer Group 重複消費與歷史回溯。"),
            ("Default Exchange 的工作原理？", "是一個名稱為空字串的 Direct Exchange。每個新建的 Queue 都會自動以自己的佇列名稱作為 Routing Key 繫結到該 Default Exchange 上。")
        ],
        "pitfalls": [
            "在 Producer 中為每一條訊息都頻繁建立與銷毀 TCP 連線，導致作業系統 Socket 耗盡，應使用 Connection/Channel 連線池進行複用",
            "未建立 Binding 即發送訊息，導致訊息被 Exchange 直接丟棄"
        ]
    },
    {
        "q": "四種 Exchange 類型與萬用字元比對？",
        "core": "Exchange 依路由規則分為四種：1) Direct：精確比對 Routing Key；2) Topic：模式比對，支援 `*`（比對一個單字）與 `#`（比對零個或多個單字）；3) Fanout：廣播模式，忽略 Routing Key，分發至所有繫結的 Queue；4) Headers：依據 Message Headers 的屬性進行路由（效能較低，少用）。",
        "dive": [
            "Topic 萬用字元例：`sport.football.*` 可匹配 `sport.football.match1`，但無法匹配 `sport.football.match1.goal`；而 `sport.football.#` 則兩者皆可匹配",
            "Fanout Exchange 由於不進行 Routing Key 比對，路由效能是所有 Exchange 中最高的",
            "在進行路由匹配時，若訊息無法路由至任何佇列，且 mandatory 設為 true，Broker 會將訊息退回給 Producer"
        ],
        "followups": [
            ("體育即時賠率應如何設計 Routing Key？", "使用 Topic Exchange，Routing Key 設計為 `odds.{provider}.{sport}.{matchId}`。下游計算模組可依據需求訂閱 `odds.betradar.soccer.#`（訂閱特定廠商的足球所有事件）或 `odds.*.basketball.12345`（訂閱該賽事的所有廠商賠率）。"),
            ("什麼是 Headers Exchange？", "不依賴 Routing Key，而是匹配訊息屬性中的 Headers 鍵值對。可設定 x-match=all（所有 Header 均需匹配）或 any（任一 Header 匹配即可）。由於要在記憶體中解析複雜的 Map 結構，效能顯著低於其他類型。")
        ],
        "pitfalls": [
            "誤將 Topic 的 `*` 當成字元級別的萬用字元（如寫成 `sport*`），實際上 RabbitMQ 的萬用字元是以 `.` 分割的單字為單位進行匹配的",
            "使用 Fanout 卻繫結了過多無用的 Queue，導致 Broker 記憶體與網路頻寬被瞬間寫入的廣播訊息撐爆"
        ]
    },
    {
        "q": "訊息確認機制 (ACK) 與手動 ACK 記憶體洩漏？",
        "core": "RabbitMQ 提供雙向確認：1) Publisher Confirm：確認訊息是否成功抵達 Broker 並安全落盤/複製；2) Consumer ACK：Consumer 處理完後手動呼叫 `basic.ack` 確認，失敗時呼叫 `basic.nack`/`basic.reject` 並指定是否重新排隊 (requeue) 或送入死信交換機 (DLX)。手動 ACK 下若忘記確認，會導致訊息積壓於記憶體中造成 OOM。",
        "dive": [
            "自動確認 (autoAck=true)：Broker 發送訊息後立即刪除，若 Consumer 處理中途當機，該訊息將永久遺失。推薦生產環境使用手動確認",
            "Unacked 狀態：當 Consumer 收到訊息但未進行 Ack 時，該訊息在 Broker 中標記為 Unacked。當 Channel 關閉或 Consumer 斷開時，這些訊息會被 Broker 自動歸還並重新排隊",
            "手動 ACK 忘記提交：Unacked 訊息會一直佔用 Broker 的記憶體，且該 Consumer 不會再收到新訊息，最終導致記憶體洩漏與服務停擺"
        ],
        "followups": [
            ("basic.reject 與 basic.nack 的區別？", "basic.reject 僅支援拒絕單一條訊息；basic.nack 是 RabbitMQ 的擴充，支援批次拒絕多條訊息（透過 multiple=true 參數）。"),
            ("Publisher Confirm 的幾種實現方式？", "1) 同步等待 (waitForConfirms)：發一條等一條，效能極低；2) 批次確認：發送一批後調用，一旦有一條失敗需整批重發；3) 非同步監聽 (addConfirmListener)：註冊成功與失敗的 Callback 執行緒，最推薦，效能最高。")
        ],
        "pitfalls": [
            "開啟手動 ACK，但在代碼的 catch 區塊中忘記呼叫 basic.nack，且未設置 finally 釋放 Channel，導致 Broker 的記憶體因 Unacked 訊息過多而耗盡",
            "在非同步處理中盲目設定 requeue=true，當訊息本身有 Bug 導致處理反覆失敗時，會造成該訊息無限循環排隊重試，佔滿 CPU"
        ]
    },
    {
        "q": "持久化與 Quorum Queue 的三者結合？",
        "core": "單純設定持久化不代表訊息絕對安全，必須**三者同時成立**：1) Queue 宣告為 Durable（保證佇列結構重啟還在）；2) 訊息的 deliveryMode 設為 2（宣告訊息持久化到磁碟）；3) 啟用 Publisher Confirm 確保落盤成功。然而，單機持久化無法防止硬體故障，生產環境必須搭配基於 Raft 的 **Quorum Queue** 實現強一致性多副本複製。",
        "dive": [
            "Classic Mirrored Queue（鏡像佇列）因同步協定缺陷，在 3.9+ 標記為 Deprecated，並在 **RabbitMQ 4.0 中被完全移除**",
            "Quorum Queue 基於 Raft 演算法，由一個 Leader 和多個 Follower 組成，訊息必須同步寫入過半數 (Quorum) 節點的 Raft WAL 日誌後才回應 Ack",
            "Lazy Queue（惰性佇列）：優先將訊息寫入磁碟而非記憶體，大幅減少記憶體佔用，適合處理大量訊息堆積，但吞吐量低於純記憶體佇列"
        ],
        "followups": [
            ("Quorum Queue 與傳統鏡像佇列相比的優勢？", "鏡像佇列的同步是阻斷式的，且在網路分割區恢復時容易發生腦裂或資料不一致；Quorum Queue 基於標準 Raft 協議，具備自動選主、網路分割區自動恢復能力，且資料一致性極強。"),
            ("持久化是否意味著每次發送都會呼叫 fsync？", "不一定。RabbitMQ 會將寫入快取，每隔一段時間（如數百毫秒）或快取滿時批次呼叫 fsync 刷盤。啟用 Publisher Confirm 則會迫使 Broker 在訊息安全寫入磁碟後再發送 ACK。")
        ],
        "pitfalls": [
            "將 Queue 宣告為 Durable，但發送訊息時 deliveryMode 未設為 2，導致 Broker 當機重啟後佇列還在，但其中的訊息全部消失",
            "Quorum Queue 的副本數設為偶數（如 4 個），這不僅無法增加容錯能力（同樣只能容忍 1 台損壞），反而會因為 Raft 多數決限制（需要 3 台同意）降低寫入效能"
        ]
    },
    {
        "q": "Dead Letter Exchange (DLX) 與延遲佇列排隊阻塞問題？",
        "core": "DLX（死信交換機）用於接收因下列原因被拒絕的訊息：1) basic.reject/nack 且 requeue=false；2) 訊息在佇列中超時 (TTL)；3) 佇列達到最大長度限制。使用「TTL + DLX」可實作延遲佇列，但若在訊息上設定 TTL 會遇到**排隊阻塞**問題（因佇列為 FIFO，僅檢查隊首訊息是否過期），需透過專屬延遲外掛解決。",
        "dive": [
            "配置方式：在宣告主佇列時，傳入引數 `x-dead-letter-exchange` 與 `x-dead-letter-routing-key` 指向 DLX",
            "排隊阻塞解決方案 1：為每種不同的延遲時間宣告一個獨立的死信佇列（如 delay_5s, delay_10s），各佇列設定固定的 x-message-ttl",
            "排隊阻塞解決方案 2：啟用 `rabbitmq_delayed_message_exchange` 外掛，訊息直接在 Exchange 層級（基於 Mnesia）進行定時等待，到期後再路由至佇列，避開佇列 FIFO 限制"
        ],
        "followups": [
            ("死信佇列中的訊息如何追蹤與除錯？", "訊息進入 DLX 後，其 Header 中會被自動添加一個名為 `x-death` 的數組，記錄了該訊息何時死亡、死亡原因（expired, rejected）、死在哪個佇列等詳細歷史資訊。"),
            ("什麼是 x-max-length 策略？", "定義了佇列可容納的最大訊息條數或容量。當佇列滿且有新訊息進入時，RabbitMQ 會依據拒絕策略，將隊首的舊訊息丟棄或送入 DLX，以此保護記憶體。")
        ],
        "pitfalls": [
            "使用訊息級別的 TTL（如訂單支付倒數，有的 30 分鐘，有的 5 分鐘）在同一個佇列中進行排隊，導致 5 分鐘的訂單被前面 30 分鐘的訂單卡死，無法按時關閉",
            "死信佇列本身未設定任何消費者與監控，導致「毒藥訊息」被送入後在 DLQ 中無限堆積，最終撐爆磁碟空間"
        ]
    },
    {
        "q": "Prefetch 參數與 Consumer 公平排程 (Fair Dispatch)？",
        "core": "RabbitMQ 預設採輪詢（Round-Robin）分發訊息，不管 Consumer 處理速度。透過設定 `channel.basicQos(prefetchCount=n)`，限制 Broker 發送給該 Channel 的「未確認 (Unacked)」訊息上限。Prefetch 設為 1 可實現最公平的排程（能者多勞）；在追求高吞吐量時，則應適當增大 Prefetch值。",
        "dive": [
            "prefetchCount = 0 代表無限制（預設值），Broker 會一次性將所有訊息發送給 Consumer，若某個實例處理極慢，會造成嚴重的訊息積壓與 OOM 風險",
            "在多核心、高併發的 Consumer 端，將 prefetchCount 設為 50-100，能讓 Consumer 端有足夠的本地訊息緩衝，避免網路等待，極大提升吞吐量",
            "global 參數：basicQos 支援 global 屬性，若設為 true，則 prefetch 限制適用於整個 Connection 下的所有 Channel，而非單一 Channel"
        ],
        "followups": [
            ("處理慢的 Consumer 如何設定 Prefetch？", "應將 prefetchCount 設為 1，確保該 Consumer 在處理完當前訊息並發送 ACK 之前，Broker 不會再分配新訊息給它，實現「公平排程」。"),
            ("高吞吐 Consumer 的併發配置？", "配合 `concurrency`（併發消費者執行緒數）調整。例如 concurrency=10，prefetch=20，則該節點最多可同時緩衝 200 條 Unacked 訊息。")
        ],
        "pitfalls": [
            "將 prefetchCount 設為 1 用於高吞吐數據處理，導致 Consumer 大部分時間都花在等待網路 ACK 回傳與拉取新訊息的往返延遲上，造成系統效能極差",
            "在單執行緒的 Consumer 中設定了極大的 prefetchCount，導致該節點攬下過多訊息卻處理不及，而其他空閒的 Consumer 節點卻無訊息可處理"
        ]
    },
    {
        "q": "RabbitMQ 叢集架構與 Khepri 元資料庫演進？",
        "core": "RabbitMQ 傳統叢集（Classic Cluster）僅共享 Exchange/Queue 的元資料，Queue 的實體資料僅儲存於其宣告的節點上（若該節點掛掉且未開鏡像，服務即中斷）。為了高可用，必須使用基於 Raft 的 Quorum Queue。在元資料管理上，新版 RabbitMQ 引入了基於 Raft 的 **Khepri** 儲存庫，逐步取代舊有的 Mnesia 資料庫，以解決叢集分裂時的元資料一致性問題。",
        "dive": [
            "Mnesia 缺點：在遭遇網路分割區 (Network Partitioning) 時，Mnesia 容易發生分裂，重組叢集時常需要手動干預且易失步",
            "Khepri 優勢：將元資料（vhost, user, queue, exchange 宣告）的管理納入 Raft 共識協定，網路分裂時會遵循多數決，自動復原且強一致",
            "Federation 與 Shovel 外掛：用於跨資料中心（WAN）的叢集間資料複製與同步，避免因跨地區網路抖動導致叢集崩潰"
        ],
        "followups": [
            ("叢集腦裂後的恢復策略 (cluster_partition_handling)？", "傳統 Mnesia 下可配置：1) autoheal：自動選擇一個分區勝出，重啟其他分區（可能丟失這期間的數據）；2) pause_minority：一旦檢測到處於少數派分區，自動暫停自身服務，等網路恢復後自動重連，這是最安全的生產配置。"),
            ("什麼是 Stream Queue？", "RabbitMQ 3.9+ 引入的唯追加、持久化的新型佇列，其儲存結構與效能指標極其類似 Kafka，支援訊息重複讀取（透過 offset 回溯），專為大數據吞吐量設計。")
        ],
        "pitfalls": [
            "在沒有開啟 Quorum Queue 的情況下，以為部署了 Classic 叢集就擁有了高可用，一旦儲存 Queue 實體資料的 Node 掛掉，該 Queue 立即無法讀寫",
            "跨地區 (WAN) 部署單個 RabbitMQ 叢集，由於節點間 Erlang 心跳對網路延遲極度敏感，會頻繁引發叢集腦裂與重組"
        ]
    },
    {
        "q": "RabbitMQ vs Kafka/RocketMQ 核心選型對比？",
        "core": "RabbitMQ 是以 AMQP 協定為基礎的傳統訊息代理，主打微秒級低延遲、強大靈活的路由匹配能力（Exchange/Routing Key）與豐富的消費控制，但吞吐量受限於 CPU 鎖競爭且訊息消費完即物理刪除。Kafka/RocketMQ 則是基於 Commit Log 的時序串流平台，主打分割區水平擴展、百萬級高吞吐與資料持久化可重複消費。選型應視「路由複雜度」與「吞吐/串流回溯需求」而定。",
        "dive": [
            "儲存與回溯：RabbitMQ 基於 Erlang Actor 記憶體佇列，Consumer ACK 後 Broker 會立即物理刪除訊息；Kafka/RocketMQ 採順序追加寫入磁碟 (Append-only Log)，Consumer 僅移動 Offset 指標，支援歷史重播與多訂閱者獨立重複消費。",
            "路由靈活性：RabbitMQ 內建 Direct/Fanout/Topic/Headers 多樣 Exchange，支援複雜萬用字元動態繫結；Kafka/RocketMQ 僅支援 Topic/Tag 的簡單過濾，複雜路由需依賴下游串流處理框架。",
            "積壓承載力：RabbitMQ 大量積壓時記憶體與 Mnesia 索引壓力極大，會觸發流控機制阻塞 Producer；Kafka/RocketMQ 基於 Log 分割區，大面積積壓對寫入吞吐無影響。"
        ],
        "followups": [
            ("何時必須選擇 RabbitMQ？", "微服務間需要高頻、低延遲的 RPC 雙向通訊（如 Direct Reply-to）、需要依賴複雜萬用字元進行細粒度動態路由（如體育即時賠率分流），且訊息處理完即可拋棄的場景。"),
            ("Kafka 和 RocketMQ 的選型差異？", "Kafka 主打極限高吞吐與日誌大數據處理；RocketMQ 對商用業務支援極佳（如任意精度延遲訊息、分佈式事務訊息、消費重試與死信佇列），適合金融與電商交易場景。")
        ],
        "pitfalls": [
            "將 RabbitMQ 作為事件溯源 (Event Sourcing) 或大數據稽核日誌備份平台，因其不具備 Offset 歷史重播與持久化持久儲存能力。",
            "在高吞吐量資料管線中盲目使用 RabbitMQ 作為全局核心，這會因為繁重的記憶體 Ack 狀態維護與 CPU 佇列鎖競爭使 Broker 成為效能瓶頸。"
        ]
    },
    {
        "q": "RabbitMQ 記憶體/磁碟告警與流控機制？",
        "core": "當 Broker 記憶體使用率達到高水位線（vm_memory_high_watermark，預設 40% 實體記憶體）或磁碟剩餘空間低於閾值時，會觸發**全域流控告警**。此時 Broker 會**阻斷 (Block)** 所有發送訊息的 Connection（停止從 socket 讀取數據），但 Consumer 的 Connection 不受影響，以確保消費能繼續進行，釋放記憶體。此外，還能透過 Lazy Queue 將訊息直接落盤以防 OOM。",
        "dive": [
            "Paging（換頁）機制：當記憶體使用率達到高水位線的 50%（預設）時，RabbitMQ 會開始將記憶體中的訊息非同步寫入磁碟，以防記憶體飆升",
            "流控狀態：在 Web 管理介面上，觸發告警的連線會顯示為紅色 `blocking` 或 `blocked` 狀態，Producer 的 send API 會同步阻塞或拋出超時異常",
            "透過 `rabbitmqctl set_vm_memory_high_watermark` 可以動態調整記憶體閾值，或配置絕對值限制"
        ],
        "followups": [
            ("Lazy Queue (惰性佇列) 的運作機制？", "Lazy Queue 在訊息到達後直接寫入磁碟，僅在記憶體中保留少量索引。當 Consumer 消費時才從磁碟讀取載入。這使其能安全地存放數百萬條積壓訊息而不引起 Page Cache 與記憶體崩潰，缺點是發送與消費的 I/O 損耗較大，吞吐量較低。"),
            ("如何應對突發性的磁碟滿告警？", "1) 立即增加磁碟空間；2) 檢查是否有開啟大量不必要的 Trace 插件；3) 使用 `rabbitmqctl` 臨時提高磁碟警報閾值，或將非核心的堆積佇列進行 Purge（清空）。")
        ],
        "pitfalls": [
            "未對 vm_memory_high_watermark_paging_ratio 進行微調，導致記憶體在還沒來得及 Paging 到磁碟前就已衝破 40% 閥值，引發 Producer 瞬間全部被 blocked",
            "單個佇列積壓了數百萬條訊息且未開啟 Lazy Queue 模式，導致 Broker 記憶體被積壓的訊息元資料與資料撐爆，引發 OOM 當機"
        ]
    },
    {
        "q": "RabbitMQ RPC 模式與 Direct Reply-to 優化？",
        "core": "RabbitMQ 實作 RPC：Client 發送 Request 訊息至請求佇列，訊息中攜帶 `replyTo`（指定回覆佇列名稱）與 `correlationId`（請求唯一識別碼）；Server 消費並處理後，將 Response 訊息發送至指定的回覆佇列，Client 監聽該佇列並依據 correlationId 匹配回覆。**Direct Reply-to** 特性可免去為每個 Client 頻繁建立/銷毀排他性回覆佇列的開銷，大幅提升效能。",
        "dive": [
            "傳統 RPC 痛點：為每個 Client 宣告一個 Exclusive Temp Queue，會對 Broker 的元資料庫（Mnesia）造成極大的寫入壓力，且易發生 Queue 洩漏",
            "Direct Reply-to 原理：Client 不需要宣告回覆佇列，只需將 `replyTo` 屬性設為預定義的系統虛擬佇列 `amq.rabbitmq.reply-to`。Broker 會自動在 Channel 層級建立一個匿名的虛擬回覆通道",
            "Client 隨後直接對 `amq.rabbitmq.reply-to` 進行 consume，Broker 會將對應的回覆訊息路由回該 Channel，效能與安全性極佳"
        ],
        "followups": [
            ("correlationId 的作用？", "用於在非同步多路複用中識別該 Response 對應哪一個 Request。當 Client 發送多個 Request 且 Response 非同步返還時，Client 可憑此 ID 將回覆配對給正確的執行緒。"),
            ("RPC 模式下如何防止 Client 永久等待？", "在 Client 端設定 Timeout 機制。若在規定時間內未收到對應 correlationId 的回覆，則拋出超時異常，並清理本地的 Callback 映射表。")
        ],
        "pitfalls": [
            "使用傳統 RPC 模式但未設定 auto-delete 參數，當 Client 異常崩潰時，其宣告的臨時回覆佇列殘留於 Broker 中，造成嚴重的佇列洩漏",
            "correlationId 未採用安全隨機數（如 UUID），在併發請求時發生衝突，導致用戶收到錯誤的其他請求回覆"
        ]
    },
    {
        "q": "如何保證訊息順序與 Requeue 亂序坑？",
        "core": "RabbitMQ 僅保證「單一 Queue 且單一 Consumer」下的訊息嚴格有序。一旦有多個 Consumer 並行消費，或者訊息處理失敗被重新排隊（Requeue），順序就會被打破。特別要注意：呼叫 `basic.nack(requeue=true)` 時，訊息會被插入回佇列的**隊首 (Head)**，在多消費者場景下這會徹底破壞消費順序。",
        "dive": [
            "Requeue 亂序過程：訊息 A 處理失敗呼叫 requeue，被重新插回隊首。此時其他執行緒正在消費後續的訊息 B 和 C，這時訊息 A 會被分發給另一個 Consumer 執行，導致 A 的實際完成時間落後於 B 和 C",
            "解決方案 1：如果必須保證順序且容許重試，在失敗時**絕對不可 requeue=true**，應在 Consumer 本地進行有限度的執行緒重試，若重試失敗則將訊息發送至 DLQ 進行非同步補償，並 commit 當前訊息",
            "解決方案 2：使用 RabbitMQ Consistent Hash Exchange 外掛，依據 Sharding Key 將訊息路由到多個子佇列，每個子佇列僅由一個專屬 Consumer 消費，在保證並行的同時確保分割區順序"
        ],
        "followups": [
            ("什麼是 Single Active Consumer (SAC)？", "在宣告 Queue 時設定 `x-single-active-consumer=true`。這使得該 Queue 在同一個時間只會允許一個 Consumer 處於 Active 狀態進行消費。若該 Consumer 掛掉，其他 standby 的 Consumer 才會接管，這在不需要 Sharding 但要保證高可用與順序消費的場景非常有用。"),
            ("是否可以使用 exclusive consumer？", "可以。在 consume 時設定 exclusive=true，該 Queue 將只允許當前 Consumer 獨佔，其他 Consumer 企圖監聽會被拒絕。")
        ],
        "pitfalls": [
            "以為將訊息發送到 Topic Exchange 並由多個消費者訂閱同一個 Queue 能保證順序處理，實際上各 Consumer 執行緒的調度隨機性極高，必然失序",
            "在生產環境中誤用 `requeue=true` 處理業務邏輯錯誤（如資料庫連線失敗），導致訊息不斷在隊首重試，卡死整個佇列且造成極高的 CPU 消耗"
        ]
    },
    {
        "q": "RabbitMQ 在體育資料項目中的角色與多 MQ 架構？",
        "core": "在大型體育資料管線（如 Betgenius/Betradar 數據同步）中，常採用多 MQ 混合架構：Kafka 作為統一的高吞吐量資料接入與日誌歸檔中心；而 RabbitMQ則利用其強大靈活的 **Topic Exchange 路由匹配**能力，負責將特定賠率、特定聯賽（League）的即時變更事件精確地路由分發到不同的微服務與下游特定訂閱用戶端。",
        "dive": [
            "Kafka 做大池子，RabbitMQ 做細粒度分發：將 Kafka 資料拉取後，依據 sport/region/match 結構發送至 RabbitMQ Topic Exchange",
            "結合 Redis 進行狀態緩衝：RabbitMQ 僅傳送輕量級的變更事件通知（如 OddsUpdatedEvent），下游收到後去 Redis 讀取最完整的賠率快照，減少網路傳輸壓力",
            "使用 Federation 插件，將即時賠率資料從總部叢集自動同步到多個區域（如美洲、歐洲）的邊緣 RabbitMQ 節點，實現地理分發與低延遲讀取"
        ],
        "followups": [
            ("為何不統一使用 Kafka，而要同時保留 RabbitMQ？", "歷史因素與架構優勢互補。Kafka 不支援複雜的萬用字元 Key 匹配（如在 Consumer 端動態變更過濾規則），且訊息刪除機制不適合做點對點的任務分發；RabbitMQ 的 AMQP 路由機制極起靈活，且支援 Direct Reply-to 進行同步/非同步的微服務 RPC，非常適合中小型吞吐、複雜業務路由。"),
            ("多 MQ 架構下如何保證雙寫一致性？", "避免使用雙寫（即 Producer 同時向 Kafka 和 RabbitMQ 發送相同訊息）。應採單一寫入點原則：僅寫入 Kafka，再透過專屬的轉發服務（Bridge Service）或 Kafka Connect 將資料轉發至 RabbitMQ。")
        ],
        "pitfalls": [
            "在體育賠率這種高頻率更新場景中，對 RabbitMQ 的每個即時更新事件都使用 Durable Queue + Persistent Message + Publisher Confirm，導致磁碟 I/O 嚴重過載，即時賠率大幅延遲（高達數秒），應將即時行情設定為 transient，僅依靠記憶體分發以確保低延遲",
            "未對 Shovel 或 Federation 跨地區傳輸設定斷線重連快取限制，導致兩地網路中斷時，本地 Broker 記憶體被待傳送訊息撐爆而當機"
        ],
        "scenario": "高吞吐量體育資料管線實務：整合多數據來源 (REST/Websocket)，藉由 Kafka 進行數據緩衝與持久化，再透過 RabbitMQ Topic 路由將精確賠率推播至訂閱端"
    }
]

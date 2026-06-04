# -*- coding: utf-8 -*-
"""Redis and MySQL interview topics."""

REDIS_TOPICS = [
    {
        "q": "Redis 五種基本資料結構及其底層實現？",
        "core": "String(SDS)、List(quicklist=listpack/ziplist)、Hash(listpack/hashtable)、Set(intset/hashtable)、ZSET(listpack/skiplist+hashtable)。Redis 依元素數量與大小在緊湊編碼（listpack/intset）與雜湊表（hashtable）間自動轉換，以平衡記憶體與 O(1)/O(logN) 操作。自 Redis 7.0+ 起，listpack 已完全替代 ziplist 以解決其級聯更新問題。",
        "dive": [
            "SDS：O(1) 取得長度、二進位安全、預分配減少 realloc",
            "skiplist：多層索引，ZSET range/score 查詢 O(logN)，內部為跳躍表與雜湊表雙重指針結構",
            "listpack：緊湊連續記憶體，解決 ziplist 級聯更新（Cascade Update）問題，節省小物件空間",
            "encoding 轉換不可逆（大→小需主動刪除重建）",
        ],
        "followups": [
            ("K 線場景為何用 ZSET？", "score=時間戳記，member=OHLC JSON；ZREVRANGEBYSCORE 取時間窗 O(logN+M)"),
            ("intset 何時用？", "set 全為整數且元素少時"),
        ],
        "pitfalls": ["大 listpack/ziplist 轉 hashtable 造成 latency spike", "誤用 KEYS * 阻塞"],
        "svg": """
<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="skiplist 多層索引結構，查詢平均 O(log N)">
  <text x="330" y="22" fill="#56c2ff" font-size="13" font-weight="700" text-anchor="middle">skiplist：上層稀疏索引，查詢平均 O(log N)</text>
  <text x="18" y="62" fill="#9aa3b5" font-size="10">L2</text>
  <text x="18" y="110" fill="#9aa3b5" font-size="10">L1</text>
  <text x="18" y="158" fill="#9aa3b5" font-size="10">L0</text>
  <g font-size="12" text-anchor="middle">
    <rect x="25" y="43" width="46" height="30" rx="5" fill="#0d1017" stroke="#54dd9b"/><text x="48" y="63" fill="#54dd9b">head</text>
    <rect x="283" y="43" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="306" y="63" fill="#ffb454">19</text>
    <rect x="543" y="43" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="566" y="63" fill="#ffb454">38</text>
    <rect x="25" y="91" width="46" height="30" rx="5" fill="#0d1017" stroke="#54dd9b"/><text x="48" y="111" fill="#54dd9b">head</text>
    <rect x="153" y="91" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="176" y="111" fill="#ffb454">7</text>
    <rect x="283" y="91" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="306" y="111" fill="#ffb454">19</text>
    <rect x="543" y="91" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="566" y="111" fill="#ffb454">38</text>
    <rect x="25" y="139" width="46" height="30" rx="5" fill="#0d1017" stroke="#54dd9b"/><text x="48" y="159" fill="#54dd9b">head</text>
    <rect x="153" y="139" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="176" y="159" fill="#ffb454">7</text>
    <rect x="283" y="139" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="306" y="159" fill="#ffb454">19</text>
    <rect x="413" y="139" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="436" y="159" fill="#ffb454">26</text>
    <rect x="543" y="139" width="46" height="30" rx="5" fill="#13161f" stroke="#56c2ff"/><text x="566" y="159" fill="#ffb454">38</text>
  </g>
  <g stroke="#56c2ff" stroke-width="1.4" marker-end="url(#sk)">
    <path d="M71 58 L283 58"/><path d="M329 58 L543 58"/>
    <path d="M71 106 L153 106"/><path d="M199 106 L283 106"/><path d="M329 106 L543 106"/>
    <path d="M71 154 L153 154"/><path d="M199 154 L283 154"/><path d="M329 154 L413 154"/><path d="M459 154 L543 154"/>
  </g>
  <text x="330" y="196" fill="#9aa3b5" font-size="10" text-anchor="middle">向右走過頭就下降一層，逐層逼近目標 → ZSET range/score 查詢 O(log N)</text>
  <defs><marker id="sk" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 z" fill="#56c2ff"/></marker></defs>
</svg>
""".strip(),
        "scenario": "例如用 Redis ZSET 重構 時間序列/圖表資料快取，將圖表載入從 量化的延遲區間 降至 量化的延遲區間",
    },
    {
        "q": "SDS 與 C 字串有何不同？",
        "core": "SDS 依長度選擇不同 header（sdshdr8/16/32/64 等），記錄 len 與 alloc（除 sdshdr5 外），O(1) 取得長度；支援二進位安全（可含 \\0）；空間預分配與惰性釋放減少 realloc。C 字串以 \\0 結尾，strlen O(N)，不適合二進位 blob。",
        "dive": ["hdr 5/8/16/32/64 依長度選 header", "append 時若 free 夠則原位寫入", "相容部分 C 函數（以 \\0 結尾部分）"],
        "followups": [("String 最大 512MB？", "是 Redis 限制"), ("embstr vs raw？", "短字串 embstr 一次分配 header+buf")],
        "pitfalls": ["以為 Redis String 只是 char*"],
    },
    {
        "q": "RDB 持久化原理與優缺點？",
        "core": "RDB 是某時間點全量記憶體快照，fork 子行程寫 dump.rdb。利用作業系統的寫時複製（COW）機制，在主行程有寫入操作時才複製記憶體分頁。還原速度快、檔案小，但兩次快照間資料可能遺失（分鐘級）。",
        "dive": ["save/bgsave 觸發", "fork 瞬間 latency 可能抖動", "子行程寫完原子 rename"],
        "followups": [("fork 失敗？", "記憶體不足或 overcommit 關閉"), ("適合冷備？", "是，配合異地備份")],
        "pitfalls": ["大 instance fork 慢", "只做 RDB 無法秒級 RPO"],
    },
    {
        "q": "AOF 三種 fsync 策略？何時 rewrite？",
        "core": "always：每條命令 fsync，最安全最慢；everysec：每秒 fsync，預設，最多遺失 1 秒；no：OS 決定，最快最危險。AOF rewrite 由子行程依當前記憶體狀態重寫命令集，壓縮體積。Redis 7.0+ 採用 Multi-Part AOF 機制，將 AOF 拆分為 base、incremental 與 manifest 檔案，重寫時增量寫入新 incremental 檔案，完成後原子替換，避免舊版 rewrite 期間複雜的緩衝區累積。",
        "dive": ["Multi-Part AOF 機制（Redis 7.0+）", "混合持久化 RDB+AOF header 加速還原", "auto-aof-rewrite-min-size/percentage"],
        "followups": [("線上選 everysec？", "多數場景平衡"), ("rewrite 阻塞？", "fork+寫新檔，主行程仍服務")],
        "pitfalls": ["AOF 檔案無限增長未 rewrite", "always 在 SSD 上仍可能拖垮 IOPS"],
        "scenario": "交易/行情系統；關鍵狀態需 everysec 或混合",
    },
    {
        "q": "Redis 主從複製流程？",
        "core": "從節點 (Replica) 發送 PSYNC；全量：主節點 (Master) bgsave RDB 傳給從節點載入；增量：透過複製積壓緩衝區（repl_backlog）傳播後續命令。斷線重連 partial resync 若 offset 仍在 backlog 中。",
        "dive": ["repl_backlog 環形緩衝區", "replica 預設唯讀 (read-only)", "非同步複製，master 不等待 replica ack（除非使用 WAIT 命令）"],
        "followups": [("複製延遲？", "網路延遲 + replica 寫入速度"), ("腦裂？", "需 Sentinel/Cluster 自動容錯移轉 (Failover)")],
        "pitfalls": ["以為 replica 寫入會回傳 master", "backlog 太小導致頻繁全量複製"],
    },
    {
        "q": "Sentinel 與 Cluster 架構差異？",
        "core": "Sentinel：監控 master/replica，自動容錯移轉，用戶端向 Sentinel 查詢 master 位址；單分片 (shard)。Cluster：16384 slots 分片，多 master，節點間 Gossip 協定，MOVED/ASK 重新導向，水平擴充。",
        "dive": ["Cluster slot 遷移時 ASKING", "Sentinel quorum", "最少 3 master 建議 Cluster"],
        "followups": [("跨 slot 多 key？", "MGET 需在相同 slot；hash tag {user}:1"), ("Sentinel 腦裂？", "quorum+min-replicas")],
        "pitfalls": ["Cluster 大 key 遷移阻塞", "用戶端未支援 Cluster 協定"],
    },
    {
        "q": "記憶體淘汰策略 LRU/LFU/TTL？",
        "core": "maxmemory 達上限按 policy 淘汰：noeviction、allkeys-lru、volatile-lru、allkeys-lfu（4.0+）、volatile-ttl 等。近似 LRU 用取樣池，非精確 LRU。LFU 適合 hot key 穩定場景。",
        "dive": ["lazyfree 非同步刪除大 key", "maxmemory-policy 與持久化交互", "tracking 用戶端快取失效"],
        "followups": [("快取與 DB 一致性？", "見 cache-aside+TTL+canal"), ("OOM 行為？", "noeviction 寫入報錯")],
        "pitfalls": ["volatile-lru 只淘汰有 TTL key 可能 OOM", "大 key 刪除阻塞"],
    },
    {
        "q": "快取穿透、擊穿、雪崩如何解？",
        "core": "快取穿透：查不存在 key 打到 DB；解：布隆過濾器、空值快取、參數校驗。快取擊穿：熱點 key 過期瞬間大量請求 DB；解：互斥鎖重建、邏輯過期、永遠不過期+非同步更新。快取雪崩：大量 key 同時過期；解：TTL 加隨機擾動（Jitter）、多級快取、熔斷限流。",
        "dive": ["singleflight 合併回源", "Redis 叢集分片降低單點壓力", "本地快取 + Redis 二級快取"],
        "followups": [("布隆 false positive？", "存在可能誤判，不存在一定不存在"), ("互斥鎖用 SETNX？", "需過期+唯一 value+Lua 釋放")],
        "pitfalls": ["空值快取 TTL 過長佔滿記憶體", "互斥鎖未釋放死鎖"],
        "scenario": "例如修復 Redis 快取穿透：空值快取 + 布隆過濾器非法 ID",
    },
    {
        "q": "Redis 分散式鎖如何實現？Redlock 爭議？",
        "core": "單機：SET key uuid NX PX ttl，釋放用 Lua 比對 uuid 再 DEL。Redlock：多獨立 master 過半成功；爭議在 clock skew 與 GC pause 可能雙持鎖. 實務常單 Redis+ fencing token 或 etcd/ZooKeeper。",
        "dive": ["鎖續期看門狗機制 (watchdog)", "主從非同步複製導致鎖可能遺失", "fencing token 寫 DB 拒舊 token"],
        "followups": [("Redlock 還用嗎？", "Martin vs Antirez 論戰；高一致用 ZK"), ("鎖粒度？", "業務 id 級，TTL>最大執行時間")],
        "pitfalls": ["DEL 別人鎖", "無 TTL 死鎖", "鎖內做長 IO"],
    },
    {
        "q": "Hot key 與 Big key 問題？",
        "core": "Hot key：單 key QPS 過高，單 slot/單一執行緒瓶頸；解：本地快取 (local cache)、拆分 key（suffix 分片）、唯讀副本 (read replica)。Big key：大 hash/zset/list，刪除/序列化阻塞；解：拆分、UNLINK、分批 HSCAN。",
        "dive": ["Redis 6 IO 執行緒只加速網路 I/O", "hot key 發現：monitor、redis-cli --hotkeys", "big key：--bigkeys 掃描"],
        "followups": [("Cluster hot slot？", "reshard 或 hashtag 打散"), ("ZSET 百萬 member？", "按時間分 key")],
        "pitfalls": ["KEYS 找 big key 生產禁用", "熱 key 本地快取不一致"],
        "scenario": "時間序列/圖表資料 ZSET 按 symbol+interval 分 key，避免單 key 百萬 candle",
    },
    {
        "q": "Redis 6 Threaded I/O 解決什麼？",
        "core": "多執行緒處理 read/write/parse protocol，主執行緒仍執行命令。解決大連線數下網路 CPU 瓶頸，命令執行仍單執行緒（除 modules）。io-threads 與 io-threads-do-reads 配置。",
        "dive": ["預設 1 執行緒", "只對網路多執行緒處理", "memtier 基準可提升 QPS"],
        "followups": [("命令還是單執行緒？", "是，無需修改用戶端鎖"), ("與 Memcached 多執行緒比？", "Redis 選擇保持命令原子簡單")],
        "pitfalls": ["以為 IO 多執行緒=命令並行", "io-threads 設定過多導致頻繁上下文切換"],
    },
    {
        "q": "Redis 與 DB 一致性策略？",
        "core": "Cache-Aside：讀取未命中 (Miss) 查詢 DB 並寫入快取；寫入 DB 後刪除快取（或延遲雙刪）。強一致：分散式交易（Seata）、Canal 訂閱 binlog 更新快取、寫透 write-through。最終一致最常見。",
        "dive": ["先刪除快取再寫入 DB 仍可能不一致", "binlog+MQ 非同步更新", "version 欄位拒舊寫入"],
        "followups": [("先更新 DB 還是快取？", "一般先更新 DB 再刪除快取"), ("雙寫失敗？", "重試+補償+對帳")],
        "pitfalls": ["更新快取而非刪除導致並行髒讀", "無 TTL 兜底"],
        "scenario": "實務架構：時間序列/圖表資料寫入 MySQL 預存程序後刪除/更新 Redis ZSET，讀以快取為主、DB 為備援 (fallback)",
    },
    {
        "q": "Pipeline 與 Transaction 差異？",
        "core": "Pipeline：批量發命令減 RTT，無原子性保證。MULTI/EXEC：命令排隊，EXEC 原子執行，樂觀鎖 WATCH。Lua 腳本：原子執行複雜邏輯，應控制執行時間。",
        "dive": ["Pipeline 不需要交易", "交易不支援回滾，若 EXEC 期間某命令發生執行期錯誤，其餘命令仍會繼續執行且不回滾", "Lua redis.call 錯誤回滾腳本"],
        "followups": [("Pipeline 大小？", "分批避免 buffer 爆"), ("WATCH 衝突？", "EXEC nil 需重試")],
        "pitfalls": ["Lua 腳本過長阻塞", "把 Pipeline 當作交易"],
    },
    {
        "q": "HyperLogLog、Bitmap、GEO 應用？",
        "core": "HLL：近似基數 O(1) 記憶體；Bitmap：點陣圖簽到/線上使用者；GEO：geohash+ZSET 附近的人。Stream：Consumer Group 訊息流，類似 Kafka lite。",
        "dive": ["HLL 標準誤差 0.81%", "Bitmap offset=userid", "XREADGROUP ACK 至少一次"],
        "followups": [("HLL 合併？", "PFMERGE"), ("Stream vs List？", "Stream 有 ack/consumer group")],
        "pitfalls": ["HLL 不能取得具體元素", "Bitmap 使用者 id 過大需分片"],
    },
    {
        "q": "Redis 過期刪除策略？",
        "core": "惰性刪除：存取時檢查過期。定期刪除：隨機抽樣刪除過期 key。記憶體淘汰是另一機制。TTL 支援毫秒級精度（PEXPIRE/PTTL），內部以毫秒時間戳記儲存。key 不存在與 expired 皆返回 nil。",
        "dive": ["過期字典 (expires dict) 與鍵值字典 (dict) 分離", "持久化 RDB 不會載入已過期 key", "AOF 刪除時會向 AOF 檔案追加一條 DEL 命令"],
        "followups": [("大量 key 同時過期？", "可能引發 CPU 抖動，過期時間加隨機擾動 (jitter)"), ("TTL -1/-2？", "-1 無 TTL，-2 不存在")],
        "pitfalls": ["依賴 expire 做精確排程", "過期 key 仍佔記憶體直到被刪除"],
    },
    {
        "q": "Redis 為什麼單執行緒還這麼快？",
        "core": "純記憶體操作、高效的資料結構、I/O 多工 (epoll)、避免鎖競爭與執行緒上下文切換。瓶頸常在網路或記憶體而非 CPU。6.0+ I/O 執行緒進一步解放網路 I/O 效能。",
        "dive": ["單執行緒簡化原子語意", "O(N) 命令如 KEYS 仍極度危險", "持久化 fork 是額外開銷"],
        "followups": [("多核如何利用？", "多實例/sharded cluster"), ("與 Memcached 比？", "Redis 資料結構更豐富")],
        "pitfalls": ["單執行緒執行慢命令拖垮全域"],
    },
    {
        "q": "Redis 叢集 rebalance 與 slot 遷移？",
        "core": "reshard 將 slot 從 A 移到 B：IMPORTING/EXPORTING 狀態，MIGRATE key，原子 slot 中繼資料更新。遷移期間 ASK 重新導向。",
        "dive": ["MIGRATE 可原子搬移 key", "大 slot 遷移時間長", "用戶端需支援智慧路由 (smart routing)"],
        "followups": [("遷移阻塞？", "單 key 原子，整體漸進"), ("擴縮容計劃？", "低峰期+限速")],
        "pitfalls": ["遷移中斷需恢復", "無 hash tag 的 multi-key 跨 slot"],
    },
    {
        "q": "Redis 慢查詢如何排查？",
        "core": "SLOWLOG 記錄超過 slowlog-log-slower-than 的命令。latency doctor/latency history 診斷。避免 O(N) 命令、大 value、fork、AOF rewrite 疊加。",
        "dive": ["CONFIG SET slowlog-log-slower-than", "LATENCY GRAPH 分類", "記憶體碎片化 (memory fragmentation)"],
        "followups": [("ZREVRANGE 大 range？", "限制 count"), ("MONITOR 生產？", "禁用，開銷極大")],
        "pitfalls": ["HGETALL 百萬 field", "生產環境 KEYS *"],
    },
    {
        "q": "Redis 交易能保證隔離嗎？",
        "core": "MULTI/EXEC 提供順序執行與批次原子性，無回滾。無隔離層級概念；WATCH 提供 CAS 樂觀鎖。",
        "dive": ["DISCARD 取消", "EXEC 時 watched key 變更則整個交易 abort", "與資料庫 ACID 不同"],
        "followups": [("需要回滾？", "使用 Lua 腳本"), ("交易中間可見？", "其他用戶端看不見 QUEUE 內容")],
        "pitfalls": ["以為 EXEC 失敗全部回滾"],
    },
    {
        "q": "Redis 在 K 線/OHLC 場景的資料模型？",
        "core": "ZSET score=timestamp member=OHLC JSON 或緊湊二進位；按 symbol:interval 分鍵；ZREVRANGEBYSCORE 拉取最近 N 根；最新價可用 String/HASH。寫入 batch ZADD pipeline。",
        "dive": ["定期 trim ZREMRANGEBYRANK", "與 MySQL 預存程序 (SP) 聚合分工", "MGET 多 symbol 並行"],
        "followups": [("毫秒 K 線？", "score 用毫秒時間戳記"), ("重複 K 線？", "ZADD NX 或在 member 中加入版本號")],
        "pitfalls": ["單鍵儲存全歷史", "無 trim 導致記憶體爆炸"],
        "scenario": "例如優化：MySQL SP 聚合 + Redis ZSET 分鍵 + 索引重建，延遲 量化的延遲區間→量化的延遲區間",
    },
]

MYSQL_TOPICS = [
    {
        "q": "InnoDB 與 MyISAM 核心差異？",
        "core": "InnoDB：列鎖 (Row Lock)、MVCC、交易支援、崩潰復原（redo/undo log）、聚集索引 (Clustered Index)。MyISAM：表鎖 (Table Lock)、無交易、非聚集索引、count(*) 快（有專門計數器）但寫入不安全. 生產環境 OLTP 幾乎全用 InnoDB。",
        "dive": ["InnoDB buffer pool 快取資料頁", "MyISAM 適合唯讀 archive", "InnoDB 主鍵即資料本身"],
        "followups": [("為何 count(*) 慢？", "InnoDB 估算或全表掃描 vs MyISAM 讀計數器"), ("MyISAM 還用在哪？", "極少，legacy 舊系統")],
        "pitfalls": ["混用引擎無法保證交易", "無 PK 的 InnoDB 表會使用隱式 row_id"],
    },
    {
        "q": "B+ 樹索引為何適合 MySQL？",
        "core": "B+ 樹多路平衡，樹高低（3-4 層可容納百萬行）、磁碟 I/O 少；非葉子節點僅儲存鍵值與分岔指標，擁有極高的分支因子 (Fanout)；葉子節點包含所有資料並以雙向鏈結串列相連，能完美支援範圍掃描 (Range Scan)。相比 B 樹（非葉子節點亦存資料）能減少樹高；相比哈希不支援排序與範圍查詢。",
        "dive": ["資料頁預設 16KB", "聚集索引葉子節點 = 行資料本身", "二級索引（輔助索引）葉子節點 = 主鍵值（需回表）"],
        "followups": [("為何不用紅黑樹？", "紅黑樹是二叉樹，樹高過高，導致磁碟 I/O 次數多"), ("UUID PK 問題？", "隨機插入導致頻繁的頁分裂與隨機 I/O")],
        "pitfalls": ["過寬的主鍵會大幅增大二級索引體積", "在索引欄位上使用函數導致索引失效"],
        "svg": """
<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="B+ 樹：非葉只存 key，葉子鏈結支援 range scan">
  <g text-anchor="middle" font-size="12">
    <rect x="270" y="34" width="120" height="34" rx="5" fill="#13161f" stroke="#56c2ff" stroke-width="1.5"/>
    <text x="300" y="56" fill="#ffb454">30</text><text x="360" y="56" fill="#ffb454">60</text>
    <line x1="330" y1="34" x2="330" y2="68" stroke="#2f3645"/>
    <rect x="40" y="138" width="140" height="34" rx="5" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
    <text x="75" y="160" fill="#e7eaf2">10</text><text x="115" y="160" fill="#e7eaf2">20</text>
    <rect x="262" y="138" width="160" height="34" rx="5" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
    <text x="292" y="160" fill="#e7eaf2">30</text><text x="342" y="160" fill="#e7eaf2">40</text><text x="392" y="160" fill="#e7eaf2">50</text>
    <rect x="500" y="138" width="140" height="34" rx="5" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
    <text x="535" y="160" fill="#e7eaf2">60</text><text x="575" y="160" fill="#e7eaf2">70</text>
  </g>
  <g stroke="#56c2ff" stroke-width="1.4" marker-end="url(#bt)" fill="none">
    <path d="M300 68 Q200 100 110 136"/>
    <path d="M330 68 L340 136"/>
    <path d="M360 68 Q470 100 568 136"/>
  </g>
  <g stroke="#ffb454" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#btl)" fill="none">
    <path d="M180 155 L260 155"/>
    <path d="M422 155 L498 155"/>
  </g>
  <text x="330" y="206" fill="#9aa3b5" font-size="11" text-anchor="middle">非葉節點只存 key（高 fanout，樹高 3~4 層）；葉子節點鏈結支援 range scan</text>
  <defs>
    <marker id="bt" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#56c2ff"/></marker>
    <marker id="btl" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#ffb454"/></marker>
  </defs>
</svg>
""".strip(),
        "scenario": "K 线表 rebuild index 优化 time range 查询",
    },
    {
        "q": "聚簇索引與二級索引？回表與覆蓋索引？",
        "core": "InnoDB 表資料按主鍵 (PK) 聚簇儲存；二級索引（次級索引）儲存格式為 (index_col, PK)。查詢需回表：先查二級索引取得 PK 值，再至聚簇索引查完整行資料。覆蓋索引：SELECT 所需列均在二級索引中，無需回表（Using index）。",
        "dive": ["ICP 索引下推減少回表過濾次數", "MRR（Multi-Range Read）排序 PK 進行批次回表", "聯合索引遵循最左前綴原則"],
        "followups": [("無 PK？", "選擇唯一非空欄位，或由 InnoDB 生成隱式 row_id"), ("二級索引越多越好？", "會帶來寫入放大與優化器選擇成本")],
        "pitfalls": ["濫用 SELECT * 導致覆蓋索引失效", "隱式型態轉換導致索引失效"],
    },
    {
        "q": "MVCC 原理？Read View 如何判斷可見性？",
        "core": "每行資料含有隱式欄位 DB_TRX_ID、DB_ROLL_PTR，並透過 undo log 鏈組成歷史版本。Read View 包含 m_ids（活躍交易 ID 列表）、min_trx_id（活躍交易最小值）、max_trx_id（下一個將分配的交易 ID）。可見性規則：1) trx_id == creator_trx_id → 可見；2) trx_id < min_trx_id → 已提交，可見；3) trx_id >= max_trx_id → 建立後開啟，不可見；4) min <= trx_id < max 且不在 m_ids 中 → 已提交，可見；其餘不可見。RR 在首次讀取時建立 View，RC 每次讀取皆新建。",
        "dive": ["undo log 儲存舊版本", "delete mark 僅作刪除標記而未立即實體刪除", "purge 執行緒清理不再被 any Read View 需要的 undo log"],
        "followups": [("RR 如何避免幻讀？", "快照讀靠 MVCC；目前讀 (Current Read) 靠間隙鎖 (Gap Lock)"), ("長交易危害？", "導致 undo log 堆積，阻止 purge 執行緒清理，使資料表膨脹")],
        "pitfalls": ["以為 MVCC 完全無鎖", "RC 下使用 binlog statement 格式可能導致主從不一致歷史問題"],
        "svg": """
<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MVCC 版本鏈：DB_ROLL_PTR 沿 undo log 回溯，Read View 決定可見性">
  <rect x="20" y="34" width="620" height="40" rx="8" fill="#0d1017" stroke="#c79cff" stroke-width="1.3"/>
  <text x="330" y="59" fill="#c79cff" font-size="12" text-anchor="middle">Read View：活躍 m_ids = {50}，min_trx_id = 50（trx 50 未提交，對讀取者不可見）</text>
  <rect x="40" y="104" width="150" height="76" rx="8" fill="#13161f" stroke="#ff6b6b" stroke-width="1.5"/>
  <text x="115" y="128" fill="#ff6b6b" font-size="12" text-anchor="middle">最新版本</text>
  <text x="115" y="148" fill="#e7eaf2" font-size="11" text-anchor="middle">DB_TRX_ID = 50</text>
  <text x="115" y="166" fill="#9aa3b5" font-size="10" text-anchor="middle">活躍/未提交</text>
  <rect x="255" y="104" width="150" height="76" rx="8" fill="#13161f" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="330" y="128" fill="#54dd9b" font-size="12" text-anchor="middle">undo 版本</text>
  <text x="330" y="148" fill="#e7eaf2" font-size="11" text-anchor="middle">DB_TRX_ID = 30</text>
  <text x="330" y="166" fill="#9aa3b5" font-size="10" text-anchor="middle">已提交 → 命中</text>
  <rect x="470" y="104" width="150" height="76" rx="8" fill="#13161f" stroke="#2f3645" stroke-width="1.5"/>
  <text x="545" y="128" fill="#9aa3b5" font-size="12" text-anchor="middle">undo 版本</text>
  <text x="545" y="148" fill="#e7eaf2" font-size="11" text-anchor="middle">DB_TRX_ID = 20</text>
  <text x="545" y="166" fill="#9aa3b5" font-size="10" text-anchor="middle">更舊</text>
  <path d="M190 142 L253 142" stroke="#ffb454" stroke-width="1.6" marker-end="url(#mv)"/>
  <text x="221" y="134" fill="#ffb454" font-size="9" text-anchor="middle">roll_ptr</text>
  <path d="M405 142 L468 142" stroke="#ffb454" stroke-width="1.6" marker-end="url(#mv)"/>
  <text x="436" y="134" fill="#ffb454" font-size="9" text-anchor="middle">roll_ptr</text>
  <text x="330" y="214" fill="#9aa3b5" font-size="11" text-anchor="middle">讀取者沿 roll_ptr 回溯 undo log：跳過活躍的 trx 50 → 命中已提交的 trx 30</text>
  <defs><marker id="mv" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#ffb454"/></marker></defs>
</svg>
""".strip(),
    },
    {
        "q": "四種隔離層級與現象？",
        "core": "RU：髒讀（Read Uncommitted）。RC：無髒讀，但有不可重複讀（Read Committed）。RR：快照讀藉由 MVCC 避免不可重複讀，目前讀 (Current Read) 藉由間隙鎖防幻讀（InnoDB 預設）。Serializable：所有讀取皆加鎖，效能最差。",
        "dive": ["快照讀 (Snapshot Read) vs 目前讀 (Current Read)", "間隙鎖 (Gap Lock) 與 Next-key Lock", "Semi-consistent read 最佳化"],
        "followups": [("RR 隔離層級一定無幻讀？", "非也。若先快照讀，隨後執行 UPDATE 修改了其他交易剛提交的新插入列，則會將該列的 trx_id 改為自己，導致後續讀取產生幻讀；寫入偏斜 (Write Skew) 也需注意"), ("為何很多生產環境使用 RC？", "鎖定範圍小、死鎖機率低，且對 binlog row 格式友好")],
        "pitfalls": ["混用 FOR UPDATE 與普通 SELECT 造成認知不一致", "間隙鎖導致死鎖"],
    },
    {
        "q": "InnoDB 鎖類型？Record/Gap/Next-Key？",
        "core": "Record lock 鎖定索引記錄；Gap lock 鎖定間隙防插入；Next-key = Record + Gap 鎖。插入意向鎖（Insert Intention Lock）與 Gap/Next-Key 鎖互斥，當間隙被鎖定時插入會阻塞。無索引欄位更新會導致全表掃描並鎖定所有掃描行，並非鎖升級（InnoDB 無鎖升級機制）。",
        "dive": ["表級意向鎖 IS/IX", "AUTO-inc 鎖", "中繼資料鎖 (Metadata Lock)"],
        "followups": [("死鎖日誌？", "SHOW ENGINE INNODB STATUS"), ("如何減少鎖定？", "利用精確索引、縮短交易、使用 RC")],
        "pitfalls": ["varchar 未加引號導致隱式轉換使索引失效鎖全表", "範圍更新在無索引時加鎖範圍巨大"],
    },
    {
        "q": "死鎖如何產生與排查？",
        "core": "兩個交易以不同順序鎖定資源，形成循環等待。InnoDB 會自動偵測並選擇回滾代價最小的交易。排查：SHOW ENGINE INNODB STATUS、performance_schema.data_locks。",
        "dive": ["應用層固定鎖定順序", "合理的重試機制", "縮小交易範圍"],
        "followups": [("間隙鎖死鎖例子？", "兩個交易同時在同一個間隙取得 Gap 鎖，並隨後嘗試寫入該間隙"), ("死鎖監控？", "開啟 innodb_print_all_deadlocks")],
        "pitfalls": ["捕獲死鎖異常卻未在應用層進行重試", "長交易持有鎖定時間過長"],
    },
    {
        "q": "redo log 與 undo log 與 binlog 區別？",
        "core": "redo log：InnoDB 專屬物理頁修改日誌，用於崩潰復原（Crash Recovery），循環寫入。undo log：保存歷史版本，用於交易回滾與 MVCC。binlog：MySQL Server 層邏輯日誌，用於主從複製與 point-in-time 還原。兩階段提交（2PC）用於協調 redo 與 binlog 的一致性。",
        "dive": ["WAL（Write-Ahead Logging）：先寫日誌，再刷髒頁", "binlog 格式：Row、Statement、Mixed", "sync_binlog=1 與 innodb_flush_log_at_trx_commit=1 最安全雙一配置"],
        "followups": [("redo 循環覆蓋？", "覆蓋舊 checkpoint 前必須將對應髒頁刷盤"), ("半同步複製？", "主庫寫入後需等待至少一個從庫的 ACK 回包")],
        "pitfalls": ["binlog 使用 statement 格式導致主從不一致", "redo log 空間不足阻塞寫入"],
    },
    {
        "q": "兩階段提交（2PC）在 MySQL 中？",
        "core": "交易提交時：1) redo log prepare 2) 寫入 binlog 3) redo log commit。崩潰復原時以 binlog 是否寫入為準協調：若 binlog已寫入但 redo 處於 prepare，則提交交易；若無 binlog 且 redo 處於 prepare，則回滾交易。保證 redo 與 binlog 資料一致。",
        "dive": ["XID 關聯標識", "群組提交 (Group Commit) 最佳化 fsync 頻率", "分散式 XA 交易是另一概念"],
        "followups": [("為何需要 binlog 與 redo 兩套？", "redo 是引擎層的崩潰復原保證；binlog 是 Server 層的複製與還原基礎"), ("遺失 binlog 危害？", "會導致主從資料不一致")],
        "pitfalls": ["誤以為 redo log 是用於主從複製的"],
    },
    {
        "q": "慢查詢如何分析與最佳化？",
        "core": "開啟 slow_query_log、long_query_time；使用 EXPLAIN 分析 type、key、rows、Extra 欄位。最佳化手段：建立精確索引、改寫 SQL、拆分查詢、引入快取。避免 SELECT *、欄位套用函數、隱式型態轉換。",
        "dive": ["EXPLAIN ANALYZE 實際執行計畫與耗時", "pt-query-digest 聚合分析", "optimizer trace 追蹤最佳化器決策"],
        "followups": [("type 為 ALL 一定壞？", "極小表全表掃描比走索引快"), ("filesort 最佳化？", "利用索引的有序性消除 filesort")],
        "pitfalls": ["只關注 rows 而忽略了 filtered 欄位", "上線複雜 SQL 前未進行 EXPLAIN 檢查"],
        "scenario": "例如用 EXPLAIN + index rebuild 优化 K 线聚合 SP",
    },
    {
        "q": "聯合索引與最左前綴？",
        "core": "索引 (a,b,c) 可用於 a、ab、abc 條件；跳過 b 單用 c 則無法發揮索引定位作用。欄位順序設計：高選擇性、常查欄位靠前；等值查詢欄位在前，範圍查詢欄位在後（因範圍查詢後的索引欄位無法用於精確定位）。",
        "dive": ["索引合併 index_merge", "覆蓋索引包含所有查詢列", "前綴索引省空間但無法用於排序"],
        "followups": [("條件 (a,b) 只查 b？", "通常無法走索引，除非觸發 8.0 Index Skip Scan"), ("order by b,c 走索引？", "需要最左 a 欄位為等值條件匹配")],
        "pitfalls": ["範圍欄位後面的索引欄位失效", "重複建立多個多餘索引"],
    },
    {
        "q": "索引下推（ICP）是什麼？",
        "core": "MySQL 5.6+ 引入。在二級索引掃描時，儲存引擎層會先利用索引列過濾 WHERE 條件，符合條件後再進行回表，大幅減少回表次數。Extra 顯示 Using index condition。",
        "dive": ["僅適用於 InnoDB 二級索引", "包含主鍵欄位的條件下推", "與覆蓋索引不同，覆蓋索引是不需要回表"],
        "followups": [("何時無效？", "聚簇索引掃描時"), ("效能提升場景？", "二級索引中包含部分未走最左前綴的過濾條件")],
        "pitfalls": ["以為 ICP 與覆蓋索引是同一個概念"],
    },
    {
        "q": "索引失效常見場景？",
        "core": "對欄位進行函數運算、隱式型態轉換（如字串與數字比較）、使用 like '%x' 前導模糊、OR 連接一側無索引、使用不等於 (<> / !=)、最佳化器估算成本過高（統計資訊過舊）、聯合索引違反最左字首原則。",
        "dive": ["force index 強制走索引（慎用）", "analyze table 更新過時統計資訊", "8.0 直方圖 (Histogram) 最佳化估算"],
        "followups": [("!= 一定不走索引？", "若選擇性極高，最佳化器仍可能選擇索引"), ("字元集轉換失效？", "關聯欄位字元集不同（如 utf8mb4 與 utf8）導致隱式轉換")],
        "pitfalls": ["SQL 改寫後未重新 explain 驗證", "MRR/ICP 被最佳化器誤判"],
    },
    {
        "q": "預存程序 (Stored Procedure) 優缺點？K 線（OHLC）場景如何用？",
        "core": "預存程序在資料庫內部聚合以減少網路來回 (network round-trip)、適合封裝複雜 OHLC 邏輯。缺點：版本管理與 CI/CD 難、除錯弱、佔用資料庫 CPU/記憶體資源、移植性差。實務上在寫入端利用預存程序進行 K 線聚合與異常 duplicate 清洗。",
        "dive": ["與 app 層職責劃分", "Prepared Statement 的效能優勢", "預存程序內的安全防範（防 SQL 注入）"],
        "followups": [("何時不建議使用？", "業務邏輯複雜且變更頻繁時"), ("效能權衡？", "減少網路傳輸但將計算壓力轉移到 DB")],
        "pitfalls": ["預存程序內無索引導致全表掃描", "業務邏輯散落於 app 與 SP 中難以維護"],
        "scenario": "例如：MySQL SP 聚合 K 線 + index rebuild，配合 Redis ZSET，延遲 量化的延遲區間→量化的延遲區間",
    },
    {
        "q": "主從複製原理與延遲？",
        "core": "主庫 binlog → 從庫 I/O 執行緒寫入中繼日誌 (relay log) → SQL 執行緒重放。預設為非同步複製；半同步複製至少等待一個從庫 ACK；GTID 簡化故障切換。平行複製（基於 Write Set 或交易提交時間戳記）可降低延遲。",
        "dive": ["中繼日誌 (relay log) 機制", "讀寫分離下的過期髒讀問題", "Seconds_Behind_Master 的不準確性"],
        "followups": [("延遲過大原因？", "大交易、從庫硬體瓶頸、單執行緒 apply 限制"), ("雙主 (Active-Active) 限制？", "需防範雙向寫入衝突與自增 ID 重複")],
        "pitfalls": ["從庫讀取 RR 級別仍可能讀到舊資料", "大表 DDL 導致主從複製嚴重延遲"],
    },
    {
        "q": "分庫分表策略？",
        "core": "垂直分割：按業務模組拆分資料庫。水平分割：選定 Shard Key 進行 Hash/Range 分片。挑戰：跨 Shard Join 效能極差、分散式唯一 ID、擴充時資料遷移與平衡。常見中介軟體：ShardingSphere、Vitess。",
        "dive": ["Snowflake 雪花演算法產生唯一 ID", "全局次級索引表設計", "雙倍擴充遷移法（降低停機時間）"],
        "followups": [("Shard Key 選擇 user_id 的優劣？", "優點為使用者相關資料內聚，缺點為易產生熱點使用者"), ("分散式交易？", "二階段提交 XA 或基於 MQ 的最終一致性 TCC/Saga")],
        "pitfalls": ["熱點 Shard 導致單點負載過高", "跨 Shard 進行排序與分頁操作 (LIMIT/OFFSET)"],
        "svg": """
<svg viewBox="0 0 660 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="一致性哈希環：key 順時針落到下一個節點，增刪節點僅影響相鄰區段">
  <circle cx="330" cy="150" r="104" fill="none" stroke="#2f3645" stroke-width="1.5"/>
  <circle cx="330" cy="46" r="12" fill="#54dd9b"/><text x="330" y="32" fill="#54dd9b" font-size="12" text-anchor="middle">Node A</text>
  <circle cx="420" cy="202" r="12" fill="#54dd9b"/><text x="452" y="222" fill="#54dd9b" font-size="12" text-anchor="middle">Node B</text>
  <circle cx="240" cy="202" r="12" fill="#54dd9b"/><text x="208" y="222" fill="#54dd9b" font-size="12" text-anchor="middle">Node C</text>
  <circle cx="397" cy="70" r="7" fill="#ffb454"/><text x="412" y="62" fill="#ffb454" font-size="11">k1</text>
  <circle cx="312" cy="252" r="7" fill="#ffb454"/><text x="312" y="274" fill="#ffb454" font-size="11" text-anchor="middle">k2</text>
  <circle cx="232" cy="114" r="7" fill="#ffb454"/><text x="214" y="108" fill="#ffb454" font-size="11">k3</text>
  <g stroke="#c79cff" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#hr)" fill="none">
    <path d="M403 78 Q430 140 418 190"/>
    <path d="M305 256 Q270 240 250 212"/>
    <path d="M238 108 Q290 60 322 52"/>
  </g>
  <text x="330" y="160" fill="#9aa3b5" font-size="11" text-anchor="middle">key 順時針</text>
  <text x="330" y="178" fill="#9aa3b5" font-size="11" text-anchor="middle">落到下一個節點</text>
  <text x="330" y="285" fill="#9aa3b5" font-size="10" text-anchor="middle">增刪節點只需搬遷相鄰區段的 key，避免全量 rehash（虛擬節點可均衡負載）</text>
  <defs><marker id="hr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#c79cff"/></marker></defs>
</svg>
""".strip(),
    },
    {
        "q": "MySQL 連線池如何配置？",
        "core": "使用 HikariCP 或 Go sql.DB 時設定：max_open_conns、max_idle_conns、conn_max_lifetime。連線數過大會耗盡 DB 記憶體/執行緒資源；過小會造成請求排隊。常用經驗公式：connections ≈ (core*2) + disk_spindle，仍需依實際業務進行壓測調整。",
        "dive": ["wait_timeout 與 conn_max_lifetime 的匹配", "Prepared Statement 快取設定", "連線洩漏 (Connection Leak) 偵測"],
        "followups": [("Go sql.DB 預設？", "預設無限制，高流量下極度危險"), ("RDS max_connections 限制？", "通常與資料庫實例規格（CPU/記憶體）正相關")],
        "pitfalls": ["未設定逾時時間 (Timeout)", "長交易佔用連線不釋放"],
    },
    {
        "q": "ORDER BY 與 GROUP BY 最佳化？",
        "core": "利用索引的有序性避免 filesort（Extra 顯示 Using filesort 即為硬體排序）。GROUP BY 可利用鬆散索引掃描 (Loose Index Scan)。當暫存表超出 tmp_table_size 限制時會寫入磁碟，導致效能暴跌。",
        "dive": ["only_full_group_by 語法限制", "distinct vs group by 的最佳化選擇", "MySQL 8.0 視窗函數 (Window Functions)"],
        "followups": [("filesort 演算法？", "單路排序 vs 雙路排序 (sort_buffer_size)"), ("深度分頁最佳化？", "利用延遲關聯 (Deferred Join)")],
        "pitfalls": ["對非索引欄位進行 GROUP BY", "大型 GROUP BY 導致記憶體溢出寫入磁碟"],
    },
    {
        "q": "InnoDB Buffer Pool 機制？",
        "core": "快取資料頁與索引頁，採用改進型 LRU 演算法（分為 young/old 兩區域，以 midpoint 劃分，防止全表掃描污染快取）。髒頁 (Dirty Page) 由 redo log 保護，透過 checkpoint 機制非同步刷盤。生產環境快取命中率應達 99% 以上。",
        "dive": ["Change Buffer：對非唯一二級索引寫入的快取最佳化", "Doublewrite Buffer：雙寫緩衝區防範半頁寫入 (Partial Page Write) 損壞", "innodb_buffer_pool_size 設定為系統記憶體的 70-80%"],
        "followups": [("Buffer Pool 預熱？", "重啟時自動 dump 與 load 快取頁結構"), ("頁淘汰邏輯？", "優先淘汰乾淨頁，髒頁則會觸發非同步 flush")],
        "pitfalls": ["Buffer Pool 設定過小導致頻繁磁碟 I/O", "未監控快取命中率 (Hit Rate)"],
    },
    {
        "q": "如何設計 K 線/OHLC 表結構？",
        "core": "建立資料表：主鍵或唯一索引為 (symbol_id, interval, open_time)；包含 open/high/low/close/volume 等欄位。建立索引 (symbol_id, interval, open_time DESC)。歷史資料分區：使用 BY RANGE(open_time) 進行歷史分割區管理。寫入使用 ON DUPLICATE KEY UPDATE 實現冪等 upsert。",
        "dive": ["與 Redis ZSET 職責分工：DB 作為權威存儲，ZSET 提供熱區間高速查詢", "利用預存程序聚合 tick → candle", "異常 duplicate 數據的清洗"],
        "followups": [("分表策略？", "按 symbol_id 進行 hash 分表，或按時間進行分區"), ("Tick 級數據？", "建議使用時序資料庫 (Time-Series DB) 如 InfluxDB/TimescaleDB")],
        "pitfalls": ["無唯一約束導致重複的 K 線", "範圍查詢未命中索引"],
        "scenario": "例如經驗：SP 清洗 duplicate + index rebuild + Redis ZSET 热数据",
    },
    {
        "q": "線上對大表加索引/改欄位如何不鎖表？（gh-ost / pt-osc）",
        "core": "MySQL 5.6+ 支援 Online DDL（ALGORITHM=INPLACE, LOCK=NONE），多數加索引可線上完成，但修改欄位型態、加全文索引等仍會重建表 (rebuild table) 或短暫鎖定。大表生產環境常用 gh-ost 或 pt-online-schema-change：建影子表 → 透過 binlog (gh-ost) 或觸發器 (pt-osc) 同步增量 → 分批複製舊資料 → 原子 rename 切換，避免長時間鎖定與主從延遲堆積。",
        "dive": [
            "pt-osc 使用觸發器同步原表變更；gh-ost 解析 binlog 同步，無觸發器開銷，對主庫更輕量且可動態限流/暫停",
            "INPLACE vs COPY：COPY 重建整表並鎖定；INSTANT（8.0.12+）可即時完成，且自 8.0.29 起支援在表中任意位置新增與刪除欄位",
            "需預留磁碟空間（容納影子表）、控制 chunk 複製大小與 replica lag 複製延遲閾值",
        ],
        "followups": [
            ("gh-ost 為何比 pt-osc 對主庫友善？", "不用觸發器、改讀 binlog，可動態限流/暫停，降低主庫負載"),
            ("8.0 INSTANT DDL 限制？", "MySQL 8.0.29+ 已支援任意位置加/刪欄位，但修改欄位型態或縮減欄位長度仍不支持"),
        ],
        "pitfalls": ["直接對大表進行 ALTER 導致長時間鎖表與主從複製延遲", "未監控從庫複製延遲，切換時下游讀到不一致資料", "磁碟空間不足導致影子表建立失敗"],
        "scenario": "時間序列/圖表資料表 rebuild index 時需考量線上變更策略，避免鎖住交易/行情讀路徑",
    },
]

# -*- coding: utf-8 -*-
"""Redis and MySQL interview topics."""

REDIS_TOPICS = [
    {
        "q": "Redis 五種基本資料結構及其底層實現？",
        "core": "String(SDS)、List(quicklist=ziplist+linkedlist)、Hash(ziplist/hashtable)、Set(intset/hashtable)、ZSET(ziplist/skiplist+hashtable)。Redis 依元素數量與大小在 compact 編碼與 hashtable 間自動轉換，以平衡記憶體與 O(1)/O(logN) 操作。",
        "dive": [
            "SDS：O(1) 取長度、二進制安全、預分配減少 realloc",
            "skiplist：多層索引，ZSET range/score 查詢 O(logN)",
            "ziplist：連續記憶體，小 hash/zset 省空間",
            "encoding 轉換不可逆（大→小需主動刪重建）",
        ],
        "followups": [
            ("K 線場景為何用 ZSET？", "score=時間戳，member=OHLC JSON；ZREVRANGEBYSCORE 取時間窗 O(logN+M)"),
            ("intset 何時用？", "set 全為整數且元素少時"),
        ],
        "pitfalls": ["大 ziplist 轉 hashtable 造成 latency spike", "誤用 KEYS * 阻塞"],
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
        "resume": "實務上用 Redis ZSET 重構 K 線快取，將圖表載入從 3–5s 降至 300–500ms。",
    },
    {
        "q": "SDS 與 C 字串有何不同？",
        "core": "SDS 記錄 len 與 free，O(1) 取長度；支援二進制安全（含 \\0）；預分配策略減少 realloc；buf 可含未使用空間。C 字串以 \\0 結尾，strlen O(N)，不適合二進制 blob。",
        "dive": ["hdr 5/8/16/32/64 依長度選 header", "append 時若 free 夠則原地寫", "兼容部分 C 函數（以 \\0 結尾部分）"],
        "followups": [("String 最大 512MB？", "是 Redis 限制"), ("embstr vs raw？", "短字串 embstr 一次分配 header+buf")],
        "pitfalls": ["以為 Redis String 只是 char*"],
    },
    {
        "q": "RDB 持久化原理與優缺點？",
        "core": "RDB 是某時間點全量記憶體快照，fork 子進程寫 dump.rdb。COW 複製頁，寫時複製增加記憶體。恢復快、檔小，但兩次快照間資料可能丟失（分鐘級）。",
        "dive": ["save/bgsave 觸發", "fork 瞬間 latency 可能抖動", "子進程寫完原子 rename"],
        "followups": [("fork 失敗？", "記憶體不足或 overcommit 關閉"), ("適合冷備？", "是，配合異地備份")],
        "pitfalls": ["大 instance fork 慢", "只做 RDB 無法秒級 RPO"],
    },
    {
        "q": "AOF 三種 fsync 策略？何時 rewrite？",
        "core": "always：每條命令 fsync，最安全最慢；everysec：每秒 fsync，預設，最多丟 1 秒；no：OS 決定，最快最危險。AOF rewrite 由子進程依當前記憶體狀態重寫命令集，壓縮體積，bgrewriteaof 觸發。",
        "dive": ["rewrite 期間增量 buf 累積", "混合持久化 RDB+AOF header 加速恢復", "auto-aof-rewrite-min-size/percentage"],
        "followups": [("線上選 everysec？", "多數場景平衡"), ("rewrite 阻塞？", "fork+寫新檔，主進程仍服務")],
        "pitfalls": ["AOF 檔無限增長未 rewrite", "always 在 SSD 上仍可能拖垮 IOPS"],
        "resume": "在交易所場景評估 RPO：行情快取可重建用 RDB+短 AOF；關鍵狀態需 everysec 或混合。",
    },
    {
        "q": "Redis 主從複製流程？",
        "core": "replica 發 PSYNC；全量：master bgsave RDB 傳 replica 載入；增量：複製緩衝區 propagation 後續命令。斷線重連 partial resync 若 offset 仍在 backlog。",
        "dive": ["repl_backlog 環形緩衝", "replica 預設 read-only", "複製異步，master 不等待 replica ack（除非 WAIT）"],
        "followups": [("複製延遲？", "network+replica 寫入速度"), ("腦裂？", "需 Sentinel/Cluster 自動 failover")],
        "pitfalls": ["以為 replica 寫入會回 master", "backlog 太小導致頻繁全量"],
    },
    {
        "q": "Sentinel 與 Cluster 架構差異？",
        "core": "Sentinel：監控 master/replica，自動 failover，client 問 Sentinel 取 master 位址；單 shard。Cluster：16384 slots 分片，多 master，節點間 gossip，MOVED/ASK 重定向，水平擴展。",
        "dive": ["Cluster slot 遷移時 ASKING", "Sentinel quorum", "最少 3 master 建議 Cluster"],
        "followups": [("跨 slot 多 key？", "MGET 需 same slot；hash tag {user}:1"), ("Sentinel 腦裂？", "quorum+min-replicas")],
        "pitfalls": ["Cluster 大 key 遷移阻塞", "客戶端未支援 Cluster 協議"],
    },
    {
        "q": "記憶體淘汰策略 LRU/LFU/TTL？",
        "core": "maxmemory 達上限按 policy 淘汰：noeviction、allkeys-lru、volatile-lru、allkeys-lfu（4.0+）、volatile-ttl 等。近似 LRU 用取樣池，非精確 LRU。LFU 適合 hot key 穩定場景。",
        "dive": ["lazyfree 異步刪大 key", "maxmemory-policy 與持久化交互", "tracking 客戶端快取失效"],
        "followups": [("快取與 DB 一致性？", "見 cache-aside+TTL+canal"), ("OOM 行為？", "noeviction 寫入報錯")],
        "pitfalls": ["volatile-lru 只淘汰有 TTL key 可能 OOM", "大 key 刪除阻塞"],
    },
    {
        "q": "快取穿透、擊穿、雪崩如何解？",
        "core": "穿透：查不存在 key，打到 DB；解：布隆過濾、空值快取、參數校驗。擊穿：hot key 過期瞬間大量請求 DB；解：互斥鎖重建、邏輯過期、never expire+async refresh。雪崩：大量 key 同時過期；解：TTL 加 jitter、多級快取、熔斷限流。",
        "dive": ["singleflight 合併回源", "Redis 集群分片降低單點", "本地 cache+Redis 二級"],
        "followups": [("布隆 false positive？", "存在可能誤判，不存在一定不存在"), ("互斥鎖用 SETNX？", "需過期+唯一 value+Lua 釋放")],
        "pitfalls": ["空值快取 TTL 過長占滿", "互斥鎖未釋放死鎖"],
        "resume": "實務上修復 Redis 快取穿透：空值快取 + 布隆過濾非法 ID。",
    },
    {
        "q": "Redis 分散式鎖如何實現？Redlock 爭議？",
        "core": "單機：SET key uuid NX PX ttl，釋放用 Lua 比對 uuid 再 DEL。Redlock：多獨立 master 過半成功；爭議在 clock skew 與 GC pause 可能雙持鎖。實務常單 Redis+ fencing token 或 etcd/ZooKeeper。",
        "dive": ["鎖續期 watchdog", "主從 async 複製鎖可能丟", "fencing token 寫 DB 拒舊 token"],
        "followups": [("Redlock 還用嗎？", "Martin vs Antirez 論戰；高一致用 ZK"), ("鎖粒度？", "業務 id 級，TTL>最大執行時間")],
        "pitfalls": ["DEL 別人鎖", "無 TTL 死鎖", "鎖內做長 IO"],
    },
    {
        "q": "Hot key 與 Big key 問題？",
        "core": "Hot key：單 key QPS 過高，單 slot/單 thread 瓶頸；解：local cache、拆分 key（suffix 分片）、read replica。Big key：大 hash/zset/list，刪/序列化阻塞；解：拆分、UNLINK、分批 HSCAN。",
        "dive": ["Redis 6 IO threads 只加速 network", "hot key 發現：monitor、redis-cli --hotkeys", "big key：--bigkeys 掃描"],
        "followups": [("Cluster hot slot？", "reshard 或 hashtag 打散"), ("ZSET 百萬 member？", "按時間分 key")],
        "pitfalls": ["KEYS 找 big key 生產禁用", "熱 key 本地 cache 不一致"],
        "resume": "K 線 ZSET 按 symbol+interval 分 key，避免單 key 百萬 candle。",
    },
    {
        "q": "Redis 6 Threaded I/O 解決什麼？",
        "core": "多線程處理 read/write/parse protocol，主線程仍執行命令。解決大連接數下 network CPU 瓶頸，命令執行仍單線程（除 modules）。io-threads 與 io-threads-do-reads 配置。",
        "dive": ["默認 1 線程", "只對 network 多線程", "memtier 基準可提升 QPS"],
        "followups": [("命令還是單線程？", "是，無需改 client 鎖"), ("與 Memcached 多线程比？", "Redis 選擇保持命令原子簡單")],
        "pitfalls": ["以為 IO 多線程=命令並行", "io-threads 過多 context switch"],
    },
    {
        "q": "Redis 與 DB 一致性策略？",
        "core": "Cache-Aside：讀 miss 查 DB 寫 cache；寫 DB 後刪 cache（或 delay double delete）。強一致：分布式事务（Seata）、Canal 訂閱 binlog 更新 cache、寫透 write-through。最終一致最常見。",
        "dive": ["先刪 cache 再寫 DB 仍可能不一致", "binlog+MQ 异步刷新", "version 字段拒舊寫"],
        "followups": [("先更新 DB 還 cache？", "一般先 DB 再刪 cache"), ("双写失败？", "重试+补偿+对账")],
        "pitfalls": ["更新 cache 而非删除导致并发脏读", "无 TTL 兜底"],
        "resume": "實務架構：K 線寫 MySQL SP 後刪/更新 Redis ZSET，讀以 cache 為主、DB 為 fallback。",
    },
    {
        "q": "Pipeline 與 Transaction 差異？",
        "core": "Pipeline：批量發命令減 RTT，無原子性保證。MULTI/EXEC：命令排隊，EXEC 原子執行，樂觀鎖 WATCH。Lua 脚本：原子執行複雜邏輯，應控制執行時間。",
        "dive": ["Pipeline 不需事務", "EXEC 失敗部分已執行（Redis 7 前）", "Lua redis.call 錯誤回滾脚本"],
        "followups": [("Pipeline 大小？", "分批避免 buffer 爆"), ("WATCH 衝突？", "EXEC nil 需重试")],
        "pitfalls": ["Lua 脚本過長阻塞", "把 Pipeline 当事务"],
    },
    {
        "q": "HyperLogLog、Bitmap、GEO 應用？",
        "core": "HLL：近似基数 O(1) 内存；Bitmap：位图签到/在线用户；GEO：geohash+ZSET 附近的人。Stream：Consumer Group 消息流，类似 Kafka lite。",
        "dive": ["HLL 标准误差 0.81%", "Bitmap offset=userid", "XREADGROUP ACK 至少一次"],
        "followups": [("HLL 合并？", "PFMERGE"), ("Stream vs List？", "Stream 有 ack/consumer group")],
        "pitfalls": ["HLL 不能取具体元素", "Bitmap 用户 id 过大需分片"],
    },
    {
        "q": "Redis 过期删除策略？",
        "core": "惰性删除：访问时检查过期。定期删除：随机抽 sample 删除过期 key。内存淘汰是另一机制。TTL 精度秒级；key 不存在 vs expired 返回 nil。",
        "dive": ["expire set 与 dict 分离", "持久化 RDB 不过期 key 可能复活（需策略）", "AOF 过期 del 命令"],
        "followups": [("大量 key 同时 expire？", "可能 CPU spike，加 jitter"), ("TTL -1/-2？", "-1 无 TTL，-2 不存在")],
        "pitfalls": ["依赖 expire 做精确调度", "过期 key 仍占内存直到被删"],
    },
    {
        "q": "Redis 為什麼單線程還這麼快？",
        "core": "純內存、高效数据结构、IO 多路复用 epoll、避免锁竞争与上下文切换。瓶颈常在 network/memory 而非 CPU。6.0+ IO 线程进一步解放 network。",
        "dive": ["单线程简化原子语义", "O(N) 命令如 KEYS 仍危险", "持久化 fork 是额外开销"],
        "followups": [("多核如何利用？", "多实例/sharded cluster"), ("与 Memcached 比？", "Redis 数据结构更丰富")],
        "pitfalls": ["单线程执行慢命令拖全局"],
    },
    {
        "q": "Redis 集群 rebalance 与 slot 迁移？",
        "core": "reshard 将 slot 从 A 移到 B：IMPORTING/EXPORTING 状态，MIGRATE key，原子 slot 元数据更新。迁移期间 ASK 重定向。",
        "dive": ["MIGRATE 可原子搬 key", "大 slot 迁移时间长", "客户端需 smart routing"],
        "followups": [("迁移阻塞？", "单 key 原子，整体渐进"), ("扩缩容计划？", "低峰+限速")],
        "pitfalls": ["迁移中断需恢复", "无 hash tag 的 multi-key 跨 slot"],
    },
    {
        "q": "Redis 慢查询如何排查？",
        "core": "SLOWLOG 记录超过 slowlog-log-slower-than 的命令。latency doctor/latency history 诊断。避免 O(N) 命令、大 value、fork、AOF rewrite 叠加。",
        "dive": ["CONFIG SET slowlog-log-slower-than", "LATENCY GRAPH 分类", "memory fragmentation"],
        "followups": [("ZREVRANGE 大 range？", "限制 count"), ("MONITOR 生产？", "禁用，开销极大")],
        "pitfalls": ["HGETALL 百万 field", "生产 KEYS *"],
    },
    {
        "q": "Redis 事务能保证隔离吗？",
        "core": "MULTI/EXEC 提供顺序执行与 batch 原子性，无 rollback（命令语法错在 QUEUE 阶段发现）。无隔离级别概念；WATCH 提供 CAS 乐观锁。",
        "dive": ["DISCARD 取消", "EXEC 时 watched key 变则 abort", "与 DB ACID 不同"],
        "followups": [("需要 rollback？", "用 Lua"), ("事务中间可见？", "其他 client 看不见 QUEUE 内容")],
        "pitfalls": ["以为 EXEC 失败全部回滚"],
    },
    {
        "q": "Redis 在 K 線/OHLC 場景的資料模型？",
        "core": "ZSET score=timestamp member=OHLC JSON 或 compact binary；按 symbol:interval 分 key；ZREVRANGEBYSCORE 拉最近 N 根；最新价可用 String/HASH。写入 batch ZADD pipeline。",
        "dive": ["定期 trim ZREMRANGEBYRANK", "与 MySQL SP 聚合分工", "MGET 多 symbol 并行"],
        "followups": [("毫秒 K 线？", "score 用 ms 时间戳"), ("duplicate candle？", "ZADD NX 或 version in member")],
        "pitfalls": ["单 key 存全历史", "无 trim 内存爆炸"],
        "resume": "實際優化：MySQL SP 聚合 + Redis ZSET 分 key + index rebuild，延遲 3–5s→300–500ms。",
    },
]

MYSQL_TOPICS = [
    {
        "q": "InnoDB 与 MyISAM 核心差异？",
        "core": "InnoDB：行锁、MVCC、事务、崩溃恢复（redo/undo）、聚簇索引。MyISAM：表锁、无事务、非聚簇、count(*) 快但不安全写。生产 OLTP 几乎全 InnoDB。",
        "dive": ["InnoDB buffer pool 缓存页", "MyISAM 适合只读 archive", "InnoDB 主键即数据"],
        "followups": [("为何 count(*) 慢？", "InnoDB 估算 vs 全表扫"), ("MyISAM 还用在哪？", "极少，legacy")],
        "pitfalls": ["混用引擎无法事务", "无 PK 的 InnoDB 隐式 row_id"],
    },
    {
        "q": "B+ 树索引为何适合 MySQL？",
        "core": "B+ 树多路平衡，树高低（3-4 层百万行）、磁盘 IO 少；叶子链表支持 range scan；非叶子只存 key 更 fanout。相比 B 树叶子不存数据链接、相比 hash 支持排序与范围。",
        "dive": ["页默认 16KB", "聚簇索引叶子=行数据", "二级索引叶子=PK 值需回表"],
        "followups": [("为何不用红黑树？", "磁盘 IO 次数多"), ("UUID PK 问题？", "随机插入页分裂")],
        "pitfalls": ["过宽 PK 增大二级索引", "函数索引前导列失效"],
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
        "resume": "K 线表 rebuild index 优化 time range 查询。",
    },
    {
        "q": "聚簇索引与二级索引？回表与覆盖索引？",
        "core": "InnoDB 表数据按 PK 聚簇存储；二级索引存 (index_col, PK)。查询需回表：先查二级索引得 PK 再查聚簇。覆盖索引：SELECT 列全在索引中则无需回表（Using index）。",
        "dive": ["ICP 索引下推减少回表前过滤", "MRR 排序 PK 批量回表", "联合索引最左前缀"],
        "followups": [("无 PK？", "选唯一非空或隐式 row_id"), ("二级索引越多越好？", "写放大、optimizer 选择")],
        "pitfalls": ["SELECT * 无法覆盖", "隐式类型转换索引失效"],
    },
    {
        "q": "MVCC 原理？Read View 如何判断可见性？",
        "core": "每行有 DB_TRX_ID、DB_ROLL_PTR、undo log 链。Read View 含 m_ids（活跃事务）、min/max_trx_id。规则：trx_id < min → 可见；> max → 不可见；在 m_ids 中 → 不可见；否则可见。RR 首次读建立 View，RC 每次读新建。",
        "dive": ["undo log 存旧版本", "delete mark 未物理删", "purge 线程清理无 read view 需要的 undo"],
        "followups": [("RR 避免幻读？", "当前读 gap lock；快照读靠 MVCC"), ("长事务危害？", "undo 堆积、purge 阻塞")],
        "pitfalls": ["以为 MVCC 完全无锁", "RC+binlog statement 不一致历史问题"],
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
        "q": "四种隔离级别与现象？",
        "core": "RU：脏读。RC：不可脏读，可不可重复读。RR（InnoDB 默认）：快照读避免不可重复读，当前读靠 gap lock 防幻读。Serializable：读加锁，最严。",
        "dive": ["快照读 vs 当前读", "gap lock/next-key lock", "semi-consistent read 优化"],
        "followups": [("RR 一定无幻读？", "当前读 INSERT 仍可能；写倾斜需注意"), ("为何很多用 RC？", "锁少、binlog row 友好")],
        "pitfalls": ["混用 FOR UPDATE 与普通 SELECT 认知不一致", "gap lock 死锁"],
    },
    {
        "q": "InnoDB 锁类型？Record/Gap/Next-Key？",
        "core": "Record lock 锁索引记录；Gap lock 锁间隙防插入；Next-key = record+gap。Insert intention lock 兼容 gap。无索引列 update 可能锁全表（lock escalation 到全表扫描行）。",
        "dive": ["意向锁 IS/IX 表级", "AUTO-inc 锁", "metadata lock（DDL）"],
        "followups": [("死锁日志？", "SHOW ENGINE INNODB STATUS"), ("如何减锁？", "索引精准、短事务、RC")],
        "pitfalls": ["varchar 不加引号隐式转换", "范围更新无索引 gap 锁大"],
    },
    {
        "q": "死锁如何产生与排查？",
        "core": "两事务以不同顺序锁资源→循环等待。InnoDB 自动检测回滚代价小的事务。排查：SHOW ENGINE INNODB STATUS、performance_schema.data_locks。",
        "dive": ["应用层固定锁顺序", "重试机制", "小事务"],
        "followups": [("gap lock 死锁例子？", "两事务插入同一 gap"), ("监控？", "innodb_print_all_deadlocks")],
        "pitfalls": ["捕获死锁不重试", "长事务持锁"],
    },
    {
        "q": "redo log 与 undo log 与 binlog 区别？",
        "core": "redo：InnoDB 物理页变更，crash recovery，循环写。undo：事务回滚与 MVCC 旧版本。binlog：Server 层逻辑日志，主从复制与 PITR。两阶段提交协调 redo 与 binlog 一致。",
        "dive": ["WAL：先写 redo 再刷脏页", "binlog row/statement/mixed", "sync_binlog=1 最安全"],
        "followups": [("redo 512MB 循环？", "覆盖旧 checkpoint 前需刷脏"), ("半同步复制？", "至少一从 ack")],
        "pitfalls": ["binlog 开 statement 主从不一致", "redo 满阻塞写入"],
    },
    {
        "q": "两阶段提交（2PC）在 MySQL 中？",
        "core": "commit 时：1) redo prepare 2) 写 binlog 3) redo commit。崩溃恢复时以 binlog 为准协调：有 binlog 无 redo commit 则提交；有 prepare 无 binlog 则回滚。保证 redo 与 binlog 一致。",
        "dive": ["XID 关联", "组提交优化 fsync", "分布式 XA 是另一概念"],
        "followups": [("为何需要 binlog 与 redo？", "redo InnoDB 独有；binlog 复制"), ("丢 binlog？", "从库不一致")],
        "pitfalls": ["以为 redo 用于复制"],
    },
    {
        "q": "慢查询如何分析与优化？",
        "core": "开启 slow_query_log、long_query_time；EXPLAIN 看 type、key、rows、Extra。优化：索引、改写 SQL、拆分、缓存。避免 SELECT *、函数包列、隐式转换。",
        "dive": ["EXPLAIN ANALYZE 实际行数", "pt-query-digest 聚合", "optimizer trace"],
        "followups": [("type ALL 一定坏？", "小表 OK"), ("filesort 优化？", "索引排序 Avoid filesort")],
        "pitfalls": ["只看 rows 不看 filtered", "上线无 explain"],
        "resume": "實務上用 EXPLAIN + index rebuild 优化 K 线聚合 SP。",
    },
    {
        "q": "联合索引与最左前缀？",
        "core": "索引 (a,b,c) 可用于 a、ab、abc 条件；跳过 b 用 c 无法走索引（除 index skip scan 8.0+）。列顺序：高选择性、常查列靠前；等于在前范围在后。",
        "dive": ["索引合并 index_merge", "覆盖索引含查询列", "前缀索引省空间但排序弱"],
        "followups": [("(a,b) 查 b alone？", "通常不走"), ("order by b,c 索引？", "需最左 a 或匹配")],
        "pitfalls": ["范围列后无法再用于其他列", "过多重复索引"],
    },
    {
        "q": "索引下推（ICP）是什么？",
        "core": "MySQL 5.6+ 二级索引扫描时，在存储引擎层用索引列先过滤 WHERE 条件，再回表，减少回表次数。Extra: Using index condition。",
        "dive": ["仅 InnoDB 二级索引", "含 PK 列条件下推", "与覆盖索引不同"],
        "followups": [("何时无效？", "主键索引扫描"), ("性能提升场景？", "二级索引+部分列匹配")],
        "pitfalls": ["以为 ICP=覆盖索引"],
    },
    {
        "q": "索引失效常见场景？",
        "core": "对列函数/运算、隐式类型转换、like '%x'、OR 一侧无索引、不等于、优化器选错（统计信息旧）、联合索引违背最左。",
        "dive": ["force index 慎用", "analyze table 更新统计", "8.0 histogram"],
        "followups": [("!= 一定不走索引？", "看选择性 optimizer 决定"), ("字符集转换？", "col 与常量字符集不同")],
        "pitfalls": ["SQL 改写后未 explain", "MRR/ICP 误判"],
    },
    {
        "q": "Stored Procedure 优缺点？K 线（OHLC）场景如何用？",
        "core": "SP 在 DB 内聚合减少 network round-trip、可封装复杂 OHLC 逻辑。缺点：版本管理难、调试弱、锁 DB 资源、可移植性差。實務上用 SP 做 K 线聚合+清洗异常 duplicate。",
        "dive": ["与 app 层职责划分", "prepared statement 类似边界", "权限与安全 SQL injection in SP"],
        "followups": [("何时不用 SP？", "复杂业务规则、频繁变更"), ("性能？", "减少 RTT 但 CPU 在 DB")],
        "pitfalls": ["SP 无索引表扫描", "逻辑散落 app+SP 难维护"],
        "resume": "實務經驗：MySQL SP 聚合 K 线 + index rebuild，配合 Redis ZSET，延迟 3–5s→300–500ms。",
    },
    {
        "q": "主从复制原理与延迟？",
        "core": "主库 binlog → 从库 IO thread 拉 relay log → SQL thread 重放。异步默认有延迟；半同步等一从 ack；GTID 简化 failover。并行复制（基于 commit timestamp）减 lag。",
        "dive": ["relay log", "read/write split 脏读", "Seconds_Behind_Master 不准确"],
        "followups": [("延迟大？", "大事务、从库硬件、单线程 apply"), ("双主？", "谨慎环冲突")],
        "pitfalls": ["从库读 RR 仍可能旧", "DDL 阻塞复制"],
    },
    {
        "q": "分库分表策略？",
        "core": "垂直：按业务拆库。水平：shard key hash/range。挑战：跨 shard join、分布式 ID、扩容 rebalance。中间件 ShardingSphere、Vitess。",
        "dive": ["snowflake ID", "全局二级索引表", "扩容双倍迁移"],
        "followups": [("shard key 选 user_id？", "均衡+业务局部性"), ("事务？", "XA 或最终一致")],
        "pitfalls": ["热点 shard", "跨 shard 排序分页"],
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
        "q": "MySQL 连接池如何配置？",
        "core": "HikariCP/Go sql.DB：max_open、max_idle、conn_max_lifetime。过大连接耗尽 DB；过小排队。公式参考：connections ≈ (core*2) + disk_spindle，需压测。",
        "dive": ["wait_timeout 与 lifetime", "prepared stmt 缓存", "连接泄漏检测"],
        "followups": [("Go sql.DB 默认？", "无 limit 危险"), ("RDS max_connections？", "与实例规格相关")],
        "pitfalls": ["不设 timeout", "长事务占连接"],
    },
    {
        "q": "ORDER BY 与 GROUP BY 优化？",
        "core": "利用索引有序 Avoid filesort。GROUP BY 可走 loose index scan（满足前缀）。临时表内存 tmp_table_size 超限落盘。",
        "dive": ["only_full_group_by", "distinct vs group by", "窗口函数 8.0"],
        "followups": [("filesort 两种算法？", "单路/双路 sort buffer"), ("limit 优化？", "延迟关联")],
        "pitfalls": ["group by 非索引列", "大 group 内存 sort"],
    },
    {
        "q": "InnoDB Buffer Pool 机制？",
        "core": "缓存数据页与索引页，LRU 变种（young/old  midpoint）。dirty page 由 redo 保护，checkpoint 刷盘。命中率应 >99%。",
        "dive": ["change buffer 二级索引写优化", "doublewrite 防 partial page write", "innodb_buffer_pool_size 70-80% RAM"],
        "followups": [("buffer pool dump？", "重启预热"), ("页淘汰？", "clean 优先，dirty 触发 flush")],
        "pitfalls": ["buffer pool 过小频繁磁盘读", "未监控 hit rate"],
    },
    {
        "q": "如何设计 K 线/OHLC 表结构？",
        "core": "表：(symbol_id, interval, open_time) PK 或 unique；列 open/high/low/close/volume。索引 (symbol, interval, open_time DESC)。历史分区 BY RANGE(open_time)。写入 upsert ON DUPLICATE KEY UPDATE。",
        "dive": ["与 Redis ZSET 分工：DB 权威、cache 热窗", "SP 聚合 tick→candle", "异常 duplicate 清洗"],
        "followups": [("分表？", "按 symbol hash 或 time 分区"), ("tick 级？", "时序库或分表")],
        "pitfalls": ["无 unique 重复 candle", "range 查询无索引"],
        "resume": "實際經驗：SP 清洗 duplicate + index rebuild + Redis ZSET 热数据。",
    },
    {
        "q": "線上對大表加索引/改欄位如何不鎖表？（gh-ost / pt-osc）",
        "core": "MySQL 5.6+ 支援 Online DDL（ALGORITHM=INPLACE, LOCK=NONE），多數加索引可線上完成，但改欄位型別、加全文索引等仍會 rebuild table 或短暫鎖。大表生產常用 gh-ost 或 pt-online-schema-change：建影子表 → 用觸發器/binlog 同步增量 → 分批 copy 舊資料 → 原子 rename 切換，避免長時間鎖與主從延遲堆積。",
        "dive": [
            "pt-osc 用觸發器同步原表變更到新表；gh-ost 解析 binlog 同步，對主庫更輕量、可暫停限流",
            "INPLACE vs COPY：COPY 重建整表並鎖；INSTANT（8.0.12+）尾部加欄位可即時完成",
            "需預留磁碟空間（影子表）、控制 chunk 大小與 replica lag 閾值",
        ],
        "followups": [
            ("gh-ost 為何比 pt-osc 對主庫友善？", "不用觸發器、改讀 binlog，可動態限流/暫停，降低主庫負載"),
            ("8.0 INSTANT DDL 限制？", "只支援部分操作（如尾部加欄位），不能加在中間或改型別"),
        ],
        "pitfalls": ["直接對大表 ALTER 造成長時間鎖與主從延遲", "忘了監控 replica lag，切換時下游讀到不一致", "磁碟空間不足導致影子表失敗"],
        "resume": "K 線表 rebuild index 時需考量線上變更策略，避免鎖住交易/行情讀路徑。",
    },
]

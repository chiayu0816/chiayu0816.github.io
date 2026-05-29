# Redis 面試 Q&A

> 來源：interview-go（redis/base）、go-questions、tech-vault
> 題數：20 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: Redis 五種基本資料結構及其底層實現？

**核心回答：**
String(SDS)、List(quicklist=ziplist+linkedlist)、Hash(ziplist/hashtable)、Set(intset/hashtable)、ZSET(ziplist/skiplist+hashtable)。Redis 依元素數量與大小在 compact 編碼與 hashtable 間自動轉換，以平衡記憶體與 O(1)/O(logN) 操作。

**深入原理：**
- SDS：O(1) 取長度、二進位制安全、預分配減少 realloc
- skiplist：多層索引，ZSET range/score 查詢 O(logN)
- ziplist：連續記憶體，小 hash/zset 省空間
- encoding 轉換不可逆（大→小需主動刪重建）

```svg
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
```

**考官可能追問：**
- Q: K 線場景為何用 ZSET？
  - A: score=時間戳，member=OHLC JSON；ZREVRANGEBYSCORE 取時間窗 O(logN+M)
- Q: intset 何時用？
  - A: set 全為整數且元素少時

**常見陷阱 / 易錯點：**
- 大 ziplist 轉 hashtable 造成 latency spike
- 誤用 KEYS * 阻塞

**結合履歷：**
實務上用 Redis ZSET 重構 K 線快取，將圖表載入從 3–5s 降至 300–500ms。

---
### Q: SDS 與 C 字串有何不同？

**核心回答：**
SDS 記錄 len 與 free，O(1) 取長度；支援二進位制安全（含 \0）；預分配策略減少 realloc；buf 可含未使用空間。C 字串以 \0 結尾，strlen O(N)，不適合二進位制 blob。

**深入原理：**
- hdr 5/8/16/32/64 依長度選 header
- append 時若 free 夠則原地寫
- 相容部分 C 函式（以 \0 結尾部分）

**考官可能追問：**
- Q: String 最大 512MB？
  - A: 是 Redis 限制
- Q: embstr vs raw？
  - A: 短字串 embstr 一次分配 header+buf

**常見陷阱 / 易錯點：**
- 以為 Redis String 只是 char*

---
### Q: RDB 持久化原理與優缺點？

**核心回答：**
RDB 是某時間點全量記憶體快照，fork 子程序寫 dump.rdb。COW 複製頁，寫時複製增加記憶體。恢復快、檔小，但兩次快照間資料可能丟失（分鐘級）。

**深入原理：**
- save/bgsave 觸發
- fork 瞬間 latency 可能抖動
- 子程序寫完原子 rename

**考官可能追問：**
- Q: fork 失敗？
  - A: 記憶體不足或 overcommit 關閉
- Q: 適合冷備？
  - A: 是，配合異地備份

**常見陷阱 / 易錯點：**
- 大 instance fork 慢
- 只做 RDB 無法秒級 RPO

---
### Q: AOF 三種 fsync 策略？何時 rewrite？

**核心回答：**
always：每條命令 fsync，最安全最慢；everysec：每秒 fsync，預設，最多丟 1 秒；no：OS 決定，最快最危險。AOF rewrite 由子程序依當前記憶體狀態重寫命令集，壓縮體積，bgrewriteaof 觸發。

**深入原理：**
- rewrite 期間增量 buf 累積
- 混合持久化 RDB+AOF header 加速恢復
- auto-aof-rewrite-min-size/percentage

**考官可能追問：**
- Q: 線上選 everysec？
  - A: 多數場景平衡
- Q: rewrite 阻塞？
  - A: fork+寫新檔，主程序仍服務

**常見陷阱 / 易錯點：**
- AOF 檔無限增長未 rewrite
- always 在 SSD 上仍可能拖垮 IOPS

**結合履歷：**
在交易所場景評估 RPO：行情快取可重建用 RDB+短 AOF；關鍵狀態需 everysec 或混合。

---
### Q: Redis 主從複製流程？

**核心回答：**
replica 發 PSYNC；全量：master bgsave RDB 傳 replica 載入；增量：複製緩衝區 propagation 後續命令。斷線重連 partial resync 若 offset 仍在 backlog。

**深入原理：**
- repl_backlog 環形緩衝
- replica 預設 read-only
- 複製非同步，master 不等待 replica ack（除非 WAIT）

**考官可能追問：**
- Q: 複製延遲？
  - A: network+replica 寫入速度
- Q: 腦裂？
  - A: 需 Sentinel/Cluster 自動 failover

**常見陷阱 / 易錯點：**
- 以為 replica 寫入會回 master
- backlog 太小導致頻繁全量

---
### Q: Sentinel 與 Cluster 架構差異？

**核心回答：**
Sentinel：監控 master/replica，自動 failover，client 問 Sentinel 取 master 位址；單 shard。Cluster：16384 slots 分片，多 master，節點間 gossip，MOVED/ASK 重定向，水平擴展。

**深入原理：**
- Cluster slot 遷移時 ASKING
- Sentinel quorum
- 最少 3 master 建議 Cluster

**考官可能追問：**
- Q: 跨 slot 多 key？
  - A: MGET 需 same slot；hash tag {user}:1
- Q: Sentinel 腦裂？
  - A: quorum+min-replicas

**常見陷阱 / 易錯點：**
- Cluster 大 key 遷移阻塞
- 客戶端未支援 Cluster 協議

---
### Q: 記憶體淘汰策略 LRU/LFU/TTL？

**核心回答：**
maxmemory 達上限按 policy 淘汰：noeviction、allkeys-lru、volatile-lru、allkeys-lfu（4.0+）、volatile-ttl 等。近似 LRU 用取樣池，非精確 LRU。LFU 適合 hot key 穩定場景。

**深入原理：**
- lazyfree 非同步刪大 key
- maxmemory-policy 與持久化互動
- tracking 客戶端快取失效

**考官可能追問：**
- Q: 快取與 DB 一致性？
  - A: 見 cache-aside+TTL+canal
- Q: OOM 行為？
  - A: noeviction 寫入報錯

**常見陷阱 / 易錯點：**
- volatile-lru 只淘汰有 TTL key 可能 OOM
- 大 key 刪除阻塞

---
### Q: 快取穿透、擊穿、雪崩如何解？

**核心回答：**
穿透：查不存在 key，打到 DB；解：布隆過濾、空值快取、引數校驗。擊穿：hot key 過期瞬間大量請求 DB；解：互斥鎖重建、邏輯過期、never expire+async refresh。雪崩：大量 key 同時過期；解：TTL 加 jitter、多級快取、熔斷限流。

**深入原理：**
- singleflight 合併回源
- Redis 叢集分片降低單點
- 本地 cache+Redis 二級

**考官可能追問：**
- Q: 布隆 false positive？
  - A: 存在可能誤判，不存在一定不存在
- Q: 互斥鎖用 SETNX？
  - A: 需過期+唯一 value+Lua 釋放

**常見陷阱 / 易錯點：**
- 空值快取 TTL 過長佔滿
- 互斥鎖未釋放死鎖

**結合履歷：**
實務上修復 Redis 快取穿透：空值快取 + 布隆過濾非法 ID。

---
### Q: Redis 分散式鎖如何實現？Redlock 爭議？

**核心回答：**
單機：SET key uuid NX PX ttl，釋放用 Lua 比對 uuid 再 DEL。Redlock：多獨立 master 過半成功；爭議在 clock skew 與 GC pause 可能雙持鎖。實務常單 Redis+ fencing token 或 etcd/ZooKeeper。

**深入原理：**
- 鎖續期 watchdog
- 主從 async 複製鎖可能丟
- fencing token 寫 DB 拒舊 token

**考官可能追問：**
- Q: Redlock 還用嗎？
  - A: Martin vs Antirez 論戰；高一致用 ZK
- Q: 鎖粒度？
  - A: 業務 id 級，TTL>最大執行時間

**常見陷阱 / 易錯點：**
- DEL 別人鎖
- 無 TTL 死鎖
- 鎖內做長 IO

---
### Q: Hot key 與 Big key 問題？

**核心回答：**
Hot key：單 key QPS 過高，單 slot/單 thread 瓶頸；解：local cache、拆分 key（suffix 分片）、read replica。Big key：大 hash/zset/list，刪/序列化阻塞；解：拆分、UNLINK、分批 HSCAN。

**深入原理：**
- Redis 6 IO threads 只加速 network
- hot key 發現：monitor、redis-cli --hotkeys
- big key：--bigkeys 掃描

**考官可能追問：**
- Q: Cluster hot slot？
  - A: reshard 或 hashtag 打散
- Q: ZSET 百萬 member？
  - A: 按時間分 key

**常見陷阱 / 易錯點：**
- KEYS 找 big key 生產停用
- 熱 key 本地 cache 不一致

**結合履歷：**
K 線 ZSET 按 symbol+interval 分 key，避免單 key 百萬 candle。

---
### Q: Redis 6 Threaded I/O 解決什麼？

**核心回答：**
多執行緒處理 read/write/parse protocol，主執行緒仍執行命令。解決大連線數下 network CPU 瓶頸，命令執行仍單執行緒（除 modules）。io-threads 與 io-threads-do-reads 配置。

**深入原理：**
- 預設 1 執行緒
- 只對 network 多執行緒
- memtier 基準可提升 QPS

**考官可能追問：**
- Q: 命令還是單執行緒？
  - A: 是，無需改 client 鎖
- Q: 與 Memcached 多執行緒比？
  - A: Redis 選擇保持命令原子簡單

**常見陷阱 / 易錯點：**
- 以為 IO 多執行緒=命令並行
- io-threads 過多 context switch

---
### Q: Redis 與 DB 一致性策略？

**核心回答：**
Cache-Aside：讀 miss 查 DB 寫 cache；寫 DB 後刪 cache（或 delay double delete）。強一致：分散式事務（Seata）、Canal 訂閱 binlog 更新 cache、寫透 write-through。最終一致最常見。

**深入原理：**
- 先刪 cache 再寫 DB 仍可能不一致
- binlog+MQ 非同步重新整理
- version 欄位拒舊寫

**考官可能追問：**
- Q: 先更新 DB 還 cache？
  - A: 一般先 DB 再刪 cache
- Q: 雙寫失敗？
  - A: 重試+補償+對賬

**常見陷阱 / 易錯點：**
- 更新 cache 而非刪除導致併發髒讀
- 無 TTL 兜底

**結合履歷：**
實務架構：K 線寫 MySQL SP 後刪/更新 Redis ZSET，讀以 cache 為主、DB 為 fallback。

---
### Q: Pipeline 與 Transaction 差異？

**核心回答：**
Pipeline：批次發命令減 RTT，無原子性保證。MULTI/EXEC：命令排隊，EXEC 原子執行，樂觀鎖 WATCH。Lua 指令碼：原子執行複雜邏輯，應控制執行時間。

**深入原理：**
- Pipeline 不需事務
- EXEC 失敗部分已執行（Redis 7 前）
- Lua redis.call 錯誤回滾指令碼

**考官可能追問：**
- Q: Pipeline 大小？
  - A: 分批避免 buffer 爆
- Q: WATCH 衝突？
  - A: EXEC nil 需重試

**常見陷阱 / 易錯點：**
- Lua 指令碼過長阻塞
- 把 Pipeline 當事務

---
### Q: HyperLogLog、Bitmap、GEO 應用？

**核心回答：**
HLL：近似基數 O(1) 記憶體；Bitmap：點陣圖簽到/線上使用者；GEO：geohash+ZSET 附近的人。Stream：Consumer Group 訊息流，類似 Kafka lite。

**深入原理：**
- HLL 標準誤差 0.81%
- Bitmap offset=userid
- XREADGROUP ACK 至少一次

**考官可能追問：**
- Q: HLL 合併？
  - A: PFMERGE
- Q: Stream vs List？
  - A: Stream 有 ack/consumer group

**常見陷阱 / 易錯點：**
- HLL 不能取具體元素
- Bitmap 使用者 id 過大需分片

---
### Q: Redis 過期刪除策略？

**核心回答：**
惰性刪除：訪問時檢查過期。定期刪除：隨機抽 sample 刪除過期 key。記憶體淘汰是另一機制。TTL 精度秒級；key 不存在 vs expired 返回 nil。

**深入原理：**
- expire set 與 dict 分離
- 持久化 RDB 不過期 key 可能復活（需策略）
- AOF 過期 del 命令

**考官可能追問：**
- Q: 大量 key 同時 expire？
  - A: 可能 CPU spike，加 jitter
- Q: TTL -1/-2？
  - A: -1 無 TTL，-2 不存在

**常見陷阱 / 易錯點：**
- 依賴 expire 做精確排程
- 過期 key 仍佔記憶體直到被刪

---
### Q: Redis 為什麼單執行緒還這麼快？

**核心回答：**
純記憶體、高效資料結構、IO 多路複用 epoll、避免鎖競爭與上下文切換。瓶頸常在 network/memory 而非 CPU。6.0+ IO 執行緒進一步解放 network。

**深入原理：**
- 單執行緒簡化原子語義
- O(N) 命令如 KEYS 仍危險
- 持久化 fork 是額外開銷

**考官可能追問：**
- Q: 多核如何利用？
  - A: 多實例/sharded cluster
- Q: 與 Memcached 比？
  - A: Redis 資料結構更豐富

**常見陷阱 / 易錯點：**
- 單執行緒執行慢命令拖全域

---
### Q: Redis 叢集 rebalance 與 slot 遷移？

**核心回答：**
reshard 將 slot 從 A 移到 B：IMPORTING/EXPORTING 狀態，MIGRATE key，原子 slot 後設資料更新。遷移期間 ASK 重定向。

**深入原理：**
- MIGRATE 可原子搬 key
- 大 slot 遷移時間長
- 客戶端需 smart routing

**考官可能追問：**
- Q: 遷移阻塞？
  - A: 單 key 原子，整體漸進
- Q: 擴縮容計劃？
  - A: 低峰+限速

**常見陷阱 / 易錯點：**
- 遷移中斷需恢復
- 無 hash tag 的 multi-key 跨 slot

---
### Q: Redis 慢查詢如何排查？

**核心回答：**
SLOWLOG 記錄超過 slowlog-log-slower-than 的命令。latency doctor/latency history 診斷。避免 O(N) 命令、大 value、fork、AOF rewrite 疊加。

**深入原理：**
- CONFIG SET slowlog-log-slower-than
- LATENCY GRAPH 分類
- memory fragmentation

**考官可能追問：**
- Q: ZREVRANGE 大 range？
  - A: 限制 count
- Q: MONITOR 生產？
  - A: 停用，開銷極大

**常見陷阱 / 易錯點：**
- HGETALL 百萬 field
- 生產 KEYS *

---
### Q: Redis 事務能保證隔離嗎？

**核心回答：**
MULTI/EXEC 提供順序執行與 batch 原子性，無 rollback（命令語法錯在 QUEUE 階段發現）。無隔離級別概念；WATCH 提供 CAS 樂觀鎖。

**深入原理：**
- DISCARD 取消
- EXEC 時 watched key 變則 abort
- 與 DB ACID 不同

**考官可能追問：**
- Q: 需要 rollback？
  - A: 用 Lua
- Q: 事務中間可見？
  - A: 其他 client 看不見 QUEUE 內容

**常見陷阱 / 易錯點：**
- 以為 EXEC 失敗全部回滾

---
### Q: Redis 在 K 線/OHLC 場景的資料模型？

**核心回答：**
ZSET score=timestamp member=OHLC JSON 或 compact binary；按 symbol:interval 分 key；ZREVRANGEBYSCORE 拉最近 N 根；最新價可用 String/HASH。寫入 batch ZADD pipeline。

**深入原理：**
- 定期 trim ZREMRANGEBYRANK
- 與 MySQL SP 聚合分工
- MGET 多 symbol 並行

**考官可能追問：**
- Q: 毫秒 K 線？
  - A: score 用 ms 時間戳
- Q: duplicate candle？
  - A: ZADD NX 或 version in member

**常見陷阱 / 易錯點：**
- 單 key 存全歷史
- 無 trim 記憶體爆炸

**結合履歷：**
實際最佳化：MySQL SP 聚合 + Redis ZSET 分 key + index rebuild，延遲 3–5s→300–500ms。

---

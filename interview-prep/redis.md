# Redis 面試 Q&A

> 來源：interview-go（redis/base）、go-questions、tech-vault
> 題數：20 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: Redis 五種基本資料結構及其底層實現？

**核心回答：**
String(SDS)、List(quicklist=listpack/ziplist)、Hash(listpack/hashtable)、Set(intset/hashtable)、ZSET(listpack/skiplist+hashtable)。Redis 依元素數量與大小在緊湊編碼（listpack/intset）與雜湊表（hashtable）間自動轉換，以平衡記憶體與 O(1)/O(logN) 操作。自 Redis 7.0+ 起，listpack 已完全替代 ziplist 以解決其級聯更新問題。

**深入原理：**
- SDS：O(1) 取得長度、二進位安全、預分配減少 realloc
- skiplist：多層索引，ZSET range/score 查詢 O(logN)，內部為跳躍表與雜湊表雙重指標結構
- listpack：緊湊連續記憶體，解決 ziplist 級聯更新（Cascade Update）問題，節省小物件空間
- encoding 轉換不可逆（大→小需主動刪除重建）

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
  - A: score=時間戳記，member=OHLC JSON；ZREVRANGEBYSCORE 取時間窗 O(logN+M)
- Q: intset 何時用？
  - A: set 全為整數且元素少時

**常見陷阱 / 易錯點：**
- 大 listpack/ziplist 轉 hashtable 造成 latency spike
- 誤用 KEYS * 阻塞

**實務場景：**
例如用 Redis ZSET 重構 時間序列/圖表資料快取，將圖表載入從 量化的延遲區間 降至 量化的延遲區間

---
### Q: SDS 與 C 字串有何不同？

**核心回答：**
SDS 依長度選擇不同 header（sdshdr8/16/32/64 等），記錄 len 與 alloc（除 sdshdr5 外），O(1) 取得長度；支援二進位安全（可含 \0）；空間預分配與惰性釋放減少 realloc。C 字串以 \0 結尾，strlen O(N)，不適合二進位 blob。

**深入原理：**
- hdr 5/8/16/32/64 依長度選 header
- append 時若 free 夠則原位寫入
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
RDB 是某時間點全量記憶體快照，fork 子行程寫 dump.rdb。利用作業系統的寫時複製（COW）機制，在主行程有寫入操作時才複製記憶體分頁。還原速度快、檔案小，但兩次快照間資料可能遺失（分鐘級）。

**深入原理：**
- save/bgsave 觸發
- fork 瞬間 latency 可能抖動
- 子行程寫完原子 rename

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
always：每條命令 fsync，最安全最慢；everysec：每秒 fsync，預設，最多遺失 1 秒；no：OS 決定，最快最危險。AOF rewrite 由子行程依當前記憶體狀態重寫命令集，壓縮體積。Redis 7.0+ 採用 Multi-Part AOF 機制，將 AOF 拆分為 base、incremental 與 manifest 檔案，重寫時增量寫入新 incremental 檔案，完成後原子替換，避免舊版 rewrite 期間複雜的緩衝區累積。

**深入原理：**
- Multi-Part AOF 機制（Redis 7.0+）
- 混合持久化 RDB+AOF header 加速還原
- auto-aof-rewrite-min-size/percentage

**考官可能追問：**
- Q: 線上選 everysec？
  - A: 多數場景平衡
- Q: rewrite 阻塞？
  - A: fork+寫新檔，主行程仍服務

**常見陷阱 / 易錯點：**
- AOF 檔案無限增長未 rewrite
- always 在 SSD 上仍可能拖垮 IOPS

**實務場景：**
交易/行情繫統；關鍵狀態需 everysec 或混合

---
### Q: Redis 主從複製流程？

**核心回答：**
從節點 (Replica) 傳送 PSYNC；全量：主節點 (Master) bgsave RDB 傳給從節點載入；增量：透過複製積壓緩衝區（repl_backlog）傳播後續命令。斷線重連 partial resync 若 offset 仍在 backlog 中。

**深入原理：**
- repl_backlog 環形緩衝區
- replica 預設唯讀 (read-only)
- 非同步複製，master 不等待 replica ack（除非使用 WAIT 命令）

**考官可能追問：**
- Q: 複製延遲？
  - A: 網路延遲 + replica 寫入速度
- Q: 腦裂？
  - A: 需 Sentinel/Cluster 自動容錯移轉 (Failover)

**常見陷阱 / 易錯點：**
- 以為 replica 寫入會回傳 master
- backlog 太小導致頻繁全量複製

---
### Q: Sentinel 與 Cluster 架構差異？

**核心回答：**
Sentinel：監控 master/replica，自動容錯移轉，使用者端向 Sentinel 查詢 master 位址；單分片 (shard)。Cluster：16384 slots 分片，多 master，節點間 Gossip 協定，MOVED/ASK 重新導向，水平擴充。

**深入原理：**
- Cluster slot 遷移時 ASKING
- Sentinel quorum
- 最少 3 master 建議 Cluster

**考官可能追問：**
- Q: 跨 slot 多 key？
  - A: MGET 需在相同 slot；hash tag {user}:1
- Q: Sentinel 腦裂？
  - A: quorum+min-replicas

**常見陷阱 / 易錯點：**
- Cluster 大 key 遷移阻塞
- 使用者端未支援 Cluster 協定

---
### Q: 記憶體淘汰策略 LRU/LFU/TTL？

**核心回答：**
maxmemory 達上限按 policy 淘汰：noeviction、allkeys-lru、volatile-lru、allkeys-lfu（4.0+）、volatile-ttl 等。近似 LRU 用取樣池，非精確 LRU。LFU 適合 hot key 穩定場景。

**深入原理：**
- lazyfree 非同步刪除大 key
- maxmemory-policy 與持久化互動
- tracking 使用者端快取失效

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
快取穿透：查不存在 key 打到 DB；解：布隆過濾器、空值快取、引數校驗。快取擊穿：熱點 key 過期瞬間大量請求 DB；解：互斥鎖重建、邏輯過期、永遠不過期+非同步更新。快取雪崩：大量 key 同時過期；解：TTL 加隨機擾動（Jitter）、多級快取、熔斷限流。

**深入原理：**
- singleflight 合併回源
- Redis 叢集分片降低單點壓力
- 本地快取 + Redis 二級快取

**考官可能追問：**
- Q: 布隆 false positive？
  - A: 存在可能誤判，不存在一定不存在
- Q: 互斥鎖用 SETNX？
  - A: 需過期+唯一 value+Lua 釋放

**常見陷阱 / 易錯點：**
- 空值快取 TTL 過長佔滿記憶體
- 互斥鎖未釋放死鎖

**實務場景：**
例如修復 Redis 快取穿透：空值快取 + 布隆過濾器非法 ID

---
### Q: Redis 分散式鎖如何實現？Redlock 爭議？

**核心回答：**
單機：SET key uuid NX PX ttl，釋放用 Lua 比對 uuid 再 DEL。Redlock：多獨立 master 過半成功；爭議在 clock skew 與 GC pause 可能雙持鎖. 實務常單 Redis+ fencing token 或 etcd/ZooKeeper。

**深入原理：**
- 鎖續期看門狗機制 (watchdog)
- 主從非同步複製導致鎖可能遺失
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
Hot key：單 key QPS 過高，單 slot/單一執行緒瓶頸；解：本地快取 (local cache)、拆分 key（suffix 分片）、唯讀副本 (read replica)。Big key：大 hash/zset/list，刪除/序列化阻塞；解：拆分、UNLINK、分批 HSCAN。

**深入原理：**
- Redis 6 IO 執行緒只加速網路 I/O
- hot key 發現：monitor、redis-cli --hotkeys
- big key：--bigkeys 掃描

**考官可能追問：**
- Q: Cluster hot slot？
  - A: reshard 或 hashtag 打散
- Q: ZSET 百萬 member？
  - A: 按時間分 key

**常見陷阱 / 易錯點：**
- KEYS 找 big key 生產禁用
- 熱 key 本地快取不一致

**實務場景：**
時間序列/圖表資料 ZSET 按 symbol+interval 分 key，避免單 key 百萬 candle

---
### Q: Redis 6 Threaded I/O 解決什麼？

**核心回答：**
多執行緒處理 read/write/parse protocol，主執行緒仍執行命令。解決大連線數下網路 CPU 瓶頸，命令執行仍單執行緒（除 modules）。io-threads 與 io-threads-do-reads 配置。

**深入原理：**
- 預設 1 執行緒
- 只對網路多執行緒處理
- memtier 基準可提升 QPS

**考官可能追問：**
- Q: 命令還是單執行緒？
  - A: 是，無需修改使用者端鎖
- Q: 與 Memcached 多執行緒比？
  - A: Redis 選擇保持命令原子簡單

**常見陷阱 / 易錯點：**
- 以為 IO 多執行緒=命令並行
- io-threads 設定過多導致頻繁上下文切換

---
### Q: Redis 與 DB 一致性策略？

**核心回答：**
Cache-Aside：讀取未命中 (Miss) 查詢 DB 並寫入快取；寫入 DB 後刪除快取（或延遲雙刪）。強一致：分散式交易（Seata）、Canal 訂閱 binlog 更新快取、寫透 write-through。最終一致最常見。

**深入原理：**
- 先刪除快取再寫入 DB 仍可能不一致
- binlog+MQ 非同步更新
- version 欄位拒舊寫入

**考官可能追問：**
- Q: 先更新 DB 還是快取？
  - A: 一般先更新 DB 再刪除快取
- Q: 雙寫失敗？
  - A: 重試+補償+對帳

**常見陷阱 / 易錯點：**
- 更新快取而非刪除導致並行髒讀
- 無 TTL 兜底

**實務場景：**
實務架構：時間序列/圖表資料寫入 MySQL 預存程式後刪除/更新 Redis ZSET，讀以快取為主、DB 為備援 (fallback)

---
### Q: Pipeline 與 Transaction 差異？

**核心回答：**
Pipeline：批次發命令減 RTT，無原子性保證。MULTI/EXEC：命令排隊，EXEC 原子執行，樂觀鎖 WATCH。Lua 指令碼：原子執行複雜邏輯，應控制執行時間。

**深入原理：**
- Pipeline 不需要交易
- 交易不支援回滾，若 EXEC 期間某命令發生執行期錯誤，其餘命令仍會繼續執行且不回滾
- Lua redis.call 錯誤回滾指令碼

**考官可能追問：**
- Q: Pipeline 大小？
  - A: 分批避免 buffer 爆
- Q: WATCH 衝突？
  - A: EXEC nil 需重試

**常見陷阱 / 易錯點：**
- Lua 指令碼過長阻塞
- 把 Pipeline 當作交易

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
- HLL 不能取得具體元素
- Bitmap 使用者 id 過大需分片

---
### Q: Redis 過期刪除策略？

**核心回答：**
惰性刪除：存取時檢查過期。定期刪除：隨機抽樣刪除過期 key。記憶體淘汰是另一機制。TTL 支援毫秒級精度（PEXPIRE/PTTL），內部以毫秒時間戳記儲存。key 不存在與 expired 皆返回 nil。

**深入原理：**
- 過期字典 (expires dict) 與鍵值字典 (dict) 分離
- 持久化 RDB 不會載入已過期 key
- AOF 刪除時會向 AOF 檔案追加一條 DEL 命令

**考官可能追問：**
- Q: 大量 key 同時過期？
  - A: 可能引發 CPU 抖動，過期時間加隨機擾動 (jitter)
- Q: TTL -1/-2？
  - A: -1 無 TTL，-2 不存在

**常見陷阱 / 易錯點：**
- 依賴 expire 做精確排程
- 過期 key 仍佔記憶體直到被刪除

---
### Q: Redis 為什麼單執行緒還這麼快？

**核心回答：**
純記憶體操作、高效的資料結構、I/O 多工 (epoll)、避免鎖競爭與執行緒上下文切換。瓶頸常在網路或記憶體而非 CPU。6.0+ I/O 執行緒進一步解放網路 I/O 效能。

**深入原理：**
- 單執行緒簡化原子語意
- O(N) 命令如 KEYS 仍極度危險
- 持久化 fork 是額外開銷

**考官可能追問：**
- Q: 多核如何利用？
  - A: 多實例/sharded cluster
- Q: 與 Memcached 比？
  - A: Redis 資料結構更豐富

**常見陷阱 / 易錯點：**
- 單執行緒執行慢命令拖垮全域

---
### Q: Redis 叢集 rebalance 與 slot 遷移？

**核心回答：**
reshard 將 slot 從 A 移到 B：IMPORTING/EXPORTING 狀態，MIGRATE key，原子 slot 中繼資料更新。遷移期間 ASK 重新導向。

**深入原理：**
- MIGRATE 可原子搬移 key
- 大 slot 遷移時間長
- 使用者端需支援智慧路由 (smart routing)

**考官可能追問：**
- Q: 遷移阻塞？
  - A: 單 key 原子，整體漸進
- Q: 擴縮容計劃？
  - A: 低峰期+限速

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
- 記憶體碎片化 (memory fragmentation)

**考官可能追問：**
- Q: ZREVRANGE 大 range？
  - A: 限制 count
- Q: MONITOR 生產？
  - A: 禁用，開銷極大

**常見陷阱 / 易錯點：**
- HGETALL 百萬 field
- 生產環境 KEYS *

---
### Q: Redis 交易能保證隔離嗎？

**核心回答：**
MULTI/EXEC 提供順序執行與批次原子性，無回滾。無隔離層級概念；WATCH 提供 CAS 樂觀鎖。

**深入原理：**
- DISCARD 取消
- EXEC 時 watched key 變更則整個交易 abort
- 與資料庫 ACID 不同

**考官可能追問：**
- Q: 需要回滾？
  - A: 使用 Lua 指令碼
- Q: 交易中間可見？
  - A: 其他使用者端看不見 QUEUE 內容

**常見陷阱 / 易錯點：**
- 以為 EXEC 失敗全部回滾

---
### Q: Redis 在 K 線/OHLC 場景的資料模型？

**核心回答：**
ZSET score=timestamp member=OHLC JSON 或緊湊二進位；按 symbol:interval 分鍵；ZREVRANGEBYSCORE 拉取最近 N 根；最新價可用 String/HASH。寫入 batch ZADD pipeline。

**深入原理：**
- 定期 trim ZREMRANGEBYRANK
- 與 MySQL 預存程式 (SP) 聚合分工
- MGET 多 symbol 並行

**考官可能追問：**
- Q: 毫秒 K 線？
  - A: score 用毫秒時間戳記
- Q: 重複 K 線？
  - A: ZADD NX 或在 member 中加入版本號

**常見陷阱 / 易錯點：**
- 單鍵儲存全歷史
- 無 trim 導致記憶體爆炸

**實務場景：**
例如最佳化：MySQL SP 聚合 + Redis ZSET 分鍵 + 索引重建，延遲 量化的延遲區間→量化的延遲區間

---

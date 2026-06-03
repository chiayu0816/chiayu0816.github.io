# MongoDB 面試 Q&A

> 來源：tech-vault、體育/客服實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: MongoDB 文件模型與 BSON？

**核心回答：**
BSON 二進位制 JSON，支援 date、ObjectId、decimal。Collection 無固定 schema（靈活但需應用約束）。Embedded vs Reference 建模權衡。

**深入原理：**
- ObjectId 12位元組 timestamp
- schema validation $jsonSchema
- extended JSON

**考官可能追問：**
- Q:  vs JSONB PostgreSQL？
  - A: Mongo 原生分片
- Q: 大文件？
  - A: 16MB limit

**常見陷阱 / 易錯點：**
- 無 schema 資料質量差
- 深層巢狀查詢慢

---
### Q: WiredTiger 儲存引擎？

**核心回答：**
預設引擎：文件級鎖、壓縮、checkpoint、MVCC snapshot讀。Cache 類似 buffer pool。journal 保證 durability。

**深入原理：**
- snappy/zlib 壓縮
- checkpoint 間隔
- cache_size 配置

**考官可能追問：**
- Q: MMAPv1？
  - A: 已廢棄
- Q: read concern snapshot？
  - A: MVCC

**常見陷阱 / 易錯點：**
- cache 過小 disk thrash
- 未監控 wt cache

---
### Q: MongoDB 索引型別？

**核心回答：**
Single/compound/multikey(text/geospatial/TTL/hashed)。ESR 規則：Equality→Sort→Range。多鍵索引陣列每元素條目。

**深入原理：**
- partial index 條件
- sparse 跳過缺失
- hidden index 測試

**考官可能追問：**
- Q: 陣列索引？
  - A: multikey
- Q: TTL index？
  - A: expireAfterSeconds

**常見陷阱 / 易錯點：**
- compound 順序錯
- 過多 index 寫放大

---
### Q: Replica Set 原理？

**核心回答：**
Primary 寫，Secondary oplog 複製；Election 選主；Read Preference primary/secondary/nearest。Write Concern majority。

**深入原理：**
- oplog capped collection
- rollback 小機率
- arbiter 僅投票

**考官可能追問：**
- Q: 讀從庫 stale？
  - A: accept eventual
- Q: WC majority？
  - A: durability

**常見陷阱 / 易錯點：**
- 無 majority 寫丟
- secondary 讀 critical 資料

---
### Q: Sharding 分片策略？

**核心回答：**
Shard key 選高基數+均衡；hashed 防熱點；range 易熱點但 range 查好。Config server 存後設資料。mongos 路由。

**深入原理：**
- jumbo chunk
- zone sharding
- reshard 線上

**考官可能追問：**
- Q: shard key 選 userId？
  - A: 熱點 user
- Q: hashed？
  - A: 均衡 scatter gather

**常見陷阱 / 易錯點：**
- monotonic shard key 熱點
- chunk 過大遷移慢

---
### Q: Transaction 與 ACID？

**核心回答：**
MongoDB 4.0 起副本集、4.2 起分片支援多文件事務，語義接近關聯式 ACID，但**代價高**：跨分片要兩階段提交、持鎖時間長、且與 WiredTiger 快照隔離互動。設計上應優先**利用單文件的原子性**（一份文件的更新本身就是原子的）與冪等設計（embed 相關資料、用 upsert/版本欄位），把多文件事務當最後手段。

**深入原理：**
- 單文件更新天然原子：把『需一起改的資料』embed 進同一文件，多數情況免多文件事務
- 多文件事務：session.startTransaction，跨分片走 2PC，有 maxTransactionLockRequestTimeoutMillis 與時間上限
- 與快照隔離互動：事務讀在一致快照上，寫衝突會 abort，需應用層重試
- 替代方案：embedding、冪等 upsert、應用層 saga/補償

**考官可能追問：**
- Q: 何時事務？
  - A: 確實需多 doc 強一致才用
- Q: 替代？
  - A: embedding+idempotent upsert+saga

**常見陷阱 / 易錯點：**
- 長事務持鎖拖垮併發
- 高併發事務頻繁 abort 重試
- 以為像 RDB 一樣廉價

---
### Q: Aggregation Pipeline？

**核心回答：**
$match $group $lookup $sort $project 階段管道。$lookup 類似 join（注意效能）。索引支援 $match 前置。

**深入原理：**
- allowDiskUse 大 sort
- $facet 分頁
- explain aggregation

**考官可能追問：**
- Q: $lookup 慢？
  - A: 索引+pipeline 順序
- Q: MapReduce？
  - A: deprecated 用 aggregation

**常見陷阱 / 易錯點：**
- $match 放 $lookup 後
- 無 index full scan

---
### Q: MongoDB 一致性：Read/Write Concern？

**核心回答：**
Read Concern local/majority/snapshot；Write Concern w:1/majority/journal。線性一致需 causal consistency session。

**深入原理：**
- afterClusterTime
- hedged reads
- retryable writes

**考官可能追問：**
- Q: finance？
  - A: majority+retryable
- Q: cache 一致？
  - A: app 層

**常見陷阱 / 易錯點：**
- w:1 主宕丟寫
- ignore write concern error

---
### Q: Change Streams 應用？

**核心回答：**
oplog 封裝 watch collection/database 變更，推 insert/update/delete。用於 CDC、cache 失效、同步 ES。

**深入原理：**
- resume token
- fullDocument lookup
- split large event

**考官可能追問：**
- Q:  vs Debezium？
  - A: native 簡單
- Q: 丟失？
  - A: token 持久化

**常見陷阱 / 易錯點：**
- 無 resume 重放全量
- oplog 視窗不足

---
### Q: MongoDB 效能調優？

**核心回答：**
explain()、proper index、projection 減欄位、batch size、連線池、avoid large skip（用 range）。

**深入原理：**
- covered query
- index intersection
- profiler slowms

**考官可能追問：**
- Q: 100萬 skip？
  - A: 用 _id range
- Q: collscan？
  - A: 加 index

**常見陷阱 / 易錯點：**
- regex 字首無 index
- allowDiskUse 掩蓋問題

---
### Q: Embedding vs Referencing 建模？

**核心回答：**
Embed：1-N 小、常一起讀、原子更新。Reference：N 大、獨立增長、多對多。體育資料：match embed odds snapshot vs ref。

**深入原理：**
- document growth 16MB
- 雙向 ref 維護
- subset pattern

**考官可能追問：**
- Q: 陣列無限增長？
  - A: bucketing
- Q: join 頻繁？
  - A: embed 或 $lookup

**常見陷阱 / 易錯點：**
- embed 陣列無界
- ref 無 index

---
### Q: MongoDB 實務使用場景？

**核心回答：**
體育/客服場景：非結構化日誌、contact logs、靈活 schema 報表。非核心交易（交易在 MySQL/Redis）。

**深入原理：**
- 與 MySQL 分工
- TTL 日誌 collection
- aggregation KPI

**考官可能追問：**
- Q: 為何不用 Mongo 做訂單？
  - A: ACID+關係
- Q: 遷移？
  - A: schema 收斂

**常見陷阱 / 易錯點：**
- Mongo 當主交易庫

**實務場景：**
高吞吐資料管線實務：高吞吐資料管線 資料 Mongo+MySQL；客服系統用 MongoDB 做 KPI

---

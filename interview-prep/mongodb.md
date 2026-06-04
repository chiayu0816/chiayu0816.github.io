# MongoDB 面試 Q&A

> 來源：tech-vault、體育/客服實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: MongoDB 檔案模型與 BSON？

**核心回答：**
BSON 二進位 JSON，支援 date、ObjectId、decimal。Collection 無固定 schema（具備彈性但仍需應用程式約束）。巢狀嵌入 (Embedded) vs 引用 (Reference) 建模之權衡。

**深入原理：**
- ObjectId 12 位元組含 timestamp
- $jsonSchema 檔案驗證
- Extended JSON

**考官可能追問：**
- Q:  vs PostgreSQL JSONB？
  - A: MongoDB 原生支援分片 (Sharding)
- Q: 大檔案限制？
  - A: 單一檔案大小限制為 16MB

**常見陷阱 / 易錯點：**
- 無 schema 約束導致資料品質差
- 深層巢狀查詢效能低落

---
### Q: WiredTiger 儲存引擎？

**核心回答：**
MongoDB 預設引擎：支援檔案級鎖定（Document-level Concurrency Control）、資料壓縮、Checkpoint、MVCC 快照讀取。WiredTiger Cache 運作機制類似 Buffer Pool。Journal 日誌保證永續性 (Durability)。

**深入原理：**
- snappy/zlib 壓縮演演算法
- checkpoint 觸發間隔
- cache_size 記憶體大小配置

**考官可能追問：**
- Q: MMAPv1 引擎？
  - A: 已完全廢棄
- Q: Read Concern snapshot？
  - A: 利用 WiredTiger 的 MVCC 快照隔離實作

**常見陷阱 / 易錯點：**
- Cache 設定過小導致磁碟頻繁 I/O (Disk Thrashing)
- 未監控 WiredTiger 快取命中與髒資料比例

---
### Q: MongoDB 索引型別？

**核心回答：**
支援單欄位 (Single)、複合 (Compound)、多鍵 (Multikey，適用陣列)、文字 (Text)、地理空間 (Geospatial)、TTL、雜湊 (Hashed) 索引。複合索引設計遵循 ESR 原則：Equality（等值） → Sort（排序） → Range（範圍）。

**深入原理：**
- 部分索引 (Partial Index) 條件過濾
- 稀疏索引 (Sparse Index) 跳過缺失欄位
- 隱藏索引 (Hidden Index) 線上效能測試

**考官可能追問：**
- Q: 陣列欄位索引？
  - A: 會觸發多鍵索引 (Multikey)，為陣列中的每個元素建立一個索引條目
- Q: TTL 索引機制？
  - A: 利用 expireAfterSeconds 設定過期秒數，由背景執行緒刪除

**常見陷阱 / 易錯點：**
- 複合索引欄位順序錯誤
- 建立過多索引引發嚴重的寫入放大 (Write Amplification)

---
### Q: Replica Set 副本集原理？

**核心回答：**
Primary 節點負責寫入，Secondary 節點重放 oplog 進行非同步複製。基於 Raft 變種協定進行 Election 選主。Read Preference 決定讀取路由（primary/secondary/nearest）。Write Concern majority 保證資料寫入大多數節點以防遺失。

**深入原理：**
- oplog 作為 capped collection 的限制
- 主從切換時的 Rollback 機制
- 仲裁節點 (Arbiter) 僅參與投票不儲存資料

**考官可能追問：**
- Q: 讀取次級節點 (Secondary) 導致過期資料？
  - A: 需接受最終一致性 (Eventual Consistency)
- Q: Write Concern 為 majority 的開銷？
  - A: 提高永續性與一致性保證，但會增加寫入延遲

**常見陷阱 / 易錯點：**
- 未設定 majority 導致 Primary 故障時寫入資料遺失
- 在 Secondary 讀取關鍵的強一致性資料

---
### Q: Sharding 分片叢集策略？

**核心回答：**
Shard Key 應選擇高基數（High Cardinality）且分佈均衡的欄位。Hashed 分片防範寫入熱點；Range 分片利於範圍查詢。Config Server 儲存元資料（Metadata）。mongos 作為請求路由層。MongoDB 5.0+ 支援線上重新分片 (Live Resharding)。

**深入原理：**
- Jumbo Chunk（超大區塊）無法遷移問題
- Zone Sharding 定向資料分佈
- Live Resharding 線上更改 Shard Key

**考官可能追問：**
- Q: Shard Key 選擇 userId？
  - A: 若單一 user 資料量極大易形成熱點與 Jumbo Chunk
- Q: Hashed 索引範圍查詢？
  - A: 會退化為 Scatter-Gather 查詢，mongos 需廣播至所有分片

**常見陷阱 / 易錯點：**
- 使用單調遞增欄位作為 Shard Key 導致寫入熱點集中在最後一個分片
- Chunk 過大導致資料遷移緩慢或停滯

---
### Q: 交易 (Transaction) 與 ACID？

**核心回答：**
MongoDB 4.0 起副本集、4.2 起分片支援多檔案交易（Multi-Document Transactions），語意接近關聯式 ACID，但**代價高**：跨分片交易需要兩階段提交 (2PC)、持鎖時間長、且與 WiredTiger 快照隔離互動。設計上應優先**利用單檔案原子性**（巢狀嵌入相關資料，單一檔案的更新本身即為原子性）與冪等設計（如 upsert、版本欄位），將多檔案交易視為最後手段。

**深入原理：**
- 單檔案更新天然原子性：將『需一起修改的資料』嵌入同一檔案，多數情況可避免多檔案交易
- 多檔案交易：session.startTransaction，跨分片走兩階段提交 (2PC)，受限於最大持鎖超時與時間上限
- 寫入衝突與重試：交易在一致性快照上執行，若發生寫入衝突會自動中止 (Abort)，需在應用層實作重試邏輯
- 替代方案：巢狀嵌入 (Embedding)、冪等 upsert、應用層 Saga 模式或補償交易

**考官可能追問：**
- Q: 何時必須使用多檔案交易？
  - A: 確實需要跨多個 Collection 或檔案進行強一致性更新且無法合併時
- Q: 替代交易的優雅設計？
  - A: Embedding + 單檔案原子操作 + 應用層補償機制

**常見陷阱 / 易錯點：**
- 長交易持有鎖定拖垮整個叢集並行效能
- 高並行下交易頻繁 Abort 導致應用程式重試雪崩
- 以為 NoSQL 交易與 RDB 一樣低開銷而濫用

---
### Q: Aggregation Pipeline 聚合管道？

**核心回答：**
$match、$group、$lookup、$sort、$project 等階段組成的管道。$lookup 類似 SQL 的 Join 操作（注意索引效能）。索引支援 $match 階段前置以過濾資料。

**深入原理：**
- allowDiskUse 允許大資料量排序寫入暫存磁碟
- $facet 多維度分頁與統計
- 使用 explain() 分析聚合管道執行計畫

**考官可能追問：**
- Q: $lookup 效能極差？
  - A: 需確保關聯欄位有索引，且盡可能在 $lookup 前使用 $match 縮減資料量
- Q: MapReduce？
  - A: 自 5.0 起廢棄，6.0 中已被完全移除，聚合管道是唯一推薦方式

**常見陷阱 / 易錯點：**
- 將 $match 過濾階段放在 $lookup 之後
- 無索引導致聚合階段觸發 COLLSCAN（全表掃描）

---
### Q: MongoDB 一致性：Read/Write Concern？

**核心回答：**
Read Concern 包含 local、majority、linearizable、snapshot。Write Concern 包含 w:1、w:majority、j:true/false。線性一致性 (Linearizable) 需搭配 causal consistency session 確保因果一致性。

**深入原理：**
- afterClusterTime快照同步
- Hedged Reads 降低讀取延遲
- Retryable Writes 寫入自動重試

**考官可能追問：**
- Q: 金融訂單場景？
  - A: 使用 Write Concern majority + j:true 配合 Retryable Writes
- Q: 快取與 MongoDB 一致性？
  - A: 依賴應用層 Cache-Aside 或雙寫機制

**常見陷阱 / 易錯點：**
- Write Concern w:1 時主節點損壞導致未同步寫入遺失
- 忽略寫入確認錯誤 (Write Concern Error)

---
### Q: Change Streams 應用？

**核心回答：**
基於 oplog 封裝，訂閱監聽 Collection/Database 的變更（insert、update、delete），推送實時變更事件。常用於 CDC（變更資料擷取）、快取失效、同步至 Elasticsearch 等。

**深入原理：**
- Resume Token 斷點續傳機制
- fullDocument: 'updateLookup' 獲取更新後的完整檔案
- 大變更事件拆分與過濾

**考官可能追問：**
- Q:  vs Debezium？
  - A: Change Streams 是原生的且配置簡單，Debezium 則適合異構資料庫統一 CDC
- Q: 網路斷線如何恢復？
  - A: 儲存 Resume Token，重連時傳入 resumeAfter

**常見陷阱 / 易錯點：**
- 未儲存 Resume Token 導致斷線重連後重放全量資料
- oplog 空間不足導致 Resume Token 溢位過期

---
### Q: MongoDB 效能調優與最佳化？

**核心回答：**
使用 explain() 分析執行計畫、設計合適索引（遵循 ESR）、利用 Projection 僅返回所需欄位、調整批次大小 (Batch Size)、合理配置連線池、避免 large skip（改用 _id 範圍查詢）。

**深入原理：**
- 覆蓋查詢 (Covered Query) 無需回表
- 索引交集 (Index Intersection)
- Database Profiler 與 slowms 慢查詢定義

**考官可能追問：**
- Q: 百萬級資料 skip 分頁？
  - A: 改用 _id > last_seen_id 的範圍查詢定位
- Q: EXPLAIN 顯示 COLLSCAN？
  - A: 立即針對查詢條件建立合適索引

**常見陷阱 / 易錯點：**
- 正規表示式前置模糊查詢導致索引失效
- 濫用 allowDiskUse 掩蓋索引未建立或記憶體排序超限問題

---
### Q: 巢狀嵌入 (Embedding) vs 引用 (Referencing) 建模？

**核心回答：**
巢狀嵌入：適用於 1-to-N 且 N 較小、經常需要一起讀取、要求原子性更新的場景。引用：適用於 N 較大且獨立增長、多對多 (M-to-N) 關係的場景。權衡標準在於檔案大小與查詢模式。

**深入原理：**
- 檔案最大 16MB 限制與檔案增長 (Document Growth)
- 雙向引用維護一致性成本
- Subset Pattern（子集模式）最佳化常用資料讀取

**考官可能追問：**
- Q: 陣列欄位無限增長？
  - A: 使用分桶模式 (Bucketing Pattern) 拆分檔案
- Q: 關聯查詢頻繁？
  - A: 考慮反正規化嵌入，或使用 $lookup 關聯

**常見陷阱 / 易錯點：**
- 巢狀嵌入陣列無邊界增長導致檔案超出 16MB 限制
- 引用關聯欄位忘記建立索引

---
### Q: MongoDB 實務使用場景？

**核心回答：**
體育/客服場景：適用於非結構化日誌、客服通聯記錄 (contact logs)、彈性 schema 報表。不建議作為核心交易與強關聯性的帳務資料庫（核心交易仍應採用 MySQL/PostgreSQL）。

**深入原理：**
- 與關聯式資料庫 (RDB) 的分工協同
- 利用 TTL 索引自動清理過期日誌
- 聚合框架產出 KPI 報表

**考官可能追問：**
- Q: 訂單系統為何不用 MongoDB？
  - A: 需要關聯式資料庫的嚴格 ACID 與複雜多表 Join 關係保證
- Q: Schema 遷移？
  - A: 應用層進行漸進式 schema 收斂與遷移

**常見陷阱 / 易錯點：**
- 將 MongoDB 當作傳統關聯式資料庫進行高度正規化設計
- 直接將 MongoDB 作為主交易資料庫而無備援機制

**實務場景：**
高吞吐量資料管線實務：資料管線資料分散儲存於 MongoDB 與 MySQL；客服系統用 MongoDB 作為 KPI 統計來源

---

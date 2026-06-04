# MySQL 面試 Q&A

> 來源：interview-go（mysql/）、tech-vault
> 題數：21 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: InnoDB 與 MyISAM 核心差異？

**核心回答：**
InnoDB：列鎖 (Row Lock)、MVCC、交易支援、崩潰復原（redo/undo log）、聚集索引 (Clustered Index)。MyISAM：表鎖 (Table Lock)、無交易、非聚集索引、count(*) 快（有專門計數器）但寫入不安全. 生產環境 OLTP 幾乎全用 InnoDB。

**深入原理：**
- InnoDB buffer pool 快取資料頁
- MyISAM 適合唯讀 archive
- InnoDB 主鍵即資料本身

**考官可能追問：**
- Q: 為何 count(*) 慢？
  - A: InnoDB 估算或全表掃描 vs MyISAM 讀計數器
- Q: MyISAM 還用在哪？
  - A: 極少，legacy 舊系統

**常見陷阱 / 易錯點：**
- 混用引擎無法保證交易
- 無 PK 的 InnoDB 表會使用隱式 row_id

---
### Q: B+ 樹索引為何適合 MySQL？

**核心回答：**
B+ 樹多路平衡，樹高低（3-4 層可容納百萬行）、磁碟 I/O 少；非葉子節點僅儲存鍵值與分岔指標，擁有極高的分支因子 (Fanout)；葉子節點包含所有資料並以雙向鏈結串列相連，能完美支援範圍掃描 (Range Scan)。相比 B 樹（非葉子節點亦存資料）能減少樹高；相比雜湊不支援排序與範圍查詢。

**深入原理：**
- 資料頁預設 16KB
- 聚集索引葉子節點 = 行資料本身
- 二級索引（輔助索引）葉子節點 = 主鍵值（需回表）

```svg
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
```

**考官可能追問：**
- Q: 為何不用紅黑樹？
  - A: 紅黑樹是二叉樹，樹高過高，導致磁碟 I/O 次數多
- Q: UUID PK 問題？
  - A: 隨機插入導致頻繁的頁分裂與隨機 I/O

**常見陷阱 / 易錯點：**
- 過寬的主鍵會大幅增大二級索引體積
- 在索引欄位上使用函式導致索引失效

**實務場景：**
K 線表 rebuild index 最佳化 time range 查詢

---
### Q: 聚簇索引與二級索引？回表與覆蓋索引？

**核心回答：**
InnoDB 表資料按主鍵 (PK) 聚簇儲存；二級索引（次級索引）儲存格式為 (index_col, PK)。查詢需回表：先查二級索引取得 PK 值，再至聚簇索引查完整行資料。覆蓋索引：SELECT 所需列均在二級索引中，無需回表（Using index）。

**深入原理：**
- ICP 索引下推減少回表過濾次數
- MRR（Multi-Range Read）排序 PK 進行批次回表
- 聯合索引遵循最左字首原則

**考官可能追問：**
- Q: 無 PK？
  - A: 選擇唯一非空欄位，或由 InnoDB 生成隱式 row_id
- Q: 二級索引越多越好？
  - A: 會帶來寫入放大與最佳化器選擇成本

**常見陷阱 / 易錯點：**
- 濫用 SELECT * 導致覆蓋索引失效
- 隱式型態轉換導致索引失效

---
### Q: MVCC 原理？Read View 如何判斷可見性？

**核心回答：**
每行資料含有隱式欄位 DB_TRX_ID、DB_ROLL_PTR，並透過 undo log 鏈組成歷史版本。Read View 包含 m_ids（活躍交易 ID 列表）、min_trx_id（活躍交易最小值）、max_trx_id（下一個將分配的交易 ID）。可見性規則：1) trx_id == creator_trx_id → 可見；2) trx_id < min_trx_id → 已提交，可見；3) trx_id >= max_trx_id → 建立後開啟，不可見；4) min <= trx_id < max 且不在 m_ids 中 → 已提交，可見；其餘不可見。RR 在首次讀取時建立 View，RC 每次讀取皆新建。

**深入原理：**
- undo log 儲存舊版本
- delete mark 僅作刪除標記而未立即實體刪除
- purge 執行緒清理不再被 any Read View 需要的 undo log

```svg
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
```

**考官可能追問：**
- Q: RR 如何避免幻讀？
  - A: 快照讀靠 MVCC；目前讀 (Current Read) 靠間隙鎖 (Gap Lock)
- Q: 長交易危害？
  - A: 導致 undo log 堆積，阻止 purge 執行緒清理，使資料表膨脹

**常見陷阱 / 易錯點：**
- 以為 MVCC 完全無鎖
- RC 下使用 binlog statement 格式可能導致主從不一致歷史問題

---
### Q: 四種隔離層級與現象？

**核心回答：**
RU：髒讀（Read Uncommitted）。RC：無髒讀，但有不可重複讀（Read Committed）。RR：快照讀藉由 MVCC 避免不可重複讀，目前讀 (Current Read) 藉由間隙鎖防幻讀（InnoDB 預設）。Serializable：所有讀取皆加鎖，效能最差。

**深入原理：**
- 快照讀 (Snapshot Read) vs 目前讀 (Current Read)
- 間隙鎖 (Gap Lock) 與 Next-key Lock
- Semi-consistent read 最佳化

**考官可能追問：**
- Q: RR 隔離層級一定無幻讀？
  - A: 非也。若先快照讀，隨後執行 UPDATE 修改了其他交易剛提交的新插入列，則會將該列的 trx_id 改為自己，導致後續讀取產生幻讀；寫入偏斜 (Write Skew) 也需注意
- Q: 為何很多生產環境使用 RC？
  - A: 鎖定範圍小、死鎖機率低，且對 binlog row 格式友好

**常見陷阱 / 易錯點：**
- 混用 FOR UPDATE 與普通 SELECT 造成認知不一致
- 間隙鎖導致死鎖

---
### Q: InnoDB 鎖型別？Record/Gap/Next-Key？

**核心回答：**
Record lock 鎖定索引記錄；Gap lock 鎖定間隙防插入；Next-key = Record + Gap 鎖。插入意向鎖（Insert Intention Lock）與 Gap/Next-Key 鎖互斥，當間隙被鎖定時插入會阻塞。無索引欄位更新會導致全表掃描並鎖定所有掃描行，並非鎖升級（InnoDB 無鎖升級機制）。

**深入原理：**
- 表級意向鎖 IS/IX
- AUTO-inc 鎖
- 中繼資料鎖 (Metadata Lock)

**考官可能追問：**
- Q: 死鎖日誌？
  - A: SHOW ENGINE INNODB STATUS
- Q: 如何減少鎖定？
  - A: 利用精確索引、縮短交易、使用 RC

**常見陷阱 / 易錯點：**
- varchar 未加引號導致隱式轉換使索引失效鎖全表
- 範圍更新在無索引時加鎖範圍巨大

---
### Q: 死鎖如何產生與排查？

**核心回答：**
兩個交易以不同順序鎖定資源，形成迴圈等待。InnoDB 會自動偵測並選擇回滾代價最小的交易。排查：SHOW ENGINE INNODB STATUS、performance_schema.data_locks。

**深入原理：**
- 應用層固定鎖定順序
- 合理的重試機制
- 縮小交易範圍

**考官可能追問：**
- Q: 間隙鎖死鎖例子？
  - A: 兩個交易同時在同一個間隙取得 Gap 鎖，並隨後嘗試寫入該間隙
- Q: 死鎖監控？
  - A: 開啟 innodb_print_all_deadlocks

**常見陷阱 / 易錯點：**
- 捕獲死鎖異常卻未在應用層進行重試
- 長交易持有鎖定時間過長

---
### Q: redo log 與 undo log 與 binlog 區別？

**核心回答：**
redo log：InnoDB 專屬物理頁修改日誌，用於崩潰復原（Crash Recovery），迴圈寫入。undo log：儲存歷史版本，用於交易回滾與 MVCC。binlog：MySQL Server 層邏輯日誌，用於主從複製與 point-in-time 還原。兩階段提交（2PC）用於協調 redo 與 binlog 的一致性。

**深入原理：**
- WAL（Write-Ahead Logging）：先寫日誌，再刷髒頁
- binlog 格式：Row、Statement、Mixed
- sync_binlog=1 與 innodb_flush_log_at_trx_commit=1 最安全雙一配置

**考官可能追問：**
- Q: redo 迴圈覆蓋？
  - A: 覆蓋舊 checkpoint 前必須將對應髒頁刷盤
- Q: 半同步複製？
  - A: 主庫寫入後需等待至少一個從庫的 ACK 回包

**常見陷阱 / 易錯點：**
- binlog 使用 statement 格式導致主從不一致
- redo log 空間不足阻塞寫入

---
### Q: 兩階段提交（2PC）在 MySQL 中？

**核心回答：**
交易提交時：1) redo log prepare 2) 寫入 binlog 3) redo log commit。崩潰復原時以 binlog 是否寫入為準協調：若 binlog已寫入但 redo 處於 prepare，則提交交易；若無 binlog 且 redo 處於 prepare，則回滾交易。保證 redo 與 binlog 資料一致。

**深入原理：**
- XID 關聯標識
- 群組提交 (Group Commit) 最佳化 fsync 頻率
- 分散式 XA 交易是另一概念

**考官可能追問：**
- Q: 為何需要 binlog 與 redo 兩套？
  - A: redo 是引擎層的崩潰復原保證；binlog 是 Server 層的複製與還原基礎
- Q: 遺失 binlog 危害？
  - A: 會導致主從資料不一致

**常見陷阱 / 易錯點：**
- 誤以為 redo log 是用於主從複製的

---
### Q: 慢查詢如何分析與最佳化？

**核心回答：**
開啟 slow_query_log、long_query_time；使用 EXPLAIN 分析 type、key、rows、Extra 欄位。最佳化手段：建立精確索引、改寫 SQL、拆分查詢、引入快取。避免 SELECT *、欄位套用函式、隱式型態轉換。

**深入原理：**
- EXPLAIN ANALYZE 實際執行計畫與耗時
- pt-query-digest 聚合分析
- optimizer trace 追蹤最佳化器決策

**考官可能追問：**
- Q: type 為 ALL 一定壞？
  - A: 極小表全表掃描比走索引快
- Q: filesort 最佳化？
  - A: 利用索引的有序性消除 filesort

**常見陷阱 / 易錯點：**
- 只關注 rows 而忽略了 filtered 欄位
- 上線複雜 SQL 前未進行 EXPLAIN 檢查

**實務場景：**
例如用 EXPLAIN + index rebuild 最佳化 K 線聚合 SP

---
### Q: 聯合索引與最左字首？

**核心回答：**
索引 (a,b,c) 可用於 a、ab、abc 條件；跳過 b 單用 c 則無法發揮索引定位作用。欄位順序設計：高選擇性、常查欄位靠前；等值查詢欄位在前，範圍查詢欄位在後（因範圍查詢後的索引欄位無法用於精確定位）。

**深入原理：**
- 索引合併 index_merge
- 覆蓋索引包含所有查詢列
- 字首索引省空間但無法用於排序

**考官可能追問：**
- Q: 條件 (a,b) 只查 b？
  - A: 通常無法走索引，除非觸發 8.0 Index Skip Scan
- Q: order by b,c 走索引？
  - A: 需要最左 a 欄位為等值條件匹配

**常見陷阱 / 易錯點：**
- 範圍欄位後面的索引欄位失效
- 重複建立多個多餘索引

---
### Q: 索引下推（ICP）是什麼？

**核心回答：**
MySQL 5.6+ 引入。在二級索引掃描時，儲存引擎層會先利用索引列過濾 WHERE 條件，符合條件後再進行回表，大幅減少回表次數。Extra 顯示 Using index condition。

**深入原理：**
- 僅適用於 InnoDB 二級索引
- 包含主鍵欄位的條件下推
- 與覆蓋索引不同，覆蓋索引是不需要回表

**考官可能追問：**
- Q: 何時無效？
  - A: 聚簇索引掃描時
- Q: 效能提升場景？
  - A: 二級索引中包含部分未走最左字首的過濾條件

**常見陷阱 / 易錯點：**
- 以為 ICP 與覆蓋索引是同一個概念

---
### Q: 索引失效常見場景？

**核心回答：**
對欄位進行函式運算、隱式型態轉換（如字串與數字比較）、使用 like '%x' 前導模糊、OR 連線一側無索引、使用不等於 (<> / !=)、最佳化器估算成本過高（統計資訊過舊）、聯合索引違反最左字首原則。

**深入原理：**
- force index 強制走索引（慎用）
- analyze table 更新過時統計資訊
- 8.0 直方圖 (Histogram) 最佳化估算

**考官可能追問：**
- Q: != 一定不走索引？
  - A: 若選擇性極高，最佳化器仍可能選擇索引
- Q: 字元集轉換失效？
  - A: 關聯欄位字元集不同（如 utf8mb4 與 utf8）導致隱式轉換

**常見陷阱 / 易錯點：**
- SQL 改寫後未重新 explain 驗證
- MRR/ICP 被最佳化器誤判

---
### Q: 預存程式 (Stored Procedure) 優缺點？K 線（OHLC）場景如何用？

**核心回答：**
預存程式在資料庫內部聚合以減少網路來回 (network round-trip)、適合封裝複雜 OHLC 邏輯。缺點：版本管理與 CI/CD 難、除錯弱、佔用資料庫 CPU/記憶體資源、移植性差。實務上在寫入端利用預存程式進行 K 線聚合與異常 duplicate 清洗。

**深入原理：**
- 與 app 層職責劃分
- Prepared Statement 的效能優勢
- 預存程式內的安全防範（防 SQL 注入）

**考官可能追問：**
- Q: 何時不建議使用？
  - A: 業務邏輯複雜且變更頻繁時
- Q: 效能權衡？
  - A: 減少網路傳輸但將計算壓力轉移到 DB

**常見陷阱 / 易錯點：**
- 預存程式內無索引導致全表掃描
- 業務邏輯散落於 app 與 SP 中難以維護

**實務場景：**
例如：MySQL SP 聚合 K 線 + index rebuild，配合 Redis ZSET，延遲 量化的延遲區間→量化的延遲區間

---
### Q: 主從複製原理與延遲？

**核心回答：**
主庫 binlog → 從庫 I/O 執行緒寫入中繼日誌 (relay log) → SQL 執行緒重放。預設為非同步複製；半同步複製至少等待一個從庫 ACK；GTID 簡化故障切換。平行複製（基於 Write Set 或交易提交時間戳記）可降低延遲。

**深入原理：**
- 中繼日誌 (relay log) 機制
- 讀寫分離下的過期髒讀問題
- Seconds_Behind_Master 的不準確性

**考官可能追問：**
- Q: 延遲過大原因？
  - A: 大交易、從庫硬體瓶頸、單執行緒 apply 限制
- Q: 雙主 (Active-Active) 限制？
  - A: 需防範雙向寫入衝突與自增 ID 重複

**常見陷阱 / 易錯點：**
- 從庫讀取 RR 級別仍可能讀到舊資料
- 大表 DDL 導致主從複製嚴重延遲

---
### Q: 分庫分表策略？

**核心回答：**
垂直分割：按業務模組拆分資料庫。水平分割：選定 Shard Key 進行 Hash/Range 分片。挑戰：跨 Shard Join 效能極差、分散式唯一 ID、擴充時資料遷移與平衡。常見中介軟體：ShardingSphere、Vitess。

**深入原理：**
- Snowflake 雪花演演算法產生唯一 ID
- 全域次級索引表設計
- 雙倍擴充遷移法（降低停機時間）

```svg
<svg viewBox="0 0 660 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="一致性雜湊環：key 順時針落到下一個節點，增刪節點僅影響相鄰區段">
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
```

**考官可能追問：**
- Q: Shard Key 選擇 user_id 的優劣？
  - A: 優點為使用者相關資料內聚，缺點為易產生熱點使用者
- Q: 分散式交易？
  - A: 二階段提交 XA 或基於 MQ 的最終一致性 TCC/Saga

**常見陷阱 / 易錯點：**
- 熱點 Shard 導致單點負載過高
- 跨 Shard 進行排序與分頁操作 (LIMIT/OFFSET)

---
### Q: MySQL 連線池如何配置？

**核心回答：**
使用 HikariCP 或 Go sql.DB 時設定：max_open_conns、max_idle_conns、conn_max_lifetime。連線數過大會耗盡 DB 記憶體/執行緒資源；過小會造成請求排隊。常用經驗公式：connections ≈ (core*2) + disk_spindle，仍需依實際業務進行壓測調整。

**深入原理：**
- wait_timeout 與 conn_max_lifetime 的匹配
- Prepared Statement 快取設定
- 連線洩漏 (Connection Leak) 偵測

**考官可能追問：**
- Q: Go sql.DB 預設？
  - A: 預設無限制，高流量下極度危險
- Q: RDS max_connections 限制？
  - A: 通常與資料庫實例規格（CPU/記憶體）正相關

**常見陷阱 / 易錯點：**
- 未設定逾時時間 (Timeout)
- 長交易佔用連線不釋放

---
### Q: ORDER BY 與 GROUP BY 最佳化？

**核心回答：**
利用索引的有序性避免 filesort（Extra 顯示 Using filesort 即為硬體排序）。GROUP BY 可利用鬆散索引掃描 (Loose Index Scan)。當暫存表超出 tmp_table_size 限制時會寫入磁碟，導致效能暴跌。

**深入原理：**
- only_full_group_by 語法限制
- distinct vs group by 的最佳化選擇
- MySQL 8.0 視窗函式 (Window Functions)

**考官可能追問：**
- Q: filesort 演演算法？
  - A: 單路排序 vs 雙路排序 (sort_buffer_size)
- Q: 深度分頁最佳化？
  - A: 利用延遲關聯 (Deferred Join)

**常見陷阱 / 易錯點：**
- 對非索引欄位進行 GROUP BY
- 大型 GROUP BY 導致記憶體溢位寫入磁碟

---
### Q: InnoDB Buffer Pool 機制？

**核心回答：**
快取資料頁與索引頁，採用改進型 LRU 演演算法（分為 young/old 兩區域，以 midpoint 劃分，防止全表掃描汙染快取）。髒頁 (Dirty Page) 由 redo log 保護，透過 checkpoint 機制非同步刷盤。生產環境快取命中率應達 99% 以上。

**深入原理：**
- Change Buffer：對非唯一二級索引寫入的快取最佳化
- Doublewrite Buffer：雙寫緩衝區防範半頁寫入 (Partial Page Write) 損壞
- innodb_buffer_pool_size 設定為系統記憶體的 70-80%

**考官可能追問：**
- Q: Buffer Pool 預熱？
  - A: 重啟時自動 dump 與 load 快取頁結構
- Q: 頁淘汰邏輯？
  - A: 優先淘汰乾淨頁，髒頁則會觸發非同步 flush

**常見陷阱 / 易錯點：**
- Buffer Pool 設定過小導致頻繁磁碟 I/O
- 未監控快取命中率 (Hit Rate)

---
### Q: 如何設計 K 線/OHLC 表結構？

**核心回答：**
建立資料表：主鍵或唯一索引為 (symbol_id, interval, open_time)；包含 open/high/low/close/volume 等欄位。建立索引 (symbol_id, interval, open_time DESC)。歷史資料分割槽：使用 BY RANGE(open_time) 進行歷史分割區管理。寫入使用 ON DUPLICATE KEY UPDATE 實現冪等 upsert。

**深入原理：**
- 與 Redis ZSET 職責分工：DB 作為權威儲存，ZSET 提供熱區間高速查詢
- 利用預存程式聚合 tick → candle
- 異常 duplicate 資料的清洗

**考官可能追問：**
- Q: 分表策略？
  - A: 按 symbol_id 進行 hash 分表，或按時間進行分割槽
- Q: Tick 級資料？
  - A: 建議使用時序資料庫 (Time-Series DB) 如 InfluxDB/TimescaleDB

**常見陷阱 / 易錯點：**
- 無唯一約束導致重複的 K 線
- 範圍查詢未命中索引

**實務場景：**
例如經驗：SP 清洗 duplicate + index rebuild + Redis ZSET 熱資料

---
### Q: 線上對大表加索引/改欄位如何不鎖表？（gh-ost / pt-osc）

**核心回答：**
MySQL 5.6+ 支援 Online DDL（ALGORITHM=INPLACE, LOCK=NONE），多數加索引可線上完成，但修改欄位型態、加全文索引等仍會重建表 (rebuild table) 或短暫鎖定。大表生產環境常用 gh-ost 或 pt-online-schema-change：建影子表 → 透過 binlog (gh-ost) 或觸發器 (pt-osc) 同步增量 → 分批複製舊資料 → 原子 rename 切換，避免長時間鎖定與主從延遲堆積。

**深入原理：**
- pt-osc 使用觸發器同步原表變更；gh-ost 解析 binlog 同步，無觸發器開銷，對主庫更輕量且可動態限流/暫停
- INPLACE vs COPY：COPY 重建整表並鎖定；INSTANT（8.0.12+）可即時完成，且自 8.0.29 起支援在表中任意位置新增與刪除欄位
- 需預留磁碟空間（容納影子表）、控制 chunk 複製大小與 replica lag 複製延遲閾值

**考官可能追問：**
- Q: gh-ost 為何比 pt-osc 對主庫友善？
  - A: 不用觸發器、改讀 binlog，可動態限流/暫停，降低主庫負載
- Q: 8.0 INSTANT DDL 限制？
  - A: MySQL 8.0.29+ 已支援任意位置加/刪欄位，但修改欄位型態或縮減欄位長度仍不支援

**常見陷阱 / 易錯點：**
- 直接對大表進行 ALTER 導致長時間鎖表與主從複製延遲
- 未監控從庫複製延遲，切換時下游讀到不一致資料
- 磁碟空間不足導致影子表建立失敗

**實務場景：**
時間序列/圖表資料表 rebuild index 時需考量線上變更策略，避免鎖住交易/行情讀路徑

---

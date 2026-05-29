# MySQL 面試 Q&A

> 來源：interview-go（mysql/）、tech-vault
> 題數：21 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: InnoDB 與 MyISAM 核心差異？

**核心回答：**
InnoDB：行鎖、MVCC、事務、崩潰恢復（redo/undo）、聚簇索引。MyISAM：表鎖、無事務、非聚簇、count(*) 快但不安全寫。生產 OLTP 幾乎全 InnoDB。

**深入原理：**
- InnoDB buffer pool 快取頁
- MyISAM 適合只讀 archive
- InnoDB 主鍵即資料

**考官可能追問：**
- Q: 為何 count(*) 慢？
  - A: InnoDB 估算 vs 全表掃
- Q: MyISAM 還用在哪？
  - A: 極少，legacy

**常見陷阱 / 易錯點：**
- 混用引擎無法事務
- 無 PK 的 InnoDB 隱式 row_id

---
### Q: B+ 樹索引為何適合 MySQL？

**核心回答：**
B+ 樹多路平衡，樹高低（3-4 層百萬行）、磁碟 IO 少；葉子連結串列支援 range scan；非葉子只存 key 更 fanout。相比 B 樹葉子不存資料鏈接、相比 hash 支援排序與範圍。

**深入原理：**
- 頁預設 16KB
- 聚簇索引葉子=行資料
- 二級索引葉子=PK 值需回表

**考官可能追問：**
- Q: 為何不用紅黑樹？
  - A: 磁碟 IO 次數多
- Q: UUID PK 問題？
  - A: 隨機插入頁分裂

**常見陷阱 / 易錯點：**
- 過寬 PK 增大二級索引
- 函式索引前導列失效

**結合履歷：**
Roy K 線表 rebuild index 最佳化 time range 查詢。

---
### Q: 聚簇索引與二級索引？回表與覆蓋索引？

**核心回答：**
InnoDB 表資料按 PK 聚簇儲存；二級索引存 (index_col, PK)。查詢需回表：先查二級索引得 PK 再查聚簇。覆蓋索引：SELECT 列全在索引中則無需回表（Using index）。

**深入原理：**
- ICP 索引下推減少回表前過濾
- MRR 排序 PK 批量回表
- 聯合索引最左字首

**考官可能追問：**
- Q: 無 PK？
  - A: 選唯一非空或隱式 row_id
- Q: 二級索引越多越好？
  - A: 寫放大、optimizer 選擇

**常見陷阱 / 易錯點：**
- SELECT * 無法覆蓋
- 隱式型別轉換索引失效

---
### Q: MVCC 原理？Read View 如何判斷可見性？

**核心回答：**
每行有 DB_TRX_ID、DB_ROLL_PTR、undo log 鏈。Read View 含 m_ids（活躍事務）、min/max_trx_id。規則：trx_id < min → 可見；> max → 不可見；在 m_ids 中 → 不可見；否則可見。RR 首次讀建立 View，RC 每次讀新建。

**深入原理：**
- undo log 存舊版本
- delete mark 未物理刪
- purge 執行緒清理無 read view 需要的 undo

**考官可能追問：**
- Q: RR 避免幻讀？
  - A: 當前讀 gap lock；快照讀靠 MVCC
- Q: 長事務危害？
  - A: undo 堆積、purge 阻塞

**常見陷阱 / 易錯點：**
- 以為 MVCC 完全無鎖
- RC+binlog statement 不一致歷史問題

---
### Q: 四種隔離級別與現象？

**核心回答：**
RU：髒讀。RC：不可髒讀，可不可重複讀。RR（InnoDB 預設）：快照讀避免不可重複讀，當前讀靠 gap lock 防幻讀。Serializable：讀加鎖，最嚴。

**深入原理：**
- 快照讀 vs 當前讀
- gap lock/next-key lock
- semi-consistent read 最佳化

**考官可能追問：**
- Q: RR 一定無幻讀？
  - A: 當前讀 INSERT 仍可能；寫傾斜需注意
- Q: 為何很多用 RC？
  - A: 鎖少、binlog row 友好

**常見陷阱 / 易錯點：**
- 混用 FOR UPDATE 與普通 SELECT 認知不一致
- gap lock 死鎖

---
### Q: InnoDB 鎖型別？Record/Gap/Next-Key？

**核心回答：**
Record lock 鎖索引記錄；Gap lock 鎖間隙防插入；Next-key = record+gap。Insert intention lock 相容 gap。無索引列 update 可能鎖全表（lock escalation 到全表掃描行）。

**深入原理：**
- 意向鎖 IS/IX 表級
- AUTO-inc 鎖
- metadata lock（DDL）

**考官可能追問：**
- Q: 死鎖日誌？
  - A: SHOW ENGINE INNODB STATUS
- Q: 如何減鎖？
  - A: 索引精準、短事務、RC

**常見陷阱 / 易錯點：**
- varchar 不加引號隱式轉換
- 範圍更新無索引 gap 鎖大

---
### Q: 死鎖如何產生與排查？

**核心回答：**
兩事務以不同順序鎖資源→迴圈等待。InnoDB 自動檢測回滾代價小的事務。排查：SHOW ENGINE INNODB STATUS、performance_schema.data_locks。

**深入原理：**
- 應用層固定鎖順序
- 重試機制
- 小事務

**考官可能追問：**
- Q: gap lock 死鎖例子？
  - A: 兩事務插入同一 gap
- Q: 監控？
  - A: innodb_print_all_deadlocks

**常見陷阱 / 易錯點：**
- 捕獲死鎖不重試
- 長事務持鎖

---
### Q: redo log 與 undo log 與 binlog 區別？

**核心回答：**
redo：InnoDB 物理頁變更，crash recovery，迴圈寫。undo：事務回滾與 MVCC 舊版本。binlog：Server 層邏輯日誌，主從複製與 PITR。兩階段提交協調 redo 與 binlog 一致。

**深入原理：**
- WAL：先寫 redo 再刷髒頁
- binlog row/statement/mixed
- sync_binlog=1 最安全

**考官可能追問：**
- Q: redo 512MB 迴圈？
  - A: 覆蓋舊 checkpoint 前需刷髒
- Q: 半同步複製？
  - A: 至少一從 ack

**常見陷阱 / 易錯點：**
- binlog 開 statement 主從不一致
- redo 滿阻塞寫入

---
### Q: 兩階段提交（2PC）在 MySQL 中？

**核心回答：**
commit 時：1) redo prepare 2) 寫 binlog 3) redo commit。崩潰恢復時以 binlog 為準協調：有 binlog 無 redo commit 則提交；有 prepare 無 binlog 則回滾。保證 redo 與 binlog 一致。

**深入原理：**
- XID 關聯
- 組提交最佳化 fsync
- 分散式 XA 是另一概念

**考官可能追問：**
- Q: 為何需要 binlog 與 redo？
  - A: redo InnoDB 獨有；binlog 複製
- Q: 丟 binlog？
  - A: 從庫不一致

**常見陷阱 / 易錯點：**
- 以為 redo 用於複製

---
### Q: 慢查詢如何分析與最佳化？

**核心回答：**
開啟 slow_query_log、long_query_time；EXPLAIN 看 type、key、rows、Extra。最佳化：索引、改寫 SQL、拆分、快取。避免 SELECT *、函式包列、隱式轉換。

**深入原理：**
- EXPLAIN ANALYZE 實際行數
- pt-query-digest 聚合
- optimizer trace

**考官可能追問：**
- Q: type ALL 一定壞？
  - A: 小表 OK
- Q: filesort 最佳化？
  - A: 索引排序 Avoid filesort

**常見陷阱 / 易錯點：**
- 只看 rows 不看 filtered
- 上線無 explain

**結合履歷：**
Roy 用 EXPLAIN + index rebuild 最佳化 K 線聚合 SP。

---
### Q: 聯合索引與最左字首？

**核心回答：**
索引 (a,b,c) 可用於 a、ab、abc 條件；跳過 b 用 c 無法走索引（除 index skip scan 8.0+）。列順序：高選擇性、常查列靠前；等於在前範圍在後。

**深入原理：**
- 索引合併 index_merge
- 覆蓋索引含查詢列
- 字首索引省空間但排序弱

**考官可能追問：**
- Q: (a,b) 查 b alone？
  - A: 通常不走
- Q: order by b,c 索引？
  - A: 需最左 a 或匹配

**常見陷阱 / 易錯點：**
- 範圍列後無法再用於其他列
- 過多重複索引

---
### Q: 索引下推（ICP）是什麼？

**核心回答：**
MySQL 5.6+ 二級索引掃描時，在儲存引擎層用索引列先過濾 WHERE 條件，再回表，減少回表次數。Extra: Using index condition。

**深入原理：**
- 僅 InnoDB 二級索引
- 含 PK 列條件下推
- 與覆蓋索引不同

**考官可能追問：**
- Q: 何時無效？
  - A: 主鍵索引掃描
- Q: 效能提升場景？
  - A: 二級索引+部分列匹配

**常見陷阱 / 易錯點：**
- 以為 ICP=覆蓋索引

---
### Q: 索引失效常見場景？

**核心回答：**
對列函式/運算、隱式型別轉換、like '%x'、OR 一側無索引、不等於、最佳化器選錯（統計資訊舊）、聯合索引違背最左。

**深入原理：**
- force index 慎用
- analyze table 更新統計
- 8.0 histogram

**考官可能追問：**
- Q: != 一定不走索引？
  - A: 看選擇性 optimizer 決定
- Q: 字元集轉換？
  - A: col 與常量字元集不同

**常見陷阱 / 易錯點：**
- SQL 改寫後未 explain
- MRR/ICP 誤判

---
### Q: Stored Procedure 優缺點？Roy K 線場景？

**核心回答：**
SP 在 DB 內聚合減少 network round-trip、可封裝複雜 OHLC 邏輯。缺點：版本管理難、除錯弱、鎖 DB 資源、可移植性差。Roy 用 SP 做 K 線聚合+清洗異常 duplicate。

**深入原理：**
- 與 app 層職責劃分
- prepared statement 類似邊界
- 許可權與安全 SQL injection in SP

**考官可能追問：**
- Q: 何時不用 SP？
  - A: 複雜業務規則、頻繁變更
- Q: 效能？
  - A: 減少 RTT 但 CPU 在 DB

**常見陷阱 / 易錯點：**
- SP 無索引表掃描
- 邏輯散落 app+SP 難維護

**結合履歷：**
Roy：MySQL SP 聚合 K 線 + index rebuild，配合 Redis ZSET，延遲 3–5s→300–500ms。

---
### Q: 主從複製原理與延遲？

**核心回答：**
主庫 binlog → 從庫 IO thread 拉 relay log → SQL thread 重放。非同步預設有延遲；半同步等一從 ack；GTID 簡化 failover。並行複製（基於 commit timestamp）減 lag。

**深入原理：**
- relay log
- read/write split 髒讀
- Seconds_Behind_Master 不準確

**考官可能追問：**
- Q: 延遲大？
  - A: 大事務、從庫硬體、單執行緒 apply
- Q: 雙主？
  - A: 謹慎環衝突

**常見陷阱 / 易錯點：**
- 從庫讀 RR 仍可能舊
- DDL 阻塞複製

---
### Q: 分庫分表策略？

**核心回答：**
垂直：按業務拆庫。水平：shard key hash/range。挑戰：跨 shard join、分散式 ID、擴容 rebalance。中介軟體 ShardingSphere、Vitess。

**深入原理：**
- snowflake ID
- 全域二級索引表
- 擴容雙倍遷移

**考官可能追問：**
- Q: shard key 選 user_id？
  - A: 均衡+業務區域性性
- Q: 事務？
  - A: XA 或最終一致

**常見陷阱 / 易錯點：**
- 熱點 shard
- 跨 shard 排序分頁

---
### Q: MySQL 連線池如何配置？

**核心回答：**
HikariCP/Go sql.DB：max_open、max_idle、conn_max_lifetime。過大連線耗盡 DB；過小排隊。公式參考：connections ≈ (core*2) + disk_spindle，需壓測。

**深入原理：**
- wait_timeout 與 lifetime
- prepared stmt 快取
- 連線洩漏檢測

**考官可能追問：**
- Q: Go sql.DB 預設？
  - A: 無 limit 危險
- Q: RDS max_connections？
  - A: 與實例規格相關

**常見陷阱 / 易錯點：**
- 不設 timeout
- 長事務佔連線

---
### Q: ORDER BY 與 GROUP BY 最佳化？

**核心回答：**
利用索引有序 Avoid filesort。GROUP BY 可走 loose index scan（滿足字首）。臨時表記憶體 tmp_table_size 超限落盤。

**深入原理：**
- only_full_group_by
- distinct vs group by
- 視窗函式 8.0

**考官可能追問：**
- Q: filesort 兩種演算法？
  - A: 單路/雙路 sort buffer
- Q: limit 最佳化？
  - A: 延遲關聯

**常見陷阱 / 易錯點：**
- group by 非索引列
- 大 group 記憶體 sort

---
### Q: InnoDB Buffer Pool 機制？

**核心回答：**
快取資料頁與索引頁，LRU 變種（young/old  midpoint）。dirty page 由 redo 保護，checkpoint 刷盤。命中率應 >99%。

**深入原理：**
- change buffer 二級索引寫最佳化
- doublewrite 防 partial page write
- innodb_buffer_pool_size 70-80% RAM

**考官可能追問：**
- Q: buffer pool dump？
  - A: 重啟預熱
- Q: 頁淘汰？
  - A: clean 優先，dirty 觸發 flush

**常見陷阱 / 易錯點：**
- buffer pool 過小頻繁磁碟讀
- 未監控 hit rate

---
### Q: 如何設計 K 線/OHLC 表結構？

**核心回答：**
表：(symbol_id, interval, open_time) PK 或 unique；列 open/high/low/close/volume。索引 (symbol, interval, open_time DESC)。歷史分割槽 BY RANGE(open_time)。寫入 upsert ON DUPLICATE KEY UPDATE。

**深入原理：**
- 與 Redis ZSET 分工：DB 權威、cache 熱窗
- SP 聚合 tick→candle
- 異常 duplicate 清洗

**考官可能追問：**
- Q: 分表？
  - A: 按 symbol hash 或 time 分割槽
- Q: tick 級？
  - A: 時序庫或分表

**常見陷阱 / 易錯點：**
- 無 unique 重複 candle
- range 查詢無索引

**結合履歷：**
Roy 實際經驗：SP 清洗 duplicate + index rebuild + Redis ZSET 熱資料。

---
### Q: 線上對大表加索引/改欄位如何不鎖表？（gh-ost / pt-osc）

**核心回答：**
MySQL 5.6+ 支援 Online DDL（ALGORITHM=INPLACE, LOCK=NONE），多數加索引可線上完成，但改欄位型別、加全文索引等仍會 rebuild table 或短暫鎖。大表生產常用 gh-ost 或 pt-online-schema-change：建影子表 → 用觸發器/binlog 同步增量 → 分批 copy 舊資料 → 原子 rename 切換，避免長時間鎖與主從延遲堆積。

**深入原理：**
- pt-osc 用觸發器同步原表變更到新表；gh-ost 解析 binlog 同步，對主庫更輕量、可暫停限流
- INPLACE vs COPY：COPY 重建整表並鎖；INSTANT（8.0.12+）尾部加欄位可即時完成
- 需預留磁碟空間（影子表）、控制 chunk 大小與 replica lag 閾值

**考官可能追問：**
- Q: gh-ost 為何比 pt-osc 對主庫友善？
  - A: 不用觸發器、改讀 binlog，可動態限流/暫停，降低主庫負載
- Q: 8.0 INSTANT DDL 限制？
  - A: 只支援部分操作（如尾部加欄位），不能加在中間或改型別

**常見陷阱 / 易錯點：**
- 直接對大表 ALTER 造成長時間鎖與主從延遲
- 忘了監控 replica lag，切換時下游讀到不一致
- 磁碟空間不足導致影子表失敗

**結合履歷：**
Roy K 線表 rebuild index 時需考量線上變更策略，避免鎖住交易/行情讀路徑。

---

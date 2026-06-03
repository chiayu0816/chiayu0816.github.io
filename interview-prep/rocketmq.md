# RocketMQ 面試 Q&A

> 來源：tech-vault、交易所實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景（個人對照見 resume_overlay.py）

---

### Q: RocketMQ 架構：NameServer/Broker/Producer/Consumer？

**核心回答：**
NameServer 輕量路由註冊（無強一致）；Broker 存訊息 Master-Slave；Producer 發 MessageQueue；Consumer Push/Pull，Clustering/Broadcasting。

**深入原理：**
- Broker 與 NameServer 心跳
- Topic→Queue 對映
- Dledger 自動主從切換

**考官可能追問：**
- Q: NameServer 無 ZK？
  - A: 去中心化路由
- Q:  vs Kafka broker？
  - A: RMQ 多佇列 per topic

**常見陷阱 / 易錯點：**
- NameServer 全掛需重啟路由
- Broker 磁碟滿

**實務場景：**
交易/行情繫統以 gRPC/WS 整合 RocketMQ 承載 market/trading flow

---
### Q: Topic、Tag、MessageQueue 關係？

**核心回答：**
Topic 邏輯分類；Tag 子過濾（SQL92 訂閱）；MessageQueue 是實際儲存分片（類似 Kafka partition）。Consumer 訂閱 Topic+Tag 過濾。

**深入原理：**
- 一個 Topic 多 Queue 並行
- Tag hash 不影響佇列選擇
- Key 決定佇列保序

**考官可能追問：**
- Q: Tag vs 多 Topic？
  - A: Tag 輕量過濾
- Q: Queue 數？
  - A: 預設 4 可配

**常見陷阱 / 易錯點：**
- Tag 濫用致訂閱複雜
- Queue 過少吞吐低

---
### Q: 順序訊息如何實現？

**核心回答：**
MessageQueueSelector 同 sharding key 進同一 Queue；Consumer 單執行緒消費該 Queue 或 MessageListenerOrderly 加鎖順序處理。

**深入原理：**
- 區域性順序非全域
- 失敗重試阻塞佇列
- FIFO 與併發權衡

**考官可能追問：**
- Q: 訂單狀態機？
  - A: orderId 作 key
- Q: 重試亂序？
  - A: 順序消費失敗 suspend queue

**常見陷阱 / 易錯點：**
- 多 Queue 期望全域順序
- 慢訊息阻塞整佇列

---
### Q: 延遲訊息原理？

**核心回答：**
18 個固定延遲 level（1s 5s 1m...），訊息先存 SCHEDULE_TOPIC_XXXX，定時任務到期轉真實 topic。非任意精度延遲。

**深入原理：**
- 不支援任意 delay ms
- 定時掃表
- 高 level 靠 schedule service

**考官可能追問：**
- Q: 精確延遲？
  - A: RocketMQ 5 timer message 或外部排程
- Q: 大量延遲？
  - A: schedule topic 壓力

**常見陷阱 / 易錯點：**
- 以為任意 delay
- 延遲 level 選錯

---
### Q: 事務訊息（半訊息）流程？

**核心回答：**
1) 發 half message 2) 執行本地事務 3) commit/rollback half message。未決訊息回查 CheckTransactionListener。保證本地事務與訊息最終一致。

**深入原理：**
- Half message 對消費者不可見
- 回查次數限制
- 與 Kafka transaction 對比

**考官可能追問：**
- Q: 回查失敗？
  - A: rollback 訊息
- Q: 場景？
  - A: 扣庫存+發訂單訊息

**常見陷阱 / 易錯點：**
- 本地事務已提交回查失敗
- 回查邏輯非冪等

**實務場景：**
交易/行情繫統可用事務訊息保證 trading 狀態與下游通知一致

---
### Q: RocketMQ 消費模式 Push vs Pull？

**核心回答：**
Push 是長輪詢封裝，Broker 有訊息即推；Pull 消費者主動拉。Clustering 負載均衡；Broadcast 每實例全收。

**深入原理：**
- Push 背壓 consumeConcurrentlyMaxSpan
- Pull 適合流控
- Rebalance 類似 Kafka

**考官可能追問：**
- Q: Broadcast 用途？
  - A: 本地快取重新整理
- Q: 消費失敗？
  - A: 重試 16 次進 DLQ

**常見陷阱 / 易錯點：**
- Broadcast 寫 DB 重複
- 併發消費亂序

---
### Q: RocketMQ 高吞吐實踐？

**核心回答：**
Batch 發/消費、非同步 send、多 Queue、CommitLog 順序寫、ConsumeMessageConcurrently。Broker 頁快取+ mmap。

**深入原理：**
- 單檔案 CommitLog
- ConsumeQueue 索引
- 非同步刷盤 vs 同步

**考官可能追問：**
- Q: 同步刷盤？
  - A: 金融場景 durability
- Q: Batch size？
  - A: 平衡延遲吞吐

**常見陷阱 / 易錯點：**
- 同步刷盤效能驟降
- 單 Queue 熱點

---
### Q: RocketMQ 與 Kafka 選型？

**核心回答：**
RMQ：低延遲交易、Tag、延遲/事務訊息、運維國內文件多。Kafka：日誌流、大資料、超高吞吐、生態 Flink/Spark。

**深入原理：**
- RMQ 5.x gRPC proxy
- Kafka log compaction
- 混合架構常見

**考官可能追問：**
- Q: 都支援順序？
  - A: 都需 sharding key
- Q: 遷移成本？
  - A: Consumer 重寫

**常見陷阱 / 易錯點：**
- Kafka 強行做延遲訊息
- RMQ 當 data lake

---
### Q: 訊息重複與冪等？

**核心回答：**
At least once：網路重試、Rebalance 重複投遞。解決：業務冪等 key、DB unique、Redis SETNX、狀態機校驗。

**深入原理：**
- Producer retry
- Consumer 成功後 ack
- MessageId 去重表

**考官可能追問：**
- Q: Exactly once？
  - A: 事務訊息+冪等消費
- Q: 去重表膨脹？
  - A: TTL+partition

**常見陷阱 / 易錯點：**
- 無冪等重複扣款
- 去重 key 粒度錯

---
### Q: Broker 高可用與主從？

**核心回答：**
Sync Master-Slave 同步 flush；Dledger 組 commit 自動選主。NameServer 多實例無狀態。

**深入原理：**
- 非同步複製可能丟
- Slave 可讀?
- 故障切換時間

**考官可能追問：**
- Q: 腦裂？
  - A: Dledger 多數派
- Q: 跨機房？
  - A: 非同步複製+補償

**常見陷阱 / 易錯點：**
- 單 Master 無 Slave
- 磁碟 sync 未監控

---
### Q: RocketMQ 訊息堆積如何處理？

**核心回答：**
擴 Consumer 實例、增 Queue（需新建）、臨時跳過非核心、批次消費、下游提速、限流生產。

**深入原理：**
- 堆積監控 consume TPS vs produce
- 擴容 Queue 需重新分配
- 歷史訊息過期

**考官可能追問：**
- Q: 緊急擴容？
  - A: 加 consumer 實例最快
- Q: 堆積影響？
  - A: 磁碟 delay

**常見陷阱 / 易錯點：**
- 只加 consumer 不擴 queue
- 下游 DB 瓶頸未解

---
### Q: RocketMQ 在 crypto exchange 場景？

**核心回答：**
Market data、order events、hedging signals、notification 解耦；與 gRPC/WS 配合：MQ 非同步持久，WS 推實時。

**深入原理：**
- Topic 按 domain 分
- 關鍵路徑 sync gRPC
- MQ 削峰填谷

**考官可能追問：**
- Q: 延遲敏感撮合？
  - A: 記憶體+RPC 主路徑 MQ 輔助
- Q: 合規 audit？
  - A: 訊息軌跡 MessageTrace

**常見陷阱 / 易錯點：**
- 所有路徑走 MQ
- 訊息無序導致狀態錯

**實務場景：**
交易/行情繫統（matching/market data/hedging）經 RocketMQ 整合解耦

---

# RocketMQ 面試 Q&A

> 來源：tech-vault、交易所實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: RocketMQ 架架構：NameServer/Broker/Producer/Consumer？

**核心回答：**
RocketMQ 採分散式架構：NameServer 是無狀態、輕量級的路由註冊中心（採 AP 模型，不保證強一致，互相獨立）；Broker 負責訊息儲存與分發，支援 Master-Slave 架構；Producer 向指定 Queue 傳送訊息；Consumer 依據負載平衡分配 Queue 進行消費，支援群組消費 (Clustering) 與廣播消費 (Broadcasting)。

**深入原理：**
- Broker 每 30 秒向所有 NameServer 傳送心跳，NameServer 每 10 秒掃描一次，若超過 120 秒未收到心跳則剔除該 Broker
- Topic 與 Queue 對映關係存於 NameServer，Client（Producer/Consumer）定時從 NameServer 拉取路由資訊
- 5.x 架構引入 gRPC Proxy 模式，客戶端透過 Proxy 統一入口，大幅簡化容器化部署與網路穿透問題

**考官可能追問：**
- Q: 為何不使用 ZooKeeper 而自研 NameServer？
  - A: ZooKeeper 採 CP 模型，在 Leader 選舉期間服務不可用，且維護複雜。NameServer 各節點互不通訊，無狀態，單臺掛掉不影響其他節點運作，極其輕量穩定，非常適合僅需要路由註冊的 MQ 場景。
- Q: Dledger 模式與 5.x Controller 模式的區別？
  - A: Dledger 基於 Raft 協定，由 Dledger 接管 CommitLog 儲存，寫入效能較差。5.x 引入 Controller 角色（可部署於 NameServer 內），作為元資料中心控制主從切換，Broker 副本間則採更輕量高效的日誌複製協定，效能大幅提升。

**常見陷阱 / 易錯點：**
- NameServer 全部宕機時，雖然現有已連線的 Client 仍可憑本地快取傳送/消費訊息，但無法更新路由，一旦有 Broker 增減或 Topic 變更將立即失效
- 未對 Broker 磁碟水位設定警報，磁碟滿時 Broker 會拒絕所有寫入，導致業務中斷

**實務場景：**
交易/行情繫統以 gRPC/WS 整合 RocketMQ，承載即時交易流與行情分發

---
### Q: Topic、Tag、MessageQueue 關係與讀寫佇列？

**核心回答：**
Topic 代表邏輯訊息分類；Tag 是 Topic 下的子分類，用於輕量級過濾；MessageQueue 是實際的儲存分片與並行單位。RocketMQ 獨創「讀寫佇列分離」設計（writeQueueNums 與 readQueueNums），可在不中斷服務的情況下平滑進行佇列的擴縮容。

**深入原理：**
- 一個 Topic 在一個 Broker 上預設為 4 個寫佇列與 4 個讀佇列，兩者數量通常保持一致
- Tag 過濾在 Broker 端先進行 Hash 篩選，最後在 Consumer 端進行精確的字串比對
- 利用 MessageKey 可以作為訊息的唯一識別碼，並透過 MessageQueueSelector 將相同 Key 的訊息傳送至同一個 Queue

**考官可能追問：**
- Q: 讀寫佇列分離的具體應用場景？
  - A: 若要縮減佇列，可先將 writeQueueNums 從 8 縮小為 4，此時 Producer 僅會向 0-3 號佇列寫入訊息。待 Consumer 將 4-7 號佇列的存量訊息消費完畢後，再將 readQueueNums 調小為 4，如此可確保平滑縮容且不遺失訊息。
- Q: Tag 與多 Topic 的選型原則？
  - A: 若訊息關聯性強、結構相似，建議使用同一個 Topic 配合不同的 Tag 進行過濾（如 Topic=Order，Tag=Pay/Refund）；若訊息型別截然不同、安全存取控制粒度不同，則應宣告不同的 Topic。

**常見陷阱 / 易錯點：**
- 在同一個 Consumer Group 內，不同 Consumer 實例訂閱了同一個 Topic 但指定了不同的 Tag，這會破壞訂閱關係一致性（Subscription Relation），導致部分訊息隨機遺失或無法消費
- 佇列數量設定過少，限制了 Consumer 的並行度，成為系統效能瓶頸

---
### Q: 順序訊息如何實現與底層鎖機制？

**核心回答：**
RocketMQ 透過將相同 Sharding Key 的訊息傳送至同一個 MessageQueue，並在消費端使用 `MessageListenerOrderly` 來保證順序。其實作依賴三層鎖機制：Broker 端的佇列鎖（確保同一時間僅一個 Consumer 執行緒組消費該佇列）、Consumer 本地對應該佇列的 ProcessQueue 鎖，以及消費執行緒內的處理鎖，三者結合實現嚴格順序消費。

**深入原理：**
- Broker 鎖：Consumer 背景執行緒定時向 Broker 租借該 MessageQueue 的分散式鎖（預設有效期 20 秒），防止 Rebalance 時併發消費
- ProcessQueue 鎖：防止同一個 Consumer 實例內多個消費執行緒並行處理同一個佇列的訊息
- 順序消費失敗時，RocketMQ 不會將訊息送往重試佇列，而是將當前佇列掛起 (suspend)，在本地間隔重試，確保順序不被打亂

**考官可能追問：**
- Q: 順序消費遇到「毒藥訊息」卡死怎麼辦？
  - A: 由於順序消費失敗會持續在本地重試，因此必須在業務程式碼中對重試次數進行計數，超限時手動將訊息寫入死信佇列或資料庫，並回傳 CONSUME_SUCCESS 以跳過卡死狀態。
- Q: 全域順序如何實現？
  - A: 將 Topic 的 MessageQueue 數量設為 1，且僅部署一個 Consumer 實例。但這會完全失去並行能力，僅適用於低吞吐、對順序有絕對要求的場景。

**常見陷阱 / 易錯點：**
- 以為將訊息傳送到多個 Queue，在 Consumer 端開啟 MessageListenerConcurrently 仍能保證順序
- 本地事務未完成就傳送了順序訊息，或者網路重試導致順序訊息在傳送端就已失序

---
### Q: 延遲訊息原理與 5.x 任意精度定時訊息？

**核心回答：**
在 RocketMQ 4.x 中，僅支援 18 個固定的延遲級別（1s, 5s...2h），訊息先被寫入系統 Topic `SCHEDULE_TOPIC_XXXX`，定時任務到期後再還原至真實 Topic。而自 **RocketMQ 5.0** 起，引進了基於**時間輪 (Timing Wheel) 與 RocksDB** 的內建定時器，原生支援**任意精度（精確到毫秒）**的定時與延遲訊息。

**深入原理：**
- 4.x 延遲原理：Broker 內部為 18 個 Level 建立對應的 ConsumeQueue，並啟動 18 個定時任務定時掃描並還原訊息
- 5.x 任意精度：定時訊息先寫入系統的 TimerMessageLog，透過時間輪演算法進行滾動管理，時間到期後重新投遞
- 定時訊息的狀態儲存在本地 RocksDB 中，即使 Broker 重啟也能正確恢復定時任務

**考官可能追問：**
- Q: 如何宣告 5.x 的任意精度延遲訊息？
  - A: 在傳送訊息時設定 Message 的 DeliverTimeMs（預期投遞的時間戳記），而非設定延遲級別。
- Q: 大量定時訊息是否會壓垮 Broker？
  - A: 在 5.x 下，定時器有專門的執行緒池與 RocksDB 緩衝，但若在同一個毫秒點有數百萬條訊息到期，仍會造成瞬間的 CPU 與 I/O 尖峰，應盡量將定時時間進行微幅隨機打散（Jitter）。

**常見陷阱 / 易錯點：**
- 在 4.x 環境中企圖傳入自訂的 delayTimeMs，導致屬性被忽略或訊息傳送失敗
- 使用延遲訊息作為高頻率的定時任務排程器（如秒級輪詢），這會增加 Broker 的磁碟讀寫負擔，應結合專業的排程框架（如 XXL-JOB）

---
### Q: 事務訊息（半訊息）流程與實現原理？

**核心回答：**
RocketMQ 事務訊息保證了「本地事務執行」與「傳送 MQ 訊息」的原子性（最終一致性）。流程：1) Producer 傳送 Half Message 至 Broker；2) Broker 將 Topic 改為 `RMQ_SYS_TRANS_HALF_TOPIC` 暫存，對 Consumer 不可見並回傳 ACK；3) Producer 執行本地事務；4) Producer 提交 Commit/Rollback 給 Broker。若第四步失敗，Broker 會定時向 Producer 傳送「事務狀態回查」確認狀態。

**深入原理：**
- Half Message 儲存於 `HALF_TOPIC` 中，因 Consumer 未訂閱該系統 Topic，故無法消費，從而達到隔離效果
- Broker 每隔一段時間（預設 6 秒）掃描 `HALF_TOPIC`，若發現無對應 Op 標記（記錄在 `RMQ_SYS_TRANS_OP_HALF_TOPIC` 中），則向 Producer 回查
- 回查上限為 15 次，若 15 次回查皆未能取得狀態（如服務當機），Broker 將自動 Rollback 該訊息

**考官可能追問：**
- Q: 與 Kafka 事務有何不同？
  - A: Kafka 事務是資料庫式的二階段提交，側重於 read-process-write 的原子性，必須由 Kafka 全權控管。RocketMQ 事務專門設計用來協調外部本地事務（如資料庫操作）與訊息傳送的一致性，並具備反向回查機制，更加彈性。
- Q: 如果回查時本地事務尚未提交完畢（如併發鎖延遲）怎麼辦？
  - A: 回查 Listener 應返回 UNKNOWN 狀態，讓 Broker 稍後再次回查，不可盲目返回 COMMIT 或 ROLLBACK。

**常見陷阱 / 易錯點：**
- 本地事務已成功 Commit，但回查邏輯因資料庫主從複製延遲未能查到資料，導致回查返回 ROLLBACK 或 UNKNOWN
- 回查邏輯中包含耗時的外部服務呼叫，導致回查執行緒池被佔滿，造成事務確認積壓

**實務場景：**
交易/行情繫統使用事務訊息確保「扣減帳戶餘額」與「傳送交易完成通知訊息」兩者同生共死

---
### Q: RocketMQ 消費模式 Push vs Pop？

**核心回答：**
在 RocketMQ 4.x 中，Push 模式（實為 Client 端長輪詢拉取）與 Pull 模式皆依賴 Client 端的 Rebalance 演演算法，若某個 Consumer 當機或消費慢，會導致其分配到的 Queue 阻塞。**RocketMQ 5.x 引入了全新的 Pop 模式**，改由 Broker 端無狀態分配訊息，多個 Consumer 可並行消費同一個 Queue，解決了慢消費阻塞的問題。

**深入原理：**
- Push 模式底層：PullMessageService 執行緒定時拉取，當 Broker 無訊息時掛起請求（長輪詢預設 15 秒）
- Pop 模式原理：Consumer 向 Broker 傳送 Pop 請求，Broker 從 Queue 中取出訊息並標記為不可見（Lock），Consumer 消費完後傳送 Ack 進行確認
- 若 Pop 訊息消費超時未 Ack，Broker 會自動重新投遞該訊息，類似於 RabbitMQ 的 Ack 機制

**考官可能追問：**
- Q: 廣播模式 (Broadcasting) 的運作與限制？
  - A: 廣播模式下，同一個 Consumer Group 內的所有 Consumer 實例都會收到 Topic 的全量訊息。消費進度 (Offset) 儲存在 Consumer 本地而非 Broker，因此不支援消費失敗重試與訊息回溯。
- Q: 消費失敗後的重試機制？
  - A: 在群組模式下，消費失敗（丟擲異常或返回 RECONSUME_LATER）的訊息會被送往重試佇列 `%RETRY%GroupName`，最多重試 16 次且間隔時間逐次拉長，最後進入死信佇列 (DLQ)。

**常見陷阱 / 易錯點：**
- 在廣播模式下使用資料庫寫入操作，導致所有實例重複寫入相同資料
- 併發消費 (ConsumeMessageConcurrentlyService) 時，誤以為消費失敗的訊息會按順序立刻重試，實際上會進入重試佇列導致亂序

---
### Q: RocketMQ 高吞吐量實踐與暫存池最佳化？

**核心回答：**
RocketMQ 高吞吐量基於：1) 批次傳送與非同步傳送；2) CommitLog 單一檔案順序寫入；3) MappedByteBuffer (mmap) 記憶體對映讀寫。進階最佳化可啟用 **TransientStorePool (臨時儲存池)**，將寫入與刷盤記憶體隔離，降低 Page Cache 鎖競爭。

**深入原理：**
- TransientStorePool 原理：開啟後，訊息寫入由 Pool 分配的堆外記憶體 (Direct ByteBuffer)，再由背景執行緒非同步 commit 到 Page Cache，最後由刷盤執行緒 flush 到磁碟
- 這實現了「讀寫分離」：寫入時往堆外記憶體寫，讀取時從 Page Cache 讀，極大減輕了作業系統 Page Cache 的讀寫鎖衝突
- 非同步刷盤 (Async Flush) 配合 TransientStorePool 能達到極致寫入效能，但 Broker 異常斷電會遺失 Direct Memory 中未 commit 的資料

**考官可能追問：**
- Q: 何時選擇同步刷盤 (Sync Flush)？
  - A: 在金融交易、核心帳務等對可靠性要求極高、不允許遺失任何訊息的場景。此時訊息必須安全寫入磁碟 (fsync) 後才回應 Producer 成功，代價是吞吐量顯著下降。
- Q: CommitLog 大小為何固定為 1GB？
  - A: 因為 RocketMQ 使用 mmap 進行記憶體對映，而在 Java 中，MappedByteBuffer 的單個對映長度限制在 Integer.MAX_VALUE 內，為了便於管理與避免虛擬記憶體碎片化，設定為 1GB。

**常見陷阱 / 易錯點：**
- 在高併發寫入時未開啟 TransientStorePool，導致 OS Page Cache 頻繁發生髒頁回寫阻塞（Page Cache Busy），造成 Producer 傳送延遲尖峰
- 忽視單一 MessageQueue 的寫入熱點，所有 Producer 皆指定同一個 Key，導致整個 Topic 的吞吐量受限於單一佇列

---
### Q: RocketMQ 與 Kafka 適用選型對比？

**核心回答：**
選型核心在於業務屬性。RocketMQ 偏向於**業務整合與金融級可靠性**，提供原生事務訊息、定時/任意精度延遲訊息、Tag SQL92 過濾、消費失敗重試、消費順序掛起等貼近商務邏輯的特性；Kafka 偏向於**高吞吐量資料管道與大資料處理**，生態鏈（Flink/Spark/Connect）極其強大，儲存設計更簡單直覺。

**深入原理：**
- 儲存模型：Kafka 每個 Partition 一個檔案，適合少量 Topic；RocketMQ 所有 Topic 共用 CommitLog，適合海量 Topic（支援幾萬個）
- 通訊協定：Kafka 使用自訂的 TCP 協定；RocketMQ 5.x 採用 gRPC 協定，提供更好的跨語言支援與雲原生架構相容性
- 運維成本：Kafka 目前去 ZK 後運維已大幅簡化；RocketMQ 的 NameServer 極其穩定，運維成本同樣很低

**考官可能追問：**
- Q: 是否能用 Kafka 強行實現延遲訊息？
  - A: Kafka 無原生延遲訊息。若強行實作，需建立大量延遲 Topic，並在應用程式中寫定時輪詢，這會產生嚴重的磁碟隨機 I/O 且維護成本極高，不建議。
- Q: 兩者在 Broker 當機時的選主速度？
  - A: KRaft 模式下的 Kafka 選主可在秒級內完成；RocketMQ 5.x 藉由 Controller 進行自動主從切換，同樣能實現秒級切換（通常 < 5s）。

**常見陷阱 / 易錯點：**
- 將 RocketMQ 當作大資料日誌收集平臺，造成 Broker 端 ConsumeQueue 索引檔案建置速度跟不上寫入速度，導致記憶體崩潰
- 在 Kafka 中為每個使用者建立獨立的 Topic，當 Topic 數量突破數萬時，Broker 會因大量隨機 I/O 導致磁碟寫入卡死

---
### Q: 訊息重複與業務冪等性處理？

**核心回答：**
由於網路波動、ACK 遺失、Rebalance 觸發等原因，分散式 MQ 僅能保證「至少一次投遞 (At-Least-Once)」，訊息重複在所難免。解決重複消費的核心是**業務冪等性**。RocketMQ 會在客戶端生成唯一的 `MsgId`（在傳送時），並在 Broker 儲存時生成 `OffsetMsgId`。建議在業務層使用自訂的業務唯一 Key（如訂單 ID）結合資料庫唯一鍵或 Redis 去重表來實現冪等。

**深入原理：**
- MsgId：由 Producer 使用者端生成，代表該訊息的邏輯 ID，重試傳送時該 ID 保持不變
- OffsetMsgId：由 Broker 端生成，代表訊息在 CommitLog 中的實體偏移量，若傳送重試或路由到不同佇列，該 ID 會改變
- 冪等實現手法：DB 唯一鍵（Insert 衝突拒絕）、Redis SETNX（設定過期時間作為分散式鎖去重）、樂觀鎖/狀態機（更新時帶上 status 條件）

**考官可能追問：**
- Q: 能不能依賴 OffsetMsgId 來做消費去重？
  - A: 絕對不能。因為同一條訊息在重試投遞或負載平衡重新分配時，其實體偏移量可能會變，導致 OffsetMsgId 發生變化，從而失效。必須使用 MsgId 或訊息內容中的業務唯一 ID。
- Q: 去重表資料無限膨脹如何處理？
  - A: 建立帶有 TTL 的去重表，僅保留 7-14 天的資料（依據業務訊息的最大有效期而定），並定期進行物理刪除或歷史歸檔。

**常見陷阱 / 易錯點：**
- 僅在消費端使用簡單的「印日誌」而未做任何實質去重，導致高併發重試時發生重複扣款等重大資安事故
- 去重 Key 的粒度過粗，導致不同業務實體的訊息被誤判為重複訊息而丟棄

---
### Q: Broker 副本複製與高可用？

**核心回答：**
RocketMQ 支援 Master-Slave 架構。複製方式分為：**同步複製 (Sync Replication)**（Master 收到訊息後，需等待 Slave 複製成功才回應 Producer）與**非同步複製 (Async Replication)**（Master 寫入成功即回應，Slave 非同步同步）。5.x 引入 Controller 角色實現自動主從切換與 Epoch 複製，保證強一致性與高可用性。

**深入原理：**
- 當 Master 掛掉後，Consumer 可以自動切換到其對應的 Slave 進行唯讀消費，保證消費不中斷
- 5.x Controller 模式下，Controller 監控 Broker 存活狀態。當 Master 故障時，Controller 決定新的 Master，並發布 Epoch 變更，防止腦裂
- Epoch 機制：Broker 會記錄每個 Epoch 寫入的日誌起點，在主從切換時進行日誌對齊，防止髒資料被錯誤覆蓋

**考官可能追問：**
- Q: 非同步複製在 Master 當機時會丟資料嗎？
  - A: 會。若 Master 收到寫入但尚未同步給 Slave 時突然當機，此時若自動切換 Slave 為 Master，這部分未同步的訊息將會遺失。對資料一致性敏感的場景應強制開啟同步複製。
- Q: 如何防止腦裂 (Split-Brain)？
  - A: 在 5.x Controller 模式中，Controller 群組本身使用 Raft 協定，遵循多數決原則（Quorum）。只有獲得多數 Controller 認可的 Broker 才能成為 Master，從根本上避免了雙 Master 腦裂的可能。

**常見陷阱 / 易錯點：**
- 生產環境僅配置單個 Master 節點而無 Slave 副本，一旦該實體機磁碟損壞或系統崩潰，將導致服務完全中斷且資料面臨永久遺失風險
- Slave Broker 的記憶體與 CPU 配置遠低於 Master，當發生主備切換時，Slave 無法承受突發的消費與讀取負載，導致二次崩潰

---
### Q: RocketMQ 訊息堆積緊急處理方案？

**核心回答：**
當出現百萬級訊息堆積時，說明消費速度遠低於生產速度。緊急處理策略為：1) 擴充 Consumer 實例數量；2) 增加 Topic 的 MessageQueue 數量（需同時進行）；3) 若無法擴佇列，可部署臨時的「中轉消費服務」，快速將訊息拉取並寫入具有多倍分割槽的臨時 Topic，再由大量臨時消費者消費新 Topic；4) 暫時關閉非核心業務邏輯以提升下游處理速度。

**深入原理：**
- 只增加 Consumer 實例而不擴充 MessageQueue 數量是無效的，因為一個 Queue 只能被同一個 Group 內的一個 Consumer 實例消費
- 透過 RocketMQ Admin 工具或 Prometheus 監控 `consume TPS` 與 `produce TPS` 的差值，以及 `accumulated messages` 指標，設定水位線告警
- 排查堆積源頭：檢查資料庫是否有死鎖、外部 API 呼叫是否超時、Consumer 執行緒是否因丟擲異常未捕獲而陷入死迴圈

**考官可能追問：**
- Q: 如何做臨時中轉分發？
  - A: 編寫一個極簡 the Consumer，不進行任何資料庫寫入或業務計算，僅將 poll 到手的訊息傳送至臨時 Topic（如 temp_topic，分割槽數設為 30），隨後立即 Commit。接著部署 30 個臨時 Consumer 實例去消費 temp_topic，實現極速分流。
- Q: 歷史堆積訊息能否直接跳過？
  - A: 在非核心業務場景（如非金流通知），可使用 RocketMQ Admin 重置消費位點 (Reset Offset) 到最新位置，將積壓的訊息直接跳過，事後再透過日誌進行補償。

**常見陷阱 / 易錯點：**
- 在發生大量訊息堆積時，盲目重啟 Consumer 服務，這會觸發頻繁的 Rebalance，導致消費中斷更嚴重，雪上加霜
- 下游資料庫（如 MySQL）已經達到 I/O 瓶頸，此時盲目擴容 Consumer 只會把壓力轉移到 DB，導致資料庫崩潰

---
### Q: RocketMQ 在加密貨幣交易所 (Crypto Exchange) 場景的應用？

**核心回答：**
加密貨幣交易所要求高併發、極致可靠性與精確的狀態變更。RocketMQ 主要用於解耦非核心路徑：1) 撮合引擎 (Matching Engine) 透過記憶體與 gRPC 完成主路徑交易後，將交易事件 (Trade Events) 傳送至 RocketMQ；2) 下游的帳戶餘額更新、資產清算、使用者即時推播 (Websocket)、合規審計等模組非同步消費 MQ 訊息，避免影響撮合核心效能。

**深入原理：**
- 使用事務訊息 (Transaction Message) 確保使用者的「鏈上提現/充值操作」與「帳戶系統狀態變更」保持最終一致性
- 使用訊息軌跡 (MessageTrace) 記錄每一條訂單事件的傳送時間、儲存位置與消費狀態，滿足金融監管的審計與回溯要求
- 使用順序訊息保證特定交易對（如 BTC/USDT）的訂單建立與取消事件在同一個 Queue 中按順序處理，防止撮合狀態機失序

**考官可能追問：**
- Q: 撮合引擎主路徑是否可以直接使用 RocketMQ？
  - A: 不行。撮合核心要求微秒級的延遲，任何磁碟 I/O 或網路 MQ 傳輸都會成為瓶頸。撮合引擎應採用 LMAX Disruptor 在記憶體中進行，並以 RocketMQ 作為非同步持久化與下游分發的媒介。
- Q: 如何應對極端行情（如插針、大波動）時的流量暴增？
  - A: 利用 RocketMQ 的 CommitLog 順序磁碟寫入能力，充當緩衝墊，吸收暴增的交易與行情訊息；Websocket 推送模組可配置 Pop 模式或 BroadCasting 模式，快速廣播行情資料。

**常見陷阱 / 易錯點：**
- 將撮合引擎的同步確認邏輯與 RocketMQ 傳送繫結，一旦 MQ 發生瞬間網路抖動，會直接拖垮整個交易撮合主鏈
- 行情廣播訊息未設定過期時間或丟棄策略，導致使用者端接收到幾分鐘前的歷史行情，引發客訴

---

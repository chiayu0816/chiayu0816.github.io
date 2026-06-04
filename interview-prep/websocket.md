# WebSocket 面試 Q&A

> 來源：tech-vault、行情推送實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: WebSocket 交握與協定基礎？

**核心回答：**
使用者端傳送 HTTP Upgrade 請求，伺服器回傳 101 Switching Protocols 狀態碼。交握成功後轉為 TCP 全雙工通訊。通訊內容為影格化訊息 (Framed Messages：包含文字、二進位、Ping/Pong 心跳及 Close)。

**深入原理：**
- 交握校驗：伺服器將 `Sec-WebSocket-Key` 拼接 Magic UUID (`258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)，進行 SHA-1 雜湊並以 Base64 編碼，回傳於 `Sec-WebSocket-Accept` 供驗證
- 遮罩機制 (Masking)：使用者端傳送至伺服器的影格必須進行遮罩防護，以防快取汙染與毒化 (Cache Poisoning) 攻擊
- 影格欄位：包含 FIN 標記 (訊息結束)、Opcode (決定資料格式)、Payload Length

**考官可能追問：**
- Q: vs HTTP Long Polling？
  - A: WebSocket 連線建立後影格標頭僅有數位元組開銷，遠低於每次 HTTP 請求的 Header 開銷
- Q: 加密傳輸？
  - A: 生產環境必須使用 WSS (WebSocket Secure)，對應 TLS 加密

**常見陷阱 / 易錯點：**
- 反向代理 (如 Nginx) 未正確設定 Upgrade 與 Connection 標頭
- 未配置 Heartbeat 心跳機制，導致被中間防火牆或負載平衡器因 Idle 超時強制中斷而不知情

---
### Q: WebSocket 與 SSE 對比？

**核心回答：**
SSE 單向 server→client、HTTP/2 友好、自動重連。WS 雙向、二進位制、更低 overhead。行情推送若僅 server push 可考慮 SSE。

**深入原理：**
- SSE text/event-stream
- WS subprotocol
- HTTP/2 SSE multiplex

**考官可能追問：**
- Q: 防火牆？
  - A: SSE 像 HTTP
- Q: binary tick？
  - A: WS

**常見陷阱 / 易錯點：**
- SSE 無 binary
- WS 需自定義心跳

---
### Q: 心跳與斷線重連策略？

**核心回答：**
Ping/pong 或 app-level heartbeat；超時 close 重連 exponential backoff；重連帶 last_seq 補訊息。

**深入原理：**
- idle timeout NAT 60s
- reconnect storm 限流
- session resume token

**考官可能追問：**
- Q: 丟訊息？
  - A: seq+gap fill REST
- Q: 多端登入？
  - A: kick old session

**常見陷阱 / 易錯點：**
- 無 backoff 打爆 server
- 重連無 auth refresh

---
### Q: WebSocket 水平擴展與 Sticky Session？

**核心回答：**
WebSocket 是有狀態連線 (Stateful)。負載平衡器的 Sticky Session (如 IP Hash 或 Sticky Cookie) **僅用於升級交握階段 (Upgrade Handshake)** 確保同一握手打在同一個執行個體上。一旦連線建立，跨實例的訊息傳送與廣播必須依賴分散式訂閱機制 (如 Redis Pub/Sub) 進行路由轉發。

**深入原理：**
- 訊息廣播路由：伺服器 A 欲傳送訊息給在伺服器 B 上的使用者 U，將訊息傳送到 Redis Pub/Sub channel，各節點監聽並自行推送給自身連線的 Client
- K8s 擴展：使用 Headless Service 繞過 L4 負載平衡器直接建立連線，或由 API 閘道進行串流分發
- Connection Registry：建立外部儲存 (如 Redis) 記錄各使用者的連線節點 (User-to-Node mapping) 以實現精準單播

**考官可能追問：**
- Q: K8s 縮容與排水 (Drain)？
  - A: 優雅關閉服務前，逐步斷開 WebSocket 連線 (Graceful Drain)，使用隨機延遲退避重新連線，防範重連風暴
- Q: 跨節點通訊？
  - A: 採用 Redis Pub/Sub 或 RabbitMQ 進行節點間的訊息分發

**常見陷阱 / 易錯點：**
- 擴展後無 Pub/Sub 機制導致「訊息孤島」 (訊息傳送失敗)
- 負載平衡器未配置 Sticky Session 導致頻繁連線失敗

---
### Q: 背壓與流量控制？

**核心回答：**
使用者端消費變慢 $ightarrow$ TCP 接收快取滿 $ightarrow$ 反向觸發伺服器 TCP 傳送快取滿 $ightarrow$ 伺服器 `Write()` 呼叫阻斷。伺服端應針對每個連線使用「有界佇列 (Bounded Queue)」，當佇列滿時採取捨棄非關鍵舊資料或直接斷開慢速連線的策略，避免記憶體耗盡 (OOM)。

**深入原理：**
- TCP 流量控制 (Flow Control) 如何向上阻斷執行緒/協程
- 合流 (Coalescing) 機制：針對高頻 Tick 推送，在傳送前將多個更新合併成一個影格
- 優先權佇列：優先保障心跳 (Ping/Pong) 與交易成交訊息的傳送

**考官可能追問：**
- Q: 如何隔離慢使用者？
  - A: 非同步 Write Loop 連線通道設定 WriteDeadline，寫入超時即強制關閉連線
- Q: 突發流量控制？
  - A: 應用層實作令牌桶演演算法對單一連線的訂閱頻率做限流保護

**常見陷阱 / 易錯點：**
- 使用無界緩衝區 (Unbounded Queue) 快取訊息，導致慢連線引發伺服器記憶體溢位 (OOM)
- 廣播訊息時阻塞在慢連線上，進而拖垮所有正常使用者

---
### Q: WebSocket 安全：認證與授權？

**核心回答：**
生產環境必須強製作為 WSS 連線。瀏覽器端原生 JavaScript API 於交握升級階段**不支援自訂 HTTP Headers**，因此 JWT 通常透過 Cookie、Query Parameters（但存在日誌洩漏風險）或 `Sec-WebSocket-Protocol` 子協定標頭傳遞。交握完成後需進行 Topic 訂閱許可權 ACL 檢驗，並透過檢查 `Origin` 標頭防範跨網站 WebSocket 綁架 (CSWSH)。

**深入原理：**
- 連線中途 Token 過期處理 (動態重連或主動中斷)
- 細粒度主題訂閱控制 (Per-Topic ACL)
- 認證連續失敗時的 IP 限流機制 (WAF)

**考官可能追問：**
- Q: Token 放 URL 引數的風險？
  - A: 容易出現在伺服器存取日誌、CDN 快取及瀏覽器歷史記錄中，一般應優先選擇 Cookie 或 Subprotocol 傳遞
- Q: 防範連線洪水 DDoS 攻擊？
  - A: 在 API 閘道層限制單一 IP 併發連線數，並搭配 WAF 防禦

**常見陷阱 / 易錯點：**
- 使用明文未加密的 ws 連線導致封包被竊聽
- 交握成功建立長連線後不再做任何訂閱許可權審查

---
### Q: 訊息格式：JSON vs Protobuf？

**核心回答：**
JSON 易於除錯與開發；Protobuf/二進位格式節省頻寬且解析速度極快。可採 JSON envelope 包裝 Protobuf 資料或加上壓縮。欄位升級需保證版本相容性。

**深入原理：**
- Schema Registry 統一規範
- Msgpack 作為中間平衡點
- 固定標頭長度 (Header Length) 的二進位協議設計

**考官可能追問：**
- Q: 訂單簿 (Order Book) 增量推送？
  - A: 推薦二進位二進階結構 (如 Protobuf 或 FlatBuffers)
- Q: 除錯支援？
  - A: 透過 Feature Flag 開啟 JSON 除錯模式

**常見陷阱 / 易錯點：**
- 無 Schema 演進與向後相容計劃
- 大 JSON 解析導致嚴重的 CPU 效能瓶頸

---
### Q: Go 實作 WebSocket 注意點？

**核心回答：**
使用 `gorilla/websocket` 或 `nhooyr` 套件時：需呼叫 `SetReadDeadline` 防範殭屍連線、自訂 `PingHandler`；**`Conn` 連線物件的併發寫入不是執行緒安全的，併發寫入必須加互斥鎖 (Mutex) 或使用寫入通道 (Write Channel)**；Context 取消時優雅關閉連線。

**深入原理：**
- 一個 Reader、一個 Writer 限制與底層 buffer 複用
- 利用 `sync.Pool` 建立 Buffer Pool 以降低 GC 壓力
- 透過 pprof 檢查排查 Goroutine 洩漏

**考官可能追問：**
- Q: 併發呼叫 WriteJSON？
  - A: 必須加鎖 (Lock) 保護，或改採單一寫入協程 (Write Loop) 從 Channel 消費傳送
- Q: 優雅關閉 (Graceful Shutdown)？
  - A: 向使用者端傳送 Close 控制影格 (status code 1000)，並等待其回應後關閉連線

**常見陷阱 / 易錯點：**
- 多協程併發寫入同一連線導致 write panic 或影格損壞
- Handler 阻塞在 business logic 中，進而卡死整個 Read Loop 讀取

**實務場景：**
交易/行情繫統場景以 WebSocket 推送即時盤口與行情資料 (Market Data)

---
### Q: Order Book / 行情推送架構？

**核心回答：**
撮合引擎 $ightarrow$ MQ $ightarrow$ WS Gateway；採取 Snapshot (全量快照) + Delta (增量更新) 機制；每個增量更新帶有遞增的 sequence ID (`seq_id`)，使用者端先拉取快照，再套用大於該快照 `seq_id` 的增量資料。

**深入原理：**
- 100ms 合流 (Coalesce) 合併推送以減少 Client 負擔
- 訂閱深度限制 (Depth Limit，如只看 top 20/50 檔)
- 訂閱對應對映關係與動態分流機制

**考官可能追問：**
- Q: 增量更新發生亂序或遺失？
  - A: 使用者端檢驗 `seq_id` 是否為連續的 `n+1`，若發現 sequence 遺失 (Gap)，必須丟棄當前狀態並向 REST API 重新載入 Snapshot 進行重步
- Q: 百萬級連線推送？
  - A: 分散式部署邊緣推送節點 (WS Edge Nodes)，依交易對 (Symbol) 進行 Sharding 分流訂閱

**常見陷阱 / 易錯點：**
- 沒有 Snapshot 機制而僅推送增量，導致新進入使用者無法建立盤口狀態
- 未設計 `seq_id` 連續性驗證，致使資料在網路傳輸遺失時客戶端展示錯誤行情
-  sequence ID 數值溢位處理不當

---
### Q: WebSocket 壓測與監控？

**核心回答：**
指標：連線數、msg/s、latency、p99 disconnect rate。工具：k6、websocket bench。trace 連線生命週期。

**深入原理：**
- prometheus gauge conns
- alert fd limit
- memory per conn

**考官可能追問：**
- Q: 單機連線上限？
  - A: OS fd+memory
- Q: GC 壓力？
  - A: reuse buffer

**常見陷阱 / 易錯點：**
- 無連線數告警
- 壓測未含 TLS

---
### Q: 與 gRPC streaming 的分工？

**核心回答：**
內部服務 gRPC；對外客戶端 WS/REST。gateway 轉換。實務上 gRPC 走內部 trading flow，WS 推 ticker/K線。

**深入原理：**
- 統一 event schema
- MQ decouple
- CQRS read side WS

**考官可能追問：**
- Q: mobile 用 gRPC？
  - A: 可以
- Q: web 用 gRPC-web？
  - A: 可行

**常見陷阱 / 易錯點：**
- 內部 WS 無必要

---
### Q: 常見 WebSocket 面試陷阱題？

**核心回答：**
TCP 之上非 HTTP；需處理 partial frame；proxy timeout；瀏覽器同源；message 不保證與 TCP 包邊界一致但 frame 完整。

**深入原理：**
- close code 1000 normal
- 1006 abnormal
- max message size

**考官可能追問：**
- Q: WS 可靠？
  - A: 無 app ack 仍可能 app 層丟
- Q: firewall 443？
  - A: WSS 走 443

**常見陷阱 / 易錯點：**
- 以為 WS 自帶 message ordering 跨 reconnect

---

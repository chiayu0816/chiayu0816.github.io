# gRPC 面試 Q&A

> 來源：tech-vault、交易所/體育資料實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景

---

### Q: gRPC 與 REST 核心差異？

**核心回答：**
gRPC 基於 HTTP/2、Protobuf 二進位制、強型別 schema（.proto）、支援 streaming（ unary/server/client/bidi）。REST JSON 人類可讀、瀏覽器友好。內部微服務 gRPC 低延遲小 payload。

**深入原理：**
- HTTP/2 多路複用
- Protobuf 欄位 tag 編碼
- code generation stub

**考官可能追問：**
- Q: 何時 REST？
  - A: 公開 API/Browser
- Q: 版本相容？
  - A: proto field number 不可改

**常見陷阱 / 易錯點：**
- breaking proto change
- 無 deadline 呼叫掛死

**實務場景：**
交易/行情繫統 market/trading flow 以 gRPC 整合

---
### Q: Protobuf 編碼與版本相容？

**核心回答：**
Field number 標識欄位，wire type 決定編碼。新增 optional/repeated 向後相容；不可刪改 number、不可改型別。unknown field 跳過。

**深入原理：**
- varint zigzag
- packed repeated
- oneof/map

**考官可能追問：**
- Q: JSON 互轉？
  - A: google.protobuf.Struct/jsonpb
- Q: enum 相容？
  - A: 保留 deprecated value

**常見陷阱 / 易錯點：**
- 改 field type
- reuse field number

---
### Q: gRPC 四種呼叫模式？

**核心回答：**
Unary 一問一答；Server streaming 一發多收；Client streaming 多發一收；Bidirectional streaming 雙工。Streaming 適合大檔案、實時推送。

**深入原理：**
- flow control HTTP/2 window
- grpc.MaxRecvMsgSize
- context cancel 終止 stream

**考官可能追問：**
- Q: streaming 錯誤？
  - A: trailers status
- Q: backpressure？
  - A: Recv 速度控制

**常見陷阱 / 易錯點：**
- streaming 無 timeout
- 單 message 過大

---
### Q: gRPC 負載平衡與服務發現？

**核心回答：**
gRPC 跑在 HTTP/2 的**單一長連線多路複用**上，傳統 L4（連線級）負載平衡只會把整條 TCP 連線導到單一後端實例，所有 RPC 都壓在同一個實例上導致流量傾斜。解決方案有二：1. **Client-side LB**：Resolver 解析位址清單（如 K8s headless service），由使用者端 Balancer 在 RPC 層分流；2. **L7 Proxy LB**：使用支援 gRPC/HTTP2 的閘道（如 Envoy、AWS ALB）在串流 (Stream) 級別分流。

**深入原理：**
- 為何 L4 LB 失效：HTTP/2 一條 TCP 連線承載多個 Stream，L4 無法解析 Stream 訊框，會將所有請求綁死在同一後端
- client-side LB：利用 Name Resolver (DNS/xDS) 回傳後端 IP 清單，使用者端負載平衡器在 RPC 層級做輪詢 (Round Robin) 或一致性雜湊 (Consistent Hashing)
- K8s Headless Service：讓 DNS 直接回傳 Pod 的實體 IP 清單（繞過單一 ClusterIP）；大規模採用 xDS (Envoy sidecar 或 proxyless)
- 連線維護：透過 keepalive ping 檢測死連線，Health Checking Protocol 讓 balancer 自動避開未就緒或故障的 Pod

**考官可能追問：**
- Q: K8s 實務？
  - A: Headless Service + DNS 輪詢，或匯入 Istio 進行 L7 邊車代理負載平衡
- Q: 特定路由黏性 (Sticky)？
  - A: 藉由 xDS 設定 Consistent Hash Balancer

**常見陷阱 / 易錯點：**
- 誤用 L4 負載平衡器導致流量全部卡在單一 Pod
- 未啟用 Health Check 導致連向已死 Pod
- DNS Resolver 快取時間過長，無法感知頻繁擴縮容的 Pod 變化

---
### Q: gRPC 攔截器（Interceptor）用途？

**核心回答：**
Unary/Stream interceptor 鏈：auth、logging、metrics、retry、tracing。類似 HTTP middleware。

**深入原理：**
- metadata 傳 token
- opentelemetry grpc stats
- recovery panic

**考官可能追問：**
- Q: JWT 驗證？
  - A: UnaryServerInterceptor
- Q: client retry？
  - A: grpc-go retry policy

**常見陷阱 / 易錯點：**
- interceptor order 錯
- metadata明文敏感

---
### Q: gRPC metadata 與 status codes？

**核心回答：**
Metadata 類似 HTTP headers（:authority、authorization）；Status codes 標準 gRPC codes（NotFound、DeadlineExceeded）。details proto 擴展錯誤資訊。

**深入原理：**
- trailers-only response
- grpc-status grpc-message headers
- rich error model

**考官可能追問：**
- Q: DeadlineExceeded？
  - A: 客戶端 deadline 到
- Q: 重試 idempotent？
  - A: 只 retry 安全碼

**常見陷阱 / 易錯點：**
- 把業務錯誤全用 Unknown
- metadata size 限制

---
### Q: gRPC 與 HTTP/2 關係？

**核心回答：**
gRPC 完全依賴 HTTP/2：二進位分框 (Binary Framing)、單一 TCP 連線上的多路復用 (Stream Multiplexing)、HPACK 標頭壓縮、流量控制 (Flow Control)。在 TLS 上透過 ALPN 協商 `h2`。

**深入原理：**
- Length-Prefixed Message：gRPC 寫入 HTTP/2 DATA 訊框前會加上 5 位元組標頭 (1 位元組壓縮標記 + 4 位元組訊息長度)
- Trailers 機制：gRPC 的狀態碼 (grpc-status) 與錯誤訊息 (grpc-message) 放在回應結尾的 Trailers (特殊的 HEADERS 訊框) 中傳遞
- 連線管理：使用 GOAWAY 訊框進行優雅關閉 (Graceful Shutdown) 與連線耗損管理

**考官可能追問：**
- Q: HTTP/1.1？
  - A: gRPC 原生不支援，需透過代理轉譯
- Q: 瀏覽器端支援？
  - A: 瀏覽器無法直接控制 HTTP/2 訊框，必須透過 grpc-web 代理伺服器轉譯

**常見陷阱 / 易錯點：**
- 中間負載平衡器 (如 Nginx) 未開啟 HTTP/2 支援
- Proxy 啟用緩衝 (Buffer) 破壞了即時串流 (Streaming)

---
### Q: gRPC 逾時、取消與 Deadline 傳播？

**核心回答：**
使用絕對時間點 (Deadline) 代替相對時間 (Timeout)。`context.WithDeadline` 設定截止時間；子呼叫 (Sub-calls) 自動繼承並傳播剩餘時間；Cancel 會沿呼叫鏈非同步傳播終止下游執行。伺服端應定期檢查 `ctx.Done()` 以提前釋放資源。

**深入原理：**
- `grpc-timeout` HTTP/2 標頭傳遞
- 鏈路總 Deadline 分配與時鐘偏移風險
- 優雅關閉與資源釋放

**考官可能追問：**
- Q: 無 Deadline 危害？
  - A: 下游服務因等待已放棄之請求而形成「殭屍請求」，引發雪崩效應 (Cascading Hang)
- Q: Go 使用者端？
  - A: Context 必傳，否則無法傳播取消與截止時間

**常見陷阱 / 易錯點：**
- 每層呼叫重新設定滿格 Timeout 而非繼承剩餘時間
- 資料庫查詢或外部呼叫忽略 Context 狀態

---
### Q: gRPC 安全：TLS/mTLS？

**核心回答：**
Server TLS credentials；mTLS 雙向證書；JWT 在 metadata。生產禁 insecure channel。

**深入原理：**
- credentials.NewClientTLSFromCert
- SPIFFE identity
- rotation

**考官可能追問：**
- Q: 內網 plaintext？
  - A: service mesh mTLS
- Q: PII？
  - A: encrypt+authz

**常見陷阱 / 易錯點：**
- skip verify 生產
-  cert 過期無告警

---
### Q: gRPC 效能最佳化？

**核心回答：**
連線複用、控制併發串流數；針對高吞吐場景需建立 `ClientConn` 連線池以繞過單條 TCP 連線 Max Concurrent Streams 限制 (通常為 100)；避免極大 Protobuf 訊息；利用 Streaming 減少 RTT；配置合理 keepalive；開啟 CPU 壓縮權衡。

**深入原理：**
- 與 REST/JSON 做吞吐量與延遲基準測試
- 複用 ClientConn 的執行緒安全特性
- Gzip/Snappy 壓縮演演算法對 CPU 與頻寬的影響

**考官可能追問：**
- Q: pprof gRPC 瓶頸？
  - A: 主要消耗於序列化 (marshal/unmarshal) 與快取複製，可改用 pool 複用 struct 物件
- Q: 過大 proto 檔案？
  - A: 拆分成多個細粒度 message 或改採 chunked streaming 傳輸

**常見陷阱 / 易錯點：**
- 每次 RPC 請求都新建連線導致效能極度劣化
- 未限制最大併發串流數導致連線佇列排隊阻塞

---
### Q: gRPC vs WebSocket 選型？

**核心回答：**
gRPC streaming 服務間 RPC；WebSocket 瀏覽器/客戶端長連線推送。交易所：gRPC 內部；WS 推行情給前端。

**深入原理：**
- WS 雙向但無 schema 強型別
- grpc-gateway 轉 REST
- 兩者可並存

**考官可能追問：**
- Q: 實時 tick？
  - A: WS 更低客戶端延遲感知
- Q: mobile？
  - A: 都支援

**常見陷阱 / 易錯點：**
- WS 承載複雜 RPC 無 contract

---
### Q: grpc-gateway 與 protobuf API 設計？

**核心回答：**
google.api.http annotation 生成 REST 反向代理。API 設計：resource 命名、pagination、error model 統一。

**深入原理：**
- OpenAPI 生成
- enum string mapping
- field behavior optional required

**考官可能追問：**
- Q: public API？
  - A: gateway+REST
- Q: breaking change 流程？
  - A: buf breaking check

**常見陷阱 / 易錯點：**
- proto 即 public contract 無 review

---

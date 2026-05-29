# gRPC 面試 Q&A

> 來源：tech-vault、交易所/體育資料實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

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

**結合履歷：**
交易所 market/trading flow 以 gRPC 整合。

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
Unary 一問一答；Server streaming 一發多收；Client streaming 多發一收；Bidirectional streaming 雙工。Streaming 適合大檔案、即時推送。

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
### Q: gRPC 負載均衡與服務發現？

**核心回答：**
gRPC 跑在 HTTP/2 的**單一長連線多路複用**上，傳統 L4（連線級）負載均衡只會把整條連線導到一個 backend，所有 RPC 都壓在同一 pod → 無法均衡。因此 gRPC 多用 **client-side LB**：resolver 解析出一組位址（K8s headless service + DNS，或 xDS/Envoy 控制面），balancer（pick_first / round_robin）在 RPC 層級分流，再搭配 gRPC Health Checking Protocol 與 keepalive 剔除壞連線。

**深入原理：**
- 為何 L4 LB 失效：HTTP/2 一條 TCP 連線承載多路 stream，L4 無法在 stream 層分流，會把流量釘在單一後端
- client-side LB：name resolver（DNS/xDS）回傳位址清單，balancer 在 RPC 層輪詢，pod 增減由 resolver 更新
- K8s 用 headless service 讓 DNS 直接回傳 pod IP 清單（而非單一 ClusterIP）；大規模用 xDS/Envoy（sidecar 或 proxyless）
- keepalive ping 檢測 dead connection；Health Protocol 讓 balancer 避開未就緒 pod

**考官可能追問：**
- Q: K8s 用？
  - A: headless service+DNS 或 service mesh istio/xDS
- Q: sticky？
  - A: consistent hash filter（xDS）

**常見陷阱 / 易錯點：**
- 誤用 L4 LB 導致流量壓單 pod
- 無 health check 連 dead pod
- DNS resolver 不感知頻繁擴縮容

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
- metadata 明文敏感

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
gRPC 完全依賴 HTTP/2：二進位制 framing、stream multiplex、HPACK 壓縮 header、flow control。TLS 上 ALPN h2。

**深入原理：**
- single TCP 多 RPC
- HEADERS+DATA frames
- GOAWAY 優雅關閉

**考官可能追問：**
- Q: HTTP/1.1？
  - A: gRPC 不支援
- Q: 瀏覽器？
  - A: grpc-web 代理

**常見陷阱 / 易錯點：**
- 中間 nginx 未開 http2
- proxy buffer 破壞 stream

---
### Q: gRPC 超時、取消與 deadline 傳播？

**核心回答：**
context.WithTimeout 設 deadline；子 call 繼承；cancel 傳播終止下游。Server 應檢查 ctx.Done()。

**深入原理：**
- grpc-timeout header
- 鏈路總 deadline 分配
- graceful shutdown

**考官可能追問：**
- Q: 無 deadline 危害？
  - A: cascade hang
- Q: Go client？
  - A: context 必傳

**常見陷阱 / 易錯點：**
- 每層重新設滿 timeout
- DB 查詢 ignore ctx

**結合履歷：**
實務上將 client disconnect 經 context 傳到下游。

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
連線複用、適當 concurrency、Protobuf 避免 huge message、streaming 減 RTT、keepalive、池化 channel。

**深入原理：**
- benchmark 對比 REST JSON
- reuse ClientConn
- compression gzip 權衡 CPU

**考官可能追問：**
- Q: pprof gRPC？
  - A: 看 marshal/unmarshal
- Q: 過大 proto？
  - A: 拆分 message

**常見陷阱 / 易錯點：**
- 每 RPC 新建 conn
- 無 limit 併發壓垮

---
### Q: gRPC vs WebSocket 選型？

**核心回答：**
gRPC streaming 服務間 RPC；WebSocket 瀏覽器/客戶端長連線推送。交易所：gRPC 內部；WS 推行情給前端。

**深入原理：**
- WS 雙向但無 schema 強型別
- grpc-gateway 轉 REST
- 兩者可並存

**考官可能追問：**
- Q: 即時 tick？
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

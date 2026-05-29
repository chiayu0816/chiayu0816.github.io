# WebSocket 面試 Q&A

> 來源：tech-vault、Roy 行情推送實務
> 題數：12 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: WebSocket 握手與協議基礎？

**核心回答：**
HTTP Upgrade 101 Switching Protocols，Sec-WebSocket-Key/Accept。建立後全雙工 framed messages（text/binary/ping/pong/close）。

**深入原理：**
- mask client→server
- frame opcode FIN
- extensions permessage-deflate

**考官可能追問：**
- Q:  vs HTTP long polling？
  - A: WS 低開銷即時
- Q: HTTPS？
  - A: WSS TLS

**常見陷阱 / 易錯點：**
- proxy 未配置 upgrade
- 無 heartbeat 斷線不知

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
有狀態連線需同一 server 或 shared pub/sub（Redis）廣播。LB 常用 ip hash 或 sticky cookie。

**深入原理：**
- Redis pub/sub fan-out
- Kafka→WS gateway 叢集
- connection registry

**考官可能追問：**
- Q: K8s 擴縮容？
  - A: graceful drain+reconnect
- Q: 跨節點訊息？
  - A: pub/sub bridge

**常見陷阱 / 易錯點：**
- scale 無 pub/sub 訊息孤島
- LB 無 sticky 頻繁斷

---
### Q: 背壓與流量控制？

**核心回答：**
讀 buffer 滿 slow consumer：drop、disconnect、或 apply backpressure（Go channel block）。限連線數、rate limit 訂閱。

**深入原理：**
- per-connection queue max
- coalesce tick updates
- priority channel

**考官可能追問：**
- Q: 慢客戶端？
  - A: isolate+kill
- Q: burst？
  - A: token bucket

**常見陷阱 / 易錯點：**
- 無界 buffer OOM
- 廣播不考慮 slow client

---
### Q: WebSocket 安全：認證與授權？

**核心回答：**
握手階段 JWT query/cookie/header；WSS 必須；訂閱 topic 授權；防 CSWSH 校驗 Origin。

**深入原理：**
- token 過期 mid-connection close
- per-topic ACL
- rate limit auth fail

**考官可能追問：**
- Q: token in URL？
  - A: 日誌洩漏風險
- Q: DDoS？
  - A: 連線限+WAF

**常見陷阱 / 易錯點：**
- 明文 ws
- 握手後無鑑權

---
### Q: 訊息格式：JSON vs Protobuf？

**核心回答：**
JSON 易除錯；Protobuf/binary 省頻寬解析快。可 JSON envelope+compression。版本 field 相容。

**深入原理：**
- schema registry
- msgpack middle ground
- 固定 header length

**考官可能追問：**
- Q: order book delta？
  - A: binary 結構
- Q: debug？
  - A: feature flag json

**常見陷阱 / 易錯點：**
- 無 schema 演進計劃
- 大 JSON parse CPU

---
### Q: Go 實現 WebSocket 注意點？

**核心回答：**
gorilla/websocket 或 nhooyr：SetReadDeadline、PingHandler、併發寫需 Mutex。context 取消關閉 conn。

**深入原理：**
- one reader one writer
- buffer pool
- pprof goroutine leak

**考官可能追問：**
- Q: 併發 WriteJSON？
  - A: 需 lock
- Q: graceful shutdown？
  - A: broadcast close

**常見陷阱 / 易錯點：**
- 併發 write panic
- handler 阻塞 read loop

**結合履歷：**
Roy 交易所 WebSocket 推 market data。

---
### Q: Order book / 行情推送架構？

**核心回答：**
Matching engine→MQ→WS gateway；snapshot+delta；seq id；client 先 snapshot 再 apply delta。

**深入原理：**
- 100ms coalesce
- depth limit
- symbol subscription map

**考官可能追問：**
- Q: 亂序 delta？
  - A: drop+resync snapshot
- Q: 百萬連線？
  - A: edge+shard

**常見陷阱 / 易錯點：**
- 無 snapshot 僅 delta
- seq 溢位

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
內部服務 gRPC；對外客戶端 WS/REST。gateway 轉換。Roy：gRPC 內部 trading flow，WS 推 ticker/K線。

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

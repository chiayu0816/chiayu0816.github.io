---
title: "WebSocket"
categories: ["Go", "WebSocket"]
---

### **什麼是 WebSocket？**  
WebSocket 是一種 **全雙工 (full-duplex)** 的通信協議，它允許 **客戶端 (Client) 與伺服器 (Server) 之間建立長連線**，並在連線期間雙向傳輸數據，而不需要像 HTTP 那樣每次請求都要重新建立連線。  

---

## **WebSocket 的運作原理**
WebSocket 的運作主要分為 **三個階段：握手 (Handshake)、數據傳輸、關閉連線 (Close Connection)**。

### **1. 握手階段 (Handshake)**
WebSocket 連線的建立是基於 **HTTP 協議**，透過 **HTTP Upgrade 機制** 來從普通的 HTTP 轉換為 WebSocket 連線。

**流程：**  
1. **客戶端 (Client) 發送 WebSocket 握手請求**
   - 這是標準的 HTTP/1.1 請求，包含 `Upgrade` 和 `Connection` 頭部，要求升級至 WebSocket 連線：
   ```http
   GET /chat HTTP/1.1
   Host: example.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   ```

2. **伺服器 (Server) 回應並確認升級**
   - 伺服器會檢查請求，若支援 WebSocket，則回應 `101 Switching Protocols`，表明將連線升級為 WebSocket：
   ```http
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
   ```

3. **連線建立成功**
   - 完成上述步驟後，客戶端與伺服器之間的 WebSocket 連線就建立成功，可以開始雙向通訊。

---

### **2. 數據傳輸階段**
建立 WebSocket 連線後，客戶端與伺服器可以透過 **「訊框 (Frame)」** 方式進行數據傳輸，WebSocket 使用 **幀 (frame) 協議**，數據會被封裝成 **二進制幀** 傳輸。  

WebSocket 支援以下幾種類型的幀：
- **Text Frame**：用於傳輸文字數據（UTF-8 編碼）。
- **Binary Frame**：用於傳輸二進制數據（如圖片、影片）。
- **Ping/Pong Frame**：心跳機制，確保連線是否存活。
- **Close Frame**：關閉連線。

**特點：**
- 客戶端與伺服器可以 **主動** 發送數據，而不需要額外的請求。
- 相較於 HTTP，WebSocket **減少了開銷**，因為不需要每次發送數據都重新建立連線 (HTTP 需要重複 TCP 連線與 HTTP 標頭)。
- 適用於 **即時應用 (Real-time Applications)**，如聊天室、即時遊戲、股票交易、即時通知等。

---

### **3. 關閉連線 (Close Connection)**
當 WebSocket 連線不再需要時，任一方 (Client 或 Server) 都可以發送 **Close Frame** 來關閉連線：

1. **客戶端發送 Close Frame**
2. **伺服器回應 Close Frame**
3. **TCP 連線關閉**

```http
< 客戶端發送: Close Frame
> 伺服器回應: Close Frame
```

---

## **WebSocket 與 HTTP 的差異**
|  | **HTTP** | **WebSocket** |
|---|---|---|
| **連線方式** | 每次請求都要建立新的 TCP 連線 | 只需建立一次 TCP 連線，保持長連線 |
| **通訊方向** | 單向 (Client → Server) | 雙向 (Client ⇄ Server) |
| **請求方式** | Request/Response | Event-driven (事件驅動) |
| **協議開銷** | 每次請求都要帶 HTTP 標頭 | 只在握手時帶 HTTP 標頭，之後使用輕量 Frame |
| **適用場景** | 一般的網頁瀏覽 (靜態/動態請求) | 即時應用，如聊天室、遊戲、股票交易 |

---

## **WebSocket 應用場景**
WebSocket 非常適合 **需要即時通訊** 的應用，例如：
1. **即時聊天 (Chat Applications)**
2. **即時股票報價 (Live Stock Ticker)**
3. **多人線上遊戲 (Multiplayer Online Games)**
4. **即時通知 (Real-time Notifications)**
5. **物聯網 (IoT) 裝置即時數據傳輸**
6. **直播彈幕 (Live Streaming Comments)**

---

## **WebSocket 範例 (Go 實作)**
使用 Go 搭建一個簡單的 WebSocket 伺服器：

這邊使用 github.com/lxzan/gws 當範例

常用的 WebSocket 套件還有
github.com/gorilla/websocket


### **安裝 WebSocket 套件**
```sh
go get github.com/lxzan/gws
```

### **Go WebSocket 伺服器**
```go
package main

import (
	"net/http"
	"time"

	"github.com/lxzan/gws"
)

const (
	PingInterval = 5 * time.Second
	PingWait     = 10 * time.Second
)

func main() {
	upgrader := gws.NewUpgrader(&Handler{}, &gws.ServerOption{
		ParallelEnabled:  true,
		Recovery:          gws.Recovery,
		PermessageDeflate: gws.PermessageDeflate{Enabled: true},
	})
	http.HandleFunc("/ws", func(writer http.ResponseWriter, request *http.Request) {
		socket, err := upgrader.Upgrade(writer, request)
		if err != nil {
			return
		}
		go func() {
			socket.ReadLoop() // Blocking prevents the context from being GC.
		}()
	})
	http.ListenAndServe(":6666", nil)
}

type Handler struct{}

func (c *Handler) OnOpen(socket *gws.Conn) {
	_ = socket.SetDeadline(time.Now().Add(PingInterval + PingWait))
}

func (c *Handler) OnClose(socket *gws.Conn, err error) {}

func (c *Handler) OnPing(socket *gws.Conn, payload []byte) {
	_ = socket.SetDeadline(time.Now().Add(PingInterval + PingWait))
	_ = socket.WritePong(nil)
}

func (c *Handler) OnPong(socket *gws.Conn, payload []byte) {}

func (c *Handler) OnMessage(socket *gws.Conn, message *gws.Message) {
	defer message.Close()
	socket.WriteMessage(message.Opcode, message.Bytes())
}
```

### **啟動伺服器**
```sh
go run main.go
```

### **JavaScript 客戶端**
```javascript
const socket = new WebSocket("ws://localhost:6666/ws");

socket.onopen = function() {
    console.log("WebSocket 連線已建立");
    socket.send("Hello Server!");
};

socket.onmessage = function(event) {
    console.log("收到伺服器訊息:", event.data);
};

socket.onclose = function() {
    console.log("WebSocket 連線已關閉");
};
```

### **Terminal websocat 客戶端**
```bash
# macOS
brew install websocat

# Linux
cargo install websocat
```

### Basic Connection Test
```bash
# Connect to WebSocket server
websocat ws://localhost:6666/ws

# Connect to WebSocket and auto ping 
websocat ws://localhost:6666/ws --ping-interval 5 -v
```
---
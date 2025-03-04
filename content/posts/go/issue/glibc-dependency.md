---
title: "解決 Go 編譯問題：/libc.so.6: version GLIBC_2.32 not found"
categories: ["Go"]
tags: ["Go", "GLIBC", "CGO"]
date: 2025-03-04
description: "解決 Go 程式在不同 Linux 環境間的 GLIBC 版本相容性問題，深入探討 CGO、動態連結與靜態連結的差異"
---

## 問題背景

最近在公司開發環境佈署代碼時出現 **`/libc.so.6: version GLIBC_2.32 not found`** 問題。因為環境比較特別，其實就是 CI/CD 做得很差，導致佈署代碼都需要自行將檔案編譯後放上測試環境。

我的開發環境是 Linux Ubuntu，Go 1.23.4。在執行 `go build` 得到的執行檔在本機可以正常執行，但放上公司服務器後就無法啟動了。奇怪的是，同事使用 Windows + Git Bash 編譯出來的執行檔在公司服務器卻能正常運行！

## 問題原因

上網查詢後，得到問題發生的可能原因如下：

1. **編譯環境的 GLIBC 版本過高**
   - 用來編譯 Go 程式的系統（例如我的開發機）使用了較新的 GLIBC 版本（例如 2.32 或更高）
   - 而目標執行環境（公司 Linux 伺服器）的 GLIBC 版本較舊（低於 2.32）
   - Linux 的動態連結器在執行時發現目標系統缺少所需的 GLIBC 版本，因此報錯

2. **Go 編譯預設使用動態連結**
   - Go 編譯的執行檔預設會動態連結到系統的 C 庫（GLIBC），即使程式本身沒有直接使用 CGO
   - 如果 Go 的 runtime 或某些依賴項（如 net 或 os 包中的 DNS 解析）間接依賴 GLIBC，就會觸發這個問題

## 解決方案

後來比對 Git Bash 和自身開發環境的 `go env` 發現 `CGO_ENABLED` 這項參數配置不同：

- 在 Git Bash 上是 `0`
- 在我的 Linux 環境上是 `1`

問題很明顯了！就是這個設定讓 Git Bash 打包出來的執行檔可以正常執行。

`CGO_ENABLED=0` 這個參數的目的是：使用靜態連結編譯，告訴 Go 編譯器生成完全靜態連結的二進位檔案，這樣執行檔就不會依賴目標系統的 GLIBC。

果然，在我的 Linux 環境下使用以下指令編譯：

```bash
CGO_ENABLED=0 go build
```

編譯出的檔案就可以在服務器上正常執行了！

---

## 深入了解 CGO 和 GLIBC

既然遇到問題了，就順便深入了解一下 `CGO` 這項配置和 `GLIBC`。

### CGO 是什麼？

CGO 是 Go 程式語言中的一個功能，讓 Go 程式可以與 C 語言程式碼進行交互。簡單來說，它是 Go 提供的一個橋樑，允許你在 Go 中調用 C 函數，或者讓 C 程式碼調用 Go 函數。

#### 1. 定義

- CGO 是 Go 的工具和功能的統稱，允許 Go 程式透過編譯器和連結器與 C 語言程式碼整合
- 它由 Go 的標準工具鏈支持，需要在編譯時啟用（預設情況下，`CGO_ENABLED=1`）

#### 2. 主要用途

- **調用 C 函數**：如果你需要使用現有的 C 庫（例如某個高性能數學庫或系統級 API），可以用 CGO 在 Go 中調用它們
- **嵌入 C 程式碼**：你可以在 Go 檔案中直接嵌入 C 程式碼，透過特殊的註解（`// #include` 和 `import "C"`）
- **與外部系統交互**：某些底層功能（例如檔案系統、网络協議）可能需要 C 語言的支援，CGO 是實現這一點的方式

#### 3. 基本範例

```go
package main

/*
#include <stdio.h>
void printHello() {
    printf("Hello from C!\n");
}
*/
import "C"
import "fmt"

func main() {
    C.printHello() // 調用 C 函數
    fmt.Println("Hello from Go!")
}
```

編譯時需要啟用 CGO：

```bash
go build -o myapp main.go
```

輸出：
```
Hello from C!
Hello from Go!
```

### CGO 的工作原理

#### 1. 編譯過程

- 當你使用 CGO 時，Go 編譯器會將 Go 程式碼轉換為中間格式，並調用系統的 C 編譯器（例如 `gcc`）來編譯 C 程式碼
- 最終，Go 的連結器會將 Go 和 C 的目標檔案連結成一個可執行檔案

#### 2. 依賴外部庫

- 如果 C 程式碼或 Go 的標準庫（透過 CGO）使用了系統的 C 運行時庫（即 GLIBC），生成的執行檔會動態連結到 GLIBC

#### 3. 環境變數 `CGO_ENABLED`

- `CGO_ENABLED=1`：啟用 CGO（預設值），允許 Go 使用 C 程式碼
- `CGO_ENABLED=0`：禁用 CGO，Go 不會調用 C 編譯器，生成的執行檔通常是靜態連結的，不依賴 GLIBC

---

### CGO 與 GLIBC 的關聯

在我的案例中（Linux 下編譯出現 `/libc.so.6: version GLIBC_2.32` 錯誤），CGO 與問題密切相關：

#### 1. 動態連結與 GLIBC

- 即使 Go 程式碼沒有直接使用 CGO，Go 的標準庫（例如 `net`、`os` 或 `runtime`）可能間接透過 CGO 調用 C 函數（例如 DNS 解析或系統調用）
- 當 CGO 啟用時，編譯器會將程式連結到系統的 GLIBC（GNU C Library）
- 如果在 GLIBC 2.39 的系統上編譯，而目標系統只有 GLIBC 2.27，執行時就會報錯，因為目標系統缺少所需的 GLIBC 版本

#### 2. Git Bash vs. Linux 的差異

- **Git Bash**：當用 `GOOS=linux` 在 Git Bash 下編譯時，若未明確啟用 CGO（或 Go 工具鏈預設行為生成靜態連結），生成的檔案可能不依賴 GLIBC，或者依賴的 GLIBC 版本較低
- **Linux 環境**：預設啟用了 CGO（`CGO_ENABLED=1`），生成的執行檔動態連結到系統的 GLIBC（例如 2.32 或 2.39），導致在目標系統（GLIBC < 2.32）上無法運行

#### 3. 靜態連結解決問題

- 當設置 `CGO_ENABLED=0` 時，Go 不會使用 C 編譯器，生成的執行檔不依賴 GLIBC，而是完全依賴 Go 的內建運行時
- 使用以下指令可解決問題：

```bash
CGO_ENABLED=0 GOOS=linux go build ...
```

---

### CGO 的優點與缺點

#### 優點

- **功能擴展**：可以利用現有的 C 庫，實現 Go 無法直接完成的任務（例如硬件驅動、性能優化的計算）
- **跨語言整合**：允許 Go 和 C/C++ 協作，適合複雜項目

#### 缺點

- **依賴外部環境**：生成的執行檔可能依賴系統的 GLIBC，降低跨平台兼容性
- **編譯複雜性**：需要系統安裝 C 編譯器（例如 `gcc`），在交叉編譯時可能遇到環境配置問題
- **性能開銷**：Go 和 C 之間的調用有一定的性能損耗

---

## 在我的案例中的應用

### 1. 問題根源

- 我的 Linux 環境（GLIBC 2.39）編譯時，CGO 預設啟用，生成的檔案依賴高版本的 GLIBC
- Git Bash 編譯的檔案能在目標 Linux 上運行，可能是因為它未依賴 GLIBC（靜態連結），或者依賴的 GLIBC 版本低於目標系統

### 2. 解決方法

- **禁用 CGO**：使用 `CGO_ENABLED=0`，確保生成靜態連結的執行檔，消除 GLIBC 依賴：

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "-X match-engine/constants.VERSION=$(VERSION)" -o $(KLINE_CLIENT_LINUX_BINARY_NAME) ./cmd/ws_client/main.go
```

- **檢查程式碼**：如果程式明確使用了 CGO（例如 `import "C"`），需要確認是否真的需要它。如果不需要，移除相關代碼後用 `CGO_ENABLED=0` 編譯

### 3. 驗證

- 編譯後檢查依賴：

```bash
ldd $(KLINE_CLIENT_LINUX_BINARY_NAME)
```

- 若顯示 `not a dynamic executable`，表示成功靜態連結，應該能在任何 Linux 上運行

### 4. Git Bash 的情況

- 在 Git Bash 下使用：

```bash
GOOS=linux go build -ldflags "-X match-engine/constants.VERSION=$(VERSION)" -o $(KLINE_CLIENT_LINUX_BINARY_NAME) ./cmd/ws_client/main.go
```

- 如果生成的檔案能在目標 Linux 上運行，可能是：
  - Go 工具鏈預設生成靜態連結（取決於版本和配置）
  - 或依賴的 GLIBC 版本低於目標系統（例如 Git Bash 的 Go 環境依賴 GLIBC 2.27，而目標系統支持）
- 用 `ldd` 檢查 Git Bash 編譯的檔案，能確認它是否靜態連結

---

## 動態連結和靜態連結的實際影響

### 1. 動態連結的優勢與風險

- **優勢**：檔案小，系統更新 GLIBC 時程式自動受益（例如修補安全漏洞）
- **風險**：目標系統 GLIBC 版本低於編譯環境，導致運行失敗

### 2. 靜態連結的優勢與風險

- **優勢**：獨立性強，無版本兼容性問題，適合分發到未知環境
- **風險**：檔案較大，若庫有漏洞，需重新編譯更新

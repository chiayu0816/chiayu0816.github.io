# goroutine

***Goroutine是Go語言中的輕量級線程,由Go運行時管理。允許併發執行函數。***

1. 定義：Goroutine 是一個由 Go 運行時管理的獨立執行單元，可以看作是一種用戶級線程。
2. 特點：
   * 輕量級：初始棧大小僅約 2KB，可根據需要動態調整。
   * 高效：可以在單個操作系統線程上多路複用多個 goroutine。
   * 易用：使用 'go' 關鍵字即可輕鬆創建。
3. 調度：由 Go 運行時的協作式調度器管理，而非直接由操作系統調度。
4. 通信：主要通過 channel 進行 goroutine 間的通信和同步。
5. 規模：一個 Go 程序可以並發運行數十萬個 goroutine。
6. 使用場景：適用於需要高並發的場景，特別是涉及大量 I/O 操作或需要並行處理的任務。

範例：

```go
package main

import (
    "fmt"
    "runtime"
    "sync"
    "time"
)

func main() {
    start := time.Now()
    var wg sync.WaitGroup

    // 創建大量goroutine
    for i := 0; i < 1000000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            time.Sleep(time.Millisecond)
        }()
    }

    wg.Wait()
    elapsed := time.Since(start)

    fmt.Printf("創建並執行了1,000,000個goroutine\\n")
    fmt.Printf("耗時: %v\\n", elapsed)
    fmt.Printf("系統線程數: %d\\n", runtime.NumGoroutine())
}

```

這個例子創建了100萬個goroutine，每個只是短暫睡眠。在大多數現代系統上，這個程式可以在幾秒內完成，而且不會耗盡系統資源。相比之下，嘗試創建100萬個傳統線程可能會導致系統資源耗盡。

#### 總結：

1. Goroutine更輕量級，創建成本低，適合創建大量並發任務。
2. Goroutine由Go運行時管理，而不是操作系統，這提供了更高的靈活性和效率。
3. Goroutine使用協作式調度，而傳統線程使用搶佔式調度。
4. Go鼓勵使用channel進行通信，而不是共享內存，這簡化了並發編程。
5. Goroutine提供了更好的可擴展性，特別是在處理大量並發任務時。

#### 比較 Go 的 goroutine 和 Java 的 thread：

1. 創建和管理：
   * Goroutine：
     * 使用 `go` 關鍵字輕鬆創建
     * 由 Go 運行時管理
   * Java Thread：
     * 通過 `new Thread()` 或實現 `Runnable` 接口創建
     * 由 JVM 和操作系統共同管理
2. 內存佔用：
   * Goroutine：初始棧大小約 2KB，可動態調整
   * Java Thread：默認棧大小較大（通常是 1MB），可配置但固定
3. 調度：
   * Goroutine：使用 Go 運行時的協作式調度器
   * Java Thread：使用操作系統的搶佔式調度
4. 並發規模：
   * Goroutine：單個程序可輕鬆運行數十萬個
   * Java Thread：通常受限於系統資源，難以達到相同規模
5. 通信機制：
   * Goroutine：主要使用 channel 進行通信
   * Java Thread：通常使用共享內存和同步原語（如 synchronized, wait/notify）
6. 性能：
   * Goroutine：上下文切換成本低
   * Java Thread：上下文切換成本相對較高
7. 編程模型：
   * Goroutine：鼓勵 "不要通過共享內存來通信，而要通過通信來共享內存"
   * Java Thread：傳統的共享內存模型，需要顯式同步
8. 錯誤處理：
   * Goroutine：panic 可以被 recover
   * Java Thread：異常可以被 try-catch 捕獲
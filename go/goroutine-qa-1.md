# 主goroutine結束時,其它goroutine會怎樣?

當主goroutine結束時，其它正在運行的goroutine的行為如下：

1. 強制終止：
   * 當主goroutine結束時，Go程序會立即退出。
   * 其他正在運行的goroutine會被強制終止，不管它們是否完成了任務。
   * 這些goroutine沒有機會完成它們的工作或進行清理操作。
2. 資源釋放：
   * Go運行時會釋放所有goroutine佔用的資源。
   * 這包括記憶體分配和其他系統資源。
3. 沒有異常處理：
   * 被強制終止的goroutine中的`panic`不會被捕獲或處理。
   * `defer`語句也不會被執行。
4. 數據遺失：
   * 如果goroutine正在進行I/O操作或其他重要任務，這些操作可能會被中斷，導致資料遺失或不一致。

範例：

```go
package main

import (
    "fmt"
    "time"
)

func longRunningTask() {
    for i := 0; i < 5; i++ {
        time.Sleep(time.Second)
        fmt.Printf("Task running: %d\\n", i)
    }
    fmt.Println("Task completed!")
}

func main() {
    go longRunningTask()

    time.Sleep(2 * time.Second)
    fmt.Println("Main goroutine exiting...")
    // 主goroutine在這裡結束
}
```

在這個例子中：

1. 我們啟動了一個執行`longRunningTask`的goroutine。
2. 主goroutine等待2秒後就退出了。
3. 當運行這個程式時，你會看到：
   * "Task running: 0"
   * "Task running: 1"
   * "Main goroutine exiting..."
   * 程式結束

注意，`longRunningTask`沒有機會完成它的所有迭代或輸出"Task completed!"。

為了避免這種情況並確保所有goroutine都有機會完成它們的工作，我們可以採用以下策略：

1. 使用WaitGroup：
   * 可以使用sync.WaitGroup來等待所有goroutine完成。
2. 使用channel進行同步：
   * 可以使用channel來通知主goroutine何時可以安全退出。
3. 使用context進行取消：
   * 可以使用context.Context來取消長時間運行的操作。
4. 明確的關閉信號：
   * 可以實現一個關閉機制，允許goroutine在主程序退出前完成清理工作。

在實際應用中，正確管理goroutine的生命週期是非常重要的，特別是在處理重要數據或需要清理資源的場景中。
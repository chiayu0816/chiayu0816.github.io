# cron job

***Go語言中幾個常用的cron job函式庫簡介，robfig/cron 基本使用方式***

Go語言中幾個常用的cron job函式庫:

1. robfig/cron: 這是最受歡迎的Go cron庫之一。它提供了靈活的cron表達式支持和易用的API。
2. go-co-op/gocron: 一個輕量級的分散式作業調度器,支持多種調度方式。
3. jasonlvhit/gocron: 另一個簡單易用的cron庫,支持秒級精度。
4. adhocore/gronx: 一個快速、輕量的cron解析器和調度器。
5. cloudflare/cfssl/helpers/cron: Cloudflare開發的cron庫,作為cfssl項目的一部分。

### robfig/cron

1. 特點:
   * 支持標準的 cron 表達式
   * 支持秒級精度 (可選)
   * 線程安全
   * 支持時區
   * 可以暫停和恢復 cron 作業
2. 基本用法:

```go
package main

import (
    "fmt"
    "github.com/robfig/cron/v3"
    "time"
)

func main() {
    c := cron.New()

    c.AddFunc("0 30 * * * *", func() {
        fmt.Println("每小時的30分執行一次")
    })

    c.AddFunc("@hourly", func() {
        fmt.Println("每小時執行一次")
    })

    c.AddFunc("@every 1h30m", func() {
        fmt.Println("每1小時30分鐘執行一次")
    })

    c.Start()

    // 讓程序運行一段時間
    time.Sleep(time.Hour * 24)
}

```

1.  cron 表達式: robfig/cron 支持標準的 cron 表達式，格式為：

    ```
    秒 分 時 日 月 星期
    ```

    例如：`0 30 * * * *` 表示每小時的30分執行。
2. 預定義的調度:
   * `@yearly` (或 `@annually`): 每年執行一次
   * `@monthly`: 每月執行一次
   * `@weekly`: 每週執行一次
   * `@daily` (或 `@midnight`): 每天執行一次
   * `@hourly`: 每小時執行一次
3.  錯誤處理: 您可以為每個作業添加錯誤處理邏輯，例如：

    ```go
    c.AddFunc("@every 1m", func() {
        _, err := dangerousOperation()
        if err != nil {
            log.Printf("error: %v", err)
        }
    })

    ```
4. 停止 cron: 使用 `c.Stop()` 可以停止所有的 cron 作業。
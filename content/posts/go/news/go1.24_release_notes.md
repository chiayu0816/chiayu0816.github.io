---
title: "Go 1.24 Release Notes Highlights"
categories: ["Go"]
---

## 語言變更
- **泛型類型別名**  
  完全支援泛型類型別名。類型別名可以像定義的類型一樣進行參數化。

## 工具
- **Go Modules**  
  - 可使用 `tool` 指令追蹤可執行依賴項，不再需要將工具作為空白導入添加到 `tools.go` 檔案中。
  - `go get` 新增 `-tool` 標誌，將工具指令添加到目前模組。
  - 新增 `tool` meta-pattern，用於升級或安裝目前模組中的所有工具。

- **執行與建置工具**  
  - `go run` 和 `go tool` 建立的可執行檔現在會緩存在 Go 建置快取中，加快重複執行速度。
  - `go build` 和 `go install` 命令新增 `-json` 標誌，以 JSON 格式報告建置輸出和失敗。

- **環境變數與版本資訊**  
  - 新增 `GOAUTH` 環境變數，提供彈性的方式驗證私有模組獲取。
  - `go build` 命令現在會根據版本控制系統標籤或提交，在編譯後的二進位檔案中設定主模組的版本。

## Cgo
- **新註解支援**  
  - `#cgo noescape cFunctionName`  
    告訴編譯器傳遞給 C 函數的記憶體不會逸出。
  - `#cgo nocallback cFunctionName`  
    告訴編譯器 C 函數不會回呼任何 Go 函數。

## Objdump
- objdump 工具現在支援在 64-bit LoongArch、RISC-V 和 S390X 平台上的反組譯。

## Vet
- 新增 `tests` 分析器，報告測試套件中測試、模糊器、基準和範例宣告中的常見錯誤。

## Runtime
- **效能改進**  
  - 平均降低了 2-3% 的 CPU overhead。
  - 基於 Swiss Tables 的新內建 `map` 實現。
  - 更有效率的小物件記憶體配置。
  - 新的 runtime 內部互斥鎖實現。

## Compiler
- 編譯器現在會報告 receiver 是否表示 cgo 產生的類型錯誤。

## Linker
- 預設在 ELF 平台上產生 GNU build ID，在 macOS 上產生 UUID。

## 標準函式庫
- **新增功能**  
  - `os.Root` 類型：提供在特定目錄中執行檔案系統操作的能力。
  - Benchmark 新增 `testing.B.Loop` 方法，以執行基準測試疊代。
  - `runtime.AddCleanup` 函數：提供更靈活、更有效率的 finalization 機制。
  - `weak` 套件：提供弱指標。
  - `crypto/mlkem` 套件：實現 ML-KEM-768 和 ML-KEM-1024。
  - 新增 `crypto/hkdf`、`crypto/pbkdf2` 和 `crypto/sha3` 套件。

- **安全性與相容性**  
  - FIPS 140-3 相容性：包含新的機制以促進 FIPS 140-3 相容性。

- **測試與同步**  
  - 新增實驗性的 `testing/synctest` 套件，提供對並行程式碼的測試支援。

- **其他更新**  
  - `bytes` 和 `strings` 套件新增多個使用 iterators 的函數。
  - `crypto/tls` 現在支援 Encrypted Client Hello (ECH)。
  - `encoding`  
    引入兩個新介面：`TextAppender` 與 `BinaryAppender`，用於將物件的文字或二進位表示形式附加到 byte slice。
  - `encoding/json`  
    新增 `omitzero` 選項，當 struct 欄位的值為零時，將其省略。
  - `net/http`  
    Transport 和 Server 現在有一個 HTTP2 欄位，允許配置 HTTP/2 協定設定。
  - `sync`  
    `sync.Map` 的實現已變更，提高了效能。

## Ports
- **系統要求與支援**  
  - Go 1.24 需要 Linux 核心版本 3.2 或更高版本。
  - Go 1.24 是最後一個在 macOS 11 Big Sur 上執行的版本。

- **WebAssembly**  
  - 新增 `go:wasmexport` 編譯器指令，以便 Go 程式將函數匯出到 WebAssembly host。

- **Windows**  
  - 32-bit windows/arm port 已被標記為 broken。

---

# Go 1.24 開發語法變更與新增功能

## 泛型類型別名完全支援
- 類型別名現在可以像定義的類型一樣進行參數化，
  為程式碼的靈活性和重用性提供了更大的空間。

## Go Modules 的 `tool` 指令
- 可在 `go.mod` 檔案中追蹤可執行依賴項，
  無需再使用傳統的 `tools.go` 檔案和空白導入作為 workaround。
- `go get` 命令新增了 `-tool` 標誌，
  方便將工具指令添加到當前模組。
- `tool` meta-pattern 可以用來一次性升級或安裝當前模組中的所有工具。

## `testing.B.Loop` 方法
- 在 benchmark 測試中，`testing.B.Loop` 方法可用來執行 benchmark 迭代。
- 相較於傳統使用 `b.N` 的迴圈結構，
  此方法確保 benchmark 函數在每次 `-count` 時只執行一次，
  並且可以避免編譯器過度優化迴圈主體。

## `runtime.AddCleanup` 函數
- 提供比 `runtime.SetFinalizer` 更靈活、更有效率的 finalization 機制。
- 可為物件附加 cleanup 函數，並允許多個 cleanup 函數附加到同一個物件，
  減少記憶體洩漏風險，且不會延遲物件的釋放。

## `weak` 套件
- 提供弱指標，有助於建立記憶體效率更高的結構，
  例如 weak maps 和各種類型的快取。

## `encoding` 套件的新介面：`TextAppender` 和 `BinaryAppender`
- 可將物件的文字或二進位表示形式附加到 byte slice，
  無需每次都分配新的 slice，從而提升效能。
- 許多標準函式庫類型現在都已實作這些介面。

## `encoding/json` 的 `omitzero` 選項
- 在 marshaling JSON 時，可以使用 `omitzero` 選項來省略值為零的 struct 欄位。
- 相較於 `omitempty`，`omitzero` 更能清晰表達省略零值的意圖，
  尤其在處理 `time.Time` 類型時更具優勢。

## `go/types` 的迭代器方法
- 資料結構現在提供返回迭代器的方法，
  簡化了對 sequences 的操作。

## `bytes` 和 `strings` 套件新增的 iterator 相關函數
- 新增函數包括：
  - `Lines`
  - `SplitSeq`
  - `SplitAfterSeq`
  - `FieldsSeq`
  - `FieldsFuncSeq`
- 這些函數方便開發者使用 iterators 處理 byte slices 和 strings。

---

>以上內容是透過 AI 總結，僅供參考。詳細內容請以[官方公告](https://go.dev/doc/go1.24)為準。


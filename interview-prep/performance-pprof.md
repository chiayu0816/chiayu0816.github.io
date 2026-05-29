# Performance / pprof 面試 Q&A

> 來源：interview-go、tech-vault、Roy 生產調優實務
> 題數：15 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: Go pprof 有哪些 profile 型別？

**核心回答：**
CPU、Heap（alloc/inuse）、Goroutine、Mutex、Block、Trace（時間線）。net/http/pprof 或 go tool pprof。看 flat（自身）vs cum（累計）。

**深入原理：**
- sample 100Hz CPU
- heap 512KB default rate
- mutex/block 需 runtime.SetBlockProfileRate

**考官可能追問：**
- Q: 生產安全？
  - A: 短視窗+auth
- Q: remote pod？
  - A: kubectl port-forward

**常見陷阱 / 易錯點：**
- 只看 CPU 不看 heap
- profile 時間太短

**結合履歷：**
Roy 生產調優：pprof、flame graph、logs、metrics。

---
### Q: 如何讀火焰圖（Flame Graph）？

**核心回答：**
Y 軸棧深度，X 軸寬度=取樣佔比（非時間）。頂寬=hot function。看 platoe 找最佳化點。icicle 倒置版本。

**深入原理：**
- go tool pprof -http=:8080
- focus/ignore 過濾
- diff 兩個 profile

**考官可能追問：**
- Q: 寬但淺？
  - A: 頻繁呼叫
- Q: tail 噪聲？
  - A: focus 主路徑

**常見陷阱 / 易錯點：**
- X 軸當時間軸
- 最佳化非瓶頸

---
### Q: CPU profile 高但業務 QPS 低？

**核心回答：**
可能：鎖競爭、GC mark assist、syscall、cgo、序列化、regex。用 mutex/block profile 輔助；trace 看 STW/GC。

**深入原理：**
- sched trace
- GODEBUG=gctrace=1
- strace 極端

**考官可能追問：**
- Q: JSON marshal hot？
  - A: 換 protobuf/預分配
- Q: 鎖？
  - A: mutex profile

**常見陷阱 / 易錯點：**
- 盲目加 CPU

---
### Q: Heap profile：alloc_space vs inuse_space？

**核心回答：**
alloc_space 累計分配（找 alloc 熱點）；inuse_space 當前存活（找洩漏）。top -alloc_objects 看次數。

**深入原理：**
-  -inuse_space 預設
- cum 呼叫鏈
- escape analysis -gcflags=-m

**考官可能追問：**
- Q: alloc 高但 inuse 低？
  - A: 短生命週期
- Q: inuse 漲？
  - A: 洩漏

**常見陷阱 / 易錯點：**
- 混淆兩者
- 未壓測就 profile

---
### Q: 如何定位 goroutine 洩漏？

**核心回答：**
goroutine profile 看 stack 阻塞點；對比 baseline 數量；common：chan block、HTTP 無 timeout、WaitGroup、select 無 case。

**深入原理：**
- debug=2 棧
- pprof label 區分
- leaktest

**考官可能追問：**
- Q: 數萬 goroutine？
  - A: 限流+pool
- Q: HTTP？
  - A: context timeout

**常見陷阱 / 易錯點：**
- 重啟掩蓋
- 無監控 goroutine 數

**結合履歷：**
Luxons：pprof 定位 HTTP 第三方 API 無 timeout 洩漏。

---
### Q: Mutex/Block profile 如何使用？

**核心回答：**
runtime.SetMutexProfileFraction(1)、SetBlockProfileRate(1) 開啟取樣。看 contention 棧，最佳化鎖粒度或改無鎖/sharding。

**深入原理：**
- block 含 chan sleep
- mutex 含 RWMutex
- 延遲影響

**考官可能追問：**
- Q: RWMutex 慢？
  - A: 寫多降級 Mutex
- Q: 鎖順序？
  - A: 固定防死鎖

**常見陷阱 / 易錯點：**
- 生產長期開 fraction=1 開銷
- 忽略 block

---
### Q: execution trace 分析什麼？

**核心回答：**
go test -trace / curl trace.out；看 goroutine 排程、GC STW、syscall、network、mutex。Gantt 找 long critical path。

**深入原理：**
- UserTask region
- Minimum mutator utilization
- network wait

**考官可能追問：**
- Q: P99 高？
  - A: trace 找 long lane
- Q: GC MMU？
  - A: trace GC

**常見陷阱 / 易錯點：**
- trace 檔案巨大
- 未關聯 request id

---
### Q: benchmark 與 pprof 結合？

**核心回答：**
go test -bench -cpuprofile -memprofile；benchstat 對比；避免 dead code elimination 用 Result 消費。

**深入原理：**
- parallel bench
- warmup
- allocs/op metric

**考官可能追問：**
- Q: bench 不代表生產？
  - A: 加 realism IO mock
- Q: 最佳化驗證？
  - A: 前後 profile diff

**常見陷阱 / 易錯點：**
- bench 無-allocs
- 編譯器最佳化假象

---
### Q: 生產環境 profiling 最佳實踐？

**核心回答：**
短 duration（30s）、低峰、取樣、許可權控制、continuous profiling（Parca/Pyroscope）。告警觸發 on-demand。

**深入原理：**
- security pprof auth
- overhead <5%
- symbolize 需 binary

**考官可能追問：**
- Q: K8s？
  - A: debug container/copy binary
- Q: always on？
  - A: continuous 1% CPU

**常見陷阱 / 易錯點：**
- peak 採失真相
- 無 symbol 只看地址

---
### Q: K 線最佳化案例如何用 pprof 驗證？

**核心回答：**
最佳化前 baseline profile：CPU（JSON/SQL）、heap（[]byte 分配）、latency trace。最佳化 SP+Redis 後對比 alloc 與 latency 降。

**深入原理：**
- EXPLAIN+profile SQL
- Redis pipeline 前後
- end-to-end metric

**考官可能追問：**
- Q: 3-5s 瓶頸？
  - A: DB+無 cache
- Q: 如何證明？
  - A: before/after p99

**常見陷阱 / 易錯點：**
- 只最佳化區域性非 hot path

**結合履歷：**
Roy K線 3-5s→300-500ms：SP+index+ZSET+pprof 驗證。

---
### Q: 延遲排查：USE/RED 方法？

**核心回答：**
USE：Utilization Saturation Errors（資源）。RED：Rate Errors Duration（服務）。結合 pprof 找 Errors/Duration 根因。

**深入原理：**
- saturation queue depth
- error budget
- histogram buckets

**考官可能追問：**
- Q: CPU util 低但慢？
  - A: wait IO/lock
- Q: RED 夠嗎？
  - A: 加 traces

**常見陷阱 / 易錯點：**
- 只看 avg 不看 p99
- 無 saturation 指標

---
### Q: 系統性能 baseline 如何建立？

**核心回答：**
壓測場景定義（QPS/latency SLO）；採集 CPU/heap/goroutine/trace；存檔版本對比；chaos 下 profile。

**深入原理：**
- k6/locust
- production mirror
- regression CI bench

**考官可能追問：**
- Q: 何時 re-baseline？
  - A: major release
- Q: 資料脫敏？
  - A: staging prod-like

**常見陷阱 / 易錯點：**
- 無 baseline 口頭最佳化
- staging 配置不一致

---
### Q: log vs metric vs trace 何時用？

**核心回答：**
Metric 告警趨勢；Log 細節 debug（帶 traceId）；Trace 分散式 latency。Profile 深度 CPU/heap。

**深入原理：**
- structured json log
- high cardinality 避免 metric
- tail sampling trace

**考官可能追問：**
- Q: printf 除錯生產？
  - A: 禁
- Q: 全量 trace？
  - A: 取樣

**常見陷阱 / 易錯點：**
- metric 放 userId
- log 無級別

---
### Q: MySQL/Redis 慢而 app CPU 低？

**核心回答：**
等待外部：DB lock、慢 SQL、Redis 大 key、network RTT。App profile 空；查 DB slow log、Redis slowlog、trace span DB time。

**深入原理：**
- connection pool wait
- N+1 query
- missing index

**考官可能追問：**
- Q: 如何證明 DB？
  - A: span tag db.statement
- Q: Redis？
  - A: LATENCY DOCTOR

**常見陷阱 / 易錯點：**
- 加 app 實例無效
- 未 EXPLAIN

---
### Q: 效能最佳化優先順序方法論？

**核心回答：**
1) 測量 2) 找瓶頸（Amdahl）3) 最佳化 hot path 4) 再測量。先架構/演算法，再 micro-opt。避免過早最佳化。

**深入原理：**
- profile-guided optimization
- cost/benefit
- SLO driven

**考官可能追問：**
- Q: 同事說加快取？
  - A: 先 profile 證明 IO bound
- Q: 換語言？
  - A: 最後手段

**常見陷阱 / 易錯點：**
- 猜瓶頸
- 最佳化錯誤層

---

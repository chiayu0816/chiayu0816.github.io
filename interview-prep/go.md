# Go 面試 Q&A

> 來源：go-questions（GMP/GC/channel/map/slice/interface/context/compile）、interview-go（question/base）、go-interview-practice
> 題數：38 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景（個人對照見 resume_overlay.py）

---

### Q: 什麼是 GMP 模型？G、P、M 各自負責什麼？

**核心回答：**
Go runtime 使用 M:N 排程：G（goroutine）是使用者態協程，儲存執行棧與暫存器現場；M（machine）是 OS 執行緒，真正在 CPU 上跑；P（processor）是邏輯處理器，持有本地 run queue 與 mcache，M 必須繫結 P 才能執行 G。P 的數量由 GOMAXPROCS 決定，通常等於 CPU 核心數。

**深入原理：**
- G 結構含 stack、sched（gobuf 存 sp/pc）、status、m（繫結執行緒）、preempt 搶佔標誌
- P 維護 runq（256 長度環形佇列）、runnext（下一個優先 G）、mcache（本地 span 快取，減少全域 mcentral 鎖競爭）
- M 在無 P 時阻塞在 sched.midle，syscall 阻塞時 M 可能與 P 解綁，P 可轉給其他 M 繼續跑 G
- 全域 runq 由 sched.lock 保護，本地 runq 滿時將一半 G 轉移到全域

```svg
<svg viewBox="0 0 660 330" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GMP 排程模型：P 持有本地佇列，繫結 M，Work Stealing 平衡負載">
  <rect x="32" y="36" width="270" height="120" rx="8" fill="#13161f" stroke="#56c2ff" stroke-width="1.5"/>
  <text x="46" y="58" fill="#56c2ff" font-size="13" font-weight="700">P0 · local runq</text>
  <circle cx="70" cy="92" r="14" fill="#ffb454"/><text x="70" y="97" fill="#0a0c11" font-size="11" text-anchor="middle">G</text>
  <circle cx="108" cy="92" r="14" fill="#ffb454"/><text x="108" y="97" fill="#0a0c11" font-size="11" text-anchor="middle">G</text>
  <circle cx="146" cy="92" r="14" fill="#ffb454"/><text x="146" y="97" fill="#0a0c11" font-size="11" text-anchor="middle">G</text>
  <text x="46" y="136" fill="#9aa3b5" font-size="11">runnext · mcache</text>
  <rect x="358" y="36" width="270" height="120" rx="8" fill="#13161f" stroke="#56c2ff" stroke-width="1.5"/>
  <text x="372" y="58" fill="#56c2ff" font-size="13" font-weight="700">P1 · local runq</text>
  <circle cx="396" cy="92" r="14" fill="#ffb454"/><text x="396" y="97" fill="#0a0c11" font-size="11" text-anchor="middle">G</text>
  <text x="372" y="136" fill="#9aa3b5" font-size="11">空 → 觸發 work stealing</text>
  <rect x="32" y="180" width="270" height="44" rx="8" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="167" y="207" fill="#54dd9b" font-size="12" text-anchor="middle">M0 · OS thread（繫結 P0）</text>
  <rect x="358" y="180" width="270" height="44" rx="8" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="493" y="207" fill="#54dd9b" font-size="12" text-anchor="middle">M1 · OS thread（繫結 P1）</text>
  <rect x="32" y="256" width="596" height="48" rx="8" fill="#0d1017" stroke="#6b7385" stroke-width="1.5" stroke-dasharray="5 4"/>
  <text x="330" y="285" fill="#9aa3b5" font-size="12" text-anchor="middle">全域 run queue（sched.lock 保護，本地滿時溢位一半）</text>
  <path d="M358 96 Q330 96 304 96" fill="none" stroke="#c79cff" stroke-width="1.6" stroke-dasharray="4 3" marker-end="url(#ar)"/>
  <text x="330" y="30" fill="#c79cff" font-size="11" text-anchor="middle">steal n/2</text>
  <defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#c79cff"/></marker></defs>
</svg>
```

**考官可能追問：**
- Q: 為什麼需要 P 這一層，不直接用 M 排程 G？
  - A: P 提供 per-P 本地佇列與 mcache，避免所有 G 競爭單一全域佇列和全域 heap 鎖；M 數量可大於 P（syscall 阻塞時），但同時只有 GOMAXPROCS 個 P 在跑 user code
- Q: GOMAXPROCS 設多少合適？
  - A: 預設 = CPU 核心數；CPU-bound 保持預設；IO-bound 可略增但過多 P 增加排程開銷；容器內需配合 cgroup CPU quota 設定

**常見陷阱 / 易錯點：**
- 混淆 M 數量與 goroutine 數量
- 在 init 或 runtime.LockOSThread 後長期佔用 M
- 以為 GOMAXPROCS=1 就完全序列（sysmon 與 GC 仍可能介入）

**實務場景：**
在交易/行情繫統的行情與訂單處理場景中，會用大量 goroutine，理解 GMP 後可避免在熱路徑阻塞 M（長 syscall），並用 worker pool 控制 goroutine 數量

---
### Q: 什麼是 Work Stealing？何時觸發？

**核心回答：**
當某 P 的本地 runq 為空而全域 runq 也無 G 時，該 P 會從其他 P 的 runq **偷取一半** G 來執行，以平衡負載。偷取從隨機 P 開始，減少競爭。這是 Go 排程器保持 CPU 飽和的核心機制。

**深入原理：**
- runSteal 在 schedule 迴圈中：先查本地 runq → 全域 runq → network poll → 再 steal
- 偷取時一次性搬運 n/2 個 G（至少 1 個），降低頻繁偷取的開銷
- timer 到期也會喚醒 P 處理 timer heap 上的 G

**考官可能追問：**
- Q: Work Stealing 和 Fork-Join 執行緒池有何不同？
  - A: Go 是協作式 M:N 排程，stealing 在 P 之間自動發生；傳統執行緒池通常固定 queue，需手動分片或 work queue 設計
- Q: 為什麼不從全域佇列優先取？
  - A: 全域佇列有鎖，高併發下成為瓶頸；本地佇列無鎖（或低競爭），stealing 只在本地空閒時才做

**常見陷阱 / 易錯點：**
- 以為 goroutine 會均勻分配到所有 P（實際取決於建立時的 P 與 stealing）
- 短生命週期大量 G 仍可能造成排程開銷

**實務場景：**
高吞吐資料管線 高吞吐資料管線 並行管線與 Go goroutine pool 類似思路：本地優先、必要時再平衡

---
### Q: sysmon 是什麼？做了哪些事？

**核心回答：**
sysmon 是 runtime 啟動的**不需要 P 的後臺 M**，週期性（約 10ms+）執行：retake 長時間佔用 P 的 M、檢查 netpoll、觸發 GC、搶佔長時間執行的 G（Go 1.14+ 非同步搶佔）。它是排程器「自救」機制，防止某 G 餓死其他 G。

**深入原理：**
- retake：syscall 超過 10ms 的 P 可能被標記，M 與 P 分離後 P 可被其他 M 使用
- netpoll：將 epoll/kqueue 就緒的 fd 對應 G 放入 runq
- forcegc：若超過 2 分鐘未 GC 且環境變數允許，可觸發
- 搶佔：向 G 的 stack guard 注入 preempt 訊號，safe point 處切換

**考官可能追問：**
- Q: sysmon 會增加 CPU 開銷嗎？
  - A: 週期性喚醒但大部分時間 sleep；開銷通常可忽略，極端高 QPS 場景可 profile 確認
- Q: 沒有 sysmon 會怎樣？
  - A: network fd 可能延遲喚醒、長時間 CPU 迴圈的 G 無法被搶佔（Go 1.13 及以前）

**常見陷阱 / 易錯點：**
- 以為 goroutine 一定公平（無 sysmon 搶佔時 CPU 密集 G 可餓死 others）
- LockOSThread + 死迴圈會卡死一個 M

---
### Q: Go 1.14+ 的搶佔（preemption）如何運作？

**核心回答：**
Go 1.14 前僅在函式呼叫邊界（sync safe point）協作式讓出；1.14+ 引入**非同步搶佔**：sysmon 或 GC 向 G 棧注入 preempt 請求，signal handler 或 stack guard 觸發，在 safe point 暫停 G 重新排程。解決 tight loop 不呼叫函式時無法搶佔的問題。

**深入原理：**
- G.preempt 標誌 + stackguard0 = stackPreempt 觸發 stack growth 檢查路徑進入排程
- 非協作式路徑：向 M 發 signal（SIGURG），在 signal stack 上修改 G 的 PC 到排程入口
- cgo、部分 runtime 路徑仍可能延遲搶佔

**考官可能追問：**
- Q: 搶佔對延遲有何影響？
  - A: 被搶佔 G 需等到 safe point，通常微秒～毫秒級；對 p99 延遲敏感服務需避免超大 critical section
- Q: 和 Java 搶佔式執行緒排程比？
  - A: Go 仍是 user-level scheduling，搶佔粒度在 G 而非 OS 執行緒，切換成本更低

**常見陷阱 / 易錯點：**
- 以為 for{} 永遠無法被搶佔（1.14+ 可以）
- 在無函式呼叫的迴圈中仍假設其他 G 會立即執行

---
### Q: goroutine 和 OS 執行緒有什麼區別？

**核心回答：**
goroutine 是 Go runtime 排程的輕量協程，初始棧約 2KB（可擴展至 GB），建立/切換成本遠低於 OS 執行緒（MB 級棧、核心態切換）。Go 用少量 M 承載大量 G（M:N），由 runtime 而非核心排程。

**深入原理：**
- G 棧是連續可 grow/shrink 的 stack，溢位時 copy 到新更大 stack（非 guard page segfault 為主）
- M 數量預設無硬上限但通常 ≈ P + 阻塞 syscall 的 M
- runtime.GOMAXPROCS 控制並行度，非 goroutine 數量

**考官可能追問：**
- Q: 一個程序能建立多少 goroutine？
  - A: 受記憶體限制，每 G 至少 stack + 結構開銷；百萬級可行但需控制 stack 使用
- Q: goroutine 會對映到固定執行緒嗎？
  - A: 預設不會；runtime.LockOSThread() 可繫結 G 到 M

**常見陷阱 / 易錯點：**
- 無限制 go func() 導致 OOM
- 把 goroutine 當免費無限資源

**實務場景：**
例如用 goroutine 處理行情推送，同時用 pprof goroutine profile 監控數量異常

---
### Q: Go GC 使用什麼演演算法？三色標記如何運作？

**核心回答：**
Go 1.5+ 使用**非分代、非壓縮**的並發三色標記-清除（mark-sweep）。白色=未訪問，灰色=已訪問但子未掃完，黑色=已掃完。從 roots（goroutine stack、全域變數）出發標記，最後清除白色物件。大部分 mark 與 mutator 並發執行。

**深入原理：**
- write barrier（混合寫屏障）：標記階段插入屏障，確保「黑色物件不指向白色物件」或等價不變式
- mark assist：分配過快的 G 需協助 mark，避免 heap 增長快於 GC
- 無分代：每次 GC 掃描整個 heap（對小物件多、生命週期短場景可能不如分代 GC）

```svg
<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="三色標記：黑灰白物件與寫屏障示意">
  <rect x="20" y="58" width="150" height="64" rx="8" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="95" y="84" fill="#54dd9b" font-size="12" text-anchor="middle">GC Roots</text>
  <text x="95" y="104" fill="#9aa3b5" font-size="10" text-anchor="middle">stack / 全域變數</text>
  <circle cx="262" cy="90" r="28" fill="#3a4150" stroke="#e7eaf2" stroke-width="1.5"/>
  <text x="262" y="86" fill="#e7eaf2" font-size="12" text-anchor="middle">黑</text>
  <text x="262" y="102" fill="#9aa3b5" font-size="9" text-anchor="middle">掃完</text>
  <circle cx="410" cy="90" r="28" fill="#9aa3b5"/>
  <text x="410" y="86" fill="#0a0c11" font-size="12" text-anchor="middle">灰</text>
  <text x="410" y="102" fill="#13161f" font-size="9" text-anchor="middle">待掃子</text>
  <circle cx="558" cy="90" r="28" fill="#e7eaf2" stroke="#6b7385" stroke-width="1.5"/>
  <text x="558" y="86" fill="#0a0c11" font-size="12" text-anchor="middle">白</text>
  <text x="558" y="102" fill="#3a4150" font-size="9" text-anchor="middle">待清除</text>
  <path d="M170 90 L232 90" stroke="#56c2ff" stroke-width="1.6" marker-end="url(#gc)"/>
  <path d="M290 90 L380 90" stroke="#56c2ff" stroke-width="1.6" marker-end="url(#gc)"/>
  <path d="M438 90 L528 90" stroke="#56c2ff" stroke-width="1.6" marker-end="url(#gc)"/>
  <path d="M258 117 Q400 215 552 116" fill="none" stroke="#ff6b6b" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#gcr)"/>
  <text x="405" y="208" fill="#ff6b6b" font-size="11" text-anchor="middle">write barrier：黑→白 新指標時補標記，維持不變式</text>
  <text x="20" y="160" fill="#9aa3b5" font-size="11">標記從 roots 出發，灰色佇列掃空後只剩白色 → 並發清除回收</text>
  <defs>
    <marker id="gc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#56c2ff"/></marker>
    <marker id="gcr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#ff6b6b"/></marker>
  </defs>
</svg>
```

**考官可能追問：**
- Q: 為什麼 Go 不用分代 GC？
  - A: 簡化 runtime、降低 STW 與 barrier 複雜度；trade-off 是短生命物件可能增加 mark 工作量
- Q: 三色標記的漏標問題如何解決？
  - A: 寫屏障 + STW 短暫重新掃描 roots/stack；或 SATB/deletion barrier 變體

**常見陷阱 / 易錯點：**
- 以為 GC 完全無 STW
- 忽略 mark assist 導致 mutator 變慢

**實務場景：**
時間序列/圖表資料快取重構時用 pprof alloc_space 觀察 GC 壓力，減少高頻路徑短生命物件分配

---
### Q: Go GC 的 STW 階段有哪些？還嚴重嗎？

**核心回答：**
並發 GC 仍有短暫 STW：**mark setup**（停止所有 P，開啟 write barrier）、**mark termination**（等待 mark worker 完成、關 barrier、清理）、**sweep termination**（可選）。Go 1.8+ 典型 STW 在百微秒～低毫秒，遠小於早期版本。

**深入原理：**
- stopTheWorld：每 P 的 M 在 safe point 停住，記錄 stack roots
- GOGC 預設 100：heap 翻倍觸發下一輪 GC
- GODEBUG=gctrace=1 可觀察每輪 GC 時間與 heap 大小

**考官可能追問：**
- Q: 如何降低 GC 延遲？
  - A: 減少分配（sync.Pool、預分配 buffer）、控制 GOGC、避免超大 pointer-rich heap
- Q: STW 和 P99 延遲的關係？
  - A: STW 期間所有 mutator 暫停，直接推高 latency tail；需用 trace 關聯

**常見陷阱 / 易錯點：**
- 只調 GOGC 不減 allocation
- 在 latency 敏感路徑大量 alloc

---
### Q: write barrier 是什麼？為什麼需要？

**核心回答：**
並發 mark 時 mutator 仍在修改 pointer graph，可能出現「黑色物件新指向白色物件」導致漏標。write barrier 在 pointer 寫入時插入 runtime 程式碼，將相關白色或灰色物件標記，維持三色不變式。Go 使用 hybrid write barrier（Yuasa + Dijkstra 混合）。

**深入原理：**
- 編譯器在 *ptr = src 等寫入點插入 wbBuf 記錄
- GC 後期 flush wbBuf 批次處理
- barrier 僅在 GC mark 階段啟用，平時無開銷

**考官可能追問：**
- Q: write barrier 效能影響？
  - A: mark 期間每次 pointer write 有額外指令，通常 10-30% mutator 慢速，換取更短 STW
- Q: 和 Java G1 的 SATB 比？
  - A: 思路類似：記錄寫入以保證快照或增量標記正確性，實現細節不同

**常見陷阱 / 易錯點：**
- 以為 GC 全程無 barrier 開銷
- unsafe 繞過 barrier 可能破壞 GC（需極度小心）

---
### Q: GOGC 和 GOMEMLIMIT 如何調優？

**核心回答：**
GOGC 控制 GC 觸發閾值：新 heap 大小達 live heap 的 (100+GOGC)% 時觸發（預設 100=翻倍）。Go 1.19+ GOMEMLIMIT 設定 soft memory limit，runtime 會更積極 GC 以避免 OOM，適合容器環境。

**深入原理：**
- GOGC=off 禁用 GC（僅特殊場景）
- GOMEMLIMIT 與 cgroup memory.limit 配合，避免被 OOM killer 殺
- trade-off：更低 GOGC → 更頻繁 GC、更低 RSS、更高 CPU

**考官可能追問：**
- Q: 容器 memory limit 512Mi 怎麼設？
  - A: GOMEMLIMIT≈450MiB 留 buffer，GOGC 預設或略降視 CPU 而定
- Q: 如何觀察 GC 是否成為瓶頸？
  - A: gctrace、runtime/metrics、trace 的 GC 事件、alloc_rate

**常見陷阱 / 易錯點：**
- GOMEMLIMIT 設等於 hard limit 無 buffer
- 只看 RSS 不看 GC CPU fraction

---
### Q: channel 底層 hchan 結構是什麼？

**核心回答：**
channel 底層是 runtime.hchan：含 qcount（元素數）、dataqsiz（容量）、buf 環形佇列、sendx/recvx 索引、sendq/recvq（sudog 等待連結串列）、lock。有緩衝 channel 先寫 buf；無緩衝需 direct handoff（G 直接交換資料）。

**深入原理：**
- sudog 包裝等待的 G 與 element 指標
- close 時喚醒所有 recv waiters，send waiters panic
- elem size 決定 buf 元素步長，由 makechan 分配

```svg
<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="hchan 環形緩衝與 sendq/recvq 等待佇列">
  <text x="330" y="26" fill="#56c2ff" font-size="13" font-weight="700" text-anchor="middle">hchan：環形緩衝 + 等待佇列</text>
  <rect x="22" y="66" width="120" height="96" rx="8" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="82" y="86" fill="#54dd9b" font-size="11" text-anchor="middle">recvq</text>
  <circle cx="82" cy="120" r="16" fill="#54dd9b"/><text x="82" y="124" fill="#06140d" font-size="10" text-anchor="middle">G</text>
  <text x="82" y="153" fill="#9aa3b5" font-size="9" text-anchor="middle">等待接收</text>
  <rect x="176" y="92" width="46" height="46" fill="#ffb454"/>
  <rect x="224" y="92" width="46" height="46" fill="#ffb454"/>
  <rect x="272" y="92" width="46" height="46" fill="#ffb454"/>
  <rect x="320" y="92" width="46" height="46" fill="#13161f" stroke="#2f3645" stroke-width="1.2"/>
  <rect x="368" y="92" width="46" height="46" fill="#13161f" stroke="#2f3645" stroke-width="1.2"/>
  <rect x="416" y="92" width="46" height="46" fill="#13161f" stroke="#2f3645" stroke-width="1.2"/>
  <text x="319" y="156" fill="#9aa3b5" font-size="10" text-anchor="middle">dataqsiz = 6（環形佇列）</text>
  <path d="M199 64 L199 88" stroke="#56c2ff" stroke-width="1.6" marker-end="url(#ch)"/>
  <text x="199" y="58" fill="#56c2ff" font-size="10" text-anchor="middle">recvx</text>
  <path d="M343 178 L343 142" stroke="#c79cff" stroke-width="1.6" marker-end="url(#ch)"/>
  <text x="343" y="192" fill="#c79cff" font-size="10" text-anchor="middle">sendx</text>
  <rect x="518" y="66" width="120" height="96" rx="8" fill="#0d1017" stroke="#ff6b6b" stroke-width="1.5"/>
  <text x="578" y="86" fill="#ff6b6b" font-size="11" text-anchor="middle">sendq</text>
  <circle cx="578" cy="120" r="16" fill="#ff6b6b"/><text x="578" y="124" fill="#1a0606" font-size="10" text-anchor="middle">G</text>
  <text x="578" y="153" fill="#9aa3b5" font-size="9" text-anchor="middle">buf 滿時等待</text>
  <text x="330" y="228" fill="#9aa3b5" font-size="11" text-anchor="middle">lock 保護；無緩衝時 sender/receiver 直接 handoff（跳過 buf）</text>
  <defs><marker id="ch" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#9aa3b5"/></marker></defs>
</svg>
```

**考官可能追問：**
- Q: channel 是 lock-free 嗎？
  - A: 否，hchan 用 mutex；但 handoff 路徑可跳過 buf
- Q: nil channel 讀寫行為？
  - A: 永久阻塞，select 中 nil channel 永不 ready

**常見陷阱 / 易錯點：**
- 向 nil channel 傳送阻塞（非 panic）
- 有緩衝 channel 認為一定非阻塞

---
### Q: select 如何實現？有多個 case ready 時怎麼選？

**核心回答：**
select 將所有 case 的 channel 按**偽隨機順序**輪詢（pollorder），避免 starvation。若多個 ready，選第一個在 pollorder 中 ready 的。無 ready 且無 default 則 G 入所有 channel 的 wait queue（single wait 最佳化只入一個）。

**深入原理：**
- selectgo 編譯器展開為 runtime.selectgo 呼叫
- default case 使 select 非阻塞
- select 與 context 取消常配合：select { case <-ctx.Done(): ... case v := <-ch: ... }

**考官可能追問：**
- Q: select 公平嗎？
  - A: 長期統計近似公平，但非嚴格 FIFO across cases
- Q: 空 select {} 會怎樣？
  - A: 永久阻塞，常用於 main 阻塞（不推薦，應等 signal）

**常見陷阱 / 易錯點：**
- select 中向 closed channel 傳送仍 panic
- case 順序影響非確定性行為

---
### Q: 關閉 channel 後讀寫行為？如何優雅關閉？

**核心回答：**
關閉 channel 後：仍可讀出 buf 剩餘元素，讀空後得零值+ok=false；再 send 會 panic。關閉應由**唯一 sender** 執行，常用 sync.Once 或 context 通知退出後 close。多 producer 用 merge 或 msg 帶 done 標記而非共享 close。

**深入原理：**
- closechan 設 closed=1，喚醒 recvq，sendq 上的 G panic
- range ch 在 close 且 drain 後退出
- happened-before：close happens before recv 零值

**考官可能追問：**
- Q: 如何判斷 channel 已關閉？
  - A: 無直接 API；用 ok := v, ok := <-ch 或 select+default 模式
- Q: 多 goroutine 誰來 close？
  - A: 約定單一 owner 或 errgroup 最後一個完成者 close

**常見陷阱 / 易錯點：**
- double close panic
- receiver close
- close 後仍有 sender 競態 panic

**實務場景：**
在行情 fan-out 中用 context 取消 + 單一 writer close，避免多 goroutine close 競態

---
### Q: map 底層實現？hash 衝突與擴容（evacuation）？

**核心回答：**
map 是 hmap + bucket 陣列，每 bucket 最多 8 個 key-value（overflow bucket 連結）。hash 低位選 bucket，高位用 tophash 快速過濾。load factor 超閾值觸發**增量擴容**：每次 GC 或寫入時搬運 1-2 個 old bucket 到 new buckets（翻倍），避免一次性 STW 大搬運。

**深入原理：**
- key 必須 comparable；NaN != NaN 導致 float key 特殊處理
- 迭代順序隨機：rand 起始 bucket + 擴容期間雙表遍歷
- delete 可能觸發 same-size 擴容整理（Go 1.12+）

**考官可能追問：**
- Q: 為什麼 map 不能併發讀寫？
  - A: 無 mutex，併發寫 corrupt 內部結構；讀+寫也可能 panic
- Q: map key 為何無序？
  - A: 故意隨機化防依賴插入順序，避免 security/測試陷阱

**常見陷阱 / 易錯點：**
- 遍歷時 delete 行為（Go 1.12+ 安全但複雜）
- 取 map 元素地址（可能因擴容失效）

---
### Q: slice 和 array 區別？append 如何增長？

**核心回答：**
array 值型別、固定長度；slice 是 header（pointer、len、cap）指向底層 array。append 若 len+cap 足夠則原地寫；否則分配新 array（<256 翻倍，≥256 約 1.25 倍 + 對齊），copy 後返回新 header。傳 slice 是 header 副本，改元素可見，append 可能不影響呼叫方。

**深入原理：**
- slice[:0] 保留 cap 可 reset 重用 buffer
- subslice 共享底層 array，修改互相可見（記憶體洩漏風險：小 slice 引用大 array）
- copy(dst, src) 按 min(len) 複製

**考官可能追問：**
- Q: 如何高效拼接字串？
  - A: strings.Builder、bytes.Buffer、預分配；+ 運算子多段會多次分配
- Q: slice 作為函式引數如何修改 len？
  - A: 需返回新 slice 或傳 *[]T / 封裝結構

**常見陷阱 / 易錯點：**
- append 後未接收返回值
- subslice 記憶體洩漏
- 併發讀寫同一 slice 無保護

---
### Q: interface 的 itab 和 eface 是什麼？

**核心回答：**
空 interface（interface{}）用 eface：type 指標 + data 指標。非空 interface 用 iface：itab（含 concrete type、fun 表）+ data。itab 快取 type pair 的方法表，實現動態分派。值接收者方法集不含 pointer receiver 方法，故 *T 才實現完整介面。

**深入原理：**
- itab 由 runtime.getitab 建立並 intern 快取
- nil interface（tab/data 皆 nil）與 typed nil（tab 非 nil, data nil）不同
- interface 賦值可能 heap allocate（逃逸）

**考官可能追問：**
- Q: iface == nil 為 false 的坑？
  - A: var p *T=nil; var i interface{}=p → i!=nil，因 tab 有型別
- Q: type assertion 失敗？
  - A: v, ok := i.(T) 或 panic

**常見陷阱 / 易錯點：**
- typed nil 判斷錯誤
- 大 interface 頻繁 boxing 分配

---
### Q: defer、panic、recover 機制與效能？

**核心回答：**
defer 將函式入 _defer 連結串列，return 前 LIFO 執行；引數在 defer 語句時求值。panic 沿棧 unwind，執行 defer，無 recover 則 crash。recover 僅在 defer 中有效，捕獲同 goroutine panic。Go 1.14+ defer 用 open-coded defer 最佳化，熱路徑開銷降低但仍非零。

**深入原理：**
- _defer 含 sp、pc、link
- panic 可多次 panic（defer 中再 panic 覆蓋）
- os.Exit 不執行 defer

**考官可能追問：**
- Q: defer 在 loop 中？
  - A: 每次迭代註冊，可能 O(n) defer 開銷；應用顯式 cleanup 或封裝函式
- Q: recover 能捕獲其他 goroutine 嗎？
  - A: 不能，每個 G 獨立 panic stack

**常見陷阱 / 易錯點：**
- recover 不在 defer 直接呼叫（需 defer func(){ recover() }()）
- 用 panic 做正常流程控制

---
### Q: context 包的設計與正確使用？

**核心回答：**
context 在 goroutine 樹傳遞 cancellation、deadline、request-scoped values。WithCancel/WithTimeout/WithDeadline 返回 ctx 與 cancel func（必須 defer cancel 防洩漏）。下游 select <-ctx.Done() 退出。Value 應只傳 request metadata，不傳可選引數。

**深入原理：**
- context 是不可變連結串列，WithValue 建立子節點
- Done channel 關閉表示取消（close 廣播）
- 不應存 struct 欄位長期持有，應沿 call chain 傳遞

**考官可能追問：**
- Q: context 取消如何傳播到 gRPC？
  - A: metadata + server interceptor 監聽 client disconnect
- Q: WithValue 執行緒安全嗎？
  - A: 只讀安全；Value key 應用自定義 unexported type 防衝突

**常見陷阱 / 易錯點：**
- 忘記 cancel 導致 timer/goroutine 洩漏
- 用 context 傳大量業務引數

**實務場景：**
在 gRPC/WebSocket 服務中將 client disconnect 透過 context 傳到 DB/Redis 查詢，避免 goroutine 洩漏

---
### Q: sync.Mutex 和 RWMutex 原理與使用場景？

**核心回答：**
Mutex 基於 CAS + semaphore（futex）實現，正常鎖 fast path 無 syscall。RWMutex 允許多 reader 或單 writer；writer 優先策略可能 starve reader（Go 1.5+ 改進）。適用保護短 critical section，勿在鎖內 IO。

**深入原理：**
- Mutex state 含 locked、woken、starving、waiter count
- 不可重入：同 G 再次 Lock 死鎖
- defer Unlock 防 panic 洩漏鎖

**考官可能追問：**
- Q: Mutex vs channel 選哪個？
  - A: 保護共享記憶體用 Mutex；編排 goroutine 協作用 channel（不要混用 Mutex 傳資料）
- Q: RWMutex 一定更快嗎？
  - A: 讀極多寫極少才划算；寫多或 critical section 短則 Mutex 更簡單

**常見陷阱 / 易錯點：**
- Lock 順序不一致死鎖
- Copy 已使用的 Mutex
- 在 RLock 中 Upgrade 到 Lock（不支援）

---
### Q: sync.WaitGroup、Once、Pool、Map 詳解？

**核心回答：**
WaitGroup 計數 goroutine 完成，Add/Done/Wait，Add 必須在 Wait 前、Done 在 defer 中。Once 保證 func 只執行一次（初始化單例）。Pool 是 per-P 本地快取的臨時物件池，GC 時可能清空，不保證 Get 命中。sync.Map 適合讀多寫少或 key 穩定分片，內部 read+dirty 雙 map。

**深入原理：**
- WaitGroup 複製 struct 會 panic
- Pool New 可選，Get 未命中時呼叫
- sync.Map LoadOrStore、Range 語義與 map 不同

**考官可能追問：**
- Q: Pool 和 free list 區別？
  - A: Pool 無固定大小，GC 清空；適合 buffer 複用減輕 alloc
- Q: sync.Map vs map+RWMutex？
  - A: 一般 map+mutex 更簡單；sync.Map 特定模式少鎖

**常見陷阱 / 易錯點：**
- WaitGroup Add 與 go 併發競態
- Pool 存帶狀態未 Reset 的物件
- sync.Map 當通用 map 濫用

**實務場景：**
例如用 errgroup+context 替代裸 WaitGroup 管理子任務生命週期

---
### Q: Go Memory Model（happens-before）？

**核心回答：**
Go 記憶體模型定義哪些讀寫 guaranteed 可見：同一 goroutine 內順序執行；channel send happens before recv完成；Once、Mutex Unlock happens before 後續 Lock；go stmt happens before goroutine 開始。無同步的共享變數讀寫是 data race。

**深入原理：**
- atomic 包提供 sequentially consistent 原子操作
- close channel happens before recv 零值
- 編譯器/CPU 重排序在 happens-before 邊界內不可見

**考官可能追問：**
- Q: volatile 在 Go 有嗎？
  - A: 無，用 sync/atomic 或 channel/Mutex
- Q: 雙重檢查鎖定在 Go？
  - A: 用 sync.Once，不要手寫 DCL

**常見陷阱 / 易錯點：**
- 以為寫 bool 一定立即可見
- 無 happens-before 的 flag 同步

---
### Q: 逃逸分析是什麼？如何影響效能？

**核心回答：**
編譯器逃逸分析決定變數分配在棧還是堆：若指標逃出函式（返回、閉包、interface、傳送到 channel），則 heap allocate。棧分配 cheap 且隨函式結束回收；堆分配增加 GC 壓力。用 go build -gcflags='-m' 檢視逃逸。

**深入原理：**
- 閉包捕獲區域性變數指標導致逃逸
- fmt.Sprintf、errors 等常導致逃逸
- 大物件可能直接 heap 分配

**考官可能追問：**
- Q: 字串轉 []byte 複製嗎？
  - A: []byte(s) 通常複製；unsafe 可零複製但有 immutability 風險
- Q: 如何減少逃逸？
  - A: 值傳遞、預分配、避免 interface{}、sync.Pool

**常見陷阱 / 易錯點：**
- 盲目 unsafe
- 忽略 -m 診斷

**實務場景：**
可結合自身服務中的 goroutine、context 與 pprof 排查經驗說明取捨。

---
### Q: 如何排查 goroutine 洩漏？

**核心回答：**
症狀：記憶體漲、goroutine 數持續增、服務變慢。工具：pprof goroutine、runtime.NumGoroutine、trace。常見原因：channel 阻塞無 receiver、忘記 ctx cancel、http.Client 無 timeout、WaitGroup 誤用。

**深入原理：**
- goroutine profile 看 stack 阻塞點
- leaktest 模式：baseline vs 壓測後 diff
- http.DefaultClient 無 timeout 是經典洩漏源

**考官可能追問：**
- Q: 如何設定 goroutine 上限？
  - A: semaphore（ buffered channel 或 weighted semaphore）、worker pool
- Q: 洩漏與 GC 關係？
  - A: G 本身佔 stack 記憶體，洩漏 G 多 → RSS 漲

**常見陷阱 / 易錯點：**
- 只重啟不查根因
- 在洩漏路徑加更多 goroutine

**實務場景：**
例如曾用 pprof goroutine profile 定位 HTTP handler 未 timeout 的第三方 API 呼叫導致堆積

---
### Q: race detector 如何使用？原理？

**核心回答：**
go test -race / go run -race 啟用 ThreadSanitizer 插樁，檢測無同步的 concurrent memory access。執行時記錄 happens-before 關係，報告 data race。生產通常關閉（5-10x 慢、10x 記憶體），CI 必開。

**深入原理：**
- 檢測 read-write、write-write 衝突
- 不保證發現所有 race（覆蓋率依賴排程）
- cgo 程式碼也可能被檢測

**考官可能追問：**
- Q: race 報告誤報？
  - A: 極少；通常真有 bug
- Q: 如何修 race？
  - A: Mutex、channel、atomic，或消除共享

**常見陷阱 / 易錯點：**
- 以為 -race 透過就無併發 bug
- 只在單測跑 race 未覆蓋生產路徑

---
### Q: Go error handling 最佳實踐？errors.Is/As/wrap？

**核心回答：**
Go 1.13+ errors.Is 判斷錯誤鏈中是否含目標，errors.As 提取 typed error，fmt.Errorf("%w") wrap 保留 cause。 sentinel errors 用 var ErrX = errors.New。業務層對映 domain error，邊界 log+wrap，避免 string compare。

**深入原理：**
- error 是 interface{ Error() string }
- panic 僅用於 programmer error / 不可恢復
- multierror 可聚合（hashicorp/go-multierror）

**考官可能追問：**
- Q: 何時 return error vs panic？
  - A: 庫 return error；main/init 可 panic；不可恢復 invariant  violation 可 panic
- Q: grpc status 如何對映？
  - A: status.Errorf + codes，client 用 status.FromError

**常見陷阱 / 易錯點：**
- err == io.EOF 在 wrap 後失效
- 吞 error
- 每層都 wrap 丟 context

---
### Q: Go generics 基礎與限制？

**核心回答：**
Go 1.18+ 引入 type parameters：[T any]、constraints（comparable、constraints.Ordered 或自定義 interface）。編譯期單態化（monomorphization）生成具體型別程式碼。不支援泛型方法（僅泛型型別/函式）、無預設型別引數、無 specialization。

**深入原理：**
- type set 定義 constraint
- any = interface{}
- 泛型減少 interface{} 與 reflection

**考官可能追問：**
- Q: 泛型 vs interface{}
  - A: 泛型 compile-time 型別安全零 boxing；interface 執行時 dispatch
- Q: 何時不用泛型？
  - A: 簡單程式碼、僅一處使用、constraint 過於複雜

**常見陷阱 / 易錯點：**
- 過度抽象
- constraint 設計過大失去型別資訊

---
### Q: 併發安全 Map 如何實現？（interview-go q010/q011）

**核心回答：**
方案：sync.RWMutex+map、sync.Map、分片 map（shard by hash）。阻塞讀場景：用 channel 通知或 sync.Cond。高併發讀寫：分片減鎖競爭，每 shard 獨立 RWMutex。

**深入原理：**
- sync.Map 的 miss 路徑加鎖寫 dirty
- Copy-on-read 快照適合讀多
- atomic.Value 存 immutable map 替換

**考官可能追問：**
- Q: 讀阻塞直到 key 出現？
  - A: 單 key 用 chan 或 pub/sub；全域用 Cond+map
- Q: map fatal error concurrent？
  - A: runtime 檢測到直接 crash，無法 recover

**常見陷阱 / 易錯點：**
- range map 同時寫
- sync.Map 存指標 mutable 物件無保護

---
### Q: closed channel 讀寫會怎樣？（interview-go q018）

**核心回答：**
向 closed channel send → panic。從 closed channel recv → 先讀完 buf，之後零值+ok=false，不 panic。從 nil channel recv/send → 永久阻塞。close(nil) → panic。

**深入原理：**
- for v := range ch 在 close 後自動結束
- select 向 closed ch send 仍 panic
- 檢測 close 只能 recv side 用 ok

**考官可能追問：**
- Q: 如何 broadcast？
  - A: close channel 或 context.Done()
- Q: 多消費者 drain？
  - A: 每個 consumer range 同一 ch，元素只會一人消費

**常見陷阱 / 易錯點：**
- sender 不知道 receiver 已退出仍 send
- 用 close 作計數訊號誤用

---
### Q: HTTP 包記憶體洩漏常見場景？（interview-go q021）

**核心回答：**
經典洩漏：resp, err := client.Do(req) 後未 io.Copy(io.Discard, resp.Body) 且未 Close Body，連線無法歸還連線池。應用 defer resp.Body.Close() 並讀完 body。Client 需設定 Timeout 或 context。

**深入原理：**
- Transport MaxIdleConns 等池化引數
- CancelRequest 已廢棄，用 context
- handler 中 goroutine 未隨 request 結束退出

**考官可能追問：**
- Q: 如何限制連線數？
  - A: Transport.MaxConnsPerHost
- Q: pprof 如何定位？
  - A: goroutine stack 見 io.ReadAll 或 time.Sleep 在 handler 洩漏路徑

**常見陷阱 / 易錯點：**
- 只用 DefaultClient
- Close 但不 Drain body

**實務場景：**
例如曾修復第三方 API 呼叫洩漏：context timeout + body drain + connection pool 調優

---
### Q: CSP 模型與 Go channel 的設計哲學？

**核心回答：**
CSP（Communicating Sequential Processes）主張透過通訊共享記憶體，而非共享記憶體來通訊。Go channel 是 CSP 的實現：goroutine 透過 send/recv 同步與傳遞資料，減少顯式鎖。

**深入原理：**
- channel 同步：unbuffered send/recv rendezvous
- select 多路複用
- mutex 仍用於保護共享 state，與 channel 互補

**考官可能追問：**
- Q: 何時不用 channel？
  - A: 簡單 counter、performance critical 熱路徑、需隨機訪問結構
- Q: actor vs CSP？
  - A: actor mailbox 非同步；CSP channel 可同步 handoff

**常見陷阱 / 易錯點：**
- 用 channel 實現複雜共享狀態
- 無 buffer 導致死鎖

---
### Q: 排程陷阱：GOMAXPROCS 與 cgo/blocking syscall？

**核心回答：**
長時間 cgo 或 syscall 阻塞 M，P 可能 detach 給其他 M。若所有 M 阻塞，其他 G 無法執行（除 sysmon 補救）。Net 只阻塞當前 thread，但 file IO 等可能 block OS thread。

**深入原理：**
- runtime.LockOSThread 將 G 綁 M，減少排程但可能浪費
- 網路 IO 用 netpoller 非同步
- 檔案 IO 考慮 io_uring 或 thread pool（Go 1.XX 演進）

**考官可能追問：**
- Q: 容器 CPU throttling 影響？
  - A: P 認為有 N 核但實際 throttle → 排程延遲增
- Q: 如何檢測 syscall 阻塞？
  - A: trace / schedtrace / GODEBUG=scheddetail=1

**常見陷阱 / 易錯點：**
- 在熱路徑大量 cgo
- LockOSThread 濫用

---
### Q: sync/atomic 與 Mutex 如何選擇？

**核心回答：**
atomic 適用於簡單 counter、flag、pointer swap 等無複合 invariant 的場景。Mutex 保護多欄位 invariant。Go 1.19+ atomic 支援 typed atomic.Int64 等。

**深入原理：**
- atomic 提供 happens-before
- CAS loop 實現 lock-free stack/queue（複雜）
- false sharing：padding 熱 atomic 欄位

**考官可能追問：**
- Q: atomic.Value 用法？
  - A: Store immutable config snapshot，Load 無鎖讀
- Q: ABA 問題？
  - A: Go GC 管理記憶體的 lock-free 結構需考慮，一般用 hazard pointer 或 GC 友好設計

**常見陷阱 / 易錯點：**
- atomic 保護多欄位不一致
- 混合 atomic 與 non-atomic 讀寫同一變數

---
### Q: go mod 依賴管理與 vendor？

**核心回答：**
go.mod 宣告 module path 與 require；go.sum 校驗 hash。MVS（Minimal Version Selection）選最低相容版本。vendor/ 可離線構建。replace 用於 fork 或本地路徑。

**深入原理：**
- go work 多 module 開發
- private module GOPRIVATE
- semver tag 規範

**考官可能追問：**
- Q: 依賴衝突怎麼解？
  - A: go mod graph、upgrade、replace、或拆 interface
- Q: vendor 何時用？
  - A: CI  reproducibility、air-gapped build

**常見陷阱 / 易錯點：**
- commit 無 go.sum
- replace 進 production 未文件化

---
### Q: pprof 在 Go 效能調優中的使用？

**核心回答：**
import _ net/http/pprof 或 go tool pprof。型別：cpu、heap、goroutine、mutex、block。看 flat vs cum，火焰圖找 hot path。配合 trace 看 latency 與 GC。

**深入原理：**
- alloc_space vs inuse_space
- cum 高但 flat 低 → 呼叫鏈深處
- benchstat 對比最佳化前後

**考官可能追問：**
- Q: 生產如何採 profile？
  - A: 短視窗、取樣率、安全埠
- Q: CPU 100% 但 pprof 空？
  - A: 可能在 cgo/核心/或未採 long enough

**常見陷阱 / 易錯點：**
- 只看 CPU 不看 alloc
- 最佳化非 hot path

**實務場景：**
例如用 pprof + flame graph 最佳化 K 線路徑與第三方 HTTP 瓶頸

---
### Q: errgroup 與 context 組合模式？

**核心回答：**
golang.org/x/sync/errgroup：Group.Go 啟動子任務，Wait 等待全部完成，任一 error 取消 context（WithContext 版本）。適合 parallel fetch、pipeline fan-out，統一錯誤與取消。

**深入原理：**
- SetLimit(n) 限制併發
- 與 WaitGroup 區別：內建 error 傳播
- cancel 後子 goroutine 應 respect ctx

**考官可能追問：**
- Q: errgroup vs worker pool？
  - A: errgroup 動態任務；pool 固定 worker 複用
- Q: 第一個 error 後其他任務？
  - A: 應檢測 ctx.Done 提前退出

**常見陷阱 / 易錯點：**
- 不用 WithContext 版無法聯動 cancel
- 子任務 ignore ctx

---
### Q: Go 程式啟動流程（runtime 初始化）？

**核心回答：**
OS 載入 → runtime 初始化（sched、memory、GOMAXPROCS）→ main.main。init 函式按 import 順序執行。runtime.main 建立 main goroutine 呼叫 user main。

**深入原理：**
- import cycle 禁止
- init 不應 heavy 或依賴 order
- race detector 在 runtime 之後啟用

**考官可能追問：**
- Q: init 能 panic 嗎？
  - A: 能，程式退出
- Q: 包級 var 初始化順序？
  - A: 依賴 declaration order 與 init

**常見陷阱 / 易錯點：**
- init 中網路/DB
- import side effect 難測

---
### Q: for 迴圈變數捕獲問題（Go 1.22 前後差異）？

**核心回答：**
Go 1.22 以前，for 迴圈變數在整個迴圈共用同一份位址，經典 bug：`for _, v := range s { go func(){ use(v) }() }` 所有 goroutine 看到同一個（通常是最後一個）v。修正：迴圈內 `v := v` 複製，或把 v 當引數傳入閉包。Go 1.22 起改為**每次迭代新建迴圈變數**，此陷阱在新版預設消失，但跨版本相容仍需注意。

**深入原理：**
- 1.22 前：i、v 在迴圈作用域只有一份，閉包捕獲的是變數位址而非當下值
- 經典觸發點：goroutine、defer、把 &v 加入 slice
- 1.22 後語義由 go.mod 宣告的 go 版本決定（go 1.22+ 才啟用新 loopvar）

**考官可能追問：**
- Q: 為什麼 1.22 前要寫 v := v？
  - A: 建立 per-iteration 副本，讓每個閉包捕獲各自獨立的變數
- Q: go.mod 寫 go 1.21 但用 1.22 工具鏈編譯？
  - A: 語言語義以 go.mod 版本為準，仍用舊 loopvar 行為，避免隨工具鏈漂移

**常見陷阱 / 易錯點：**
- 1.21 以前在 range 迴圈啟動 goroutine 未複製變數
- 誤以為所有專案都已是新語義（取決於 go.mod）
- 對迴圈變數取位址 &v 全部指向同一元素

**實務場景：**
行情 fan-out 啟動大量 goroutine 時，注意 loopvar 捕獲，避免所有 worker 都處理同一個 symbol

---
### Q: 手寫一個帶限流的 worker pool（Go coding）？

**核心回答：**
固定 n 個 goroutine 從同一個 jobs channel 消費，channel 關閉即優雅退出，用 WaitGroup 等待全部結束。需要並發上限/錯誤傳播/取消時，優先用 errgroup.WithContext + SetLimit。

```go
func WorkerPool(jobs <-chan Job, n int) {
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := range jobs { // jobs 關閉後迴圈自動結束
                process(j)
            }
        }()
    }
    wg.Wait()
}
```

**深入原理：**
- n 依 CPU/IO 特性調整：CPU-bound 約 runtime.NumCPU()，IO-bound 可更大
- errgroup.WithContext + SetLimit(n)：同時得到並發上限、錯誤傳播與取消
- semaphore 寫法：sem := make(chan struct{}, n)，進入前 sem<-struct{}{}，結束 <-sem

**考官可能追問：**
- Q: 如何收集每個 job 的結果？
  - A: 另開 results channel，或用 errgroup + 預分配 slice 各寫各的 index 避免鎖
- Q: 如何支援取消？
  - A: 傳入 context，worker 內 select{ case <-ctx.Done(): return; case j, ok := <-jobs: ... }

**常見陷阱 / 易錯點：**
- 忘記 close(jobs) 導致 worker 永遠阻塞（goroutine 洩漏）
- worker 內共享 slice 未加鎖造成 data race
- panic 未 recover 拖垮整個 pool

**實務場景：**
交易/行情繫統，避免無限 go func() 造成 OOM

---
### Q: 如何合併多個 channel（fan-in / merge）？（Go coding）

**核心回答：**
每個輸入 channel 各起一個 goroutine 把值寫到共用 out；另起一個 goroutine 等所有來源結束後 close(out)，讓下游 range 正常退出。Go 1.22 前需把 c 當引數傳入，避免迴圈變數捕獲。

```go
func Merge(chans ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    for _, c := range chans {
        wg.Add(1)
        go func(c <-chan int) {
            defer wg.Done()
            for v := range c {
                out <- v
            }
        }(c)
    }
    go func() { wg.Wait(); close(out) }()
    return out
}
```

**深入原理：**
- fan-out：多 worker 從同一 channel 讀；fan-in：多來源匯入一個 channel
- 需取消時加 context，select 寫入 out 與 <-ctx.Done()
- close(out) 必須在所有 sender 結束後，否則 send on closed channel 會 panic

**考官可能追問：**
- Q: 如何避免下游慢造成阻塞？
  - A: out 加 buffer，或 select+ctx 丟棄，配合背壓策略
- Q: LMAX Disruptor 與 channel fan-in 差異？
  - A: Disruptor 用 ring buffer 單寫多讀、無鎖序號、低延遲；channel 有 mutex 與排程開銷

**常見陷阱 / 易錯點：**
- 在所有 sender 結束前 close(out)
- Go 1.22 前未傳參導致所有 goroutine 讀同一個 c

**實務場景：**
高吞吐資料管線管線把多來源事件 fan-in 後再分類處理，思路類似 Disruptor 但以 channel/goroutine 實作

---

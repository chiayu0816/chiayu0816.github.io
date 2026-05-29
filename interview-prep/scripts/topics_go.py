# -*- coding: utf-8 -*-
"""Go interview topics - 35 comprehensive Q&A."""

GO_TOPICS = [
    {
        "q": "什麼是 GMP 模型？G、P、M 各自負責什麼？",
        "core": "Go runtime 使用 M:N 調度：G（goroutine）是使用者態協程，保存執行棧與寄存器現場；M（machine）是 OS 線程，真正在 CPU 上跑；P（processor）是邏輯處理器，持有本地 run queue 與 mcache，M 必須綁定 P 才能執行 G。P 的數量由 GOMAXPROCS 決定，通常等於 CPU 核心數。",
        "dive": [
            "G 結構含 stack、sched（gobuf 存 sp/pc）、status、m（綁定線程）、preempt 搶占標誌",
            "P 維護 runq（256 長度環形隊列）、runnext（下一個優先 G）、mcache（本地 span 快取，減少全局 mcentral 鎖競爭）",
            "M 在無 P 時阻塞在 sched.midle，syscall 阻塞時 M 可能與 P 解綁，P 可轉給其他 M 繼續跑 G",
            "全局 runq 由 sched.lock 保護，本地 runq 滿時將一半 G 轉移到全局",
        ],
        "followups": [
            ("為什麼需要 P 這一層，不直接用 M 調度 G？", "P 提供 per-P 本地隊列與 mcache，避免所有 G 競爭單一全局隊列和全局 heap 鎖；M 數量可大於 P（syscall 阻塞時），但同時只有 GOMAXPROCS 個 P 在跑 user code"),
            ("GOMAXPROCS 設多少合適？", "預設 = CPU 核心數；CPU-bound 保持預設；IO-bound 可略增但過多 P 增加調度開銷；容器內需配合 cgroup CPU quota 設定"),
        ],
        "pitfalls": ["混淆 M 數量與 goroutine 數量", "在 init 或 runtime.LockOSThread 後長期佔用 M", "以為 GOMAXPROCS=1 就完全串行（sysmon 與 GC 仍可能介入）"],
        "svg": """
<svg viewBox="0 0 660 330" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GMP 調度模型：P 持有本地佇列，綁定 M，Work Stealing 平衡負載">
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
  <text x="167" y="207" fill="#54dd9b" font-size="12" text-anchor="middle">M0 · OS thread（綁定 P0）</text>
  <rect x="358" y="180" width="270" height="44" rx="8" fill="#0d1017" stroke="#54dd9b" stroke-width="1.5"/>
  <text x="493" y="207" fill="#54dd9b" font-size="12" text-anchor="middle">M1 · OS thread（綁定 P1）</text>
  <rect x="32" y="256" width="596" height="48" rx="8" fill="#0d1017" stroke="#6b7385" stroke-width="1.5" stroke-dasharray="5 4"/>
  <text x="330" y="285" fill="#9aa3b5" font-size="12" text-anchor="middle">全域 run queue（sched.lock 保護，本地滿時溢出一半）</text>
  <path d="M358 96 Q330 96 304 96" fill="none" stroke="#c79cff" stroke-width="1.6" stroke-dasharray="4 3" marker-end="url(#ar)"/>
  <text x="330" y="30" fill="#c79cff" font-size="11" text-anchor="middle">steal n/2</text>
  <defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0 0 L7 3 L0 6 z" fill="#c79cff"/></marker></defs>
</svg>
""".strip(),
        "resume": "在加密貨幣交易所的行情與訂單處理場景中，會用大量 goroutine，理解 GMP 後可避免在熱路徑阻塞 M（長 syscall），並用 worker pool 控制 goroutine 數量。",
    },
    {
        "q": "什麼是 Work Stealing？何時觸發？",
        "core": "當某 P 的本地 runq 為空而全局 runq 也無 G 時，該 P 會從其他 P 的 runq **偷取一半** G 來執行，以平衡負載。偷取從隨機 P 開始，減少競爭。這是 Go 調度器保持 CPU 飽和的核心機制。",
        "dive": [
            "runSteal 在 schedule 循環中：先查本地 runq → 全局 runq → network poll → 再 steal",
            "偷取時一次性搬運 n/2 個 G（至少 1 個），降低頻繁偷取的开銷",
            "timer 到期也會喚醒 P 處理 timer heap 上的 G",
        ],
        "followups": [
            ("Work Stealing 和 Fork-Join 線程池有何不同？", "Go 是協作式 M:N 調度，stealing 在 P 之間自動發生；傳統線程池通常固定 queue，需手動分片或 work queue 設計"),
            ("為什麼不從全局隊列優先取？", "全局隊列有鎖，高併發下成為瓶頸；本地隊列無鎖（或低競爭），stealing 只在本地空閒時才做"),
        ],
        "pitfalls": ["以為 goroutine 會均勻分配到所有 P（實際取決於創建時的 P 與 stealing）", "短生命週期大量 G 仍可能造成調度開銷"],
        "resume": "體育數據 LMAX Disruptor 并行管線與 Go goroutine pool 類似思路：本地優先、必要時再平衡。",
    },
    {
        "q": "sysmon 是什麼？做了哪些事？",
        "core": "sysmon 是 runtime 啟動的**不需要 P 的後台 M**，週期性（約 10ms+）執行：retake 長時間佔用 P 的 M、檢查 netpoll、觸發 GC、搶占長時間運行的 G（Go 1.14+ 異步搶占）。它是調度器「自救」機制，防止某 G 餓死其他 G。",
        "dive": [
            "retake：syscall 超過 10ms 的 P 可能被標記，M 與 P 分離後 P 可被其他 M 使用",
            "netpoll：將 epoll/kqueue 就绪的 fd 對應 G 放入 runq",
            "forcegc：若超過 2 分鐘未 GC 且環境變數允許，可觸發",
            "搶占：向 G 的 stack guard 注入 preempt 信號，safe point 處切換",
        ],
        "followups": [
            ("sysmon 會增加 CPU 開銷嗎？", "週期性喚醒但大部分時間 sleep；開銷通常可忽略，極端高 QPS 場景可 profile 確認"),
            ("沒有 sysmon 會怎樣？", "network fd 可能延遲喚醒、長時間 CPU 循環的 G 無法被搶占（Go 1.13 及以前）"),
        ],
        "pitfalls": ["以為 goroutine 一定公平（無 sysmon 搶占時 CPU 密集 G 可餓死 others）", "LockOSThread + 死循環會卡死一個 M"],
    },
    {
        "q": "Go 1.14+ 的搶占（preemption）如何運作？",
        "core": "Go 1.14 前僅在函數調用邊界（sync safe point）協作式讓出；1.14+ 引入**異步搶占**：sysmon 或 GC 向 G 棧注入 preempt 請求，signal handler 或 stack guard 觸發，在 safe point 暫停 G 重新調度。解決 tight loop 不調用函數時無法搶占的問題。",
        "dive": [
            "G.preempt 標誌 + stackguard0 = stackPreempt 觸發 stack growth 檢查路徑進入調度",
            "非協作式路徑：向 M 發 signal（SIGURG），在 signal stack 上修改 G 的 PC 到調度入口",
            "cgo、部分 runtime 路徑仍可能延遲搶占",
        ],
        "followups": [
            ("搶占對延遲有何影響？", "被搶占 G 需等到 safe point，通常微秒～毫秒級；對 p99 延遲敏感服務需避免超大 critical section"),
            ("和 Java 搶占式線程調度比？", "Go 仍是 user-level scheduling，搶占粒度在 G 而非 OS 線程，切換成本更低"),
        ],
        "pitfalls": ["以為 for{} 永遠無法被搶占（1.14+ 可以）", "在無函數調用的循環中仍假設其他 G 會立即運行"],
    },
    {
        "q": "goroutine 和 OS 線程有什麼區別？",
        "core": "goroutine 是 Go runtime 調度的輕量協程，初始棧約 2KB（可擴展至 GB），創建/切換成本遠低於 OS 線程（MB 級棧、內核態切換）。Go 用少量 M 承載大量 G（M:N），由 runtime 而非內核調度。",
        "dive": [
            "G 棧是連續可 grow/shrink 的 stack，溢出時 copy 到新更大 stack（非 guard page segfault 為主）",
            "M 數量預設無硬上限但通常 ≈ P + 阻塞 syscall 的 M",
            "runtime.GOMAXPROCS 控制並行度，非 goroutine 數量",
        ],
        "followups": [
            ("一個進程能創建多少 goroutine？", "受記憶體限制，每 G 至少 stack + 結構開銷；百萬級可行但需控制 stack 使用"),
            ("goroutine 會映射到固定線程嗎？", "預設不會；runtime.LockOSThread() 可綁定 G 到 M"),
        ],
        "pitfalls": ["無限制 go func() 導致 OOM", "把 goroutine 當免費無限資源"],
        "resume": "實務上用 goroutine 處理行情推送，同時用 pprof goroutine profile 監控數量異常。",
    },
    {
        "q": "Go GC 使用什麼演算法？三色標記如何運作？",
        "core": "Go 1.5+ 使用**非分代、非壓縮**的並發三色標記-清除（mark-sweep）。白色=未訪問，灰色=已訪問但子未掃完，黑色=已掃完。從 roots（goroutine stack、全局變量）出發標記，最後清除白色物件。大部分 mark 與 mutator 並發執行。",
        "dive": [
            "write barrier（混合寫屏障）：標記階段插入屏障，確保「黑色物件不指向白色物件」或等價不變式",
            "mark assist：分配過快的 G 需協助 mark，避免 heap 增長快於 GC",
            "無分代：每次 GC 掃描整個 heap（對小物件多、生命週期短場景可能不如分代 GC）",
        ],
        "followups": [
            ("為什麼 Go 不用分代 GC？", "簡化 runtime、降低 STW 與 barrier 複雜度；trade-off 是短生命物件可能增加 mark 工作量"),
            ("三色標記的漏標問題如何解決？", "寫屏障 + STW 短暫重新掃描 roots/stack；或 SATB/deletion barrier 變體"),
        ],
        "pitfalls": ["以為 GC 完全無 STW", "忽略 mark assist 導致 mutator 變慢"],
        "svg": """
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
""".strip(),
        "resume": "K 線快取重構時用 pprof alloc_space 觀察 GC 壓力，減少高頻路徑短生命物件分配。",
    },
    {
        "q": "Go GC 的 STW 階段有哪些？還嚴重嗎？",
        "core": "並發 GC 仍有短暫 STW：**mark setup**（停止所有 P，開啟 write barrier）、**mark termination**（等待 mark worker 完成、關 barrier、清理）、**sweep termination**（可選）。Go 1.8+ 典型 STW 在百微秒～低毫秒，遠小於早期版本。",
        "dive": [
            "stopTheWorld：每 P 的 M 在 safe point 停住，記錄 stack roots",
            "GOGC 預設 100：heap 翻倍觸發下一輪 GC",
            "GODEBUG=gctrace=1 可觀察每輪 GC 時間與 heap 大小",
        ],
        "followups": [
            ("如何降低 GC 延遲？", "減少分配（sync.Pool、預分配 buffer）、控制 GOGC、避免超大 pointer-rich heap"),
            ("STW 和 P99 延遲的關係？", "STW 期間所有 mutator 暫停，直接推高 latency tail；需用 trace 關聯"),
        ],
        "pitfalls": ["只調 GOGC 不減 allocation", "在 latency 敏感路徑大量 alloc"],
    },
    {
        "q": "write barrier 是什麼？為什麼需要？",
        "core": "並發 mark 時 mutator 仍在修改 pointer graph，可能出現「黑色物件新指向白色物件」導致漏標。write barrier 在 pointer 寫入時插入 runtime 代碼，將相關白色或灰色物件標記，維持三色不變式。Go 使用 hybrid write barrier（Yuasa + Dijkstra 混合）。",
        "dive": [
            "編譯器在 *ptr = src 等寫入點插入 wbBuf 記錄",
            "GC 後期 flush wbBuf 批量處理",
            "barrier 僅在 GC mark 階段啟用，平時無開銷",
        ],
        "followups": [
            ("write barrier 性能影響？", "mark 期間每次 pointer write 有額外指令，通常 10-30% mutator 慢速，換取更短 STW"),
            ("和 Java G1 的 SATB 比？", "思路類似：記錄寫入以保證快照或增量標記正確性，實現細節不同"),
        ],
        "pitfalls": ["以為 GC 全程無 barrier 開銷", "unsafe 繞過 barrier 可能破壞 GC（需極度小心）"],
    },
    {
        "q": "GOGC 和 GOMEMLIMIT 如何調優？",
        "core": "GOGC 控制 GC 觸發閾值：新 heap 大小達 live heap 的 (100+GOGC)% 時觸發（預設 100=翻倍）。Go 1.19+ GOMEMLIMIT 設定 soft memory limit，runtime 會更積極 GC 以避免 OOM，適合容器環境。",
        "dive": [
            "GOGC=off 禁用 GC（僅特殊場景）",
            "GOMEMLIMIT 與 cgroup memory.limit 配合，避免被 OOM killer 殺",
            "trade-off：更低 GOGC → 更頻繁 GC、更低 RSS、更高 CPU",
        ],
        "followups": [
            ("容器 memory limit 512Mi 怎麼設？", "GOMEMLIMIT≈450MiB 留 buffer，GOGC 預設或略降視 CPU 而定"),
            ("如何觀察 GC 是否成為瓶頸？", "gctrace、runtime/metrics、trace 的 GC 事件、alloc_rate"),
        ],
        "pitfalls": ["GOMEMLIMIT 設等於 hard limit 無 buffer", "只看 RSS 不看 GC CPU fraction"],
    },
    {
        "q": "channel 底層 hchan 結構是什麼？",
        "core": "channel 底層是 runtime.hchan：含 qcount（元素數）、dataqsiz（容量）、buf 環形佇列、sendx/recvx 索引、sendq/recvq（sudog 等待鏈表）、lock。有緩衝 channel 先寫 buf；無緩衝需 direct handoff（G 直接交換數據）。",
        "dive": [
            "sudog 包裝等待的 G 與 element 指針",
            "close 時喚醒所有 recv waiters，send waiters panic",
            "elem size 決定 buf 元素步長，由 makechan 分配",
        ],
        "followups": [
            ("channel 是 lock-free 嗎？", "否，hchan 用 mutex；但 handoff 路徑可跳過 buf"),
            ("nil channel 讀寫行為？", "永久阻塞，select 中 nil channel 永不 ready"),
        ],
        "pitfalls": ["向 nil channel 發送阻塞（非 panic）", "有緩衝 channel 認為一定非阻塞"],
        "svg": """
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
""".strip(),
    },
    {
        "q": "select 如何實現？有多個 case ready 時怎麼選？",
        "core": "select 將所有 case 的 channel 按**偽隨機順序**輪詢（pollorder），避免 starvation。若多個 ready，選第一個在 pollorder 中 ready 的。無 ready 且無 default 則 G 入所有 channel 的 wait queue（single wait 優化只入一個）。",
        "dive": [
            "selectgo 編譯器展開為 runtime.selectgo 調用",
            "default case 使 select 非阻塞",
            "select 與 context 取消常配合：select { case <-ctx.Done(): ... case v := <-ch: ... }",
        ],
        "followups": [
            ("select 公平嗎？", "長期統計近似公平，但非嚴格 FIFO across cases"),
            ("空 select {} 會怎樣？", "永久阻塞，常用於 main 阻塞（不推薦，應等 signal）"),
        ],
        "pitfalls": ["select 中向 closed channel 發送仍 panic", "case 順序影響非確定性行為"],
    },
    {
        "q": "關閉 channel 後讀寫行為？如何優雅關閉？",
        "core": "關閉 channel 後：仍可讀出 buf 剩餘元素，讀空後得零值+ok=false；再 send 會 panic。關閉應由**唯一 sender** 執行，常用 sync.Once 或 context 通知退出後 close。多 producer 用 merge 或 msg 帶 done 標記而非共享 close。",
        "dive": [
            "closechan 設 closed=1，喚醒 recvq，sendq 上的 G panic",
            "range ch 在 close 且 drain 後退出",
            "happened-before：close happens before recv 零值",
        ],
        "followups": [
            ("如何判斷 channel 已關閉？", "無直接 API；用 ok := v, ok := <-ch 或 select+default 模式"),
            ("多 goroutine 誰來 close？", "約定單一 owner 或 errgroup 最後一個完成者 close"),
        ],
        "pitfalls": ["double close panic", "receiver close", "close 後仍有 sender 競態 panic"],
        "resume": "在行情 fan-out 中用 context 取消 + 單一 writer close，避免多 goroutine close 競態。",
    },
    {
        "q": "map 底層實現？hash 衝突與擴容（evacuation）？",
        "core": "map 是 hmap + bucket 陣列，每 bucket 最多 8 個 key-value（overflow bucket 鏈接）。hash 低位選 bucket，高位用 tophash 快速過濾。load factor 超阈值觸發**增量擴容**：每次 GC 或寫入時搬運 1-2 個 old bucket 到 new buckets（翻倍），避免一次性 STW 大搬運。",
        "dive": [
            "key 必須 comparable；NaN != NaN 導致 float key 特殊處理",
            "迭代順序隨機：rand 起始 bucket + 擴容期間雙表遍歷",
            "delete 可能觸發 same-size 擴容整理（Go 1.12+）",
        ],
        "followups": [
            ("為什麼 map 不能并发读写？", "無 mutex，并发写 corrupt 內部結構；读+写也可能 panic"),
            ("map key 為何無序？", "故意隨機化防依赖插入順序，避免 security/測試陷阱"),
        ],
        "pitfalls": ["遍歷時 delete 行為（Go 1.12+ 安全但複雜）", "取 map 元素地址（可能因擴容失效）"],
    },
    {
        "q": "slice 和 array 區別？append 如何增長？",
        "core": "array 值類型、固定長度；slice 是 header（pointer、len、cap）指向底層 array。append 若 len+cap 足夠則原地寫；否則分配新 array（<256 翻倍，≥256 約 1.25 倍 + 對齊），copy 後返回新 header。傳 slice 是 header 副本，改元素可見，append 可能不影響調用方。",
        "dive": [
            "slice[:0] 保留 cap 可 reset 重用 buffer",
            "subslice 共享底層 array，修改互相可見（內存泄漏風險：小 slice 引用大 array）",
            "copy(dst, src) 按 min(len) 複製",
        ],
        "followups": [
            ("如何高效拼接字符串？", "strings.Builder、bytes.Buffer、預分配；+ 運算符多段會多次分配"),
            ("slice 作為函數參數如何修改 len？", "需返回新 slice 或傳 *[]T / 封裝結構"),
        ],
        "pitfalls": ["append 後未接收返回值", "subslice 內存泄漏", "并发读写同一 slice 無保護"],
    },
    {
        "q": "interface 的 itab 和 eface 是什麼？",
        "core": "空 interface（interface{}）用 eface：type 指針 + data 指針。非空 interface 用 iface：itab（含 concrete type、fun 表）+ data。itab 快取 type pair 的方法表，實現動態分派。值接收者方法集不含 pointer receiver 方法，故 *T 才實現完整接口。",
        "dive": [
            "itab 由 runtime.getitab 創建並 intern 快取",
            "nil interface（tab/data 皆 nil）与 typed nil（tab 非 nil, data nil）不同",
            "interface 賦值可能 heap allocate（逃逸）",
        ],
        "followups": [
            ("iface == nil 為 false 的坑？", "var p *T=nil; var i interface{}=p → i!=nil，因 tab 有類型"),
            ("type assertion 失敗？", "v, ok := i.(T) 或 panic"),
        ],
        "pitfalls": ["typed nil 判斷錯誤", "大 interface 頻繁 boxing 分配"],
    },
    {
        "q": "defer、panic、recover 機制與性能？",
        "core": "defer 將函數入 _defer 鏈表，return 前 LIFO 執行；參數在 defer 語句時求值。panic 沿棧 unwind，執行 defer，無 recover 則 crash。recover 僅在 defer 中有效，捕獲同 goroutine panic。Go 1.14+ defer 用 open-coded defer 優化，熱路徑開銷降低但仍非零。",
        "dive": [
            "_defer 含 sp、pc、link",
            "panic 可多次 panic（defer 中再 panic 覆蓋）",
            "os.Exit 不執行 defer",
        ],
        "followups": [
            ("defer 在 loop 中？", "每次迭代注册，可能 O(n) defer 開銷；应用显式 cleanup 或封装函数"),
            ("recover 能捕獲其他 goroutine 吗？", "不能，每个 G 独立 panic stack"),
        ],
        "pitfalls": ["recover 不在 defer 直接调用（需 defer func(){ recover() }()）", "用 panic 做正常流程控制"],
    },
    {
        "q": "context 包的设计与正确使用？",
        "core": "context 在 goroutine 树传递 cancellation、deadline、request-scoped values。WithCancel/WithTimeout/WithDeadline 返回 ctx 与 cancel func（必须 defer cancel 防泄漏）。下游 select <-ctx.Done() 退出。Value 应只传 request metadata，不传可选参数。",
        "dive": [
            "context 是不可变链表，WithValue 创建子节点",
            "Done channel 关闭表示取消（close 广播）",
            "不应存 struct 字段长期持有，应沿 call chain 传递",
        ],
        "followups": [
            ("context 取消如何传播到 gRPC？", "metadata + server interceptor 监听 client disconnect"),
            ("WithValue 线程安全吗？", "只读安全；Value key 应用自定义 unexported type 防冲突"),
        ],
        "pitfalls": ["忘记 cancel 导致 timer/goroutine 泄漏", "用 context 传大量业务参数"],
        "resume": "在 gRPC/WebSocket 服务中将 client disconnect 通过 context 传到 DB/Redis 查询，避免 goroutine 泄漏。",
    },
    {
        "q": "sync.Mutex 和 RWMutex 原理与使用场景？",
        "core": "Mutex 基于 CAS + semaphore（futex）实现，正常锁 fast path 无 syscall。RWMutex 允许多 reader 或单 writer；writer 优先策略可能 starve reader（Go 1.5+ 改进）。适用保护短 critical section，勿在锁内 IO。",
        "dive": [
            "Mutex state 含 locked、woken、starving、waiter count",
            "不可重入：同 G 再次 Lock 死锁",
            "defer Unlock 防 panic 泄漏锁",
        ],
        "followups": [
            ("Mutex vs channel 选哪个？", "保护共享内存用 Mutex；编排 goroutine 协作用 channel（不要混用 Mutex 传数据）"),
            ("RWMutex 一定更快吗？", "读极多写极少才划算；写多或 critical section 短则 Mutex 更简单"),
        ],
        "pitfalls": ["Lock 顺序不一致死锁", "Copy 已使用的 Mutex", "在 RLock 中 Upgrade 到 Lock（不支持）"],
    },
    {
        "q": "sync.WaitGroup、Once、Pool、Map 详解？",
        "core": "WaitGroup 计数 goroutine 完成，Add/Done/Wait，Add 必须在 Wait 前、Done 在 defer 中。Once 保证 func 只执行一次（初始化单例）。Pool 是 per-P 本地缓存的临时对象池，GC 时可能清空，不保证 Get 命中。sync.Map 适合读多写少或 key 稳定分片，内部 read+dirty 双 map。",
        "dive": [
            "WaitGroup 复制 struct 会 panic",
            "Pool New 可选，Get 未命中时调用",
            "sync.Map LoadOrStore、Range 语义与 map 不同",
        ],
        "followups": [
            ("Pool 和 free list 区别？", "Pool 无固定大小，GC 清空；适合 buffer 复用减轻 alloc"),
            ("sync.Map vs map+RWMutex？", "一般 map+mutex 更简单；sync.Map 特定模式少锁"),
        ],
        "pitfalls": ["WaitGroup Add 与 go 并发竞态", "Pool 存带状态未 Reset 的对象", "sync.Map 当通用 map 滥用"],
        "resume": "實務上用 errgroup+context 替代裸 WaitGroup 管理子任务生命周期。",
    },
    {
        "q": "Go Memory Model（happens-before）？",
        "core": "Go 内存模型定义哪些读写 guaranteed 可见：同一 goroutine 内顺序执行；channel send happens before recv完成；Once、Mutex Unlock happens before 后续 Lock；go stmt happens before goroutine 开始。无同步的共享变量读写是 data race。",
        "dive": [
            "atomic 包提供 sequentially consistent 原子操作",
            "close channel happens before recv 零值",
            "编译器/CPU 重排序在 happens-before 边界内不可见",
        ],
        "followups": [
            ("volatile 在 Go 有吗？", "无，用 sync/atomic 或 channel/Mutex"),
            ("双重检查锁定在 Go？", "用 sync.Once，不要手写 DCL"),
        ],
        "pitfalls": ["以为写 bool 一定立即可见", "无 happens-before 的 flag 同步"],
    },
    {
        "q": "逃逸分析是什么？如何影响性能？",
        "core": "编译器逃逸分析决定变量分配在栈还是堆：若指针逃出函数（返回、闭包、interface、发送到 channel），则 heap allocate。栈分配 cheap 且随函数结束回收；堆分配增加 GC 压力。用 go build -gcflags='-m' 查看逃逸。",
        "dive": [
            "闭包捕获局部变量指针导致逃逸",
            "fmt.Sprintf、errors 等常导致逃逸",
            "大对象可能直接 heap 分配",
        ],
        "followups": [
            ("字符串转 []byte 拷贝吗？", "[]byte(s) 通常拷贝；unsafe 可零拷贝但有 immutability 风险"),
            ("如何减少逃逸？", "值传递、预分配、避免 interface{}、sync.Pool"),
        ],
        "pitfalls": ["盲目 unsafe", "忽略 -m 诊断"],
        "resume": "interview-go q019/q020 类题：在热路径避免 fmt 与不必要的 heap boxing。",
    },
    {
        "q": "如何排查 goroutine 泄漏？",
        "core": "症状：内存涨、goroutine 数持续增、服务变慢。工具：pprof goroutine、runtime.NumGoroutine、trace。常见原因：channel 阻塞无 receiver、忘记 ctx cancel、http.Client 无 timeout、WaitGroup 误用。",
        "dive": [
            "goroutine profile 看 stack 阻塞点",
            "leaktest 模式：baseline vs 压测后 diff",
            "http.DefaultClient 无 timeout 是经典泄漏源",
        ],
        "followups": [
            ("如何设置 goroutine 上限？", "semaphore（ buffered channel 或 weighted semaphore）、worker pool"),
            ("泄漏与 GC 关系？", "G 本身占 stack 内存，泄漏 G 多 → RSS 涨"),
        ],
        "pitfalls": ["只重启不查根因", "在泄漏路径加更多 goroutine"],
        "resume": "实务上曾用 pprof goroutine profile 定位 HTTP handler 未 timeout 的第三方 API 调用导致堆积。",
    },
    {
        "q": "race detector 如何使用？原理？",
        "core": "go test -race / go run -race 启用 ThreadSanitizer 插桩，检测无同步的 concurrent memory access。运行时记录 happens-before 关系，报告 data race。生产通常关闭（5-10x 慢、10x 内存），CI 必开。",
        "dive": [
            "检测 read-write、write-write 冲突",
            "不保证发现所有 race（覆盖率依赖调度）",
            "cgo 代码也可能被检测",
        ],
        "followups": [
            ("race 报告误报？", "极少；通常真有 bug"),
            ("如何修 race？", "Mutex、channel、atomic，或消除共享"),
        ],
        "pitfalls": ["以为 -race 通过就无并发 bug", "只在单测跑 race 未覆盖生产路径"],
    },
    {
        "q": "Go error handling 最佳实践？errors.Is/As/wrap？",
        "core": "Go 1.13+ errors.Is 判断错误链中是否含目标，errors.As 提取 typed error，fmt.Errorf(\"%w\") wrap 保留 cause。 sentinel errors 用 var ErrX = errors.New。业务层映射 domain error，边界 log+wrap，避免 string compare。",
        "dive": [
            "error 是 interface{ Error() string }",
            "panic 仅用于 programmer error / 不可恢复",
            "multierror 可聚合（hashicorp/go-multierror）",
        ],
        "followups": [
            ("何时 return error vs panic？", "库 return error；main/init 可 panic；不可恢复 invariant  violation 可 panic"),
            ("grpc status 如何映射？", "status.Errorf + codes，client 用 status.FromError"),
        ],
        "pitfalls": ["err == io.EOF 在 wrap 后失效", "吞 error", "每层都 wrap 丢 context"],
    },
    {
        "q": "Go generics 基础与限制？",
        "core": "Go 1.18+ 引入 type parameters：[T any]、constraints（comparable、constraints.Ordered 或自定义 interface）。编译期单态化（monomorphization）生成具体类型代码。不支持泛型方法（仅泛型类型/函数）、无默认类型参数、无 specialization。",
        "dive": [
            "type set 定义 constraint",
            "any = interface{}",
            "泛型减少 interface{} 与 reflection",
        ],
        "followups": [
            ("泛型 vs interface{}", "泛型 compile-time 类型安全零 boxing；interface 运行时 dispatch"),
            ("何时不用泛型？", "简单代码、仅一处使用、constraint 过于复杂"),
        ],
        "pitfalls": ["过度抽象", "constraint 设计过大失去类型信息"],
    },
    {
        "q": "并发安全 Map 如何实现？（interview-go q010/q011）",
        "core": "方案：sync.RWMutex+map、sync.Map、分片 map（shard by hash）。阻塞读场景：用 channel 通知或 sync.Cond。高并发读写：分片减锁竞争，每 shard 独立 RWMutex。",
        "dive": [
            "sync.Map 的 miss 路径加锁写 dirty",
            "Copy-on-read 快照适合读多",
            "atomic.Value 存 immutable map 替换",
        ],
        "followups": [
            ("读阻塞直到 key 出现？", "单 key 用 chan 或 pub/sub；全局用 Cond+map"),
            ("map fatal error concurrent？", "runtime 检测到直接 crash，无法 recover"),
        ],
        "pitfalls": ["range map 同时写", "sync.Map 存指针 mutable 对象无保护"],
    },
    {
        "q": "closed channel 读写会怎样？（interview-go q018）",
        "core": "向 closed channel send → panic。从 closed channel recv → 先读完 buf，之后零值+ok=false，不 panic。从 nil channel recv/send → 永久阻塞。close(nil) → panic。",
        "dive": [
            "for v := range ch 在 close 后自动结束",
            "select 向 closed ch send 仍 panic",
            "检测 close 只能 recv side 用 ok",
        ],
        "followups": [
            ("如何 broadcast？", "close channel 或 context.Done()"),
            ("多消费者 drain？", "每个 consumer range 同一 ch，元素只会一人消费"),
        ],
        "pitfalls": ["sender 不知道 receiver 已退出仍 send", "用 close 作计数信号误用"],
    },
    {
        "q": "HTTP 包内存泄漏常见场景？（interview-go q021）",
        "core": "经典泄漏：resp, err := client.Do(req) 后未 io.Copy(io.Discard, resp.Body) 且未 Close Body，连接无法归还连接池。应用 defer resp.Body.Close() 并读完 body。Client 需设置 Timeout 或 context。",
        "dive": [
            "Transport MaxIdleConns 等池化参数",
            "CancelRequest 已废弃，用 context",
            "handler 中 goroutine 未随 request 结束退出",
        ],
        "followups": [
            ("如何限制连接数？", "Transport.MaxConnsPerHost"),
            ("pprof 如何定位？", "goroutine stack 见 io.ReadAll 或 time.Sleep 在 handler 泄漏路径"),
        ],
        "pitfalls": ["只用 DefaultClient", "Close 但不 Drain body"],
        "resume": "實務上曾修复第三方 API 调用泄漏：context timeout + body drain + connection pool 调优。",
    },
    {
        "q": "CSP 模型与 Go channel 的设计哲学？",
        "core": "CSP（Communicating Sequential Processes）主张通过通信共享内存，而非共享内存来通信。Go channel 是 CSP 的实现：goroutine 通过 send/recv 同步与传递数据，减少显式锁。",
        "dive": [
            "channel 同步：unbuffered send/recv rendezvous",
            "select 多路复用",
            "mutex 仍用于保护共享 state，与 channel 互补",
        ],
        "followups": [
            ("何时不用 channel？", "简单 counter、performance critical 热路径、需随机访问结构"),
            ("actor vs CSP？", "actor mailbox 异步；CSP channel 可同步 handoff"),
        ],
        "pitfalls": ["用 channel 实现复杂共享状态", "无 buffer 导致死锁"],
    },
    {
        "q": "调度陷阱：GOMAXPROCS 与 cgo/blocking syscall？",
        "core": "长时间 cgo 或 syscall 阻塞 M，P 可能 detach 给其他 M。若所有 M 阻塞，其他 G 无法运行（除 sysmon 补救）。Net 只阻塞当前 thread，但 file IO 等可能 block OS thread。",
        "dive": [
            "runtime.LockOSThread 将 G 绑 M，减少调度但可能浪费",
            "网络 IO 用 netpoller 异步",
            "文件 IO 考虑 io_uring 或 thread pool（Go 1.XX 演进）",
        ],
        "followups": [
            ("容器 CPU throttling 影响？", "P 认为有 N 核但实际 throttle → 调度延迟增"),
            ("如何检测 syscall 阻塞？", "trace / schedtrace / GODEBUG=scheddetail=1"),
        ],
        "pitfalls": ["在热路径大量 cgo", "LockOSThread 滥用"],
    },
    {
        "q": "sync/atomic 与 Mutex 如何选择？",
        "core": "atomic 适用于简单 counter、flag、pointer swap 等无复合 invariant 的场景。Mutex 保护多字段 invariant。Go 1.19+ atomic 支持 typed atomic.Int64 等。",
        "dive": [
            "atomic 提供 happens-before",
            "CAS loop 实现 lock-free stack/queue（复杂）",
            "false sharing：padding 热 atomic 字段",
        ],
        "followups": [
            ("atomic.Value 用法？", "Store immutable config snapshot，Load 无锁读"),
            ("ABA 问题？", "Go GC 管理内存的 lock-free 结构需考虑，一般用 hazard pointer 或 GC 友好设计"),
        ],
        "pitfalls": ["atomic 保护多字段不一致", "混合 atomic 与 non-atomic 读写同一变量"],
    },
    {
        "q": "go mod 依赖管理与 vendor？",
        "core": "go.mod 声明 module path 与 require；go.sum 校验 hash。MVS（Minimal Version Selection）选最低兼容版本。vendor/ 可离线构建。replace 用于 fork 或本地路径。",
        "dive": [
            "go work 多 module 开发",
            "private module GOPRIVATE",
            "semver tag 规范",
        ],
        "followups": [
            ("依赖冲突怎么解？", "go mod graph、upgrade、replace、或拆 interface"),
            ("vendor 何时用？", "CI  reproducibility、air-gapped build"),
        ],
        "pitfalls": ["commit 无 go.sum", "replace 进 production 未文档化"],
    },
    {
        "q": "pprof 在 Go 性能调优中的使用？",
        "core": "import _ net/http/pprof 或 go tool pprof。类型：cpu、heap、goroutine、mutex、block。看 flat vs cum，火焰图找 hot path。配合 trace 看 latency 与 GC。",
        "dive": [
            "alloc_space vs inuse_space",
            "cum 高但 flat 低 → 调用链深处",
            "benchstat 对比优化前后",
        ],
        "followups": [
            ("生产如何采 profile？", "短窗口、采样率、安全端口"),
            ("CPU 100% 但 pprof 空？", "可能在 cgo/内核/或未采 long enough"),
        ],
        "pitfalls": ["只看 CPU 不看 alloc", "优化非 hot path"],
        "resume": "實務上用 pprof + flame graph 优化 K 线路径与第三方 HTTP 瓶颈。",
    },
    {
        "q": "errgroup 与 context 组合模式？",
        "core": "golang.org/x/sync/errgroup：Group.Go 启动子任务，Wait 等待全部完成，任一 error 取消 context（WithContext 版本）。适合 parallel fetch、pipeline fan-out，统一错误与取消。",
        "dive": [
            "SetLimit(n) 限制并发",
            "与 WaitGroup 区别：内置 error 传播",
            "cancel 后子 goroutine 应 respect ctx",
        ],
        "followups": [
            ("errgroup vs worker pool？", "errgroup 动态任务；pool 固定 worker 复用"),
            ("第一个 error 后其他任务？", "应检测 ctx.Done 提前退出"),
        ],
        "pitfalls": ["不用 WithContext 版无法联动 cancel", "子任务 ignore ctx"],
    },
    {
        "q": "Go 程序启动流程（runtime 初始化）？",
        "core": "OS 加载 → runtime 初始化（sched、memory、GOMAXPROCS）→ main.main。init 函数按 import 顺序执行。runtime.main 创建 main goroutine 调用 user main。",
        "dive": [
            "import cycle 禁止",
            "init 不应 heavy 或依赖 order",
            "race detector 在 runtime 之后启用",
        ],
        "followups": [
            ("init 能 panic 吗？", "能，程序退出"),
            ("包级 var 初始化顺序？", "依赖 declaration order 与 init"),
        ],
        "pitfalls": ["init 中网络/DB", "import side effect 难测"],
    },
    {
        "q": "for 迴圈變數捕獲問題（Go 1.22 前後差異）？",
        "core": "Go 1.22 以前，for 迴圈變數在整個迴圈共用同一份位址，經典 bug：`for _, v := range s { go func(){ use(v) }() }` 所有 goroutine 看到同一個（通常是最後一個）v。修正：迴圈內 `v := v` 複製，或把 v 當參數傳入閉包。Go 1.22 起改為**每次迭代新建迴圈變數**，此陷阱在新版預設消失，但跨版本相容仍需注意。",
        "dive": [
            "1.22 前：i、v 在迴圈作用域只有一份，閉包捕獲的是變數位址而非當下值",
            "經典觸發點：goroutine、defer、把 &v 加入 slice",
            "1.22 後語義由 go.mod 宣告的 go 版本決定（go 1.22+ 才啟用新 loopvar）",
        ],
        "followups": [
            ("為什麼 1.22 前要寫 v := v？", "建立 per-iteration 副本，讓每個閉包捕獲各自獨立的變數"),
            ("go.mod 寫 go 1.21 但用 1.22 工具鏈編譯？", "語言語義以 go.mod 版本為準，仍用舊 loopvar 行為，避免隨工具鏈漂移"),
        ],
        "pitfalls": ["1.21 以前在 range 迴圈啟動 goroutine 未複製變數", "誤以為所有專案都已是新語義（取決於 go.mod）", "對迴圈變數取位址 &v 全部指向同一元素"],
        "resume": "行情 fan-out 啟動大量 goroutine 時，注意 loopvar 捕獲，避免所有 worker 都處理同一個 symbol。",
    },
    {
        "q": "手寫一個帶限流的 worker pool（Go coding）？",
        "core": (
            "固定 n 個 goroutine 從同一個 jobs channel 消費，channel 關閉即優雅退出，用 WaitGroup 等待全部結束。需要並發上限/錯誤傳播/取消時，優先用 errgroup.WithContext + SetLimit。\n\n"
            "```go\n"
            "func WorkerPool(jobs <-chan Job, n int) {\n"
            "    var wg sync.WaitGroup\n"
            "    for i := 0; i < n; i++ {\n"
            "        wg.Add(1)\n"
            "        go func() {\n"
            "            defer wg.Done()\n"
            "            for j := range jobs { // jobs 關閉後迴圈自動結束\n"
            "                process(j)\n"
            "            }\n"
            "        }()\n"
            "    }\n"
            "    wg.Wait()\n"
            "}\n"
            "```"
        ),
        "dive": [
            "n 依 CPU/IO 特性調整：CPU-bound 約 runtime.NumCPU()，IO-bound 可更大",
            "errgroup.WithContext + SetLimit(n)：同時得到並發上限、錯誤傳播與取消",
            "semaphore 寫法：sem := make(chan struct{}, n)，進入前 sem<-struct{}{}，結束 <-sem",
        ],
        "followups": [
            ("如何收集每個 job 的結果？", "另開 results channel，或用 errgroup + 預分配 slice 各寫各的 index 避免鎖"),
            ("如何支援取消？", "傳入 context，worker 內 select{ case <-ctx.Done(): return; case j, ok := <-jobs: ... }"),
        ],
        "pitfalls": ["忘記 close(jobs) 導致 worker 永遠阻塞（goroutine 洩漏）", "worker 內共享 slice 未加鎖造成 data race", "panic 未 recover 拖垮整個 pool"],
        "resume": "在交易所行情/訂單處理用 worker pool 控制 goroutine 數量，避免無限 go func() 造成 OOM。",
    },
    {
        "q": "如何合併多個 channel（fan-in / merge）？（Go coding）",
        "core": (
            "每個輸入 channel 各起一個 goroutine 把值寫到共用 out；另起一個 goroutine 等所有來源結束後 close(out)，讓下游 range 正常退出。Go 1.22 前需把 c 當參數傳入，避免迴圈變數捕獲。\n\n"
            "```go\n"
            "func Merge(chans ...<-chan int) <-chan int {\n"
            "    out := make(chan int)\n"
            "    var wg sync.WaitGroup\n"
            "    for _, c := range chans {\n"
            "        wg.Add(1)\n"
            "        go func(c <-chan int) {\n"
            "            defer wg.Done()\n"
            "            for v := range c {\n"
            "                out <- v\n"
            "            }\n"
            "        }(c)\n"
            "    }\n"
            "    go func() { wg.Wait(); close(out) }()\n"
            "    return out\n"
            "}\n"
            "```"
        ),
        "dive": [
            "fan-out：多 worker 從同一 channel 讀；fan-in：多來源匯入一個 channel",
            "需取消時加 context，select 寫入 out 與 <-ctx.Done()",
            "close(out) 必須在所有 sender 結束後，否則 send on closed channel 會 panic",
        ],
        "followups": [
            ("如何避免下游慢造成阻塞？", "out 加 buffer，或 select+ctx 丟棄，配合背壓策略"),
            ("LMAX Disruptor 與 channel fan-in 差異？", "Disruptor 用 ring buffer 單寫多讀、無鎖序號、低延遲；channel 有 mutex 與排程開銷"),
        ],
        "pitfalls": ["在所有 sender 結束前 close(out)", "Go 1.22 前未傳參導致所有 goroutine 讀同一個 c"],
        "resume": "體育數據管線把多來源事件 fan-in 後再分類處理，思路類似 Disruptor 但以 channel/goroutine 實作。",
    },
]

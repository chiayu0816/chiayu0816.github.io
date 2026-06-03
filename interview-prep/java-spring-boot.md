# Java / Spring Boot 面試 Q&A

> 來源：tech-vault、Spring Boot 重構實務
> 題數：16 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 實務場景（個人對照見 resume_overlay.py）

---

### Q: Spring Boot 自動配置原理？

**核心回答：**
@SpringBootApplication = @Configuration + @EnableAutoConfiguration + @ComponentScan。AutoConfiguration 透過 spring.factories/org.springframework.boot.autoconfigure.AutoConfiguration.imports 條件 @ConditionalOnClass 載入 bean。

**深入原理：**
- starter 依賴傳遞
- @ConditionalOnMissingBean
- 配置 properties 繫結

**考官可能追問：**
- Q: 如何自定義 starter？
  - A: autoconfigure module
- Q: 排除？
  - A: @SpringBootApplication exclude

**常見陷阱 / 易錯點：**
- bean 衝突
- 無條件 @Component 掃描過多

---
### Q: Spring IoC 與 DI 原理？

**核心回答：**
控制反轉：容器管理 bean 生命週期。依賴注入：構造器（推薦）、setter、欄位。BeanFactory vs ApplicationContext（事件、AOP）。

**深入原理：**
- singleton/prototype scope
- circular dependency 三級快取
- @PostConstruct

**考官可能追問：**
- Q: 迴圈依賴？
  - A: setter 可；構造器不行
- Q: @Autowired 失敗？
  - A: required=false

**常見陷阱 / 易錯點：**
- field injection 難測
- prototype 注入 singleton 錯

---
### Q: Spring AOP 原理與 JDK/CGLIB？

**核心回答：**
代理模式：有介面 JDK 動態代理；無介面 CGLIB 子類。切面=@Before/@Around 等+Pointcut。自呼叫不走代理。

**深入原理：**
- AspectJ weave vs Spring AOP
- proxy target vs this
- transaction 靠 AOP

**考官可能追問：**
- Q: 同類 @Transactional 無效？
  - A: 自呼叫
- Q: 效能？
  - A: 代理開銷小

**常見陷阱 / 易錯點：**
- private 方法 @Transactional 無效
- final 類 CGLIB 失敗

---
### Q: @Transactional 傳播與失效場景？

**核心回答：**
REQUIRED 預設加入；REQUIRES_NEW 新事務；NESTED savepoint。失效：非 public、自呼叫、異常被 catch、rollbackFor 未含 checked exception、wrong proxy。

**深入原理：**
- readOnly 最佳化
- isolation 繼承
- 分散式 @GlobalTransactional Seata

**考官可能追問：**
- Q: REQUIRES_NEW 用途？
  - A: 獨立日誌
- Q: 只讀？
  - A: @Transactional readOnly=true

**常見陷阱 / 易錯點：**
- 吞異常不回滾
- 大事務

---
### Q: Spring Boot 與 Struts 遷移要點？

**核心回答：**
實務遷移案例：Struts→Spring Boot。Action→Controller REST；XML→Java config/annotation；依賴注入替代 singleton util；統一 exception handler。

**深入原理：**
- session 管理遷移
- filter chain 等價
- 逐步 strangler fig

**考官可能追問：**
- Q: 風險？
  - A: 迴歸測試
- Q: 工期？
  - A: 模組分批

**常見陷阱 / 易錯點：**
- 業務邏輯留 JSP
- 無整合測試

**實務場景：**
實務：Struts→Spring Boot ECM/SCM 重構

---
### Q: JVM 記憶體結構與 GC 概述？

**核心回答：**
Heap（Young Old）、Metaspace、Stack、PC。GC：G1 預設（JDK9+），ZGC/Shenandoah 低延遲。Minor GC、Mixed GC、Full GC。

**深入原理：**
- TLAB 分配
- card table remembered set
- GC logs -Xlog:gc*

**考官可能追問：**
- Q: Full GC 頻繁？
  - A: heap 小或 leak
- Q: ZGC？
  - A: 超大堆低 pause

**常見陷阱 / 易錯點：**
- -Xmx 過大無容器 awareness
- ignore metaspace OOM

---
### Q: HashMap 與 ConcurrentHashMap 原理？

**核心回答：**
HashMap JDK8 陣列+連結串列+紅黑樹；非執行緒安全。CHM segment/CAS+synchronized bucket；sizeCtl；compute 原子。

**深入原理：**
- resize 執行緒協助 transfer
- hash 擾動
- fail-fast iterator

**考官可能追問：**
- Q: Hashtable？
  - A: 全表鎖廢棄
- Q: CHM null key？
  - A: 不允許

**常見陷阱 / 易錯點：**
- HashMap 併發死迴圈歷史
- key 無 equals/hashCode

---
### Q: Java 執行緒池 ThreadPoolExecutor 引數？

**核心回答：**
corePoolSize、maximumPoolSize、queue（有界！）、RejectedExecutionHandler。順序：core滿→queue→max→reject。

**深入原理：**
- CallerRunsPolicy 背壓
- Executors 陷阱無界 queue
- graceful shutdown

**考官可能追問：**
- Q: 佇列無界危害？
  - A: OOM
- Q: IO 密集 core 數？
  - A: 大於 CPU

**常見陷阱 / 易錯點：**
- Executors.newCachedThreadPool 無限
- 無監控 queue size

---
### Q: synchronized vs ReentrantLock？

**核心回答：**
synchronized JVM 最佳化（偏向鎖撤銷等）；Lock 可 interrupt、tryLock、公平、多 Condition。優先 synchronized 簡單場景。

**深入原理：**
- monitor enter/exit
- AQS 佇列
- virtual thread JDK21 pin 問題

**考官可能追問：**
- Q: 死鎖排查？
  - A: jstack
- Q: 讀寫？
  - A: ReadWriteLock

**常見陷阱 / 易錯點：**
- Lock 未 unlock finally
- 鎖粒度過粗

---
### Q: Java 併發：volatile 與 happens-before？

**核心回答：**
volatile 可見+禁重排序；happens-before 規則：程式順序、monitor、volatile、執行緒 start/join。

**深入原理：**
- DCL 單例
- Atomic* CAS
- false sharing @Contended

**考官可能追問：**
- Q: volatile 原子嗎？
  - A: i++ 不
- Q: CAS ABA？
  - A: AtomicStampedReference

**常見陷阱 / 易錯點：**
- volatile 當鎖
- double-checked locking 未 volatile

---
### Q: MyBatis vs JPA/Hibernate？

**核心回答：**
MyBatis SQL 可控靈活；JPA ORM 物件關係自動。Spring Data JPA 快速 CRUD；複雜報表 MyBatis。

**深入原理：**
- N+1 lazy load
- SqlSession
- @Query native

**考官可能追問：**
- Q: 動態 SQL？
  - A: MyBatis XML/if
- Q: 遷移？
  - A: 逐步

**常見陷阱 / 易錯點：**
- JPA 複雜 query 效能
- SQL injection ${}

---
### Q: Spring Security 認證授權流程？

**核心回答：**
Filter chain：SecurityContextHolder←Authentication。JWT/Session；Authorization @PreAuthorize。OAuth2 Resource Server。

**深入原理：**
- OncePerRequestFilter
- CSRF REST 可關
- method security

**考官可能追問：**
- Q: JWT 存哪？
  - A: header 非 cookie XSS
- Q: RBAC？
  - A: role+permission DB

**常見陷阱 / 易錯點：**
- CSRF 關錯場景
- permits all /**

---
### Q: RESTful API 設計在 Spring 中？

**核心回答：**
@RestController + @GetMapping；統一 ResponseEntity；@ControllerAdvice 異常；validation @Valid；HATEOAS 可選。

**深入原理：**
- pagination Pageable
- OpenAPI springdoc
- content negotiation

**考官可能追問：**
- Q: 版本？
  - A: URL /v1 或 header
- Q: 冪等 POST？
  - A: Idempotency-Key

**常見陷阱 / 易錯點：**
- 500 暴露 stack
- 無 validation

---
### Q: 微服務 Spring Cloud 元件？

**核心回答：**
Nacos/Eureka 發現；Gateway 路由；OpenFeign 客戶端；Sentinel/Hystrix 熔斷；Config 配置中心。

**深入原理：**
- loadbalancer @LoadBalanced
- circuit breaker 半開
- distributed trace sleuth

**考官可能追問：**
- Q: vs 單體？
  - A: 運維複雜度
- Q: Seata 事務？
  - A: AT mode

**常見陷阱 / 易錯點：**
- 分散式 monolith
- 無 contract test

---
### Q: 資深 Java 經驗如何在面試中陳述？

**核心回答：**
10+ 年 Java；Spring Boot 重構 Tech Lead；Go+Java 混合棧；Oracle/MySQL/MSSQL；Jenkins CI/CD。

**深入原理：**
- legacy 維護
- 效能 tuning JVM
- 與 Go 服務共存

**考官可能追問：**
- Q: 為何轉 Go？
  - A: 交易所主棧 Go
- Q: Java 還寫嗎？
  - A: 維護+整合

**常見陷阱 / 易錯點：**
- 只講舊專案無深度

**實務場景：**
實務：Spring Boot 重構、Java/Go 混合棧、Oracle/MySQL

---
### Q: JVM 類載入機制與雙親委派模型？

**核心回答：**
類載入分 載入→驗證→準備→解析→初始化。雙親委派（parent delegation）：類載入請求先委派給父載入器（AppClassLoader→Platform/Ext→Bootstrap），父載入不到才自己載入。目的：避免核心類被覆寫（自寫 java.lang.String 不會被載入）、保證類的唯一性與安全。

**深入原理：**
- 三層：Bootstrap（核心 rt/jmods）、Platform/Ext、Application（classpath）
- 打破委派：Tomcat 每個 webapp 獨立 ClassLoader、JDBC SPI 用 Thread Context ClassLoader、OSGi 模組化
- 類唯一性由（ClassLoader + 全限定名）共同決定，不同 loader 載同名類互不相等

**考官可能追問：**
- Q: 為什麼需要雙親委派？
  - A: 防止核心 API 被意外/惡意覆寫，保證 java.* 由 Bootstrap 載入，維持型別安全
- Q: 如何打破？什麼場景？
  - A: 覆寫 loadClass（非 findClass）；Tomcat 隔離、SPI、熱部署需要

**常見陷阱 / 易錯點：**
- 同類被兩個 loader 載入導致 ClassCastException
- 在 webapp 放 JDBC driver 與容器衝突
- 只覆寫 findClass 以為能改委派（應覆寫 loadClass）

**實務場景：**
維護 Java 服務時常遇 legacy 與容器類載入隔離問題，理解委派模型有助排查 ClassLoader 衝突

---

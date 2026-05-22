# 李佳育 Roy Lee

**資深後端工程師 | Go / Java**  
台北 | chiayu0816@gmail.com | [linkedin.com/in/cylee-19830816](https://www.linkedin.com/in/cylee-19830816)

---

## 專業摘要

資深後端工程師，10+ 年經驗，專精 Go 與 Java 高併發系統。現任虛擬貨幣交易所 Go 後端負責人，涵蓋撮合、行情、流動性、對沖與多通道通知；曾將 K 線載入由 3–5 秒優化至 300–500ms（Stored Procedure 資料治理 + Redis ZSET 快取重構）。獨立以 AI 輔助開發（Cursor）並上線完整 HRM 系統（Go/Gin + Vue 3），具 MCP、Agent、RAG 等實務應用經驗。曾於體育數據領域完成 Betradar 導入與即時管線優化（LMAX Disruptor、Kafka）。熟悉 gRPC、WebSocket、RocketMQ、MySQL、Redis、Oracle、MS SQL Server 及生產調校（pprof、日誌）。

---

## 技術技能

- **程式語言**：Go (Golang)、Java
- **關聯式資料庫**：MySQL、Oracle、Microsoft SQL Server、SQLite
- **NoSQL 與快取**：Redis、Redis Sorted Set (ZSET)、MongoDB
- **資料庫實務**：Stored Procedure、索引優化、資料清洗
- **訊息佇列**：Apache RocketMQ、Apache Kafka、RabbitMQ
- **API 與通訊**：gRPC、WebSocket、RESTful API
- **後端框架**：Gin、GORM、Spring Boot
- **前端**：Vue 3、Pinia、Vite、Naive UI
- **架構**：微服務、事件驅動、高併發、低延遲
- **領域**：虛擬貨幣交易所、K 線/行情、體育數據整合、電商後端、HRM
- **DevOps**：AWS、Git、Jenkins、CI/CD、Docker Compose
- **效能與協作**：pprof、火焰圖、系統設計、跨部門協作
- **AI 輔助開發**：Cursor、MCP、AI Agent、Hooks、RAG、Skills（LLM 應用實作）

---

## 工作經歷

### 資深後端工程師（Go） | 克拉科技 Kela Tech｜虛擬貨幣交易所  
**台北 | 2024.11 – 至今**

- 以 Go 開發交易所後端核心模組：流動性、行情、撮合、對沖，支援即時交易與風控流程。
- 治理 K 線資料庫大量重複與異常資料：以 Stored Procedure 清洗並重建索引；以 Redis ZSET 重構快取結構與寫入設計，將 K 線載入由平均 3–5 秒縮短至 300–500ms。
- 獨立完成並上線完整 HRM 人資系統（獲內部同仁正面評價）：後端 Go/Gin/GORM、前端 Vue 3/Pinia/Vite/Naive UI、MySQL、Docker Compose 部署；運用 Cursor AI 加速開發，並實作 MCP、Agent、Hooks、RAG、Skills 等 AI 應用模式。
- 建置並維運通知中心，統一管控平台 Email、SMS、Telegram 訊息發送；開發匯率服務支援交易與風控。
- 以 gRPC、WebSocket、RocketMQ 串接行情與跨服務事件；以 MySQL、Redis 支撐持久化與快取。
- 部門唯一 Go 工程師：獨立維運上述服務，依技術總監路線圖交付，與 PM 及跨部門協作；以 pprof、日誌與指標進行生產效能調校。

### 資深軟體工程師 | 雷速網絡科技有限公司 Luxons  
**台北 | 2023.03 – 2024.07**

- 負責 Betradar 數據源導入與驗收，設計後端整合框架，將大量賽事資料即時分發至下游服務（Kafka、RESTful API）。
- 維護並擴充既有系統（Go/Java），修正缺陷、優化效能並依 PM 需求交付新功能。
- 以 pprof、日誌與火焰圖排查生產問題，解決 HTTP 高併發導致服務不穩、第三方 API 逾時、Redis 快取擊穿等瓶頸。

### 資深軟體工程師 | 伊諾科技有限公司 INNO  
**台北 | 2020.07 – 2023.02**

- 整合 Betradar、Betgenius 等體育數據商，依即時性需求以 RESTful API、Kafka、RabbitMQ 分發整合資料（MySQL、Redis、MongoDB）。
- 將即時賠率/賽事管線端對端延遲由經常 >1000ms 顯著降低：採 LMAX Disruptor 分類事件、多執行緒處理即時資料後重組轉發，降低因資訊延遲造成的營運風險。
- 維護既有系統並持續優化資料管線穩定性與吞吐量。

### 資深軟體工程師 | 共贏資訊科技服務有限公司  
**台北 | 2019.09 – 2020.06**

- 開發客服系統模組（訊息/回覆、通話錄音、聯絡紀錄、績效統計）及排程報表（RESTful API、Oracle、MongoDB）。
- 整合第三方遊戲 API（BBIN、AG、MG）。

### 全端工程師 / 技術負責人 | 一直購數位資訊股份有限公司 Apezgo  
**台北 | 2016.08 – 2019.09**

- 帶領 3 人團隊將 Struts 電商後端重構為 Spring Boot，拆分並重建 ECM、SCM 系統。
- 建置 Jenkins + SVN CI/CD，自動化部署，降低手動 build/deploy 風險與工時。

### 全端工程師 / 技術負責人 | 蟲洞科技股份有限公司 WormHoleSoft  
**新竹 | 2011.09 – 2016.07**

- 維護企業產品，修復缺陷並優化效能；協助客戶系統導入、維運與客製開發（Java、Oracle、MySQL、MS SQL）。

---

## 學歷

- 學士，電子工程｜蘭陽技術學院｜2003 – 2007
- Java 網際網路程式設計師養成班｜資策會數位教育研究所｜2011

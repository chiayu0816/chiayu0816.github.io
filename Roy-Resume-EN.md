# Roy Lee (李佳育)

**Senior Backend Engineer | Go & Java**  
Taipei, Taiwan | chiayu0816@gmail.com | [linkedin.com/in/cylee-19830816](https://www.linkedin.com/in/cylee-19830816)

---

## Professional Summary

Senior backend engineer with 10+ years building high-concurrency systems in Go and Java. Currently sole Go owner for a cryptocurrency exchange (matching, market data, liquidity, hedging, notifications). Reduced K-line (OHLC) load latency from 3–5s to 300–500ms via MySQL stored procedures and Redis ZSET cache redesign. Independently delivered a production HRM platform using Cursor AI (Go/Gin/GORM + Vue 3), applying MCP, agents, hooks, RAG, and skills in practice. Previously integrated Betradar sports feeds and optimized real-time pipelines with LMAX Disruptor and Kafka. Proficient in gRPC, WebSocket, RocketMQ, MySQL, Redis, Oracle, MS SQL Server, and production tuning (pprof, logging).

---

## Technical Skills

- **Languages:** Go (Golang), Java
- **Relational DB:** MySQL, Oracle, Microsoft SQL Server, SQLite
- **NoSQL & Cache:** Redis, Redis Sorted Sets (ZSET), MongoDB
- **Database Practices:** Stored procedures, index optimization, data cleansing
- **Messaging:** Apache RocketMQ, Apache Kafka, RabbitMQ
- **APIs & Protocols:** gRPC, WebSocket, RESTful API
- **Backend:** Gin, GORM, Spring Boot
- **Frontend:** Vue 3, Pinia, Vite, Naive UI
- **Architecture:** Microservices, event-driven, high concurrency, low latency
- **Domain:** Cryptocurrency exchange, K-line/candlestick (OHLC), sports data, e-commerce, HRM
- **DevOps & Cloud:** AWS, Git, Jenkins, CI/CD, Docker Compose
- **Performance:** pprof, flame graphs, system design, cross-functional delivery
- **AI-Assisted Development:** Cursor, MCP, AI agents, hooks, RAG, skills (LLM application patterns)

---

## Professional Experience

### Senior Backend Engineer (Go) | Kela Tech | Cryptocurrency Exchange  
**Taipei | Nov 2024 – Present**

- Built Go backend services for a cryptocurrency exchange: liquidity, market data, order matching, and hedging.
- Remediated duplicate/anomalous K-line (OHLC) data using MySQL stored procedures and index rebuilds; re-architected Redis sorted-set (ZSET) caching and write paths, reducing chart load latency from 3–5s to 300–500ms.
- Independently designed, built, and deployed a full-stack HRM system (well received internally): Go/Gin/GORM backend, Vue 3/Pinia/Vite/Naive UI frontend, MySQL, Docker Compose; accelerated delivery with Cursor AI and applied MCP, agents, hooks, RAG, and skills patterns.
- Owned notification hub (email, SMS, Telegram) and FX exchange-rate services for trading and risk workflows.
- Integrated market/trading flows via gRPC, WebSocket, and Apache RocketMQ; persistence and caching with MySQL and Redis.
- Sole Go engineer: production ownership, CTO-led roadmap delivery, and cross-functional work with PM and peer teams; tuning via pprof, logs, and metrics.

### Senior Software Engineer | Luxons  
**Taipei | Mar 2023 – Jul 2024**

- Led Betradar source onboarding and acceptance; designed backend integration to stream high-volume sports data to downstream services (Kafka, RESTful API).
- Maintained and extended Go/Java services—bug fixes, performance improvements, and PM-driven features.
- Resolved production bottlenecks (HTTP concurrency, third-party API timeouts, Redis cache penetration) using pprof, logs, and flame graphs.

### Senior Software Engineer | INNO  
**Taipei | Jul 2020 – Feb 2023**

- Integrated multi-vendor sports data (Betradar, Betgenius) and distributed via RESTful API, Kafka, and RabbitMQ (MySQL, Redis, MongoDB).
- Cut end-to-end latency for odds/live events from frequent >1000ms using LMAX Disruptor event classification and parallel real-time processing pipelines.
- Maintained legacy systems and improved pipeline stability and throughput.

### Senior Software Engineer | Gongying  
**Taipei | Sep 2019 – Jun 2020**

- Developed customer-service modules (messaging, call recordings, contact logs, KPI stats) and scheduled reporting via RESTful API (Oracle, MongoDB).
- Integrated third-party gaming APIs (BBIN, AG, MG).

### Full-Stack Engineer / Tech Lead | Apezgo  
**Taipei | Aug 2016 – Sep 2019**

- Led a team of three to refactor Struts e-commerce backend to Spring Boot; rebuilt ECM and SCM systems.
- Implemented Jenkins + SVN CI/CD to automate deployments and reduce manual release risk.

### Full-Stack Engineer / Tech Lead | WormHoleSoft  
**Hsinchu | Sep 2011 – Jul 2016**

- Maintained enterprise products; supported customer implementations and customizations (Java, Oracle, MySQL, MS SQL).

---

## Education

- B.Eng., Electronic Engineering | Lan Yang Institute of Technology | 2003 – 2007
- Java Web Programming Training Program | Institute for Information Industry (III) | 2011

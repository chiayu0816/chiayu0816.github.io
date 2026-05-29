# Docker / AWS 面試 Q&A

> 來源：tech-vault、Roy HRM Docker Compose / AWS 實務
> 題數：15 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

### Q: Docker 映象分層與 Union FS？

**核心回答：**
映象只讀層 stack；容器 writable layer（CoW）。Dockerfile 每條指令一層；快取 build。多階段 build 減體積。

**深入原理：**
- overlay2 driver
- .dockerignore
- distroless/scratch

**考官可能追問：**
- Q: 為何分層？
  - A: 複用 cache
- Q: 大映象？
  - A: multi-stage

**常見陷阱 / 易錯點：**
- 單層 COPY 全部 invalidate cache
- root 執行安全風險

---
### Q: Dockerfile 最佳實踐？

**核心回答：**
小 base（alpine/distroless）；非 root USER；HEALTHCHECK；明確 EXPOSE；合併 RUN 減層；secrets 不 ARG 進映象。

**深入原理：**
- BuildKit cache mount
- SBOM 掃描
- pin digest 非 tag

**考官可能追問：**
- Q: Go 映象？
  - A: scratch+certs+static binary
- Q: Java？
  - A: jlink 定製 JRE

**常見陷阱 / 易錯點：**
- latest 漂移
- secrets in ENV

---
### Q: Docker Compose 用於本地/HRM 專案？

**核心回答：**
Roy HRM：Go backend + Vue + MySQL + Compose 一鍵起。service depends_on、network、volume、env file。

**深入原理：**
- healthcheck wait
- override yml
- prod 不用 compose scale

**考官可能追問：**
- Q: vs K8s？
  - A: local dev vs prod orchestration
- Q: 熱更？
  - A: volume mount dev

**常見陷阱 / 易錯點：**
- compose prod 無 resource limit
- 明文 password yml

**結合履歷：**
Roy HRM：Go/Gin/GORM + Vue3 + MySQL + Docker Compose 獨立交付。

---
### Q: 容器網路：bridge/host/overlay？

**核心回答：**
bridge 預設 NAT；host 無隔離共享埠；overlay Swarm/K8s 跨主機。DNS 服務名解析。

**深入原理：**
- iptables MASQUERADE
- publish -p
- user-defined network

**考官可能追問：**
- Q: 容器互訪？
  - A: service name:port
- Q: localhost？
  - A: host network

**常見陷阱 / 易錯點：**
- link 已廢棄
- 埠衝突

---
### Q: 容器資源 limit：CPU/Memory？

**核心回答：**
cgroups v2：--cpus --memory；K8s requests/limits。無 limit OOM killer 殺 host；Java 需 -XX:+UseContainerSupport。

**深入原理：**
- CPU throttle 延遲
- memory swap 禁
- OOM score adj

**考官可能追問：**
- Q: Go 容器記憶體？
  - A: GOMEMLIMIT
- Q: 壓測？
  - A: 找合適 limit

**常見陷阱 / 易錯點：**
- 未設 limit  noisy neighbor
- JVM 未感知 cgroup

---
### Q: Kubernetes 核心物件？

**核心回答：**
Pod最小單元；Deployment 滾動更新；Service 穩定 IP；Ingress HTTP 路由；ConfigMap/Secret 配置。

**深入原理：**
- liveness vs readiness
- HPA 自動擴
- PV/PVC 儲存

**考官可能追問：**
- Q: Pod 重啟策略？
  - A: Always OnFailure
- Q: Config 熱更？
  - A: reload sidecar

**常見陷阱 / 易錯點：**
- 無 readiness 流量到未就緒
- 單副本 prod

---
### Q: AWS EC2 vs ECS vs EKS？

**核心回答：**
EC2 虛擬機器自控；ECS AWS 容器編排；EKS 託管 K8s。Roy 簡歷 AWS 經驗：選型看團隊與 scale。

**深入原理：**
- Fargate 無 server
- ALB ingress
- IAM role IRSA

**考官可能追問：**
- Q: 小服務？
  - A: ECS Fargate
- Q: K8s 生態？
  - A: EKS

**常見陷阱 / 易錯點：**
- EC2 無自動化運維
- EKS 成本小叢集高

---
### Q: AWS RDS MySQL 運維要點？

**核心回答：**
Multi-AZ 高可用；Read Replica 讀擴展；自動 backup PITR；Parameter group 調優；監控 Enhanced Monitoring。

**深入原理：**
- storage autoscaling
- maintenance window
- Performance Insights

**考官可能追問：**
- Q: 連線？
  - A: RDS Proxy
- Q: 升級？
  - A: blue/green deployment

**常見陷阱 / 易錯點：**
- 無 replica 讀壓力
- max_connections 預設小

---
### Q: AWS ElastiCache Redis？

**核心回答：**
託管 Redis/Memcached；cluster mode 水平擴展；Multi-AZ failover；subnet group 安全組隔離。

**深入原理：**
- vs 自建 Redis
- encryption transit/at-rest
- backup snapshot

**考官可能追問：**
- Q: hot key？
  - A: application 層 local cache
- Q: TLS overhead？
  - A: 可接受

**常見陷阱 / 易錯點：**
- public accessible
- 無 AUTH token

---
### Q: AWS S3 與靜態資源？

**核心回答：**
物件儲存 11 9s；versioning；lifecycle 轉 Glacier；presigned URL；CloudFront CDN 加速。

**深入原理：**
- strong read consistency
- multipart upload 大檔案
- event notification Lambda

**考官可能追問：**
- Q: 許可權？
  - A: bucket policy IAM
- Q: 成本？
  - A: lifecycle+intelligent tier

**常見陷阱 / 易錯點：**
- public bucket 洩露
- 無 versioning 誤刪

---
### Q: AWS VPC 網路基礎？

**核心回答：**
VPC CIDR；public/private subnet；IGW NAT Gateway；Security Group 有狀態防火牆；NACL 無狀態。

**深入原理：**
- AZ 跨子網
- VPC peering
- endpoint S3 內網

**考官可能追問：**
- Q: private 出網？
  - A: NAT GW
- Q: DB 放哪？
  - A: private subnet

**常見陷阱 / 易錯點：**
- SG 0.0.0.0/0 全開
- 單 AZ

---
### Q: CI/CD：Jenkins pipeline 要點？

**核心回答：**
Roy Apezgo：Jenkins+SVN 自動化部署。Pipeline as Code；stage build/test/deploy；artifact；rollback。

**深入原理：**
- blue/green canary
- secret credentials
- docker push ECR

**考官可能追問：**
- Q: vs GitHub Actions？
  - A: 自建 vs 託管
- Q: DB migration？
  - A: flyway job

**常見陷阱 / 易錯點：**
- 無 automated test gate
- prod creds in Jenkinsfile

**結合履歷：**
Roy Apezgo：Jenkins+SVN CI/CD 減少手動釋出風險。

---
### Q: Infrastructure as Code：Terraform 概念？

**核心回答：**
宣告式描述 AWS 資源；plan/apply；state 管理；module 複用。版本化 infra 變更 review。

**深入原理：**
- remote state S3+Dynamo lock
- drift detection
- workspace env

**考官可能追問：**
- Q: vs CloudFormation？
  - A: multi cloud
- Q: secret？
  - A: vault not tfstate

**常見陷阱 / 易錯點：**
- state 無 lock 衝突
- manual change drift

---
### Q: AWS 可觀測：CloudWatch vs X-Ray？

**核心回答：**
CloudWatch metrics/logs/alarms；X-Ray 分散式 trace；Container Insights；Log Insights 查詢。

**深入原理：**
- metric filter
- SNS alert
- OpenTelemetry export

**考官可能追問：**
- Q: 成本？
  - A: log 量控制
- Q: 跨服務？
  - A: X-Ray segment

**常見陷阱 / 易錯點：**
- 無 alarm
- log 無 retention

---
### Q: 生產 incident 容器排查命令？

**核心回答：**
docker logs/stats/exec；kubectl describe/logs/exec/top；檢查 OOMKilled、CrashLoopBackOff、probe fail、資源 throttle。

**深入原理：**
- ephemeral debug container
- copy profile binary
- events 時間線

**考官可能追問：**
- Q: OOM？
  - A: 升 limit 或修 leak
- Q: 映象 pull fail？
  - A: ECR auth

**常見陷阱 / 易錯點：**
- kubectl edit prod 無變更記錄
- 未儲存 crash log

---

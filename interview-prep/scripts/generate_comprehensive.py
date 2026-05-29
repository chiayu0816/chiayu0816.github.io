#!/usr/bin/env python3
"""Generate comprehensive interview prep markdown files."""
from __future__ import annotations
import os
from pathlib import Path

import opencc

OUT = Path(__file__).resolve().parent.parent

# 統一轉成繁體中文（台灣用語）。原始 topic 來源混有簡體，這裡做最終正規化，
# 確保每次重新生成的 .md 都是一致的繁體。OpenCC 只轉換中日韓文字，
# 不會動到程式碼識別字或英文，故 fenced code block 內的 Go 程式安全。
_CC = opencc.OpenCC("s2twp")

# s2twp 偶爾會過度套用台灣慣用語，造成技術詞彙誤轉，這裡修正少數已知誤轉。
_FIX = {
    "擴充套件": "擴展",   # 扩展 → 不應變成「擴充套件(plugin)」
    "跳錶": "跳表",       # skip list 的「表」誤轉成「錶(watch)」
    "例項": "實例",       # instance 台灣慣用「實例」
    "全域性": "全域",     # 全局 → 不應加上「性」
    "掛瞭": "掛了",       # 了 作語助詞誤轉成「瞭」
}


def to_traditional(text: str) -> str:
    text = _CC.convert(text)
    for a, b in _FIX.items():
        text = text.replace(a, b)
    return text


def fmt(q: dict) -> str:
    lines = [f"### Q: {q['q']}", "", "**核心回答：**", q["core"], "", "**深入原理：**"]
    for b in q.get("dive", []):
        lines.append(f"- {b}")
    if q.get("svg"):
        # Inline SVG diagram, kept inside the 深入原理 section. Fenced as ```svg```
        # so build_site.py renders it as raw html instead of escaping it.
        lines += ["", "```svg", q["svg"].strip(), "```"]
    lines += ["", "**考官可能追問：**"]
    for fq, fa in q.get("followups", []):
        lines += [f"- Q: {fq}", f"  - A: {fa}"]
    lines += ["", "**常見陷阱 / 易錯點：**"]
    for p in q.get("pitfalls", []):
        lines.append(f"- {p}")
    if q.get("resume"):
        lines += ["", "**結合履歷：**", q["resume"]]
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def write_file(name: str, title: str, sources: str, topics: list[dict]) -> int:
    header = f"""# {title}

> 來源：{sources}
> 題數：{len(topics)} 道 | 深度：Senior Backend 面試級
> 格式：核心回答 → 深入原理 → 追問 Q&A → 常見陷阱 → 履歷結合

---

"""
    body = "".join(fmt(t) for t in topics)
    path = OUT / name
    path.write_text(to_traditional(header + body), encoding="utf-8")
    return len(topics)


# Import topic modules
from topics_go import GO_TOPICS
from topics_redis_mysql import REDIS_TOPICS, MYSQL_TOPICS
from topics_messaging import KAFKA_TOPICS, ROCKETMQ_TOPICS, RABBITMQ_TOPICS
from topics_api_nosql import GRPC_TOPICS, WEBSOCKET_TOPICS, MONGODB_TOPICS
from topics_system_perf_java_docker import (
    SYSTEM_DESIGN_TOPICS, PPROF_TOPICS, JAVA_TOPICS, DOCKER_AWS_TOPICS,
)

COUNTS = {}

COUNTS["go"] = write_file(
    "go.md", "Go 面試 Q&A",
    "go-questions（GMP/GC/channel/map/slice/interface/context/compile）、interview-go（question/base）、go-interview-practice",
    GO_TOPICS,
)
COUNTS["redis"] = write_file(
    "redis.md", "Redis 面試 Q&A",
    "interview-go（redis/base）、go-questions、tech-vault",
    REDIS_TOPICS,
)
COUNTS["mysql"] = write_file(
    "mysql.md", "MySQL 面試 Q&A",
    "interview-go（mysql/）、tech-vault",
    MYSQL_TOPICS,
)
COUNTS["kafka"] = write_file(
    "kafka.md", "Kafka 面試 Q&A",
    "interview-go（architecture/0002）、tech-vault",
    KAFKA_TOPICS,
)
COUNTS["rocketmq"] = write_file(
    "rocketmq.md", "RocketMQ 面試 Q&A",
    "tech-vault、交易所實務",
    ROCKETMQ_TOPICS,
)
COUNTS["grpc"] = write_file(
    "grpc.md", "gRPC 面試 Q&A",
    "tech-vault、交易所/體育數據實務",
    GRPC_TOPICS,
)
COUNTS["websocket"] = write_file(
    "websocket.md", "WebSocket 面試 Q&A",
    "tech-vault、行情推送實務",
    WEBSOCKET_TOPICS,
)
COUNTS["mongodb"] = write_file(
    "mongodb.md", "MongoDB 面試 Q&A",
    "tech-vault、體育/客服實務",
    MONGODB_TOPICS,
)
COUNTS["rabbitmq"] = write_file(
    "rabbitmq.md", "RabbitMQ 面試 Q&A",
    "tech-vault、體育數據實務",
    RABBITMQ_TOPICS,
)
COUNTS["system-design"] = write_file(
    "system-design.md", "System Design 面試 Q&A",
    "interview-go（architecture/）、tech-vault",
    SYSTEM_DESIGN_TOPICS,
)
COUNTS["performance-pprof"] = write_file(
    "performance-pprof.md", "Performance / pprof 面試 Q&A",
    "interview-go、tech-vault、生產調優實務",
    PPROF_TOPICS,
)
COUNTS["java-spring-boot"] = write_file(
    "java-spring-boot.md", "Java / Spring Boot 面試 Q&A",
    "tech-vault、Spring Boot 重構實務",
    JAVA_TOPICS,
)
COUNTS["docker-aws"] = write_file(
    "docker-aws.md", "Docker / AWS 面試 Q&A",
    "tech-vault、Docker Compose / AWS 實務",
    DOCKER_AWS_TOPICS,
)

total = sum(COUNTS.values())
total_bytes = sum((OUT / f"{k}.md").stat().st_size for k in COUNTS)
print("Topic counts:", COUNTS)
print(f"Total topics: {total}")
print(f"Total bytes: {total_bytes:,}")

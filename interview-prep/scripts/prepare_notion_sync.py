#!/usr/bin/env python3
"""Output Notion sync mapping."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "36f81d1e116e816e8ae3dd8f2343ee4e": "go.md",
    "36f81d1e116e817e80adf0df4300d3a6": "redis.md",
    "36f81d1e116e8110bfc6d53f9747ee25": "mysql.md",
    "36f81d1e116e81f0a165c93c6bb3720d": "kafka.md",
    "36f81d1e116e814aa2cbf4174a523ae7": "rocketmq.md",
    "36f81d1e116e8118ab9ad17fa33137f2": "grpc.md",
    "36f81d1e116e816a820ed629d7e37a7e": "websocket.md",
    "36f81d1e116e81f29f03e56b7de834ad": "mongodb.md",
    "36f81d1e116e811a9375c43dbb010ad7": "rabbitmq.md",
    "36f81d1e116e8174895deb4376028421": "system-design.md",
    "36f81d1e116e81428001fbcf9233d491": "performance-pprof.md",
    "36f81d1e116e81b18976da41014177c6": "java-spring-boot.md",
    "36f81d1e116e8106ae0bf417733361a4": "docker-aws.md",
}
out = Path("/tmp/notion_sync")
out.mkdir(exist_ok=True)
for pid, fname in PAGES.items():
    content = (ROOT / fname).read_text(encoding="utf-8")
    (out / f"{pid}.md").write_text(content, encoding="utf-8")
    print(f"{pid}\t{fname}\t{len(content)}")

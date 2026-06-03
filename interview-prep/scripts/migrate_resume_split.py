#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off: move resume → personal overlay; topics get scenario field."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from resume_utils import to_scenario, topic_id

SCRIPTS = Path(__file__).resolve().parent

# (module file, list attr, tech_key) — order matches build_site.TECHS
SOURCES = [
    ("topics_go.py", "GO_TOPICS", "go"),
    ("topics_redis_mysql.py", "REDIS_TOPICS", "redis"),
    ("topics_redis_mysql.py", "MYSQL_TOPICS", "mysql"),
    ("topics_system_perf_java_docker.py", "SYSTEM_DESIGN_TOPICS", "system-design"),
    ("topics_system_perf_java_docker.py", "PPROF_TOPICS", "performance-pprof"),
    ("topics_messaging.py", "KAFKA_TOPICS", "kafka"),
    ("topics_messaging.py", "ROCKETMQ_TOPICS", "rocketmq"),
    ("topics_api_nosql.py", "GRPC_TOPICS", "grpc"),
    ("topics_api_nosql.py", "WEBSOCKET_TOPICS", "websocket"),
    ("topics_api_nosql.py", "MONGODB_TOPICS", "mongodb"),
    ("topics_messaging.py", "RABBITMQ_TOPICS", "rabbitmq"),
    ("topics_system_perf_java_docker.py", "JAVA_TOPICS", "java-spring-boot"),
    ("topics_system_perf_java_docker.py", "DOCKER_AWS_TOPICS", "docker-aws"),
]


def load_lists():
    sys.path.insert(0, str(SCRIPTS))
    import topics_go  # noqa: E402
    import topics_redis_mysql  # noqa: E402
    import topics_messaging  # noqa: E402
    import topics_api_nosql  # noqa: E402
    import topics_system_perf_java_docker as tsp  # noqa: E402

    return {
        "GO_TOPICS": topics_go.GO_TOPICS,
        "REDIS_TOPICS": topics_redis_mysql.REDIS_TOPICS,
        "MYSQL_TOPICS": topics_redis_mysql.MYSQL_TOPICS,
        "KAFKA_TOPICS": topics_messaging.KAFKA_TOPICS,
        "ROCKETMQ_TOPICS": topics_messaging.ROCKETMQ_TOPICS,
        "RABBITMQ_TOPICS": topics_messaging.RABBITMQ_TOPICS,
        "GRPC_TOPICS": topics_api_nosql.GRPC_TOPICS,
        "WEBSOCKET_TOPICS": topics_api_nosql.WEBSOCKET_TOPICS,
        "MONGODB_TOPICS": topics_api_nosql.MONGODB_TOPICS,
        "SYSTEM_DESIGN_TOPICS": tsp.SYSTEM_DESIGN_TOPICS,
        "PPROF_TOPICS": tsp.PPROF_TOPICS,
        "JAVA_TOPICS": tsp.JAVA_TOPICS,
        "DOCKER_AWS_TOPICS": tsp.DOCKER_AWS_TOPICS,
    }


def patch_file(path: Path, replacements: list[tuple[str, str]]) -> int:
    text = path.read_text(encoding="utf-8")
    count = 0
    for old_line, new_line in replacements:
        if old_line not in text:
            # try without trailing comma variance
            old2 = old_line.rstrip(",")
            if old2 in text:
                text = text.replace(old2, new_line.rstrip(","), 1)
                count += 1
            continue
        text = text.replace(old_line, new_line, 1)
        count += 1
    path.write_text(text, encoding="utf-8")
    return count


def main():
    lists = load_lists()
    overlay: dict[str, str] = {}
    file_patches: dict[Path, list[tuple[str, str]]] = {}

    for fname, attr, tech_key in SOURCES:
        topics = lists[attr]
        path = SCRIPTS / fname
        content = path.read_text(encoding="utf-8")
        for idx, topic in enumerate(topics):
            resume = topic.get("resume")
            if not resume:
                continue
            tid = topic_id(tech_key, idx)
            overlay[tid] = resume
            scenario = to_scenario(resume, topic["q"], tech_key)
            old = f'        "resume": {json.dumps(resume, ensure_ascii=False)},'
            new = f'        "scenario": {json.dumps(scenario, ensure_ascii=False)},'
            old2 = '     "resume": ' + json.dumps(resume, ensure_ascii=False) + "},"
            new2 = '     "scenario": ' + json.dumps(scenario, ensure_ascii=False) + "},"
            if old2 in content:
                file_patches.setdefault(path, []).append((old2, new2))
            elif old in content:
                file_patches.setdefault(path, []).append((old, new))
            else:
                raise SystemExit(f"Could not find resume line for {tid} in {fname}")

    for path, reps in file_patches.items():
        n = patch_file(path, reps)
        print(f"Patched {path.name}: {n} lines")

    # write overlay
    lines = [
        '# -*- coding: utf-8 -*-',
        '"""Personal interview notes keyed by topic id (tech-index).',
        '',
        "Not embedded in public GitHub Pages builds (INCLUDE_PERSONAL=0).",
        '"""',
        "from __future__ import annotations",
        "",
        "PERSONAL_OVERLAY: dict[str, str] = {",
    ]
    for tid in sorted(overlay.keys()):
        lines.append(f"    {json.dumps(tid)}: {json.dumps(overlay[tid], ensure_ascii=False)},")
    lines.append("}")
    lines.append("")
    out = SCRIPTS / "resume_overlay.py"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(overlay)} entries)")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Helpers for splitting scenario (public) vs personal (overlay) notes."""
from __future__ import annotations

import re

_DOMAIN_REPLACEMENTS: list[tuple[str, str]] = [
    (r"（[^）]*負責人[^）]*）", ""),
    (r"（[^）]*Tech Lead[^）]*）", ""),
    (r"加密貨幣交易所|交易所場景|在交易所[^，。；]*", "交易/行情系統"),
    (r"交易所", "交易/行情系統"),
    (r"體育數據|体育数据|Betradar|LMAX Disruptor|Betgenius", "高吞吐數據管線"),
    (r"K\s*線|K线|K線", "時間序列/圖表資料"),
    (r"\d+[–\-~至到]+\d+\s*(s|ms|秒|毫秒)", "量化的延遲區間"),
    (r"\d+\s*(s|ms|秒|毫秒)", "延遲指標"),
    (r"3–5s→300–500ms|3-5s→300-500ms|>1000ms→亚秒", "明顯的延遲改善"),
    (r"實務上|實際|实务上|实际|實務經驗|实务经验|實際經驗|实际经验|我曾", "例如"),
    (r"interview-go q\d+[^。；]*", "常見面試題場景"),
    (r"全棧專案：[^。]+", "全端專案交付與容器化部署"),
    (r"实务（[^）]+）", "例如"),
]

_TECH_HINTS: dict[str, str] = {
    "go": "可結合自身服務中的 goroutine、context 與 pprof 排查經驗說明取捨。",
    "redis": "可結合快取、行情或訂單讀寫路徑中的命中率、延遲與一致性說明。",
    "mysql": "可結合索引、聚合查詢與線上變更（DDL）的實務取捨舉例。",
    "kafka": "可結合高吞吐訊息分發、consumer lag 與重平衡經驗說明。",
    "rocketmq": "可結合交易/通知場景的訊息可靠性與冪等設計舉例。",
    "grpc": "可結合內部服務整合、逾時與串流場景說明。",
    "websocket": "可結合即時推送、連線管理與水平擴展經驗說明。",
    "mongodb": "可結合文件模型、變更流與多來源資料落地舉例。",
    "rabbitmq": "可結合多 vendor 資料接入與路由策略說明。",
    "system-design": "可結合撮合、行情、對沖或秒殺等高併發系統設計經驗說明。",
    "performance-pprof": "可結合 pprof、flame graph 與生產調優案例說明。",
    "java-spring-boot": "可結合 Spring Boot 重構、JVM 與 legacy 整合經驗說明。",
    "docker-aws": "可結合容器化部署、CI/CD 與雲端維運實務說明。",
}


def to_scenario(resume: str, question: str, tech_key: str) -> str:
    """Derive a community-friendly scenario line from legacy resume text."""
    s = resume.strip()
    for pat, repl in _DOMAIN_REPLACEMENTS:
        s = re.sub(pat, repl, s)
    s = re.sub(r"\s+", " ", s).strip(" ，。；")
    if len(s) < 12 or re.search(r"3–5|300–500|Betradar|Disruptor|Gin/GORM", s):
        hint = _TECH_HINTS.get(tech_key, "建議搭配自身專案中的吞吐、延遲或一致性取捨舉例。")
        if len(s) >= 12:
            return s if len(s) <= 96 else s[:93] + "…"
        return hint
    if len(s) > 96:
        s = s[:93] + "…"
    return s


def topic_id(tech_key: str, index: int) -> str:
    return f"{tech_key}-{index}"

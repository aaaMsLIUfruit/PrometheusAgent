from __future__ import annotations

import re

from config import BOOKINFO_DISPLAY_SERVICES, DEFAULT_TIME_WINDOW_MINUTES

ZH = {
    "minute_1": "\u4e00\u5206\u949f",
    "minute_5": "\u4e94\u5206\u949f",
    "minute_10": "\u5341\u5206\u949f",
    "minute_15": "\u5341\u4e94\u5206\u949f",
    "recent": "\u6700\u8fd1",
    "memory": "\u5185\u5b58",
    "cpu_alt": "\u5904\u7406\u5668",
    "request_rate": "\u8bf7\u6c42\u91cf",
    "throughput": "\u541e\u5410",
    "error_rate": "\u9519\u8bef\u7387",
    "latency": "\u5ef6\u8fdf",
    "response_time": "\u54cd\u5e94\u65f6\u95f4",
    "restart": "\u91cd\u542f",
    "health_report": "\u5065\u5eb7\u62a5\u544a",
    "inspection": "\u5de1\u68c0",
    "cluster_status": "\u6574\u4f53\u72b6\u6001",
    "global_status": "\u5168\u5c40\u72b6\u6001",
    "trend": "\u8d8b\u52bf",
    "change": "\u53d8\u5316",
    "curve": "\u66f2\u7ebf",
    "ranking": "\u6392\u540d",
    "ranking2": "\u6392\u884c",
    "highest": "\u6700\u9ad8",
    "lowest": "\u6700\u4f4e",
    "all_services": "\u5404\u4e2a\u670d\u52a1",
    "all_services_2": "\u5404\u670d\u52a1",
}

TIME_PATTERNS = {
    1: ["1 minute", "1 min", "1m", ZH["minute_1"]],
    5: ["5 minute", "5 min", "5m", ZH["minute_5"], f"{ZH['recent']}{ZH['minute_5']}", f"{ZH['recent']}5\u5206\u949f"],
    10: ["10 minute", "10 min", "10m", ZH["minute_10"]],
    15: ["15 minute", "15 min", "15m", ZH["minute_15"]],
}

METRIC_KEYWORDS = {
    "memory": ["memory", ZH["memory"]],
    "cpu": ["cpu", ZH["cpu_alt"]],
    "request_rate": ["request", "qps", ZH["request_rate"], ZH["throughput"]],
    "error_rate": ["error", "5xx", ZH["error_rate"]],
    "latency": ["latency", ZH["latency"], ZH["response_time"]],
    "restart": ["restart", "pod", ZH["restart"]],
}


def _find_service(question: str) -> str | None:
    ordered = sorted(BOOKINFO_DISPLAY_SERVICES, key=len, reverse=True)
    lower_question = question.lower()
    for service_name in ordered:
        if service_name.lower() in lower_question:
            return service_name
    return None


def _find_metric(question: str) -> str | None:
    lower_question = question.lower()
    for metric, keywords in METRIC_KEYWORDS.items():
        if any(keyword.lower() in lower_question for keyword in keywords):
            return metric
    return None


def _find_time_window(question: str) -> tuple[int, bool]:
    lower_question = question.lower()
    for minutes, patterns in TIME_PATTERNS.items():
        if any(pattern.lower() in lower_question for pattern in patterns):
            return minutes, True
    match = re.search(rf"{ZH['recent']}?\s*(\d+)\s*\u5206\u949f", question)
    if match:
        return int(match.group(1)), True
    match = re.search(r"(?:last|recent)\s*(\d+)\s*(?:minutes|min|m)", lower_question)
    if match:
        return int(match.group(1)), True
    return DEFAULT_TIME_WINDOW_MINUTES, False


def parse_question(question: str, default_service: str | None = None, default_minutes: int | None = None) -> dict:
    clean_question = question.strip()
    lower_question = clean_question.lower()

    metric = _find_metric(clean_question)
    service = _find_service(clean_question) or default_service

    parsed_window, explicit_window = _find_time_window(clean_question) if clean_question else (DEFAULT_TIME_WINDOW_MINUTES, False)
    time_window = parsed_window if explicit_window else (default_minutes or parsed_window)

    is_health_report = any(
        keyword.lower() in lower_question
        for keyword in [ZH["health_report"], ZH["inspection"], ZH["cluster_status"], ZH["global_status"], "health report"]
    )
    is_trend = any(keyword.lower() in lower_question for keyword in [ZH["trend"], ZH["change"], ZH["curve"], "trend"])
    is_ranking = any(
        keyword.lower() in lower_question
        for keyword in [ZH["ranking"], ZH["ranking2"], ZH["highest"], ZH["lowest"], ZH["all_services"], ZH["all_services_2"], "ranking"]
    )
    is_restart = ZH["restart"] in clean_question or "restart" in lower_question

    if is_health_report:
        intent = "health_report"
    elif is_restart:
        intent = "restart_query"
        metric = metric or "restart"
    elif is_trend:
        intent = "trend_query"
    elif is_ranking or (metric == "memory" and not service):
        intent = "ranking_query"
    elif metric and service:
        intent = "metric_query"
    else:
        intent = "unknown"

    return {
        "question": clean_question,
        "intent": intent,
        "service": service,
        "metric": metric,
        "time_window_minutes": time_window,
        "time_window_explicit": explicit_window,
        "is_trend": intent == "trend_query",
        "is_ranking": intent == "ranking_query",
        "is_health_report": intent == "health_report",
    }

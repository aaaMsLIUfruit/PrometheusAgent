from __future__ import annotations

import re

from config import BOOKINFO_DISPLAY_SERVICES, DEFAULT_TIME_WINDOW_MINUTES
from llm_client import plan_question_with_llm

ZH = {
    "minute_1": "一分钟",
    "minute_5": "五分钟",
    "minute_10": "十分钟",
    "minute_15": "十五分钟",
    "recent": "最近",
    "memory": "内存",
    "cpu_alt": "处理器",
    "request_rate": "请求量",
    "throughput": "吞吐",
    "error_rate": "错误率",
    "latency": "延迟",
    "response_time": "响应时间",
    "restart": "重启",
    "health_report": "健康报告",
    "inspection": "巡检",
    "cluster_status": "整体状态",
    "global_status": "全局状态",
    "trend": "趋势",
    "change": "变化",
    "curve": "曲线",
    "ranking": "排名",
    "ranking2": "排行",
    "highest": "最高",
    "lowest": "最低",
    "all_services": "各个服务",
    "all_services_2": "各服务",
}

TIME_PATTERNS = {
    1: ["1 minute", "1 min", "1m", ZH["minute_1"]],
    5: ["5 minute", "5 min", "5m", ZH["minute_5"], f"{ZH['recent']}{ZH['minute_5']}", f"{ZH['recent']}5分钟"],
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
    match = re.search(rf"{ZH['recent']}?\s*(\d+)\s*分钟", question)
    if match:
        return int(match.group(1)), True
    match = re.search(r"(?:last|recent)\s*(\d+)\s*(?:minutes|min|m)", lower_question)
    if match:
        return int(match.group(1)), True
    return DEFAULT_TIME_WINDOW_MINUTES, False


def _fallback_parse(question: str, default_service: str | None = None, default_minutes: int | None = None) -> dict:
    clean_question = question.strip()
    lower_question = clean_question.lower()
    metric = _find_metric(clean_question)
    service = _find_service(clean_question) or default_service
    parsed_window, explicit_window = _find_time_window(clean_question) if clean_question else (DEFAULT_TIME_WINDOW_MINUTES, False)
    time_window = parsed_window if explicit_window else (default_minutes or parsed_window)
    is_health_report = any(keyword.lower() in lower_question for keyword in [ZH["health_report"], ZH["inspection"], ZH["cluster_status"], ZH["global_status"], "health report"])
    is_trend = any(keyword.lower() in lower_question for keyword in [ZH["trend"], ZH["change"], ZH["curve"], "trend"])
    is_ranking = any(keyword.lower() in lower_question for keyword in [ZH["ranking"], ZH["ranking2"], ZH["highest"], ZH["lowest"], ZH["all_services"], ZH["all_services_2"], "ranking"])
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
        "selected_tool_names": [],
        "planner_source": "rules",
    }


def parse_question(question: str, default_service: str | None = None, default_minutes: int | None = None) -> dict:
    fallback = _fallback_parse(question, default_service=default_service, default_minutes=default_minutes)
    llm_plan = plan_question_with_llm(question, default_service=default_service, default_minutes=default_minutes or DEFAULT_TIME_WINDOW_MINUTES)
    if not llm_plan.get("ok"):
        fallback["planner_error"] = llm_plan.get("error")
        return fallback
    explicit_window = fallback["time_window_explicit"]
    return {
        "question": question.strip(),
        "intent": llm_plan.get("intent", fallback["intent"]),
        "service": llm_plan.get("service", fallback["service"]),
        "metric": llm_plan.get("metric", fallback["metric"]),
        "time_window_minutes": llm_plan.get("time_window_minutes", fallback["time_window_minutes"]),
        "time_window_explicit": explicit_window,
        "is_trend": llm_plan.get("intent") == "trend_query",
        "is_ranking": llm_plan.get("intent") == "ranking_query",
        "is_health_report": llm_plan.get("intent") == "health_report",
        "selected_tool_names": llm_plan.get("selected_tool_names", []),
        "planner_reasoning": llm_plan.get("reasoning"),
        "planner_source": "llm",
    }

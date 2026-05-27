from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from metrics_client import (
    get_memory_ranking,
    get_pod_restart_counts,
    get_service_cpu,
    get_service_cpu_series,
    get_service_error_rate,
    get_service_latency,
    get_service_latency_series,
    get_service_memory,
    get_service_request_rate,
    get_service_request_rate_series,
)


@dataclass
class ToolSpec:
    name: str
    description: str
    tool_type: str
    metric: str
    function: Callable
    example: str


def get_tool_registry() -> list[ToolSpec]:
    return [
        ToolSpec("query_service_memory_ranking", "Rank Bookinfo services or Pods by memory usage.", "instant_query", "memory", get_memory_ranking, "What is the memory usage ranking in Bookinfo?"),
        ToolSpec("query_service_cpu", "Query CPU usage for one service over the last N minutes.", "instant_query", "cpu", get_service_cpu, "How much CPU is reviews using?"),
        ToolSpec("query_cpu_trend", "Query CPU trend for one service over the last N minutes.", "range_query", "cpu", get_service_cpu_series, "What is the CPU trend for reviews-v2 in the last five minutes?"),
        ToolSpec("query_service_memory", "Query current memory usage for one service.", "instant_query", "memory", get_service_memory, "How much memory is reviews using?"),
        ToolSpec("query_request_rate", "Query request rate for one service.", "instant_query", "request_rate", get_service_request_rate, "What is the request rate for productpage?"),
        ToolSpec("query_request_rate_trend", "Query request-rate trend for one service.", "range_query", "request_rate", get_service_request_rate_series, "Show the request trend for productpage."),
        ToolSpec("query_error_rate", "Query 5xx error rate for one service.", "instant_query", "error_rate", get_service_error_rate, "Does reviews have 5xx errors?"),
        ToolSpec("query_latency", "Query average latency for one service.", "instant_query", "latency", get_service_latency, "What is the latency of reviews?"),
        ToolSpec("query_latency_trend", "Query latency trend for one service.", "range_query", "latency", get_service_latency_series, "Show the latency trend for productpage."),
        ToolSpec("query_pod_restart_counts", "Query Pod restart counts in the Bookinfo namespace.", "summary_query", "restart", get_pod_restart_counts, "Are there any restarted Pods in Bookinfo?"),
    ]


def find_tool_by_name(name: str) -> ToolSpec | None:
    for tool in get_tool_registry():
        if tool.name == name:
            return tool
    return None


def choose_tools(parsed_question: dict) -> list[ToolSpec]:
    intent = parsed_question.get("intent")
    metric = parsed_question.get("metric")

    if intent == "ranking_query" and metric == "memory":
        return [find_tool_by_name("query_service_memory_ranking")]
    if intent == "trend_query" and metric == "cpu":
        return [find_tool_by_name("query_cpu_trend")]
    if intent == "trend_query" and metric == "request_rate":
        return [find_tool_by_name("query_request_rate_trend")]
    if intent == "trend_query" and metric == "latency":
        return [find_tool_by_name("query_latency_trend")]
    if intent == "restart_query":
        return [find_tool_by_name("query_pod_restart_counts")]
    if intent == "metric_query" and metric == "cpu":
        return [find_tool_by_name("query_service_cpu")]
    if intent == "metric_query" and metric == "memory":
        return [find_tool_by_name("query_service_memory")]
    if intent == "metric_query" and metric == "request_rate":
        return [find_tool_by_name("query_request_rate")]
    if intent == "metric_query" and metric == "error_rate":
        return [find_tool_by_name("query_error_rate")]
    if intent == "metric_query" and metric == "latency":
        return [find_tool_by_name("query_latency")]
    return []

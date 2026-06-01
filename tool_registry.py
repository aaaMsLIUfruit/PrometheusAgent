from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from langchain_core.tools import StructuredTool
from langchain_core.tools.render import render_text_description

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
        ToolSpec(
            "query_service_memory_ranking",
            "Query the memory ranking for all Bookinfo services or Pods. Best for questions like which service uses the most memory or whether memory usage looks abnormal.",
            "instant_query",
            "memory",
            get_memory_ranking,
            "Which Bookinfo service is using the most memory?",
        ),
        ToolSpec(
            "query_service_cpu",
            "Query CPU usage for one service in the recent time window. Best for single-service CPU status questions.",
            "instant_query",
            "cpu",
            get_service_cpu,
            "How much CPU is reviews using right now?",
        ),
        ToolSpec(
            "query_cpu_trend",
            "Query CPU trend for one service over time and use it when the user asks about changes, trends, rising load, or a line chart.",
            "range_query",
            "cpu",
            get_service_cpu_series,
            "What is the CPU trend for reviews-v2 in the last five minutes?",
        ),
        ToolSpec(
            "query_service_memory",
            "Query current memory usage for one service.",
            "instant_query",
            "memory",
            get_service_memory,
            "How much memory is ratings using?",
        ),
        ToolSpec(
            "query_request_rate",
            "Query request rate for one service. Best for traffic volume, QPS, or warm-up verification questions.",
            "instant_query",
            "request_rate",
            get_service_request_rate,
            "What is the request rate for details in the last five minutes?",
        ),
        ToolSpec(
            "query_request_rate_trend",
            "Query request-rate trend over time. Best for questions about traffic growth or traffic curves.",
            "range_query",
            "request_rate",
            get_service_request_rate_series,
            "Show the request-rate trend for productpage.",
        ),
        ToolSpec(
            "query_error_rate",
            "Query 5xx error rate for one service. Best for failure and error-monitoring questions.",
            "instant_query",
            "error_rate",
            get_service_error_rate,
            "Does reviews have a 5xx problem?",
        ),
        ToolSpec(
            "query_latency",
            "Query average latency for one service. Best for 'is it slow' or performance questions.",
            "instant_query",
            "latency",
            get_service_latency,
            "Is reviews latency high?",
        ),
        ToolSpec(
            "query_latency_trend",
            "Query latency trend over time. Best for questions about latency change, spikes, or performance charts.",
            "range_query",
            "latency",
            get_service_latency_series,
            "Show the latency trend for reviews.",
        ),
        ToolSpec(
            "query_pod_restart_counts",
            "Query restart counts for Pods in the Bookinfo namespace. Best for restart and stability questions.",
            "summary_query",
            "restart",
            get_pod_restart_counts,
            "Are there any restarted Pods in Bookinfo?",
        ),
    ]


def describe_tools_for_llm() -> str:
    return render_text_description(get_langchain_tools())


def get_langchain_tools() -> list[StructuredTool]:
    tools = []
    for tool in get_tool_registry():
        tools.append(
            StructuredTool.from_function(
                func=tool.function,
                name=tool.name,
                description=f"{tool.description} Example: {tool.example}",
            )
        )
    return tools


def find_tool_by_name(name: str) -> ToolSpec | None:
    for tool in get_tool_registry():
        if tool.name == name:
            return tool
    return None


def choose_tools(parsed_question: dict) -> list[ToolSpec]:
    selected_names = parsed_question.get("selected_tool_names") or []
    if selected_names:
        tools = [find_tool_by_name(name) for name in selected_names]
        return [tool for tool in tools if tool is not None]

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

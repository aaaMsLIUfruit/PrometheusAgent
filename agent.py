from __future__ import annotations

from config import BOOKINFO_SERVICES, MODE_MOCK_ABNORMAL, MODE_MOCK_NORMAL
from health_judge import judge_cluster_health
from k8s_client import check_productpage_access, get_service_health
from mock_data import get_mock_all_services, get_mock_memory_ranking, get_mock_metric, get_mock_series
from question_parser import parse_question
from report_generator import (
    generate_cluster_report,
    generate_memory_ranking_report,
    generate_metric_answer,
    generate_service_report,
    generate_trend_report,
    generate_unknown_question_answer,
)
from tool_registry import choose_tools


def _is_mock_mode(data_mode: str) -> bool:
    return data_mode in {MODE_MOCK_NORMAL, MODE_MOCK_ABNORMAL}


def _is_abnormal_mode(data_mode: str) -> bool:
    return data_mode == MODE_MOCK_ABNORMAL


def _format_restart_answer(items: list[dict]) -> str:
    lines = ["Current Pod restart counts:", ""]
    lines.extend(f"- {item['name']}: {item['value']} times" for item in items)
    return "\n".join(lines)


def collect_cluster_metrics() -> dict:
    from metrics_client import get_service_cpu, get_service_error_rate, get_service_latency, get_service_memory, get_service_request_rate

    all_metrics = {}
    for service_name in BOOKINFO_SERVICES:
        cpu = get_service_cpu(service_name)
        memory = get_service_memory(service_name)
        request_rate = get_service_request_rate(service_name)
        error_rate = get_service_error_rate(service_name)
        latency = get_service_latency(service_name)
        health = get_service_health(service_name)
        inferred_running = any(item.get("ok", False) for item in [cpu, memory])
        if health.get("ok"):
            status = "Running" if health.get("healthy") else "Unknown"
        else:
            status = "Running" if inferred_running else "Unknown"
        all_metrics[service_name] = {
            "cpu": cpu.get("value") or 0.0,
            "memory": memory.get("value") or 0.0,
            "request_rate": request_rate.get("value") or 0.0,
            "error_rate": error_rate.get("value") or 0.0,
            "latency": latency.get("value") or 0.0,
            "restarts": 0,
            "status": status,
            "metrics_available": {
                "cpu": cpu.get("ok", False),
                "memory": memory.get("ok", False),
                "request_rate": request_rate.get("ok", False),
                "error_rate": error_rate.get("ok", False),
                "latency": latency.get("ok", False),
            },
        }
    return all_metrics


def _run_mock(parsed: dict, data_mode: str) -> dict:
    abnormal = _is_abnormal_mode(data_mode)
    intent = parsed["intent"]
    service_name = parsed.get("service")
    metric = parsed.get("metric")
    minutes = parsed.get("time_window_minutes", 5)

    if intent == "ranking_query":
        ranking_result = get_mock_memory_ranking(abnormal=abnormal)
        return {"ok": ranking_result["ok"], "answer": generate_memory_ranking_report(ranking_result), "tool_results": [ranking_result], "chart_data": ranking_result, "chart_kind": "memory_bar"}
    if intent == "trend_query" and service_name and metric:
        series_result = get_mock_series(service_name, metric, abnormal=abnormal, minutes=minutes)
        return {"ok": series_result["ok"], "answer": generate_trend_report(service_name, metric, series_result), "tool_results": [series_result], "chart_data": series_result, "chart_kind": "series"}
    if intent == "restart_query":
        services = get_mock_all_services(abnormal=abnormal)
        items = [{"name": name, "value": values["restarts"], "unit": "count"} for name, values in services.items()]
        restart_result = {"ok": True, "metric": "restart", "items": items, "promql": "mock", "error": None, "source": "mock"}
        return {"ok": True, "answer": _format_restart_answer(items), "tool_results": [restart_result], "chart_data": None, "chart_kind": None}
    if intent == "health_report":
        services = get_mock_all_services(abnormal=abnormal)
        return {"ok": True, "answer": generate_cluster_report(services, productpage_ok=not abnormal), "tool_results": [judge_cluster_health(services)], "chart_data": None, "chart_kind": None, "cluster_metrics": services}
    if intent == "metric_query" and service_name and metric:
        metric_result = get_mock_metric(service_name, metric, abnormal=abnormal)
        return {"ok": metric_result["ok"], "answer": generate_metric_answer(parsed, metric_result), "tool_results": [metric_result], "chart_data": None, "chart_kind": None}
    return {"ok": False, "answer": generate_unknown_question_answer(), "tool_results": [], "chart_data": None, "chart_kind": None}


def _run_real(parsed: dict) -> dict:
    if parsed["intent"] == "health_report":
        all_metrics = collect_cluster_metrics()
        productpage = check_productpage_access()
        return {"ok": True, "answer": generate_cluster_report(all_metrics, productpage_ok=productpage["ok"]), "tool_results": [productpage], "chart_data": None, "chart_kind": None, "cluster_metrics": all_metrics}

    selected_tools = [tool for tool in choose_tools(parsed) if tool is not None]
    if not selected_tools:
        return {"ok": False, "answer": generate_unknown_question_answer(), "tool_results": [], "chart_data": None, "chart_kind": None}

    tool = selected_tools[0]
    service_name = parsed.get("service")
    minutes = parsed.get("time_window_minutes", 5)

    if tool.name == "query_service_memory_ranking":
        result = tool.function()
        return {"ok": result["ok"], "answer": generate_memory_ranking_report(result), "tool_results": [result], "chart_data": result, "chart_kind": "memory_bar"}
    if tool.tool_type == "range_query":
        result = tool.function(service_name, minutes)
        return {"ok": result["ok"], "answer": generate_trend_report(service_name, parsed.get("metric"), result), "tool_results": [result], "chart_data": result, "chart_kind": "series"}
    if tool.metric == "restart":
        result = tool.function()
        return {"ok": result["ok"], "answer": _format_restart_answer(result.get("items", [])), "tool_results": [result], "chart_data": None, "chart_kind": None}

    result = tool.function(service_name, minutes) if tool.metric in {"cpu", "request_rate", "error_rate", "latency"} else tool.function(service_name)
    cluster_metrics = collect_cluster_metrics() if service_name in BOOKINFO_SERVICES else None
    service_report = generate_service_report(service_name, cluster_metrics.get(service_name, {})) if cluster_metrics and service_name in cluster_metrics else None
    return {"ok": result["ok"], "answer": generate_metric_answer(parsed, result), "tool_results": [result], "chart_data": None, "chart_kind": None, "cluster_metrics": cluster_metrics, "service_report": service_report}


def run_agent(question: str, data_mode: str, default_service: str | None = None, default_minutes: int = 5) -> dict:
    parsed = parse_question(question, default_service=default_service, default_minutes=default_minutes)
    selected_tools = [tool for tool in choose_tools(parsed) if tool is not None]
    result = _run_mock(parsed, data_mode) if _is_mock_mode(data_mode) else _run_real(parsed)
    result["parsed"] = parsed
    result["selected_tools"] = [{"name": tool.name, "description": tool.description, "tool_type": tool.tool_type, "metric": tool.metric, "example": tool.example} for tool in selected_tools]
    result["error"] = None if result.get("ok") else result.get("answer")
    return result

from __future__ import annotations

import time

import requests

from config import (
    BOOKINFO_NAMESPACE,
    BOOKINFO_WORKLOAD_PATTERNS,
    DEFAULT_QUERY_STEP_SECONDS,
    DEFAULT_TIME_WINDOW_MINUTES,
    PROMETHEUS_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from k8s_client import get_pod_restart_count


def _prometheus_error(promql: str, error: str, value_key: str = "value") -> dict:
    base = {
        "ok": False,
        "promql": promql,
        "raw": None,
        "error": error,
        "source": "prometheus",
    }
    if value_key == "series":
        base["series"] = []
    else:
        base["value"] = None
    return base


def _extract_value(payload: dict) -> float | None:
    try:
        results = payload["data"]["result"]
        if not results:
            return None
        return float(results[0]["value"][1])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def query_prometheus(promql: str) -> dict:
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return _prometheus_error(promql, f"Prometheus query failed: {exc}")
    except ValueError:
        return _prometheus_error(promql, "Prometheus returned invalid JSON.")

    value = _extract_value(payload)
    if value is None:
        return _prometheus_error(promql, "Prometheus returned no data.")

    return {
        "ok": True,
        "promql": promql,
        "value": value,
        "raw": payload,
        "error": None,
        "source": "prometheus",
    }


def query_prometheus_range(promql: str, minutes: int = 5, step_seconds: int = 30) -> dict:
    end_time = int(time.time())
    start_time = end_time - max(1, minutes) * 60
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": promql,
                "start": start_time,
                "end": end_time,
                "step": max(1, step_seconds),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return _prometheus_error(promql, f"Prometheus range query failed: {exc}", value_key="series")
    except ValueError:
        return _prometheus_error(promql, "Prometheus returned invalid JSON.", value_key="series")

    try:
        results = payload["data"]["result"]
        if not results:
            return _prometheus_error(promql, "Prometheus returned no time series.", value_key="series")
        values = results[0]["values"]
        series = [{"timestamp": int(point[0]), "value": float(point[1])} for point in values]
    except (KeyError, IndexError, TypeError, ValueError):
        return _prometheus_error(promql, "Failed to parse Prometheus range result.", value_key="series")

    if not series:
        return _prometheus_error(promql, "Prometheus returned no time series.", value_key="series")

    return {
        "ok": True,
        "promql": promql,
        "series": series,
        "raw": payload,
        "error": None,
        "source": "prometheus",
    }


def _service_pattern(service_name: str) -> str:
    return BOOKINFO_WORKLOAD_PATTERNS.get(service_name, f"{service_name}.*")


def _metric_result(metric: str, service_name: str, unit: str, promql: str, response: dict, value: float | None = None) -> dict:
    return {
        "ok": response["ok"],
        "metric": metric,
        "service": service_name,
        "value": response["value"] if value is None and response["ok"] else value,
        "unit": unit,
        "promql": promql,
        "raw": response.get("raw"),
        "error": response.get("error"),
        "source": response.get("source", "prometheus"),
    }


def get_service_cpu(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    promql = (
        'sum(rate(container_cpu_usage_seconds_total{namespace="%s",pod=~"%s",container!="POD",image!=""}[%sm]))'
        % (BOOKINFO_NAMESPACE, _service_pattern(service_name), minutes)
    )
    response = query_prometheus(promql)
    return _metric_result("cpu", service_name, "cores", promql, response)


def get_service_memory(service_name: str) -> dict:
    promql = (
        'sum(container_memory_working_set_bytes{namespace="%s",pod=~"%s",container!="POD",image!=""}) / 1024 / 1024'
        % (BOOKINFO_NAMESPACE, _service_pattern(service_name))
    )
    response = query_prometheus(promql)
    return _metric_result("memory", service_name, "MiB", promql, response)


def get_service_request_rate(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    primary_promql = (
        'sum(rate(istio_requests_total{destination_service_name="%s",destination_workload_namespace="%s"}[%sm]))'
        % (service_name, BOOKINFO_NAMESPACE, minutes)
    )
    primary_response = query_prometheus(primary_promql)
    if primary_response["ok"]:
        return _metric_result("request_rate", service_name, "req/s", primary_promql, primary_response)

    fallback_promql = (
        'sum(rate(istio_requests_total{destination_workload=~"%s",destination_workload_namespace="%s"}[%sm]))'
        % (_service_pattern(service_name), BOOKINFO_NAMESPACE, minutes)
    )
    fallback_response = query_prometheus(fallback_promql)
    if fallback_response["ok"]:
        return _metric_result("request_rate", service_name, "req/s", fallback_promql, fallback_response)

    if service_name == "productpage":
        source_promql = (
            'sum(rate(istio_requests_total{source_workload=~"%s",source_workload_namespace="%s"}[%sm]))'
            % (_service_pattern(service_name), BOOKINFO_NAMESPACE, minutes)
        )
        source_response = query_prometheus(source_promql)
        if source_response["ok"]:
            result = _metric_result("request_rate", service_name, "req/s", source_promql, source_response)
            result["note"] = "Used source_workload fallback because destination-side productpage traffic was not present."
            return result

    result = _metric_result("request_rate", service_name, "req/s", primary_promql, primary_response)
    result["note"] = "No matching Istio request-rate series was found for this service."
    return result


def get_service_error_rate(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    promql = (
        'sum(rate(istio_requests_total{destination_service_name="%s",destination_workload_namespace="%s",response_code=~"5.."}[%sm]))'
        % (service_name, BOOKINFO_NAMESPACE, minutes)
    )
    response = query_prometheus(promql)
    return _metric_result("error_rate", service_name, "errors/s", promql, response)


def get_service_latency(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    promql = (
        'sum(rate(istio_request_duration_milliseconds_sum{destination_service_name="%s",destination_workload_namespace="%s"}[%sm])) / '
        'sum(rate(istio_request_duration_milliseconds_count{destination_service_name="%s",destination_workload_namespace="%s"}[%sm]))'
        % (service_name, BOOKINFO_NAMESPACE, minutes, service_name, BOOKINFO_NAMESPACE, minutes)
    )
    response = query_prometheus(promql)
    if response["ok"]:
        return _metric_result("latency", service_name, "ms", promql, response)

    fallback_promql = (
        'sum(rate(istio_request_duration_milliseconds_sum{destination_workload=~"%s",destination_workload_namespace="%s"}[%sm])) / '
        'sum(rate(istio_request_duration_milliseconds_count{destination_workload=~"%s",destination_workload_namespace="%s"}[%sm]))'
        % (_service_pattern(service_name), BOOKINFO_NAMESPACE, minutes, _service_pattern(service_name), BOOKINFO_NAMESPACE, minutes)
    )
    fallback_response = query_prometheus(fallback_promql)
    if fallback_response["ok"]:
        return _metric_result("latency", service_name, "ms", fallback_promql, fallback_response)

    result = _metric_result("latency", service_name, "ms", promql, response)
    result["note"] = "No matching Istio latency series was found for this service."
    return result


def _series_result(metric: str, service_name: str, unit: str, promql: str, response: dict) -> dict:
    return {
        "ok": response["ok"],
        "metric": metric,
        "service": service_name,
        "series": response.get("series", []),
        "unit": unit,
        "promql": promql,
        "raw": response.get("raw"),
        "error": response.get("error"),
        "source": response.get("source", "prometheus"),
    }


def get_service_cpu_series(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    promql = (
        'sum(rate(container_cpu_usage_seconds_total{namespace="%s",pod=~"%s",container!="POD",image!=""}[%sm]))'
        % (BOOKINFO_NAMESPACE, _service_pattern(service_name), minutes)
    )
    response = query_prometheus_range(promql, minutes=minutes, step_seconds=DEFAULT_QUERY_STEP_SECONDS)
    return _series_result("cpu", service_name, "cores", promql, response)


def get_service_request_rate_series(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    primary_promql = (
        'sum(rate(istio_requests_total{destination_service_name="%s",destination_workload_namespace="%s"}[%sm]))'
        % (service_name, BOOKINFO_NAMESPACE, minutes)
    )
    response = query_prometheus_range(primary_promql, minutes=minutes, step_seconds=DEFAULT_QUERY_STEP_SECONDS)
    if response["ok"]:
        return _series_result("request_rate", service_name, "req/s", primary_promql, response)

    fallback_promql = (
        'sum(rate(istio_requests_total{destination_workload=~"%s",destination_workload_namespace="%s"}[%sm]))'
        % (_service_pattern(service_name), BOOKINFO_NAMESPACE, minutes)
    )
    fallback_response = query_prometheus_range(fallback_promql, minutes=minutes, step_seconds=DEFAULT_QUERY_STEP_SECONDS)
    if fallback_response["ok"]:
        return _series_result("request_rate", service_name, "req/s", fallback_promql, fallback_response)

    if service_name == "productpage":
        source_promql = (
            'sum(rate(istio_requests_total{source_workload=~"%s",source_workload_namespace="%s"}[%sm]))'
            % (_service_pattern(service_name), BOOKINFO_NAMESPACE, minutes)
        )
        source_response = query_prometheus_range(source_promql, minutes=minutes, step_seconds=DEFAULT_QUERY_STEP_SECONDS)
        if source_response["ok"]:
            result = _series_result("request_rate", service_name, "req/s", source_promql, source_response)
            result["note"] = "Used source_workload fallback because destination-side productpage traffic was not present."
            return result

    result = _series_result("request_rate", service_name, "req/s", primary_promql, response)
    result["note"] = "No matching Istio request-rate series was found for this service."
    return result


def get_service_latency_series(service_name: str, minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    promql = (
        'sum(rate(istio_request_duration_milliseconds_sum{destination_service_name="%s",destination_workload_namespace="%s"}[%sm])) / '
        'sum(rate(istio_request_duration_milliseconds_count{destination_service_name="%s",destination_workload_namespace="%s"}[%sm]))'
        % (service_name, BOOKINFO_NAMESPACE, minutes, service_name, BOOKINFO_NAMESPACE, minutes)
    )
    response = query_prometheus_range(promql, minutes=minutes, step_seconds=DEFAULT_QUERY_STEP_SECONDS)
    return _series_result("latency", service_name, "ms", promql, response)


def get_memory_ranking(namespace: str = BOOKINFO_NAMESPACE) -> dict:
    promql = (
        'sum by (pod) (container_memory_working_set_bytes{namespace="%s",container!="POD",image!=""}) / 1024 / 1024'
        % namespace
    )
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("data", {}).get("result", [])
    except requests.RequestException as exc:
        return {"ok": False, "metric": "memory", "items": [], "promql": promql, "error": str(exc), "source": "prometheus"}
    except ValueError:
        return {"ok": False, "metric": "memory", "items": [], "promql": promql, "error": "Invalid JSON response.", "source": "prometheus"}

    if not results:
        return {"ok": False, "metric": "memory", "items": [], "promql": promql, "error": "Prometheus returned no data.", "source": "prometheus"}

    items = []
    for item in results:
        pod_name = item.get("metric", {}).get("pod", "unknown")
        value = item.get("value", [None, None])[1]
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        items.append({"name": pod_name, "value": round(numeric_value, 2), "unit": "MiB"})

    items.sort(key=lambda entry: entry["value"], reverse=True)
    return {"ok": True, "metric": "memory", "items": items, "promql": promql, "error": None, "source": "prometheus"}


def get_pod_restart_counts(namespace: str = BOOKINFO_NAMESPACE) -> dict:
    promql = 'sum by (pod) (kube_pod_container_status_restarts_total{namespace="%s"})' % namespace
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("data", {}).get("result", [])
        if results:
            items = []
            for item in results:
                pod_name = item.get("metric", {}).get("pod", "unknown")
                value = item.get("value", [None, None])[1]
                items.append({"name": pod_name, "value": int(float(value)), "unit": "count"})
            return {"ok": True, "metric": "restart", "items": items, "promql": promql, "error": None, "source": "prometheus"}
    except (requests.RequestException, ValueError):
        pass

    fallback = get_pod_restart_count(namespace=namespace)
    return {
        "ok": fallback["ok"],
        "metric": "restart",
        "items": fallback.get("items", []),
        "promql": promql,
        "error": fallback.get("error"),
        "source": "kubectl" if fallback["ok"] else "prometheus",
    }

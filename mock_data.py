from __future__ import annotations

from datetime import datetime, timedelta

from config import BOOKINFO_DISPLAY_SERVICES, METRIC_UNITS

NORMAL_METRICS = {
    "productpage": {
        "cpu": 0.05,
        "memory": 120.5,
        "request_rate": 2.1,
        "error_rate": 0.0,
        "latency": 42.0,
        "restarts": 0,
        "status": "Running",
    },
    "details": {
        "cpu": 0.02,
        "memory": 55.0,
        "request_rate": 1.8,
        "error_rate": 0.0,
        "latency": 28.0,
        "restarts": 0,
        "status": "Running",
    },
    "ratings": {
        "cpu": 0.03,
        "memory": 52.0,
        "request_rate": 1.0,
        "error_rate": 0.01,
        "latency": 65.0,
        "restarts": 1,
        "status": "Running",
    },
    "reviews": {
        "cpu": 0.12,
        "memory": 303.0,
        "request_rate": 1.5,
        "error_rate": 0.0,
        "latency": 42.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v1": {
        "cpu": 0.04,
        "memory": 96.0,
        "request_rate": 0.5,
        "error_rate": 0.0,
        "latency": 36.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v2": {
        "cpu": 0.04,
        "memory": 102.0,
        "request_rate": 0.5,
        "error_rate": 0.0,
        "latency": 48.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v3": {
        "cpu": 0.04,
        "memory": 105.0,
        "request_rate": 0.5,
        "error_rate": 0.0,
        "latency": 55.0,
        "restarts": 0,
        "status": "Running",
    },
}

ABNORMAL_METRICS = {
    "productpage": {
        "cpu": 0.24,
        "memory": 188.0,
        "request_rate": 2.4,
        "error_rate": 0.03,
        "latency": 540.0,
        "restarts": 1,
        "status": "Running",
    },
    "details": {
        "cpu": 0.03,
        "memory": 60.0,
        "request_rate": 1.6,
        "error_rate": 0.0,
        "latency": 42.0,
        "restarts": 0,
        "status": "Running",
    },
    "ratings": {
        "cpu": 0.03,
        "memory": 52.0,
        "request_rate": 1.0,
        "error_rate": 0.01,
        "latency": 65.0,
        "restarts": 1,
        "status": "Running",
    },
    "reviews": {
        "cpu": 0.12,
        "memory": 410.0,
        "request_rate": 1.3,
        "error_rate": 0.03,
        "latency": 320.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v1": {
        "cpu": 0.05,
        "memory": 120.0,
        "request_rate": 0.4,
        "error_rate": 0.0,
        "latency": 90.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v2": {
        "cpu": 0.12,
        "memory": 210.0,
        "request_rate": 0.4,
        "error_rate": 0.02,
        "latency": 330.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v3": {
        "cpu": 0.08,
        "memory": 170.0,
        "request_rate": 0.5,
        "error_rate": 0.01,
        "latency": 220.0,
        "restarts": 2,
        "status": "CrashLoopBackOff",
    },
}


def _base_metrics(abnormal: bool) -> dict:
    return ABNORMAL_METRICS if abnormal else NORMAL_METRICS


def get_mock_metric(service_name: str, metric: str, abnormal: bool = False) -> dict:
    metrics = _base_metrics(abnormal)
    item = metrics.get(service_name)
    if not item:
        return {
            "ok": False,
            "metric": metric,
            "service": service_name,
            "value": None,
            "unit": METRIC_UNITS.get(metric, ""),
            "promql": "mock",
            "raw": None,
            "error": f"Mock data for service '{service_name}' not found.",
            "source": "mock",
        }
    return {
        "ok": True,
        "metric": metric,
        "service": service_name,
        "value": float(item.get(metric, item.get("restarts", 0))),
        "unit": METRIC_UNITS.get(metric, "count"),
        "promql": "mock",
        "raw": item,
        "error": None,
        "source": "mock",
    }


def get_mock_all_services(abnormal: bool = False) -> dict:
    metrics = _base_metrics(abnormal)
    return {name: metrics[name].copy() for name in BOOKINFO_DISPLAY_SERVICES if name in metrics}


def get_mock_memory_ranking(abnormal: bool = False) -> dict:
    metrics = _base_metrics(abnormal)
    items = [
        {"name": name, "value": float(values["memory"]), "unit": "MiB"}
        for name, values in metrics.items()
    ]
    items.sort(key=lambda item: item["value"], reverse=True)
    return {
        "ok": True,
        "metric": "memory",
        "items": items,
        "promql": "mock",
        "error": None,
        "source": "mock",
    }


def get_mock_series(service_name: str, metric: str, abnormal: bool = False, minutes: int = 5) -> dict:
    result = get_mock_metric(service_name, metric, abnormal=abnormal)
    if not result["ok"]:
        return {
            "ok": False,
            "promql": "mock",
            "series": [],
            "raw": None,
            "error": result["error"],
            "source": "mock",
        }

    base_value = result["value"] or 0.0
    now = datetime.now()
    series = []
    offsets = [-0.25, -0.12, 0.08, -0.05, 0.14, -0.02, 0.1, -0.08, 0.04, 0.0]
    scale = 0.3 if abnormal else 0.12
    if metric == "latency":
        scale = 0.4 if abnormal else 0.18
    elif metric == "request_rate":
        scale = 0.22 if abnormal else 0.1

    for index in range(10):
        timestamp = now - timedelta(seconds=(9 - index) * max(1, int(minutes * 60 / 10)))
        value = max(0.0, base_value * (1 + offsets[index] * scale * 10))
        series.append({"timestamp": int(timestamp.timestamp()), "value": round(value, 4)})

    return {
        "ok": True,
        "promql": "mock",
        "series": series,
        "raw": {"service": service_name, "metric": metric},
        "error": None,
        "source": "mock",
    }

from __future__ import annotations


def judge_service_health(service_metrics: dict) -> dict:
    status = "healthy"
    problems = []
    suggestions = []

    runtime_status = service_metrics.get("status", "Unknown")
    restarts = service_metrics.get("restarts", 0) or 0
    error_rate = service_metrics.get("error_rate", 0.0) or 0.0
    latency = service_metrics.get("latency", 0.0) or 0.0
    memory = service_metrics.get("memory", 0.0) or 0.0
    cpu = service_metrics.get("cpu", 0.0) or 0.0

    if runtime_status not in {"Running", "Unknown"}:
        status = "critical"
        problems.append(f"Pod status is {runtime_status}.")
        suggestions.append("Check the failed Pod events and container logs.")

    if runtime_status == "Unknown":
        if status != "critical":
            status = "warning"
        problems.append("Runtime status could not be confirmed from live checks.")
        suggestions.append("Verify that port-forwarding and service discovery are working as expected.")

    if restarts > 0:
        if status != "critical":
            status = "warning"
        problems.append(f"Pod restarts detected: {restarts}.")
        suggestions.append("Inspect recent deployments and restart causes.")

    if error_rate > 0.01:
        if status != "critical":
            status = "warning"
        problems.append(f"5xx error rate is high: {error_rate:.3f} errors/s.")
        suggestions.append("Check upstream dependencies and application logs.")

    if latency > 500:
        status = "critical"
        problems.append(f"Latency is critical: {latency:.1f} ms.")
        suggestions.append("Investigate slow downstream calls and saturation.")
    elif latency > 200:
        if status != "critical":
            status = "warning"
        problems.append(f"Latency is elevated: {latency:.1f} ms.")
        suggestions.append("Watch latency trend and inspect slow requests.")

    if memory > 400:
        if status != "critical":
            status = "warning"
        problems.append(f"Memory usage is high: {memory:.1f} MiB.")
        suggestions.append("Check memory growth and possible leaks.")

    if cpu > 0.2:
        if status != "critical":
            status = "warning"
        problems.append(f"CPU usage is high: {cpu:.2f} cores.")
        suggestions.append("Check traffic spikes or hot code paths.")

    if not problems:
        suggestions.append("Current service state looks stable; continue routine monitoring.")

    return {
        "status": status,
        "problems": problems,
        "suggestions": suggestions,
    }


def judge_cluster_health(all_metrics: dict) -> dict:
    cluster_status = "healthy"
    service_results = {}
    all_problems = []
    all_suggestions = []

    for service_name, metrics in all_metrics.items():
        result = judge_service_health(metrics)
        service_results[service_name] = result
        all_problems.extend(f"{service_name}: {item}" for item in result["problems"])
        all_suggestions.extend(f"{service_name}: {item}" for item in result["suggestions"])

        if result["status"] == "critical":
            cluster_status = "critical"
        elif result["status"] == "warning" and cluster_status == "healthy":
            cluster_status = "warning"

    return {
        "status": cluster_status,
        "services": service_results,
        "problems": all_problems,
        "suggestions": all_suggestions,
    }

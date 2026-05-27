from __future__ import annotations

from health_judge import judge_cluster_health, judge_service_health


def generate_metric_answer(parsed_question: dict, tool_result: dict) -> str:
    if not tool_result.get("ok"):
        note = tool_result.get("note")
        if parsed_question.get("metric") == "request_rate":
            base = "No matching request-rate series was found in Prometheus for this exact filter."
            if note:
                return f"{base} {note} Try warming traffic again or querying details/reviews for a steadier demo."
            return f"{base} Try warming traffic again or querying details/reviews for a steadier demo."
        if parsed_question.get("metric") == "latency":
            return "No matching latency series was found yet. Generate a bit more traffic and query again."
        return f"Query failed: {tool_result.get('error', 'unknown error')}. Check live connectivity and metric labels."

    service_name = tool_result.get("service") or parsed_question.get("service") or "target service"
    metric = tool_result.get("metric")
    value = tool_result.get("value")
    unit = tool_result.get("unit", "")

    if metric == "cpu":
        verdict = "elevated" if (value or 0) > 0.2 else "stable"
        return f"{service_name} is using about {value:.4f} {unit} of CPU, which looks {verdict}."
    if metric == "memory":
        verdict = "high" if (value or 0) > 400 else "within a normal range"
        return f"{service_name} is using about {value:.2f} {unit} of memory, which is {verdict}."
    if metric == "request_rate":
        extra = f" {tool_result['note']}" if tool_result.get("note") else ""
        return f"{service_name} is serving about {value:.3f} {unit}. This metric is useful for verifying traffic warm-up effects.{extra}"
    if metric == "error_rate":
        verdict = "requires attention" if (value or 0) > 0.01 else "looks healthy"
        return f"{service_name} has about {value:.4f} {unit} of 5xx errors, which {verdict}."
    if metric == "latency":
        verdict = "high" if (value or 0) > 200 else "acceptable"
        extra = f" {tool_result['note']}" if tool_result.get("note") else ""
        return f"{service_name} has about {value:.2f} {unit} average latency, which is currently {verdict}.{extra}"
    return f"{service_name} returned {value} {unit} for metric {metric}."


def generate_memory_ranking_report(ranking_result: dict) -> str:
    if not ranking_result.get("ok"):
        return f"Memory ranking query failed: {ranking_result.get('error', 'unknown error')}."
    items = ranking_result.get("items", [])
    if not items:
        return "No memory ranking data is available right now."
    lines = ["Current Bookinfo memory usage ranking:", ""]
    for item in items[:4]:
        lines.append(f"- {item['name']}: {item['value']:.2f} {item['unit']}")
    lines.append("")
    lines.append(f"Highest current consumer: {items[0]['name']}.")
    return "\n".join(lines)


def generate_trend_report(service_name: str, metric: str, series_data: dict) -> str:
    if not series_data.get("ok"):
        return f"Trend query for {service_name} failed: {series_data.get('error', 'unknown error')}."
    values = [point["value"] for point in series_data.get("series", [])]
    if not values:
        return f"No trend data is available for {service_name}."
    start_value = values[0]
    end_value = values[-1]
    peak_value = max(values)
    low_value = min(values)
    if end_value > start_value * 1.15:
        direction = "shows a clear upward trend"
    elif end_value < start_value * 0.85:
        direction = "shows a downward trend"
    else:
        direction = "looks fairly stable"
    return f"{service_name} {direction} for {metric}. The observed range is about {low_value:.3f} to {peak_value:.3f}, and the latest value is about {end_value:.3f}."


def generate_service_report(service_name: str, service_metrics: dict) -> str:
    result = judge_service_health(service_metrics)
    status_map = {"healthy": "healthy", "warning": "needs attention", "critical": "is at risk"}
    lines = [f"{service_name} {status_map.get(result['status'], result['status'])}.", "", "Key evidence:"]
    lines.append(f"- CPU: {service_metrics.get('cpu', 0):.3f} cores")
    lines.append(f"- Memory: {service_metrics.get('memory', 0):.1f} MiB")
    lines.append(f"- Request rate: {service_metrics.get('request_rate', 0):.3f} req/s")
    lines.append(f"- Latency: {service_metrics.get('latency', 0):.1f} ms")
    lines.append(f"- 5xx error rate: {service_metrics.get('error_rate', 0):.4f} errors/s")
    lines.append(f"- Restarts: {service_metrics.get('restarts', 0)}")
    if result["problems"]:
        lines.append("")
        lines.append("Findings:")
        lines.extend(f"- {problem}" for problem in result["problems"])
    if result["suggestions"]:
        lines.append("")
        lines.append("Suggestions:")
        lines.extend(f"- {suggestion}" for suggestion in result["suggestions"][:3])
    return "\n".join(lines)


def summarize_riskiest_service(all_metrics: dict) -> str | None:
    if not all_metrics:
        return None
    scored = []
    for service_name, metrics in all_metrics.items():
        result = judge_service_health(metrics)
        score = {"healthy": 0, "warning": 1, "critical": 2}[result["status"]]
        signal = (metrics.get("latency", 0) or 0) + (metrics.get("error_rate", 0) or 0) * 1000 + (metrics.get("cpu", 0) or 0) * 100
        scored.append((score, signal, service_name, result))
    scored.sort(reverse=True)
    top = scored[0]
    if top[0] == 0:
        return None
    reasons = top[3]["problems"][:2]
    return f"{top[2]} ({'; '.join(reasons)})" if reasons else top[2]


def generate_cluster_report(all_metrics: dict, productpage_ok: bool = True) -> str:
    cluster = judge_cluster_health(all_metrics)
    status_map = {"healthy": "healthy", "warning": "warning", "critical": "critical"}
    lines = ["[Overall Status]", f"Bookinfo is currently {status_map.get(cluster['status'], cluster['status'])}.", "", "[Key Evidence]"]
    lines.append("- productpage is reachable." if productpage_ok else "- productpage is not reachable and should be checked first.")
    for service_name, metrics in all_metrics.items():
        lines.append(f"- {service_name}: status={metrics.get('status')}, cpu={metrics.get('cpu', 0):.3f}, memory={metrics.get('memory', 0):.1f} MiB, latency={metrics.get('latency', 0):.1f} ms")
    riskiest = summarize_riskiest_service(all_metrics)
    if riskiest:
        lines.append(f"- Highest-risk service: {riskiest}")
    lines.append("")
    lines.append("[Risk Notes]")
    if cluster["problems"]:
        lines.extend(f"- {problem}" for problem in cluster["problems"][:6])
    else:
        lines.append("- No obvious risk is detected.")
    lines.append("")
    lines.append("[Suggestions]")
    if cluster["suggestions"]:
        lines.extend(f"- {suggestion}" for suggestion in cluster["suggestions"][:6])
    else:
        lines.append("- Keep monitoring the same core metrics.")
    return "\n".join(lines)


def build_snapshot_change_rows(before: dict | None, after: dict | None) -> list[dict]:
    if not before or not after:
        return []
    rows = []
    for service_name, current in after.items():
        previous = before.get(service_name, {})
        rows.append(
            {
                "service": service_name,
                "cpu_delta": round((current.get("cpu", 0) or 0) - (previous.get("cpu", 0) or 0), 4),
                "memory_delta": round((current.get("memory", 0) or 0) - (previous.get("memory", 0) or 0), 2),
                "request_rate_delta": round((current.get("request_rate", 0) or 0) - (previous.get("request_rate", 0) or 0), 4),
                "error_rate_delta": round((current.get("error_rate", 0) or 0) - (previous.get("error_rate", 0) or 0), 4),
                "latency_delta": round((current.get("latency", 0) or 0) - (previous.get("latency", 0) or 0), 2),
            }
        )
    return rows


def generate_snapshot_summary(before: dict | None, after: dict | None) -> str:
    rows = build_snapshot_change_rows(before, after)
    if not rows:
        return "No before/after snapshot is available yet."
    rows.sort(key=lambda row: abs(row["latency_delta"]) + abs(row["request_rate_delta"]) * 20, reverse=True)
    top = rows[0]
    parts = []
    if top["request_rate_delta"] > 0.05:
        parts.append(f"request rate rose most on {top['service']} ({top['request_rate_delta']:+.3f} req/s)")
    if top["latency_delta"] > 20:
        parts.append(f"latency increased most on {top['service']} ({top['latency_delta']:+.1f} ms)")
    if top["error_rate_delta"] > 0.001:
        parts.append(f"error rate increased on {top['service']} ({top['error_rate_delta']:+.4f} errors/s)")
    return "Observed changes: " + (", ".join(parts) if parts else "the cluster stayed mostly stable between the two snapshots.")


def generate_unknown_question_answer() -> str:
    return "I could not confidently classify that question. Try memory ranking, CPU trend, request rate, error rate, latency, restarts, or a health report."

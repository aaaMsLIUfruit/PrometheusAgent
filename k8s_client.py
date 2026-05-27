from __future__ import annotations

import json
import subprocess
from pathlib import Path

import requests

from config import (
    BOOKINFO_NAMESPACE,
    DELAY_INJECTION_FILE,
    KUBECTL_TIMEOUT_SECONDS,
    PRODUCTPAGE_URL,
    REQUEST_TIMEOUT_SECONDS,
    ROUTE_RESET_FILE,
)


def run_kubectl(args: list[str]) -> dict:
    command = ["kubectl", *args]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=KUBECTL_TIMEOUT_SECONDS,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
            "error": None if completed.returncode == 0 else (completed.stderr or "kubectl command failed."),
        }
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "", "returncode": -1, "error": "kubectl is not installed or not in PATH."}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "", "returncode": -1, "error": "kubectl command timed out."}
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": "", "returncode": -1, "error": str(exc)}


def get_pod_status(namespace: str = BOOKINFO_NAMESPACE) -> dict:
    result = run_kubectl(["get", "pods", "-n", namespace])
    if not result["ok"]:
        return {"ok": False, "items": [], "raw": result["stdout"], "error": result["error"]}

    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    items = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 5:
            items.append({"name": parts[0], "ready": parts[1], "status": parts[2], "restarts": int(parts[3]) if parts[3].isdigit() else parts[3], "age": parts[4]})
    return {"ok": True, "items": items, "raw": result["stdout"], "error": None}


def get_pod_restart_count(namespace: str = BOOKINFO_NAMESPACE) -> dict:
    result = run_kubectl(["get", "pods", "-n", namespace, "-o", "json"])
    if not result["ok"]:
        fallback = get_pod_status(namespace=namespace)
        if not fallback["ok"]:
            return {"ok": False, "items": [], "error": result["error"]}
        items = [{"name": item["name"], "value": int(item["restarts"]) if str(item["restarts"]).isdigit() else 0, "unit": "count"} for item in fallback["items"]]
        return {"ok": True, "items": items, "error": None}

    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {"ok": False, "items": [], "error": "Failed to parse kubectl JSON output."}

    items = []
    for pod in payload.get("items", []):
        restart_sum = 0
        for container in pod.get("status", {}).get("containerStatuses", []):
            restart_sum += int(container.get("restartCount", 0) or 0)
        items.append({"name": pod.get("metadata", {}).get("name", "unknown"), "value": restart_sum, "unit": "count"})
    return {"ok": True, "items": items, "error": None}


def get_service_health(service_name: str) -> dict:
    result = run_kubectl(["get", "pods", "-n", BOOKINFO_NAMESPACE, "-l", f"app={service_name}", "-o", "json"])
    if not result["ok"]:
        return {"ok": False, "service": service_name, "healthy": False, "pods": [], "error": result["error"]}
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {"ok": False, "service": service_name, "healthy": False, "pods": [], "error": "Failed to parse pod health JSON."}

    pods = []
    healthy = False
    for item in payload.get("items", []):
        phase = item.get("status", {}).get("phase", "Unknown")
        pods.append({"name": item.get("metadata", {}).get("name", "unknown"), "status": phase})
        if phase == "Running":
            healthy = True
    return {"ok": True, "service": service_name, "healthy": healthy, "pods": pods, "error": None}


def check_productpage_access() -> dict:
    try:
        response = requests.get(PRODUCTPAGE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        return {"ok": response.status_code == 200, "status_code": response.status_code, "error": None if response.status_code == 200 else f"Unexpected status code: {response.status_code}"}
    except requests.RequestException as exc:
        return {"ok": False, "status_code": None, "error": str(exc)}


def check_prometheus_access(prometheus_url: str = "http://127.0.0.1:9090") -> dict:
    try:
        response = requests.get(f"{prometheus_url}/-/ready", timeout=REQUEST_TIMEOUT_SECONDS)
        return {"ok": response.status_code == 200, "status_code": response.status_code, "error": None if response.status_code == 200 else f"Unexpected status code: {response.status_code}"}
    except requests.RequestException as exc:
        return {"ok": False, "status_code": None, "error": str(exc)}


def warm_productpage_traffic(request_count: int = 80) -> dict:
    success_count = 0
    errors = []
    for _ in range(max(1, request_count)):
        try:
            response = requests.get(PRODUCTPAGE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                success_count += 1
            else:
                errors.append(f"HTTP {response.status_code}")
        except requests.RequestException as exc:
            errors.append(str(exc))
    return {
        "ok": success_count > 0,
        "requested": request_count,
        "successful": success_count,
        "failed": request_count - success_count,
        "error": None if success_count > 0 else ("; ".join(errors[:3]) if errors else "All traffic requests failed."),
    }


def _apply_manifest(manifest_path: str) -> dict:
    path = Path(manifest_path)
    if not path.exists():
        return {"ok": False, "stdout": "", "stderr": "", "returncode": -1, "error": f"Manifest file not found: {manifest_path}"}
    return run_kubectl(["apply", "-n", BOOKINFO_NAMESPACE, "-f", str(path)])


def inject_delay() -> dict:
    result = _apply_manifest(DELAY_INJECTION_FILE)
    return {"ok": result["ok"], "action": "inject_delay", "error": result.get("error"), "stdout": result.get("stdout", "")}


def reset_bookinfo_routes() -> dict:
    result = _apply_manifest(ROUTE_RESET_FILE)
    return {"ok": result["ok"], "action": "reset_routes", "error": result.get("error"), "stdout": result.get("stdout", "")}

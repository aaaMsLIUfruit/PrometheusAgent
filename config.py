import os

from dotenv import load_dotenv

load_dotenv()

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090")
PRODUCTPAGE_URL = os.getenv("PRODUCTPAGE_URL", "http://127.0.0.1:9080/productpage")
BOOKINFO_NAMESPACE = os.getenv("BOOKINFO_NAMESPACE", "bookinfo")

BOOKINFO_SERVICES = [
    "productpage",
    "details",
    "ratings",
    "reviews",
]

BOOKINFO_DISPLAY_SERVICES = [
    "productpage",
    "details",
    "ratings",
    "reviews",
    "reviews-v1",
    "reviews-v2",
    "reviews-v3",
]

BOOKINFO_WORKLOAD_PATTERNS = {
    "productpage": "productpage.*",
    "details": "details.*",
    "ratings": "ratings.*",
    "reviews": "reviews.*",
    "reviews-v1": "reviews-v1.*",
    "reviews-v2": "reviews-v2.*",
    "reviews-v3": "reviews-v3.*",
}

DEFAULT_TIME_WINDOW_MINUTES = 5
DEFAULT_QUERY_STEP_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 5
KUBECTL_TIMEOUT_SECONDS = 8
LIVE_LOAD_REQUEST_COUNT = int(os.getenv("LIVE_LOAD_REQUEST_COUNT", "80"))
DELAY_INJECTION_FILE = os.getenv(
    "DELAY_INJECTION_FILE",
    r"E:\Social_apps\QQ\downlowd\istio-1.29.1-win-amd64\istio-1.29.1\samples\bookinfo\networking\virtual-service-ratings-test-delay.yaml",
)
ROUTE_RESET_FILE = os.getenv(
    "ROUTE_RESET_FILE",
    r"E:\Social_apps\QQ\downlowd\istio-1.29.1-win-amd64\istio-1.29.1\samples\bookinfo\networking\virtual-service-all.yaml",
)

MODE_REAL = "Real Environment"
MODE_MOCK_NORMAL = "Mock Normal"
MODE_MOCK_ABNORMAL = "Mock Abnormal"

DATA_MODES = [MODE_REAL, MODE_MOCK_NORMAL, MODE_MOCK_ABNORMAL]

METRIC_LABELS = {
    "cpu": "CPU",
    "memory": "Memory",
    "request_rate": "Request Rate",
    "error_rate": "Error Rate",
    "latency": "Latency",
    "restart": "Restart",
}

METRIC_UNITS = {
    "cpu": "cores",
    "memory": "MiB",
    "request_rate": "req/s",
    "error_rate": "errors/s",
    "latency": "ms",
    "restart": "count",
}

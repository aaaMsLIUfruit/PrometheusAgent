
# Bookinfo 微服务智能监控问答助手需求文档

## 1. 项目背景

本项目是微服务课程大作业，选题为：

> 场景一：智能监控问答助手

在实验二中，我们通过 Python 脚本调用 Prometheus API，并手动编写 PromQL 查询语句来获取集群 CPU 占用率、内存使用量、Pod 重启次数、请求量、错误率、延迟等指标。这种方式要求使用者掌握 PromQL 语法和 Kubernetes 相关命令，使用门槛较高。

本项目希望实现一个面向 Bookinfo 微服务系统的智能监控问答助手。系统将 Prometheus 查询能力封装为多个具有明确语义的工具，使用户可以通过自然语言提问。系统根据用户问题自动选择合适工具、生成 PromQL、调用 Prometheus API、汇总数据，并生成可读的自然语言分析报告。对于趋势类问题，系统还应自动生成折线图。

本项目使用轻量级 Python 实现，不依赖 Dify、LangChain、OpenAI API 或外部大模型 API。为了保证课堂演示稳定，系统必须支持真实环境模式和 Mock 演示模式。

---

## 2. 项目名称

项目名称：

```text
Bookinfo 微服务智能监控问答助手
````

英文名称：

```text
Bookinfo Intelligent Monitoring QA Assistant
```

---

## 3. 项目目标

系统需要实现以下目标：

```text
1. 将 Prometheus 查询能力封装为多个语义化工具；
2. 每个工具包含工具名称、工具描述、参数说明、PromQL 模板和执行函数；
3. 支持用户通过自然语言查询 Bookinfo 微服务状态；
4. 系统能够根据自然语言问题自动选择合适工具；
5. 系统能够根据服务名、指标名、时间窗口自动生成 PromQL；
6. 系统能够调用 Prometheus HTTP API 获取指标数据；
7. 系统能够汇总查询结果并生成自然语言分析报告；
8. 系统能够区分即时查询 instant query 和趋势查询 range query；
9. 系统能够针对趋势类问题自动生成折线图；
10. 系统能够一键生成 Bookinfo 健康巡检报告；
11. 系统支持 Mock 正常状态和 Mock 异常状态，保证课堂演示稳定；
12. 系统使用 Streamlit 提供可视化页面，便于截图、演示和汇报。
```

---

## 4. 对齐课程场景要求

老师给出的场景一要求如下：

```text
将 Prometheus 查询能力封装为智能体工具，使运维人员可以通过自然语言向智能体提问，由智能体自主选择合适的 PromQL 查询语句、调用 Prometheus API、汇总数据并生成可读的分析报告。
```

本项目需要明确体现以下技术点：

| 老师要求                 | 本项目实现方式                                                           |
| -------------------- | ----------------------------------------------------------------- |
| Prometheus 查询能力封装为工具 | 使用 `tool_registry.py` 定义语义化工具                                     |
| 自然语言提问               | 使用 Streamlit 输入框接收用户问题                                            |
| 自主选择工具               | 使用 `agent.py` 和 `question_parser.py` 根据用户问题选择工具                   |
| 自动选择 / 生成 PromQL     | 每个工具维护 PromQL 模板，根据服务名和时间窗口填充                                     |
| 调用 Prometheus API    | 使用 `metrics_client.py` 调用 `/api/v1/query` 和 `/api/v1/query_range` |
| 汇总数据                 | 使用工具结果整理、排序和聚合                                                    |
| 生成可读报告               | 使用 `report_generator.py` 生成自然语言分析报告                               |
| 趋势类问题生成图表            | 使用 `chart_utils.py` 和 matplotlib 生成折线图                            |
| 可展示技术要点              | 页面展示工具选择过程、工具描述、PromQL 和最终回答                                      |

---

## 5. 技术栈要求

使用 Python 实现。

推荐依赖：

```text
streamlit
requests
pandas
matplotlib
python-dotenv
```

禁止使用或不要求使用：

```text
Dify
LangChain
OpenAI API
外部大模型 API
数据库
复杂前端框架
```

原因：

```text
1. 本项目重点是 Prometheus 查询工具封装和自然语言监控问答；
2. 引入复杂 Agent 平台会增加部署难度和演示风险；
3. 课程演示应优先保证稳定、可复现、可截图；
4. 规则驱动的轻量级智能体已经足够体现工具选择和 PromQL 自动生成过程。
```

---

## 6. 运行环境假设

真实环境下，用户会手动启动以下端口转发。

Prometheus：

```bash
kubectl -n istio-system port-forward svc/prometheus 9090:9090
```

Prometheus 地址：

```text
http://127.0.0.1:9090
```

productpage：

```bash
kubectl -n bookinfo port-forward svc/productpage 9080:9080
```

productpage 地址：

```text
http://127.0.0.1:9080/productpage
```

Bookinfo 命名空间：

```text
bookinfo
```

Bookinfo 服务包括：

```text
productpage
details
ratings
reviews
```

Bookinfo 中可能出现的 Pod / 版本包括：

```text
productpage-v1
details-v1
ratings-v1
reviews-v1
reviews-v2
reviews-v3
```

系统需要尽量支持服务级查询和 Pod / 版本级查询。例如：

```text
reviews 服务
reviews-v2 Pod / 工作负载
```

---

## 7. 项目文件结构

请按如下结构创建项目：

```text
bookinfo-monitor-agent/
├── app.py
├── agent.py
├── tool_registry.py
├── metrics_client.py
├── k8s_client.py
├── question_parser.py
├── report_generator.py
├── health_judge.py
├── chart_utils.py
├── mock_data.py
├── config.py
├── requirements.txt
└── README.md
```

每个文件职责如下：

| 文件                    | 职责                                     |
| --------------------- | -------------------------------------- |
| `app.py`              | Streamlit 主页面                          |
| `agent.py`            | 智能体主流程：解析问题、选择工具、调用工具、生成回答             |
| `tool_registry.py`    | 工具注册表：定义工具名称、描述、参数、PromQL 模板和执行函数      |
| `metrics_client.py`   | Prometheus HTTP API 查询函数               |
| `k8s_client.py`       | kubectl 查询、Pod 状态查询、productpage 可访问性检测 |
| `question_parser.py`  | 自然语言问题解析：识别服务、指标、时间窗口、趋势需求             |
| `report_generator.py` | 自然语言报告生成                               |
| `health_judge.py`     | 异常判断规则                                 |
| `chart_utils.py`      | 图表生成                                   |
| `mock_data.py`        | Mock 正常 / 异常数据                         |
| `config.py`           | 全局配置                                   |
| `requirements.txt`    | Python 依赖                              |
| `README.md`           | 运行说明和演示说明                              |

---

## 8. 全局配置要求

在 `config.py` 中定义：

```python
import os

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://127.0.0.1:9090")
PRODUCTPAGE_URL = os.getenv("PRODUCTPAGE_URL", "http://127.0.0.1:9080/productpage")
BOOKINFO_NAMESPACE = os.getenv("BOOKINFO_NAMESPACE", "bookinfo")

BOOKINFO_SERVICES = [
    "productpage",
    "details",
    "ratings",
    "reviews",
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
```

要求：

```text
1. 支持通过环境变量覆盖默认配置；
2. 所有模块从 config.py 读取配置；
3. 不要在多个文件中重复写死 Prometheus 地址和 namespace。
```

---

## 9. Prometheus 查询模块需求

文件：

```text
metrics_client.py
```

---

### 9.1 即时查询函数

实现：

```python
query_prometheus(promql: str) -> dict
```

功能：

```text
调用 Prometheus /api/v1/query。
```

要求：

```text
1. 使用 requests.get；
2. 使用 timeout；
3. 捕获所有异常；
4. 不允许因为 Prometheus 不可访问导致程序崩溃；
5. 返回统一结构；
6. 如果 Prometheus 返回空结果，ok=False，并给出清晰错误信息。
```

返回格式：

```python
{
    "ok": True,
    "promql": "...",
    "value": 0.0,
    "raw": {},
    "error": None,
    "source": "prometheus",
}
```

失败时：

```python
{
    "ok": False,
    "promql": "...",
    "value": None,
    "raw": None,
    "error": "错误信息",
    "source": "prometheus",
}
```

---

### 9.2 范围查询函数

实现：

```python
query_prometheus_range(
    promql: str,
    minutes: int = 5,
    step_seconds: int = 30,
) -> dict
```

功能：

```text
调用 Prometheus /api/v1/query_range，用于趋势类问题和折线图。
```

要求：

```text
1. 自动计算 start、end；
2. 默认查询最近 5 分钟；
3. 返回时间序列数据；
4. 如果没有数据，返回 ok=False；
5. 不允许抛出未捕获异常。
```

返回格式：

```python
{
    "ok": True,
    "promql": "...",
    "series": [
        {"timestamp": 1710000000, "value": 0.03},
        {"timestamp": 1710000030, "value": 0.04}
    ],
    "raw": {},
    "error": None,
    "source": "prometheus",
}
```

---

### 9.3 指标查询函数

实现以下函数：

```python
get_service_cpu(service_name: str, minutes: int = 5) -> dict
get_service_memory(service_name: str) -> dict
get_service_request_rate(service_name: str, minutes: int = 5) -> dict
get_service_error_rate(service_name: str, minutes: int = 5) -> dict
get_service_latency(service_name: str, minutes: int = 5) -> dict

get_service_cpu_series(service_name: str, minutes: int = 5) -> dict
get_service_request_rate_series(service_name: str, minutes: int = 5) -> dict
get_service_latency_series(service_name: str, minutes: int = 5) -> dict

get_memory_ranking(namespace: str = "bookinfo") -> dict
get_pod_restart_counts(namespace: str = "bookinfo") -> dict
```

统一返回格式：

```python
{
    "ok": bool,
    "metric": "cpu" | "memory" | "request_rate" | "error_rate" | "latency" | "restart",
    "service": "productpage",
    "value": float | None,
    "unit": "cores" | "MiB" | "req/s" | "errors/s" | "ms" | "count",
    "promql": "...",
    "raw": dict | None,
    "error": str | None,
    "source": "prometheus",
}
```

排名类返回格式：

```python
{
    "ok": True,
    "metric": "memory",
    "items": [
        {"name": "reviews", "value": 303.0, "unit": "MiB"},
        {"name": "productpage", "value": 120.0, "unit": "MiB"},
        {"name": "details", "value": 55.0, "unit": "MiB"},
        {"name": "ratings", "value": 48.0, "unit": "MiB"}
    ],
    "promql": "...",
    "error": None,
    "source": "prometheus",
}
```

---

### 9.4 PromQL 模板建议

CPU：

```text
sum(rate(container_cpu_usage_seconds_total{namespace="bookinfo",pod=~"<pod_pattern>",container!="POD",image!=""}[5m]))
```

内存：

```text
sum(container_memory_working_set_bytes{namespace="bookinfo",pod=~"<pod_pattern>",container!="POD",image!=""})
```

内存返回时需要转为 MiB：

```text
bytes / 1024 / 1024
```

请求量：

```text
sum(rate(istio_requests_total{destination_service_name="<service_name>",destination_workload_namespace="bookinfo"}[5m]))
```

5xx 错误率：

```text
sum(rate(istio_requests_total{destination_service_name="<service_name>",destination_workload_namespace="bookinfo",response_code=~"5.."}[5m]))
```

平均延迟：

```text
sum(rate(istio_request_duration_milliseconds_sum{destination_service_name="<service_name>",destination_workload_namespace="bookinfo"}[5m]))
/
sum(rate(istio_request_duration_milliseconds_count{destination_service_name="<service_name>",destination_workload_namespace="bookinfo"}[5m]))
```

Pod 重启次数优先尝试：

```text
sum by (pod) (kube_pod_container_status_restarts_total{namespace="bookinfo"})
```

如果环境没有 kube-state-metrics 或该 PromQL 无结果，应 fallback 到 kubectl 查询。

---

## 10. Kubernetes 查询模块需求

文件：

```text
k8s_client.py
```

---

### 10.1 命令执行函数

实现：

```python
run_kubectl(args: list[str]) -> dict
```

要求：

```text
1. 使用 subprocess.run；
2. 设置 timeout；
3. 捕获异常；
4. 返回 stdout、stderr、returncode；
5. 不允许程序崩溃。
```

返回格式：

```python
{
    "ok": True,
    "stdout": "...",
    "stderr": "",
    "returncode": 0,
    "error": None,
}
```

---

### 10.2 Pod 状态查询

实现：

```python
get_pod_status(namespace: str = "bookinfo") -> dict
```

建议命令：

```bash
kubectl get pods -n bookinfo
```

需要尽量解析出结构化信息：

```python
[
    {
        "name": "productpage-v1-xxx",
        "ready": "2/2",
        "status": "Running",
        "restarts": 0,
        "age": "10m",
    }
]
```

如果解析困难，可以同时返回原始 stdout。

---

### 10.3 Pod 重启次数查询

实现：

```python
get_pod_restart_count(namespace: str = "bookinfo") -> dict
```

优先使用：

```bash
kubectl get pods -n bookinfo
```

或：

```bash
kubectl get pods -n bookinfo -o json
```

解析每个 Pod 的 restart count。

---

### 10.4 服务健康状态查询

实现：

```python
get_service_health(service_name: str) -> dict
```

要求：

```text
1. 根据 app=<service_name> 查询 Pod；
2. 判断是否存在 Running Pod；
3. 返回服务是否健康；
4. 返回相关 Pod 列表。
```

---

### 10.5 productpage 访问检测

实现：

```python
check_productpage_access() -> dict
```

要求：

```text
1. 请求 PRODUCTPAGE_URL；
2. 设置 timeout；
3. 如果 HTTP 状态码为 200，则 ok=True；
4. 否则 ok=False；
5. 捕获异常。
```

返回格式：

```python
{
    "ok": True,
    "status_code": 200,
    "error": None,
}
```

---

## 11. 工具注册表需求

文件：

```text
tool_registry.py
```

这是本项目对齐老师“智能体工具封装”要求的核心模块。

---

### 11.1 工具定义格式

每个工具应包含：

```python
{
    "name": "query_service_memory_ranking",
    "description": "查询 bookinfo 命名空间下各服务的内存占用排名，适合回答‘各服务内存占用怎么样’、‘哪个服务内存最高’等问题。",
    "parameters": {
        "namespace": "bookinfo"
    },
    "tool_type": "instant_query" | "range_query" | "summary_query",
    "metric": "memory",
    "function": callable,
}
```

可以使用 dataclass，也可以使用字典。

---

### 11.2 必须实现的工具

至少定义以下工具。

#### 工具 1：查询服务内存排名

```text
name:
query_service_memory_ranking

description:
查询 bookinfo 命名空间下各服务或 Pod 的内存占用情况，并按内存从高到低排序。适合回答“bookinfo 各服务内存占用怎么样”“哪个服务内存最高”“内存有没有异常”等问题。

tool_type:
instant_query

metric:
memory
```

---

#### 工具 2：查询单服务 CPU

```text
name:
query_service_cpu

description:
查询指定服务最近 N 分钟的 CPU 使用率。适合回答“reviews 的 CPU 怎么样”“productpage 最近 CPU 高不高”等问题。

tool_type:
instant_query

metric:
cpu
```

---

#### 工具 3：查询 CPU 趋势

```text
name:
query_cpu_trend

description:
查询指定服务或 Pod 最近 N 分钟的 CPU 使用趋势，并返回时间序列数据。适合回答“reviews-v2 最近五分钟 CPU 使用趋势如何”“CPU 最近有没有升高”等趋势类问题。

tool_type:
range_query

metric:
cpu
```

---

#### 工具 4：查询请求量趋势

```text
name:
query_request_rate_trend

description:
查询指定服务最近 N 分钟的请求量变化趋势。适合回答“productpage 最近访问量怎么样”“请求量有没有波动”“QPS 趋势如何”等问题。

tool_type:
range_query

metric:
request_rate
```

---

#### 工具 5：查询错误率

```text
name:
query_error_rate

description:
查询指定服务最近 N 分钟的 5xx 错误率。适合回答“服务有没有报错”“有没有失败请求”“5xx 错误多不多”等问题。

tool_type:
instant_query

metric:
error_rate
```

---

#### 工具 6：查询延迟

```text
name:
query_service_latency

description:
查询指定服务最近 N 分钟的平均请求延迟。适合回答“服务慢不慢”“响应时间怎么样”“延迟是否异常”等问题。

tool_type:
instant_query

metric:
latency
```

---

#### 工具 7：查询 Pod 重启次数

```text
name:
query_pod_restarts

description:
查询 bookinfo 命名空间下各 Pod 的重启次数。适合回答“有没有 Pod 重启”“哪个服务不稳定”“是否发生过重启”等问题。

tool_type:
summary_query

metric:
restart
```

---

#### 工具 8：生成集群健康摘要

```text
name:
query_cluster_health_summary

description:
汇总 Bookinfo 各服务的运行状态、CPU、内存、请求量、错误率、延迟和 Pod 重启次数，并生成整体健康判断。适合回答“bookinfo 当前健康吗”“帮我生成健康报告”“整体状态怎么样”等问题。

tool_type:
summary_query

metric:
health
```

---

### 11.3 工具选择函数

实现：

```python
select_tools(parsed_question: dict) -> list[dict]
```

功能：

```text
根据 question_parser.py 的解析结果，从工具注册表中选择合适工具。
```

要求：

```text
1. 内存排名问题选择 query_service_memory_ranking；
2. CPU 当前值问题选择 query_service_cpu；
3. CPU 趋势问题选择 query_cpu_trend；
4. 请求量趋势问题选择 query_request_rate_trend；
5. 错误率问题选择 query_error_rate；
6. 延迟问题选择 query_service_latency；
7. 重启问题选择 query_pod_restarts；
8. 健康报告问题选择 query_cluster_health_summary；
9. 无法识别时返回空列表。
```

---

## 12. 自然语言解析模块需求

文件：

```text
question_parser.py
```

实现：

```python
parse_question(question: str) -> dict
```

返回格式：

```python
{
    "intent": "metric_query" | "ranking_query" | "trend_query" | "health_report" | "restart_query" | "unknown",
    "service": "productpage" | "details" | "ratings" | "reviews" | "reviews-v1" | "reviews-v2" | "reviews-v3" | None,
    "metric": "cpu" | "memory" | "request_rate" | "error_rate" | "latency" | "restart" | "health" | None,
    "time_window_minutes": 5,
    "need_chart": True,
    "raw_question": "...",
}
```

---

### 12.1 服务识别规则

支持识别：

```text
productpage
details
ratings
reviews
reviews-v1
reviews-v2
reviews-v3
```

如果用户提到：

```text
bookinfo
各服务
所有服务
整体
```

则 `service=None`，表示查询整体或所有服务。

---

### 12.2 指标识别规则

CPU：

```text
cpu
CPU
处理器
计算资源
```

内存：

```text
内存
memory
Memory
MiB
```

请求量：

```text
请求量
流量
QPS
qps
request
请求速率
访问量
```

错误率：

```text
错误
报错
5xx
error
失败
错误率
```

延迟：

```text
延迟
慢
响应时间
latency
耗时
```

重启：

```text
重启
restart
重启次数
```

健康报告：

```text
健康
报告
总结
巡检
状态怎么样
整体情况
是否正常
有没有异常
```

趋势图：

```text
趋势
图
折线图
变化
最近
五分钟
5分钟
最近五分钟
```

---

### 12.3 时间窗口识别

需要支持：

```text
最近一分钟
最近1分钟
最近五分钟
最近5分钟
最近十分钟
最近10分钟
最近十五分钟
最近15分钟
```

默认：

```text
5 分钟
```

---

## 13. 智能体主流程需求

文件：

```text
agent.py
```

实现：

```python
run_agent(
    question: str,
    mode: str = "mock_normal"
) -> dict
```

其中 `mode` 支持：

```text
real
mock_normal
mock_abnormal
```

---

### 13.1 run_agent 流程

`run_agent` 必须执行以下步骤：

```text
1. 接收用户自然语言问题；
2. 调用 parse_question 解析问题；
3. 调用 select_tools 选择工具；
4. 根据工具要求生成 PromQL 或使用 mock 数据；
5. 调用工具函数获取结果；
6. 对结果进行排序、聚合或异常判断；
7. 调用 report_generator 生成自然语言回答；
8. 如果是趋势类问题，返回时间序列数据供画图；
9. 返回完整工具调用轨迹，便于页面展示和截图。
```

---

### 13.2 run_agent 返回格式

```python
{
    "question": "现在 bookinfo 各个服务的内存占用情况怎么样？",
    "parsed": {
        "intent": "ranking_query",
        "service": None,
        "metric": "memory",
        "time_window_minutes": 5,
        "need_chart": False,
        "raw_question": "..."
    },
    "selected_tools": [
        {
            "name": "query_service_memory_ranking",
            "description": "查询 bookinfo 命名空间下各服务或 Pod 的内存占用情况，并按内存从高到低排序。"
        }
    ],
    "promql": [
        "sum by (pod) (...)"
    ],
    "tool_results": [],
    "answer": "当前 bookinfo 各服务内存占用情况如下：...",
    "chart_type": "bar" | "line" | None,
    "chart_data": None,
    "error": None,
    "mode": "real" | "mock_normal" | "mock_abnormal",
}
```

要求：

```text
1. 页面必须能够展示 parsed、selected_tools、promql、answer；
2. 如果工具选择失败，需要给出友好的提示；
3. 如果真实环境失败，应提示用户切换 Mock 模式；
4. 不允许程序崩溃。
```

---

## 14. Mock 数据模块需求

文件：

```text
mock_data.py
```

系统必须支持 Mock 模式，因为课堂演示时真实 Prometheus 或 Kubernetes 环境可能不可用。

---

### 14.1 Mock 模式

实现两套 Mock 数据：

```python
NORMAL_MOCK_DATA
ABNORMAL_MOCK_DATA
```

正常状态示例：

```python
NORMAL_MOCK_DATA = {
    "productpage": {
        "cpu": 0.03,
        "memory": 120.5,
        "request_rate": 2.4,
        "error_rate": 0.0,
        "latency": 35.0,
        "restarts": 0,
        "status": "Running",
    },
    "details": {
        "cpu": 0.01,
        "memory": 55.0,
        "request_rate": 1.8,
        "error_rate": 0.0,
        "latency": 18.0,
        "restarts": 0,
        "status": "Running",
    },
    "ratings": {
        "cpu": 0.02,
        "memory": 48.0,
        "request_rate": 1.2,
        "error_rate": 0.0,
        "latency": 22.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews": {
        "cpu": 0.05,
        "memory": 303.0,
        "request_rate": 1.5,
        "error_rate": 0.0,
        "latency": 42.0,
        "restarts": 0,
        "status": "Running",
    },
    "reviews-v2": {
        "cpu": 0.04,
        "memory": 145.0,
        "request_rate": 0.5,
        "error_rate": 0.0,
        "latency": 40.0,
        "restarts": 0,
        "status": "Running",
    }
}
```

异常状态示例：

```python
ABNORMAL_MOCK_DATA = {
    "productpage": {
        "cpu": 0.08,
        "memory": 150.0,
        "request_rate": 2.1,
        "error_rate": 0.02,
        "latency": 180.0,
        "restarts": 0,
        "status": "Running",
    },
    "details": {
        "cpu": 0.01,
        "memory": 56.0,
        "request_rate": 1.5,
        "error_rate": 0.0,
        "latency": 20.0,
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
    "reviews-v2": {
        "cpu": 0.12,
        "memory": 210.0,
        "request_rate": 0.4,
        "error_rate": 0.02,
        "latency": 330.0,
        "restarts": 0,
        "status": "Running",
    }
}
```

---

### 14.2 Mock 查询函数

实现：

```python
get_mock_metric(service_name: str, metric: str, abnormal: bool = False) -> dict
get_mock_all_services(abnormal: bool = False) -> dict
get_mock_memory_ranking(abnormal: bool = False) -> dict
get_mock_series(service_name: str, metric: str, abnormal: bool = False) -> dict
```

`get_mock_series` 用于生成折线图数据。

返回格式要尽量与真实查询一致。

---

## 15. 异常判断模块需求

文件：

```text
health_judge.py
```

实现：

```python
judge_service_health(service_metrics: dict) -> dict
judge_cluster_health(all_metrics: dict) -> dict
```

---

### 15.1 单服务判断规则

输入：

```python
{
    "cpu": 0.03,
    "memory": 120.5,
    "request_rate": 2.4,
    "error_rate": 0.0,
    "latency": 35.0,
    "restarts": 0,
    "status": "Running",
}
```

输出：

```python
{
    "status": "healthy" | "warning" | "critical",
    "problems": [],
    "suggestions": [],
}
```

判断规则：

```text
1. status 不是 Running → critical；
2. restarts > 0 → warning；
3. error_rate > 0.01 → warning；
4. latency > 200 ms → warning；
5. latency > 500 ms → critical；
6. memory > 400 MiB → warning；
7. CPU > 0.2 cores → warning；
8. 否则 healthy。
```

---

### 15.2 集群整体判断规则

实现：

```python
judge_cluster_health(all_metrics: dict) -> dict
```

要求：

```text
1. 如果任一服务 critical，则集群 critical；
2. 如果任一服务 warning，则集群 warning；
3. 全部 healthy，则集群 healthy；
4. 返回所有问题和建议。
```

---

## 16. 报告生成模块需求

文件：

```text
report_generator.py
```

实现：

```python
generate_metric_answer(parsed_question: dict, tool_result: dict) -> str
generate_memory_ranking_report(ranking_result: dict) -> str
generate_trend_report(service_name: str, metric: str, series_data: dict) -> str
generate_service_report(service_name: str, service_metrics: dict) -> str
generate_cluster_report(all_metrics: dict, productpage_ok: bool = True) -> str
generate_unknown_question_answer() -> str
```

---

### 16.1 内存排名报告示例

用户输入：

```text
现在 bookinfo 各个服务的内存占用情况怎么样？
```

回答示例：

```text
当前 bookinfo 各服务内存占用情况如下：

- reviews 当前内存占用最高，约 303.0 MiB；
- productpage 约 120.5 MiB；
- details 和 ratings 占用较低，分别约 55.0 MiB 和 48.0 MiB。

整体来看，所有服务均处于正常范围内，未发现明显内存异常。reviews 服务内存占用相对较高，建议继续观察其后续趋势。
```

---

### 16.2 CPU 趋势报告示例

用户输入：

```text
reviews-v2 最近五分钟的 CPU 使用趋势如何？
```

回答示例：

```text
reviews-v2 最近 5 分钟 CPU 使用整体较低，没有出现持续升高趋势。
从趋势数据看，CPU 使用率主要在 0.02 到 0.05 cores 之间波动，属于正常范围。
下面的折线图展示了该服务最近 5 分钟的 CPU 使用变化。
```

---

### 16.3 单服务报告格式

示例：

```text
reviews 服务当前状态：需要关注。

关键证据：
- CPU 使用约 0.05 cores；
- 内存占用约 303.0 MiB；
- 最近 5 分钟请求量约 1.5 req/s；
- 平均延迟约 42.0 ms；
- 5xx 错误率为 0.0 errors/s；
- Pod 重启次数为 0。

判断：
reviews 当前内存占用在 Bookinfo 服务中相对较高，但没有出现错误率升高或 Pod 重启，暂不判断为故障。

建议：
继续观察 reviews 服务的内存和延迟趋势。
```

---

### 16.4 集群健康报告格式

必须按以下结构输出：

```text
【整体状态】
...

【关键证据】
...

【风险提示】
...

【建议】
...
```

示例：

```text
【整体状态】
Bookinfo 当前整体状态为健康。

【关键证据】
- productpage 当前可以正常访问；
- productpage、details、ratings、reviews 均处于 Running 状态；
- 最近 5 分钟未发现明显 5xx 错误；
- 当前未发现 Pod 重启现象；
- reviews 内存占用最高，约 303.0 MiB。

【风险提示】
当前未发现严重异常。reviews 服务资源占用相对较高，建议继续观察。

【建议】
可以继续保持当前部署状态，并定期检查请求量、延迟和 Pod 重启次数。
```

---

## 17. 图表模块需求

文件：

```text
chart_utils.py
```

使用 matplotlib。

不要设置固定颜色，使用 matplotlib 默认样式。

实现：

```python
plot_memory_bar(ranking_result: dict)
plot_metric_series(series_data: dict, title: str, ylabel: str)
```

---

### 17.1 内存柱状图

展示：

```text
productpage / details / ratings / reviews
```

的当前内存占用。

---

### 17.2 指标趋势图

支持：

```text
CPU 趋势
请求量趋势
延迟趋势
```

要求：

```text
1. x 轴显示时间；
2. y 轴显示指标值；
3. 标题包含服务名和指标名；
4. 如果真实 Prometheus range query 没有数据，使用 mock series 兜底；
5. 返回 matplotlib Figure，供 Streamlit 展示。
```

---

## 18. Streamlit 页面需求

文件：

```text
app.py
```

---

### 18.1 页面标题

页面标题：

```text
Bookinfo 微服务智能监控问答助手
```

页面副标题：

```text
基于 Prometheus 工具封装的自然语言监控问答、健康报告与趋势图展示
```

---

### 18.2 Sidebar 控件

左侧 sidebar 包含：

```text
1. 数据模式选择：
   - 真实环境
   - Mock 正常状态
   - Mock 异常状态

2. 服务选择：
   - productpage
   - details
   - ratings
   - reviews
   - reviews-v1
   - reviews-v2
   - reviews-v3

3. 时间窗口选择：
   - 1 分钟
   - 5 分钟
   - 10 分钟
   - 15 分钟

4. 指标选择：
   - CPU
   - 内存
   - 请求量
   - 错误率
   - 延迟
```

---

### 18.3 主页面 Tab

主页面包含四个 tab：

```text
1. 智能问答
2. 工具注册表
3. 健康报告
4. 可视化图表
```

---

### 18.4 智能问答 Tab

功能：

```text
1. 用户输入自然语言问题；
2. 点击“提交问题”；
3. 调用 run_agent；
4. 展示用户问题；
5. 展示解析结果 parsed；
6. 展示 selected_tools；
7. 展示工具 description；
8. 展示自动生成的 PromQL；
9. 展示自然语言回答；
10. 如果是趋势类问题，展示折线图。
```

页面要显示示例问题：

```text
现在 bookinfo 各个服务的内存占用情况怎么样？
reviews-v2 最近五分钟的 CPU 使用趋势如何？
productpage 最近 5 分钟请求量怎么样？
bookinfo 有没有 Pod 重启？
帮我生成当前健康报告。
```

---

### 18.5 工具注册表 Tab

展示所有工具：

```text
1. 工具名称；
2. 工具描述；
3. 工具类型；
4. 适用问题示例；
5. 对应指标；
6. 是否使用 instant query / range query。
```

这个页面用于汇报时展示“我们把 Prometheus 查询封装成了智能体工具”。

---

### 18.6 健康报告 Tab

功能：

```text
1. 点击“生成 Bookinfo 健康报告”；
2. 查询全部服务指标；
3. 查询 productpage 可访问性；
4. 调用健康判断；
5. 输出结构化健康报告。
```

报告结构必须是：

```text
【整体状态】
【关键证据】
【风险提示】
【建议】
```

---

### 18.7 可视化图表 Tab

功能：

```text
1. 展示各服务内存占用柱状图；
2. 展示选中服务的 CPU / 请求量 / 延迟趋势图；
3. 如果真实数据不可用，则提示用户切换 Mock 模式；
4. 图表适合截图和 PPT 展示。
```

---

## 19. 必须稳定支持的示例

系统必须稳定支持老师示例。

---

### 19.1 示例一：内存汇总

输入：

```text
现在 bookinfo 各个服务的内存占用情况怎么样？
```

预期行为：

```text
1. 识别 intent = ranking_query；
2. 识别 metric = memory；
3. service = None；
4. 选择工具 query_service_memory_ranking；
5. 生成或展示对应 PromQL；
6. 调用 Prometheus instant query 或 Mock 数据；
7. 按内存从高到低排序；
8. 生成自然语言分析报告。
```

---

### 19.2 示例二：CPU 趋势

输入：

```text
reviews-v2 最近五分钟的 CPU 使用趋势如何？
```

预期行为：

```text
1. 识别 intent = trend_query；
2. 识别 service = reviews-v2；
3. 识别 metric = cpu；
4. 识别 time_window_minutes = 5；
5. 选择工具 query_cpu_trend；
6. 调用 Prometheus query_range 或 Mock series；
7. 返回时间序列；
8. 生成折线图；
9. 生成趋势描述。
```

---

## 20. 错误处理要求

系统必须稳定，不允许因为外部服务不可用直接崩溃。

需要处理：

```text
1. Prometheus 无法访问；
2. Prometheus 返回空结果；
3. kubectl 命令不存在；
4. Kubernetes 集群未连接；
5. productpage 无法访问；
6. 用户输入无法识别；
7. 指标值为 None；
8. query_range 没有时间序列数据；
9. 工具选择失败；
10. PromQL 查询失败。
```

处理方式：

```text
1. 页面显示清晰错误信息；
2. 建议用户切换 Mock 模式；
3. 程序继续运行；
4. 不抛出未捕获异常；
5. run_agent 返回 error 字段，而不是直接报错。
```

---

## 21. README 要求

文件：

```text
README.md
```

必须包含：

```text
1. 项目简介；
2. 对齐场景一的说明；
3. 文件结构；
4. 安装依赖方法；
5. 启动真实环境前置命令；
6. 运行 Streamlit 方法；
7. Mock 模式说明；
8. 示例问题；
9. 演示流程；
10. 截图建议；
11. 常见问题。
```

---

### 21.1 安装依赖

```bash
pip install -r requirements.txt
```

---

### 21.2 真实环境前置命令

```bash
kubectl -n istio-system port-forward svc/prometheus 9090:9090
kubectl -n bookinfo port-forward svc/productpage 9080:9080
```

---

### 21.3 运行系统

```bash
streamlit run app.py
```

---

### 21.4 演示建议

```text
1. 先使用 Mock 正常状态演示页面；
2. 输入：现在 bookinfo 各个服务的内存占用情况怎么样？
3. 展示工具选择、PromQL、排序报告；
4. 输入：reviews-v2 最近五分钟的 CPU 使用趋势如何？
5. 展示 query_range、折线图、趋势描述；
6. 切换 Mock 异常状态展示异常判断；
7. 如果真实环境可用，再切换真实环境展示 Prometheus 查询结果。
```

---

## 22. requirements.txt 要求

至少包含：

```text
streamlit
requests
pandas
matplotlib
python-dotenv
```

---

## 23. 验收标准

最终项目必须满足以下验收条件。

---

### 23.1 基础验收

```text
1. pip install -r requirements.txt 能成功；
2. streamlit run app.py 能启动；
3. 页面能正常打开；
4. Mock 正常状态可以演示；
5. Mock 异常状态可以演示；
6. 智能问答可以展示工具选择过程；
7. 工具注册表页面可以展示工具描述；
8. 健康报告可以生成；
9. 至少一张柱状图可以展示；
10. 至少一张趋势图可以展示。
```

---

### 23.2 场景一验收

必须支持：

```text
1. 用户输入“现在 bookinfo 各个服务的内存占用情况怎么样？”
   系统选择 query_service_memory_ranking；
   系统展示 PromQL；
   系统输出内存排序分析报告。

2. 用户输入“reviews-v2 最近五分钟的 CPU 使用趋势如何？”
   系统选择 query_cpu_trend；
   系统展示 PromQL；
   系统生成折线图；
   系统输出趋势描述。
```

---

### 23.3 真实环境验收

如果 Prometheus 和 Bookinfo 端口转发可用，系统应该能够：

```text
1. 查询 productpage 请求量；
2. 查询 reviews 内存；
3. 查询服务 CPU；
4. 查询服务延迟；
5. 查询 productpage 可访问性；
6. 生成真实环境健康报告。
```

如果真实环境不可用，系统不应崩溃，应显示错误并允许切换 Mock 模式。

---

### 23.4 演示验收

课堂演示应能完成以下流程：

```text
1. 打开 Streamlit 页面；
2. 打开“工具注册表”页面，展示工具名称和 Description；
3. 切换 Mock 正常状态；
4. 输入“现在 bookinfo 各个服务的内存占用情况怎么样？”；
5. 展示 selected_tool、description、PromQL 和回答；
6. 输入“reviews-v2 最近五分钟的 CPU 使用趋势如何？”；
7. 展示 selected_tool、PromQL、折线图和趋势描述；
8. 切换 Mock 异常状态；
9. 生成健康报告，展示风险提示；
10. 如果真实环境可用，切换真实环境展示一次真实指标查询。
```

---

## 24. 代码质量要求

```text
1. 函数命名清晰；
2. 模块职责明确；
3. 不要把所有代码都写在 app.py；
4. 所有外部请求都要 timeout；
5. 所有外部命令都要异常处理；
6. 返回结构统一；
7. 不要写死太多魔法字符串；
8. README 能指导普通同学运行；
9. 代码中适当添加注释；
10. 页面适合截图和课堂演示；
11. Mock 模式必须优先保证可用；
12. 真实模式失败不能影响 Mock 模式。
```

---

## 25. 给 Codex 的执行要求

请直接完成整个项目，不要只给示例代码。

开发完成后，请输出：

```text
1. 创建了哪些文件；
2. 每个文件的作用；
3. 如何安装依赖；
4. 如何运行系统；
5. 如何使用 Mock 模式；
6. 如何连接真实 Prometheus；
7. 如何演示老师给出的两个问题；
8. 后续可以改进的地方。
```

请优先保证：

```text
Mock 可演示 > 工具注册表展示 > 智能问答流程 > 健康报告 > 图表展示 > 真实 Prometheus 查询
```

---

## 26. 最小可交付版本

如果时间不足，至少完成：

```text
1. app.py；
2. agent.py；
3. tool_registry.py；
4. mock_data.py；
5. question_parser.py；
6. report_generator.py；
7. health_judge.py；
8. chart_utils.py；
9. requirements.txt；
10. README.md。
```

最低要求：

```text
1. Mock 正常状态能演示；
2. Mock 异常状态能演示；
3. 工具注册表能展示；
4. 自然语言问答能展示工具选择；
5. 内存排名问题能回答；
6. CPU 趋势问题能画图；
7. 健康报告能生成。
```

真实 Prometheus 查询作为增强功能，但应尽量实现。

---

## 27. 可选加分项

如果基础功能完成，可以继续实现：

```text
1. 支持导出健康报告为 Markdown；
2. 支持下载图表 PNG；
3. 支持保存一次巡检历史；
4. 支持故障前后指标对比；
5. 支持自动生成实验报告片段；
6. 支持更多中文问题模板；
7. 支持展示完整工具调用链；
8. 支持把 PromQL 复制到剪贴板；
9. 支持更多 Bookinfo 版本级 Pod 查询，例如 reviews-v1、reviews-v2、reviews-v3。
```



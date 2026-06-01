# Bookinfo Monitoring QA Assistant

This project is a lightweight LangChain-based monitoring agent for the Bookinfo microservice system. It wraps Prometheus queries into explicit tools, lets users ask questions in natural language, and uses LangChain plus an OpenAI chat model to plan intent and tool selection before executing real monitoring queries.

## What it covers

- Toolized Prometheus queries
- Natural-language parsing for service, metric, and time window
- Automatic PromQL generation
- Instant and range queries
- Health reports and chart rendering
- Mock normal and mock abnormal modes for reliable demos

## Files

- `app.py`: Streamlit UI
- `agent.py`: main orchestration flow
- `tool_registry.py`: tool metadata and selection
- `metrics_client.py`: Prometheus HTTP API helpers
- `k8s_client.py`: kubectl and productpage access checks
- `question_parser.py`: natural-language parsing
- `report_generator.py`: report text generation
- `health_judge.py`: health rules
- `chart_utils.py`: chart rendering
- `mock_data.py`: mock datasets
- `config.py`: shared configuration

## Install

```bash
pip install -r requirements.txt
```

## Configure LLM API

Before using the real LLM planner, fill these values in `config.py`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` if you want a different model

The current implementation uses `LangChain` + `langchain-openai` in `llm_client.py`.

## Live environment setup

```bash
kubectl -n istio-system port-forward svc/prometheus 9090:9090
kubectl -n bookinfo port-forward svc/productpage 9080:9080
```

## Run

```bash
streamlit run app.py
```

## Demo modes

- `Mock Normal`: stable healthy demo
- `Mock Abnormal`: shows latency, errors, restarts, and unhealthy states
- `Real Environment`: tries live Prometheus and Kubernetes data

## Sample questions

- `现在 bookinfo 各个服务的内存占用情况怎么样？`
- `reviews-v2 最近五分钟的 CPU 使用趋势如何？`
- `productpage request rate in the last 5 minutes`
- `bookinfo 有没有 Pod 重启？`
- `Generate a health report for Bookinfo`

## Suggested classroom flow

1. Start in `Mock Normal`
2. Show the tool registry
3. Ask the memory-ranking question
4. Ask the CPU-trend question
5. Switch to `Mock Abnormal`
6. Generate the health report
7. If live services are available, switch to `Real Environment`

## Notes

- Live query failures do not crash the app.
- If Prometheus or Kubernetes is unavailable, switch to a Mock mode.
- The parser supports both Chinese and English keywords for the main demo questions.

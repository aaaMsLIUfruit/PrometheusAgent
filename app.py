from __future__ import annotations

import pandas as pd
import streamlit as st

from agent import collect_cluster_metrics, run_agent
from chart_utils import plot_memory_bar, plot_metric_series
from config import BOOKINFO_DISPLAY_SERVICES, DATA_MODES, LIVE_LOAD_REQUEST_COUNT, MODE_REAL, PROMETHEUS_URL
from health_judge import judge_cluster_health
from k8s_client import check_productpage_access, check_prometheus_access, inject_delay, reset_bookinfo_routes, warm_productpage_traffic
from mock_data import get_mock_all_services, get_mock_memory_ranking, get_mock_series
from report_generator import build_snapshot_change_rows, generate_cluster_report, generate_snapshot_summary
from tool_registry import get_tool_registry

st.set_page_config(page_title="Bookinfo Monitoring QA Assistant", layout="wide")

st.title("Bookinfo Monitoring QA Assistant")
st.caption("Prometheus-backed LLM agent for natural-language monitoring, tool selection, reports, and live environment actions")

if "baseline_snapshot" not in st.session_state:
    st.session_state.baseline_snapshot = None
if "latest_snapshot" not in st.session_state:
    st.session_state.latest_snapshot = None
if "ops_log" not in st.session_state:
    st.session_state.ops_log = []


def log_operation(message: str) -> None:
    st.session_state.ops_log = [message, *st.session_state.ops_log[:7]]


with st.sidebar:
    st.subheader("Demo Controls")
    data_mode = st.radio("Data Mode", DATA_MODES, index=1)
    selected_service = st.selectbox("Service", BOOKINFO_DISPLAY_SERVICES, index=0)
    selected_minutes = st.selectbox("Time Window (minutes)", [1, 5, 10, 15], index=1)
    selected_metric = st.selectbox("Metric", ["cpu", "memory", "request_rate", "error_rate", "latency"], index=0)

    if data_mode == MODE_REAL:
        st.divider()
        st.subheader("Live Environment")
        productpage_status = check_productpage_access()
        prometheus_status = check_prometheus_access(PROMETHEUS_URL)
        st.write(f"productpage: {'reachable' if productpage_status['ok'] else 'unreachable'}")
        st.write(f"Prometheus: {'reachable' if prometheus_status['ok'] else 'unreachable'}")

        if st.button("Capture Baseline Snapshot", width="stretch"):
            st.session_state.baseline_snapshot = collect_cluster_metrics()
            st.session_state.latest_snapshot = st.session_state.baseline_snapshot
            log_operation("Captured a new live baseline snapshot.")

        if st.button(f"Warm Traffic ({LIVE_LOAD_REQUEST_COUNT} requests)", width="stretch"):
            result = warm_productpage_traffic(LIVE_LOAD_REQUEST_COUNT)
            st.session_state.latest_snapshot = collect_cluster_metrics()
            log_operation(f"Warmed productpage traffic: {result['successful']}/{result['requested']} requests succeeded.")
            if not result["ok"]:
                st.warning(result["error"])

        if st.button("Inject Delay Fault", width="stretch"):
            result = inject_delay()
            log_operation("Applied ratings delay fault." if result["ok"] else f"Delay injection failed: {result['error']}")
            if not result["ok"]:
                st.warning(result["error"])

        if st.button("Reset Traffic Rules", width="stretch"):
            result = reset_bookinfo_routes()
            log_operation("Restored default Bookinfo traffic rules." if result["ok"] else f"Traffic reset failed: {result['error']}")
            if not result["ok"]:
                st.warning(result["error"])

tabs = st.tabs(["QA", "Tool Registry", "Health Report", "Charts"])

with tabs[0]:
    st.subheader("Natural-language QA")
    st.write("Sample questions")
    st.code(
        "\n".join(
            [
                "现在 bookinfo 各个服务的内存占用情况怎么样？",
                "reviews-v2 最近五分钟的 CPU 使用趋势如何？",
                "details 最近 5 分钟请求量怎么样？",
                "bookinfo 有没有 Pod 重启？",
                "Generate a health report for Bookinfo",
            ]
        ),
        language="text",
    )

    if st.session_state.ops_log:
        st.markdown("**Recent Live Operations**")
        for item in st.session_state.ops_log:
            st.write(f"- {item}")

    user_question = st.text_area("Question", height=100, value="")
    if st.button("Submit", type="primary"):
        result = run_agent(user_question, data_mode=data_mode, default_service=selected_service, default_minutes=selected_minutes)
        if data_mode == MODE_REAL and result.get("cluster_metrics"):
            st.session_state.latest_snapshot = result["cluster_metrics"]

        st.markdown("**Question**")
        st.write(user_question)
        st.markdown("**Parsed Result**")
        st.json(result["parsed"])
        if result["parsed"].get("planner_reasoning"):
            st.markdown("**LLM Planner Reasoning**")
            st.write(result["parsed"]["planner_reasoning"])
        st.markdown("**Selected Tools**")
        st.json(result["selected_tools"])

        promql_list = [item.get("promql") for item in result.get("tool_results", []) if item.get("promql")]
        if promql_list:
            st.markdown("**Generated PromQL**")
            for promql in promql_list:
                st.code(promql, language="text")

        st.markdown("**Answer**")
        st.write(result["answer"])

        if result.get("service_report"):
            st.markdown("**Service Assessment**")
            st.text(result["service_report"])

        if data_mode == MODE_REAL and st.session_state.baseline_snapshot and st.session_state.latest_snapshot:
            comparison_rows = build_snapshot_change_rows(st.session_state.baseline_snapshot, st.session_state.latest_snapshot)
            if comparison_rows:
                st.markdown("**Before/After Snapshot**")
                st.dataframe(pd.DataFrame(comparison_rows), width="stretch")
                st.info(generate_snapshot_summary(st.session_state.baseline_snapshot, st.session_state.latest_snapshot))

        if result.get("chart_kind") == "memory_bar":
            figure = plot_memory_bar(result["chart_data"])
            if figure:
                st.pyplot(figure)
        elif result.get("chart_kind") == "series":
            ylabel = result["tool_results"][0].get("unit", selected_metric)
            title = f"{result['parsed'].get('service') or selected_service} {result['parsed'].get('metric') or selected_metric} trend"
            figure = plot_metric_series(result["chart_data"], title=title, ylabel=ylabel)
            if figure:
                st.pyplot(figure)

with tabs[1]:
    st.subheader("Tool Registry")
    tools = get_tool_registry()
    tool_rows = [{"name": tool.name, "description": tool.description, "tool_type": tool.tool_type, "metric": tool.metric, "example": tool.example} for tool in tools]
    st.dataframe(pd.DataFrame(tool_rows), width="stretch")

with tabs[2]:
    st.subheader("Bookinfo Health Report")
    if data_mode == MODE_REAL and st.session_state.baseline_snapshot and st.session_state.latest_snapshot:
        st.markdown("**Observed Changes Since Baseline**")
        st.dataframe(pd.DataFrame(build_snapshot_change_rows(st.session_state.baseline_snapshot, st.session_state.latest_snapshot)), width="stretch")
        st.info(generate_snapshot_summary(st.session_state.baseline_snapshot, st.session_state.latest_snapshot))

    if st.button("Generate Health Report"):
        abnormal = data_mode == "Mock Abnormal"
        if data_mode.startswith("Mock"):
            all_metrics = get_mock_all_services(abnormal=abnormal)
            report = generate_cluster_report(all_metrics, productpage_ok=not abnormal)
            summary = judge_cluster_health(all_metrics)
            st.text(report)
            st.json(summary)
        else:
            result = run_agent("Generate a health report for Bookinfo", data_mode=data_mode, default_service=selected_service, default_minutes=selected_minutes)
            st.text(result["answer"])
            if result.get("cluster_metrics"):
                st.session_state.latest_snapshot = result["cluster_metrics"]
                st.json(judge_cluster_health(result["cluster_metrics"]))
            if result.get("error"):
                st.warning(result["error"])

with tabs[3]:
    st.subheader("Charts")
    if data_mode.startswith("Mock"):
        abnormal = data_mode == "Mock Abnormal"
        ranking = get_mock_memory_ranking(abnormal=abnormal)
        memory_fig = plot_memory_bar(ranking)
        if memory_fig:
            st.pyplot(memory_fig)

        series = get_mock_series(selected_service, selected_metric, abnormal=abnormal, minutes=selected_minutes)
        series_fig = plot_metric_series(series, title=f"{selected_service} {selected_metric} trend", ylabel=selected_metric)
        if series_fig:
            st.pyplot(series_fig)
    else:
        st.info("Use the QA tab to generate live charts from real Prometheus queries. Capture a baseline, warm traffic, or inject delay from the sidebar to create visible changes.")

from __future__ import annotations

from datetime import datetime

import matplotlib.pyplot as plt


def plot_memory_bar(ranking_result: dict):
    items = ranking_result.get("items", [])
    if not items:
        return None

    names = [item["name"] for item in items]
    values = [item["value"] for item in items]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, values)
    ax.set_title("Bookinfo Memory Usage Ranking")
    ax.set_ylabel("MiB")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return fig


def plot_metric_series(series_data: dict, title: str, ylabel: str):
    points = series_data.get("series", [])
    if not points:
        return None

    timestamps = [datetime.fromtimestamp(item["timestamp"]) for item in points]
    values = [item["value"] for item in points]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(timestamps, values, marker="o")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Time")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig

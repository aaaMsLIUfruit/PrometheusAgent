from __future__ import annotations

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import DEFAULT_TIME_WINDOW_MINUTES, OPENAI_API_KEY, OPENAI_MODEL
from tool_registry import describe_tools_for_llm


class MonitorPlan(BaseModel):
    intent: Literal["metric_query", "trend_query", "ranking_query", "restart_query", "health_report", "unknown"]
    service: str | None = Field(default=None)
    metric: str | None = Field(default=None)
    time_window_minutes: int = Field(default=DEFAULT_TIME_WINDOW_MINUTES)
    selected_tool_names: list[str] = Field(default_factory=list)
    reasoning: str = Field(default="")


def llm_is_enabled() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE")


def plan_question_with_llm(question: str, default_service: str | None = None, default_minutes: int = DEFAULT_TIME_WINDOW_MINUTES) -> dict:
    if not llm_is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY is not configured."}

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a Bookinfo monitoring agent built with LangChain. "
                "Your task is to understand the user's monitoring question and choose the most suitable tool based on each tool description. "
                "Prefer one primary tool unless the user asks for a health report. "
                "Return structured planning data only.",
            ),
            (
                "human",
                "Available LangChain tools:\n{tool_descriptions}\n\n"
                "User question:\n{question}\n\n"
                "Default service: {default_service}\n"
                "Default time window: {default_minutes}\n\n"
                "Interpret the question, select the best tool, and explain the choice briefly.",
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(MonitorPlan)

    try:
        result = chain.invoke(
            {
                "tool_descriptions": describe_tools_for_llm(),
                "question": question,
                "default_service": default_service,
                "default_minutes": default_minutes,
            }
        )
        payload = result.model_dump()
        payload["ok"] = True
        return payload
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

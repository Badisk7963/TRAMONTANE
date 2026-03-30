"""Benchmark: LangGraph + Mistral 3-agent code review pipeline.

Requires: pip install langgraph langchain-mistralai
"""

from __future__ import annotations

import os
import time
from typing import Any

from benchmarks.shared import CODE_TO_REVIEW, bugs_detail, count_bugs


async def run() -> dict[str, Any]:
    """Run 3-node LangGraph pipeline with Mistral models."""
    import operator
    from typing import Annotated, TypedDict

    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_mistralai import ChatMistralAI
    from langgraph.graph import END, StateGraph

    class State(TypedDict):
        messages: Annotated[list[Any], operator.add]
        review: str
        audit: str
        report: str

    model = ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.environ.get("MISTRAL_API_KEY", ""),
    )

    def review_node(state: State) -> dict[str, Any]:
        resp = model.invoke([
            SystemMessage(content="You are a senior code reviewer. Identify all bugs."),
            HumanMessage(content=f"Review this code:\n\n{CODE_TO_REVIEW}"),
        ])
        return {"review": resp.content, "messages": [resp]}

    def audit_node(state: State) -> dict[str, Any]:
        resp = model.invoke([
            SystemMessage(content="You are a security auditor. Find OWASP vulnerabilities."),
            HumanMessage(
                content=f"Audit this code:\n\n{CODE_TO_REVIEW}\n\nPrior review:\n{state['review']}"
            ),
        ])
        return {"audit": resp.content, "messages": [resp]}

    def report_node(state: State) -> dict[str, Any]:
        resp = model.invoke([
            SystemMessage(content="Write a concise summary report."),
            HumanMessage(
                content=f"Summarize:\n\nReview:\n{state['review']}\n\nAudit:\n{state['audit']}"
            ),
        ])
        return {"report": resp.content, "messages": [resp]}

    graph = StateGraph(State)
    graph.add_node("reviewer", review_node)
    graph.add_node("auditor", audit_node)
    graph.add_node("reporter", report_node)
    graph.set_entry_point("reviewer")
    graph.add_edge("reviewer", "auditor")
    graph.add_edge("auditor", "reporter")
    graph.add_edge("reporter", END)
    app = graph.compile()

    start = time.monotonic()
    result = app.invoke({
        "messages": [],
        "review": "",
        "audit": "",
        "report": "",
    })
    elapsed = time.monotonic() - start

    full_output = f"{result['review']}\n{result['audit']}\n{result['report']}"

    # LangGraph doesn't track cost natively — estimate from mistral-small pricing
    # Rough: 3 calls * ~1500 tokens each = ~4500 tokens
    est_cost = (4500 / 1_000_000) * 0.10 + (4500 / 1_000_000) * 0.30

    return {
        "framework": "langgraph",
        "wall_time_s": round(elapsed, 2),
        "cost_eur": round(est_cost, 6),
        "total_tokens": 0,  # LangGraph doesn't expose this easily
        "models_used": ["mistral-small-latest"] * 3,
        "agents": 3,
        "bugs_found": count_bugs(full_output),
        "bugs_detail": bugs_detail(full_output),
        "output_len": len(full_output),
        "status": "complete",
    }

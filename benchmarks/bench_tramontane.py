"""Benchmark: Tramontane 3-agent code review pipeline."""

from __future__ import annotations

import time
from typing import Any

from benchmarks.shared import CODE_TO_REVIEW, bugs_detail, count_bugs
from tramontane.core.agent import Agent
from tramontane.core.pipeline import Pipeline


async def run() -> dict[str, Any]:
    """Run the code review pipeline and return benchmark metrics."""
    agents = [
        Agent(
            role="Code Reviewer",
            goal="Read code and identify bugs, anti-patterns, and issues",
            backstory="Senior engineer with 10 years Python experience",
            model="auto",
            budget_eur=0.05,
        ),
        Agent(
            role="Security Auditor",
            goal="Identify security vulnerabilities and OWASP issues",
            backstory="Certified security engineer specializing in Python",
            model="auto",
            budget_eur=0.05,
            reasoning=True,
        ),
        Agent(
            role="Report Writer",
            goal="Write a concise summary report of all findings",
            backstory="Technical writer specializing in security reports",
            model="auto",
            budget_eur=0.05,
        ),
    ]

    pipeline = Pipeline(
        name="bench_code_review",
        agents=agents,
        handoffs=[
            ("Code Reviewer", "Security Auditor"),
            ("Security Auditor", "Report Writer"),
        ],
        budget_eur=0.10,
    )

    start = time.monotonic()
    result = await pipeline.run(input_text=CODE_TO_REVIEW)
    elapsed = time.monotonic() - start

    output = result.output or ""
    total_tokens = 0  # Pipeline doesn't track per-token yet; use cost proxy

    return {
        "framework": "tramontane",
        "wall_time_s": round(elapsed, 2),
        "cost_eur": round(result.total_cost_eur, 6),
        "total_tokens": total_tokens,
        "models_used": result.models_used,
        "agents": len(result.agents_used),
        "bugs_found": count_bugs(output),
        "bugs_detail": bugs_detail(output),
        "output_len": len(output),
        "status": result.status.value,
    }

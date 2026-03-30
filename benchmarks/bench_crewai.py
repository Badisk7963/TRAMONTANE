"""Benchmark: CrewAI + Mistral 3-agent code review pipeline.

Requires: pip install crewai
"""

from __future__ import annotations

import os
import time
from typing import Any

from benchmarks.shared import CODE_TO_REVIEW, bugs_detail, count_bugs


async def run() -> dict[str, Any]:
    """Run 3-agent CrewAI crew with Mistral models via LiteLLM."""
    from crewai import Agent, Crew, Process, Task

    os.environ.setdefault("MISTRAL_API_KEY", "")
    model = "mistral/mistral-small-latest"

    reviewer = Agent(
        role="Senior Code Reviewer",
        goal="Identify all bugs, anti-patterns, and issues in the code",
        backstory="You are a senior Python engineer with 10 years experience.",
        llm=model,
        verbose=False,
    )
    auditor = Agent(
        role="Security Auditor",
        goal="Find all security vulnerabilities and OWASP issues",
        backstory="You are a certified security engineer.",
        llm=model,
        verbose=False,
    )
    writer = Agent(
        role="Report Writer",
        goal="Write a concise summary report of all findings",
        backstory="You are a technical writer specializing in security reports.",
        llm=model,
        verbose=False,
    )

    review_task = Task(
        description=f"Review this code for bugs:\n\n{CODE_TO_REVIEW}",
        expected_output="List of bugs and issues found",
        agent=reviewer,
    )
    audit_task = Task(
        description=f"Security audit this code:\n\n{CODE_TO_REVIEW}",
        expected_output="List of security vulnerabilities",
        agent=auditor,
    )
    report_task = Task(
        description="Write a summary report combining the review and audit findings",
        expected_output="Structured security review report",
        agent=writer,
    )

    crew = Crew(
        agents=[reviewer, auditor, writer],
        tasks=[review_task, audit_task, report_task],
        process=Process.sequential,
        verbose=False,
    )

    start = time.monotonic()
    result = crew.kickoff()
    elapsed = time.monotonic() - start

    output = str(result)

    # CrewAI uses LiteLLM — cost tracking is limited
    # Estimate: 3 calls * ~2000 tokens * mistral-small pricing
    est_cost = (6000 / 1_000_000) * 0.10 + (6000 / 1_000_000) * 0.30

    return {
        "framework": "crewai",
        "wall_time_s": round(elapsed, 2),
        "cost_eur": round(est_cost, 6),
        "total_tokens": 0,
        "models_used": ["mistral-small-latest"] * 3,
        "agents": 3,
        "bugs_found": count_bugs(output),
        "bugs_detail": bugs_detail(output),
        "output_len": len(output),
        "status": "complete",
    }

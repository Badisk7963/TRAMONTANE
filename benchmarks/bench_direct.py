"""Benchmark: Raw Mistral SDK (no framework). Baseline comparison."""

from __future__ import annotations

import os
import time
from typing import Any

from benchmarks.shared import CODE_TO_REVIEW, bugs_detail, count_bugs


async def run() -> dict[str, Any]:
    """Run 3 sequential Mistral chat calls — the framework-free baseline."""
    from mistralai.client import Mistral

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    client = Mistral(api_key=api_key)
    model = "mistral-small-latest"

    total_input = 0
    total_output = 0
    start = time.monotonic()

    # Agent 1: Code reviewer
    r1 = await client.chat.complete_async(
        model=model,
        messages=[  # type: ignore[arg-type]
            {"role": "system", "content": "You are a senior code reviewer. Identify all bugs."},
            {"role": "user", "content": f"Review this code:\n\n{CODE_TO_REVIEW}"},
        ],
    )
    review = str(r1.choices[0].message.content or "")
    if r1.usage:
        total_input += r1.usage.prompt_tokens or 0
        total_output += r1.usage.completion_tokens or 0

    # Agent 2: Security auditor
    r2 = await client.chat.complete_async(
        model=model,
        messages=[  # type: ignore[arg-type]
            {
                "role": "system",
                "content": "You are a security auditor. Find OWASP vulnerabilities.",
            },
            {
                "role": "user",
                "content": (
                    f"Security audit this code:\n\n{CODE_TO_REVIEW}"
                    f"\n\nPrior review:\n{review}"
                ),
            },
        ],
    )
    audit = str(r2.choices[0].message.content or "")
    if r2.usage:
        total_input += r2.usage.prompt_tokens or 0
        total_output += r2.usage.completion_tokens or 0

    # Agent 3: Report writer
    r3 = await client.chat.complete_async(
        model=model,
        messages=[  # type: ignore[arg-type]
            {
                "role": "system",
                "content": "Write a concise summary report of code review findings.",
            },
            {
                "role": "user",
                "content": f"Summarize:\n\nReview:\n{review}\n\nAudit:\n{audit}",
            },
        ],
    )
    report = str(r3.choices[0].message.content or "")
    if r3.usage:
        total_input += r3.usage.prompt_tokens or 0
        total_output += r3.usage.completion_tokens or 0

    elapsed = time.monotonic() - start

    # Cost: mistral-small = EUR 0.10/1M in + 0.30/1M out
    cost = (total_input / 1_000_000) * 0.10 + (total_output / 1_000_000) * 0.30

    full_output = f"{review}\n{audit}\n{report}"

    return {
        "framework": "direct_sdk",
        "wall_time_s": round(elapsed, 2),
        "cost_eur": round(cost, 6),
        "total_tokens": total_input + total_output,
        "models_used": [model, model, model],
        "agents": 3,
        "bugs_found": count_bugs(full_output),
        "bugs_detail": bugs_detail(full_output),
        "output_len": len(full_output),
        "status": "complete",
    }

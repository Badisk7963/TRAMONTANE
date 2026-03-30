"""Tramontane Benchmark Runner.

Runs code review benchmarks across frameworks and prints a comparison table.

Usage:
    uv run python benchmarks/run_benchmarks.py
    uv run python benchmarks/run_benchmarks.py --only tramontane,direct
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import anyio
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

BENCHMARKS: dict[str, str] = {
    "tramontane": "benchmarks.bench_tramontane",
    "direct": "benchmarks.bench_direct",
    "langgraph": "benchmarks.bench_langgraph",
    "crewai": "benchmarks.bench_crewai",
}


def check_available(module_path: str) -> bool:
    """Check if a benchmark's dependencies are installed."""
    try:
        mod = importlib.import_module(module_path)
        # Try importing — if deps are missing, it will fail
        if hasattr(mod, "run"):
            return True
    except (ImportError, ModuleNotFoundError):
        return False
    return False


async def run_benchmark(name: str, module_path: str) -> dict[str, Any] | None:
    """Run a single benchmark with timeout."""
    try:
        mod = importlib.import_module(module_path)
        with anyio.fail_after(60):
            return await mod.run()  # type: ignore[no-any-return]
    except TimeoutError:
        return {"framework": name, "status": "timeout", "wall_time_s": 60.0}
    except Exception as exc:
        return {"framework": name, "status": f"error: {exc}", "wall_time_s": 0.0}


async def main() -> None:
    """Run all available benchmarks and display results."""
    if not os.environ.get("MISTRAL_API_KEY"):
        console.print("[bold red]MISTRAL_API_KEY not set. Exiting.[/]")
        sys.exit(1)

    # Parse --only flag
    only: set[str] | None = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only"):
            if "=" in arg:
                only = set(arg.split("=")[1].split(","))
            elif sys.argv.index(arg) + 1 < len(sys.argv):
                only = set(sys.argv[sys.argv.index(arg) + 1].split(","))

    console.print()
    console.print("[bold #00D4EE]TRAMONTANE Benchmark Suite[/]")
    console.print("[#4A6480]3-agent code review pipeline comparison[/]\n")

    results: list[dict[str, Any]] = []

    for name, module_path in BENCHMARKS.items():
        if only and name not in only:
            continue

        if not check_available(module_path):
            console.print(f"  [dim]SKIP[/] {name} (dependencies not installed)")
            continue

        console.print(f"  [#00D4EE]>>[/] Running {name}...")
        start = time.monotonic()
        result = await run_benchmark(name, module_path)
        elapsed = time.monotonic() - start

        if result:
            results.append(result)
            cost = result.get("cost_eur", 0)
            bugs = result.get("bugs_found", "?")
            console.print(
                f"     [green]DONE[/] ({elapsed:.1f}s) "
                f"cost=EUR {cost:.4f} bugs={bugs}/3"
            )
        else:
            console.print(f"     [red]FAIL[/] ({elapsed:.1f}s)")

    if not results:
        console.print("\n[red]No benchmarks ran.[/]")
        sys.exit(1)

    # Display comparison table
    console.print()
    table = Table(
        title="Code Review Pipeline Benchmark",
        title_style="bold #00D4EE",
        box=box.MINIMAL_HEAVY_HEAD,
        header_style="bold #00D4EE",
        border_style="dim #1C2E42",
    )
    table.add_column("Framework", style="#DCE9F5")
    table.add_column("Time (s)", justify="right")
    table.add_column("Cost (EUR)", justify="right", style="bold #FFB020")
    table.add_column("Tokens", justify="right")
    table.add_column("Models", style="italic #00D4EE")
    table.add_column("Bugs/3", justify="center")
    table.add_column("Status")

    for r in results:
        models = r.get("models_used", [])
        model_str = ", ".join(dict.fromkeys(models)) if models else "-"
        bugs = r.get("bugs_found", "?")
        bug_color = "#22D68A" if bugs == 3 else "#FFB020" if bugs == 2 else "#FF4560"

        table.add_row(
            r.get("framework", "?"),
            f"{r.get('wall_time_s', 0):.1f}",
            f"EUR {r.get('cost_eur', 0):.4f}",
            f"{r.get('total_tokens', 0):,}",
            model_str[:40],
            f"[{bug_color}]{bugs}/3[/]",
            r.get("status", "?"),
        )

    console.print(table)

    # Bug detail
    console.print()
    for r in results:
        detail = r.get("bugs_detail", {})
        if detail:
            found = [k for k, v in detail.items() if v]
            missed = [k for k, v in detail.items() if not v]
            console.print(
                f"  [{r['framework']}] Found: {found or 'none'} | Missed: {missed or 'none'}"
            )

    # Save results
    out_path = Path("benchmarks/results.json")
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    console.print(f"\n[#4A6480]Results saved to {out_path}[/]\n")


if __name__ == "__main__":
    anyio.run(main)

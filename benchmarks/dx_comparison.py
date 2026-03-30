"""Developer experience comparison — static feature matrix + LOC count."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table

console = Console()

_T, _F = True, False

FEATURES: dict[str, dict[str, bool]] = {
    "Intelligent model routing": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "EUR budget ceilings": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "Budget quality floors": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "GDPR PII detection": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "Article 30 reports": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "Checkpoint/resume": {"tramontane": _T, "langgraph": _T, "crewai": _F, "direct": _F},
    "Agentic + deterministic": {"tramontane": _T, "langgraph": _T, "crewai": _F, "direct": _F},
    "SSE streaming": {"tramontane": _T, "langgraph": _T, "crewai": _F, "direct": _F},
    "Voice input (Voxtral)": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "MCP client": {"tramontane": _T, "langgraph": _F, "crewai": _F, "direct": _F},
    "Parallel execution": {"tramontane": _F, "langgraph": _T, "crewai": _T, "direct": _F},
    "Community ecosystem": {"tramontane": _F, "langgraph": _T, "crewai": _T, "direct": _F},
    "Local/Ollama": {"tramontane": _T, "langgraph": _T, "crewai": _T, "direct": _T},
}

SETUP_FRICTION: dict[str, dict[str, Any]] = {
    "tramontane": {"pip_installs": 1, "env_vars": 1, "config_files": 0, "loc": 0},
    "langgraph": {"pip_installs": 2, "env_vars": 1, "config_files": 0, "loc": 0},
    "crewai": {"pip_installs": 1, "env_vars": 1, "config_files": 0, "loc": 0},
    "direct": {"pip_installs": 1, "env_vars": 1, "config_files": 0, "loc": 0},
}


def count_loc(path: str) -> int:
    """Count non-empty, non-comment lines in a Python file."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        return sum(
            1 for line in lines
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith('"""')
        )
    except FileNotFoundError:
        return 0


def run_comparison() -> dict[str, Any]:
    """Generate the full DX comparison data."""
    bench_dir = Path(__file__).parent

    for fw, info in SETUP_FRICTION.items():
        path = bench_dir / f"bench_{fw}.py"
        info["loc"] = count_loc(str(path))

    scores: dict[str, int] = {}
    for fw in ["tramontane", "langgraph", "crewai", "direct"]:
        scores[fw] = sum(1 for f in FEATURES.values() if f.get(fw, False))

    return {"features": FEATURES, "setup": SETUP_FRICTION, "scores": scores}


def display(data: dict[str, Any]) -> None:
    """Print Rich tables for the comparison."""
    table = Table(
        title="Feature Comparison",
        title_style="bold #00D4EE",
        box=box.MINIMAL_HEAVY_HEAD,
        header_style="bold #00D4EE",
        border_style="dim #1C2E42",
    )
    table.add_column("Feature", style="#DCE9F5")
    for fw in ["tramontane", "langgraph", "crewai", "direct"]:
        table.add_column(fw.capitalize(), justify="center")

    for feature, support in FEATURES.items():
        row = [feature]
        for fw in ["tramontane", "langgraph", "crewai", "direct"]:
            row.append("[green]Yes[/]" if support.get(fw) else "[dim]No[/]")
        table.add_row(*row)

    scores = data["scores"]
    table.add_row(
        "[bold]Score[/]",
        f"[bold #00D4EE]{scores['tramontane']}/13[/]",
        f"{scores['langgraph']}/13",
        f"{scores['crewai']}/13",
        f"{scores['direct']}/13",
    )
    console.print(table)

    console.print()
    setup_table = Table(
        title="Setup Friction",
        title_style="bold #00D4EE",
        box=box.MINIMAL_HEAVY_HEAD,
        header_style="bold #00D4EE",
        border_style="dim #1C2E42",
    )
    setup_table.add_column("Metric", style="#DCE9F5")
    for fw in ["tramontane", "langgraph", "crewai", "direct"]:
        setup_table.add_column(fw.capitalize(), justify="center")

    for metric in ["pip_installs", "env_vars", "loc"]:
        row = [metric.replace("_", " ").title()]
        for fw in ["tramontane", "langgraph", "crewai", "direct"]:
            row.append(str(data["setup"][fw][metric]))
        setup_table.add_row(*row)
    console.print(setup_table)


def save(data: dict[str, Any], path: str = "benchmarks/dx_results.json") -> None:
    """Save comparison data as JSON."""
    Path(path).write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8",
    )


if __name__ == "__main__":
    data = run_comparison()
    display(data)
    save(data)
    console.print("\n[#4A6480]Saved to benchmarks/dx_results.json[/]")

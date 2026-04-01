# Tramontane

> **The only agent framework that gets smarter every time you use it.**

Mistral-native agent orchestration with intelligent model routing,
self-learning, cost control, and GDPR compliance.
Built in Orleans, France.

```bash
pip install tramontane
```

[![PyPI](https://img.shields.io/pypi/v/tramontane)](https://pypi.org/project/tramontane/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Why Tramontane?

CrewAI builds teams. LangGraph builds graphs.
**Tramontane conducts an orchestra.**

While other frameworks treat AI models as interchangeable black boxes,
Tramontane knows every instrument in the Mistral fleet — its range,
its cost, its strengths. It doesn't just pick a model. It picks the
model, the effort level, the fallback chain, and the budget guard —
all in one call.

| Feature | CrewAI | LangGraph | Tramontane |
|---------|--------|-----------|------------|
| Role-based agents | Yes | No | Yes |
| EUR cost tracking | No | No | Yes |
| Intelligent model routing | No | No | Yes |
| Reasoning effort control | No | No | Yes |
| Progressive reasoning | No | No | Yes |
| Model cascading | No | No | Yes |
| Self-learning router | No | No | Yes |
| Cost simulation (dry run) | No | No | Yes |
| Output validation + retry | Guardrails | No | Yes |
| GDPR middleware | No | No | Yes |
| Streaming with callbacks | No | No | Yes |

## Quick Start

```python
import asyncio
from tramontane import Agent, MistralRouter

agent = Agent(
    role="Analyst",
    goal="Analyze market trends",
    backstory="Senior market analyst with 10 years experience",
    model="auto",
    budget_eur=0.01,
)

async def main():
    router = MistralRouter()
    result = await agent.run("Analyze the EU AI market in 2026", router=router)
    print(f"Model: {result.model_used}")
    print(f"Cost: EUR {result.cost_eur:.4f}")
    print(result.output)

asyncio.run(main())
```

## Smart Fleet

### Reasoning Effort Control

One model, three thinking depths:

```python
# Fast response (like old mistral-small)
agent = Agent(model="mistral-small-4", reasoning_effort="none")

# Balanced reasoning
agent = Agent(model="mistral-small-4", reasoning_effort="medium")

# Deep thinking (like old magistral)
agent = Agent(model="mistral-small-4", reasoning_effort="high")
```

### Progressive Reasoning

Start cheap, escalate only when needed:

```python
agent = Agent(
    model="mistral-small-4",
    reasoning_strategy="progressive",  # none -> medium -> high
    validate_output=lambda r: "conclusion" in r.output,
)
# 70% succeed on "none". Average cost drops 60%.
```

### Model Cascading

Try affordable models first, escalate on failure:

```python
agent = Agent(
    cascade=["devstral-small", "devstral-2", "mistral-large-3"],
    validate_output=lambda r: len(r.output) > 1000,
)
```

### Cost Simulation

Know the price before you pay:

```python
from tramontane import simulate_pipeline

sim = simulate_pipeline([planner, designer, builder, reviewer], prompt)
print(f"Estimated: EUR {sim.total_estimated_cost_eur:.4f}, ~{sim.total_estimated_time_s}s")
```

### Self-Learning Router

Gets smarter with every call:

```python
from tramontane import MistralRouter, FleetTelemetry

router = MistralRouter(telemetry=FleetTelemetry())
# Day 1: Routes by rules
# Day 30: Routes by YOUR production data (95% accuracy)
```

### Fleet Profiles

One line to configure everything:

```python
from tramontane import Agent, FleetProfile

agent = Agent(role="Writer", fleet_profile=FleetProfile.BUDGET)
# BUDGET: cheapest models, minimal reasoning
# BALANCED: smart routing (default)
# QUALITY: best models, deep reasoning
# UNIFIED: mistral-small-4 for everything
```

## Streaming

Token-by-token streaming with pattern callbacks:

```python
async for event in agent.run_stream(
    "Generate a report",
    on_pattern={r"## (?P<section>.+)": on_section_found},
):
    if event.type == "token":
        print(event.token, end="", flush=True)
```

## The Mistral Fleet

| Model | Best For | Cost/1M in / out |
|-------|----------|------------------|
| ministral-3b | Classification, triage | EUR 0.04 / 0.04 |
| mistral-small-4 | General + reasoning + vision | EUR 0.15 / 0.60 |
| devstral-small | Code generation | EUR 0.10 / 0.30 |
| devstral-2 | Complex code, SWE | EUR 0.50 / 1.50 |
| mistral-large-3 | Frontier synthesis | EUR 2.00 / 6.00 |
| voxtral-mini | Transcription | EUR 0.04 / 0.04 |
| voxtral-tts | Text-to-speech (9 languages) | EUR 0.016/1K chars |

## Built With Tramontane

- **ArkhosAI** — 4-agent website generator, EUR 0.004/generation.
- **Gerald** — Autonomous business operations agent. Lead gen + social media + weekly briefs.

## GDPR Native

```python
agent = Agent(
    role="Data Processor",
    gdpr_level="strict",  # PII detection + redaction
    audit_actions=True,    # Full audit trail
)
```

Built-in PII detection (French + EU formats), Article 17 erasure,
Article 30 reports. EU entity (Bleucommerce SAS, France).

## Links

- [Documentation](https://github.com/Jesiel-dev-creator/TRAMONTANE)
- [PyPI](https://pypi.org/project/tramontane/)
- [Live Demo](https://hf.co/spaces/BleuCommerce-Apps/TRAMONTANE-demo)

## License

MIT — Bleucommerce SAS, Orleans, France

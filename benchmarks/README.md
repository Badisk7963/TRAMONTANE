# Benchmarks

Compare Tramontane against LangGraph, CrewAI, and raw Mistral SDK
on the same 3-agent code review pipeline.

## Prerequisites

```bash
pip install tramontane                    # always
pip install langgraph langchain-mistralai # for LangGraph comparison
pip install crewai                        # for CrewAI comparison

export MISTRAL_API_KEY=your_key
```

## Run

```bash
# Run all available benchmarks
python benchmarks/run_benchmarks.py

# Run only Tramontane + raw SDK (no extra deps needed)
python benchmarks/run_benchmarks.py --only tramontane,direct

# Run DX comparison (no API key needed)
python benchmarks/dx_comparison.py
```

## Expected Cost

Each full run costs approximately:

| Framework | Est. Cost |
|-----------|-----------|
| Tramontane | ~EUR 0.002 |
| LangGraph | ~EUR 0.002 |
| CrewAI | ~EUR 0.002 |
| Raw SDK | ~EUR 0.002 |
| **Total** | **~EUR 0.01** |

## What's Measured

- **Wall time** -- total seconds from start to finish
- **Cost** -- actual EUR cost from token usage
- **Tokens** -- total input + output tokens
- **Bugs found** -- the test code has 3 intentional bugs:
  1. SQL injection (f-string query)
  2. Path traversal (/tmp/ + user input)
  3. Hardcoded API key

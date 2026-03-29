# TRAMONTANE — Claude Code Master Context

> Read this file completely before doing anything else.
> This is the single source of truth for the entire project.

---

## 🌬️ What This Project Is

**TRAMONTANE** is an open-source, Mistral-native agent orchestration framework.
It is to the Mistral ecosystem what LangGraph is to OpenAI — except built
*from* Mistral's own primitives outward, not bolted on top.

**Owner:** Jesiel · Bleucommerce SAS · Orléans, France 🇫🇷
**License:** MIT (core) · Open-core commercial (TramontaneOS Pro)
**Stack:** Python 3.12+ · uv · Pydantic v2 · FastAPI · Typer · Rich · asyncio
**Models:** Mistral fleet only — no OpenAI, no LangChain, no LiteLLM ever
**Infra:** Hetzner VPS (dev) · Scaleway EU-west-1 Paris (prod) · GDPR-native

---

## 🏗️ Three-Layer Architecture

```
Layer 1 → SDK          pip install tramontane
Layer 2 → Runtime      Router · Executor · Memory · GDPR
Layer 3 → TramontaneOS  Production API · Dashboard · Hub
```

We build Layer 1 + 2 first. Layer 3 after.

---

## 📁 Exact Repo Structure

```
tramontane/
├── tramontane/
│   ├── __init__.py
│   ├── core/
│   │   ├── agent.py          ← BUILD FIRST
│   │   ├── pipeline.py
│   │   ├── workflow.py
│   │   ├── handoff.py
│   │   ├── conversation.py
│   │   └── exceptions.py
│   ├── router/
│   │   ├── classifier.py
│   │   ├── router.py
│   │   ├── models.py
│   │   └── rules.yaml
│   ├── memory/
│   │   ├── conversation.py
│   │   ├── pipeline.py
│   │   ├── longterm.py
│   │   └── schema.sql
│   ├── gdpr/
│   │   ├── middleware.py
│   │   ├── pii.py
│   │   ├── audit.py
│   │   └── reports.py
│   ├── tools/
│   │   ├── registry.py
│   │   ├── builtin.py
│   │   ├── mcp.py
│   │   └── sandbox.py
│   ├── voice/
│   │   └── gateway.py
│   ├── hub/
│   │   ├── client.py
│   │   └── publisher.py
│   ├── cli/
│   │   └── main.py
│   └── server/
│       ├── app.py
│       ├── routes.py
│       └── streaming.py
├── pipelines/
│   ├── lead_gen_fr.yaml
│   ├── market_research.yaml
│   ├── code_review.yaml
│   └── document_analysis.yaml
├── tests/
├── examples/
├── docs/
├── pyproject.toml
├── README.md
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## 🤖 The Mistral Model Fleet (Router Targets)

| Alias | API ID | Tier | Best For | Cost/1M |
|---|---|---|---|---|
| `ministral-3b` | ministral-3b-latest | 0 | Classification, PII, triage | €0.04 |
| `ministral-7b` | ministral-8b-latest | 1 | Bulk, extraction, tool calls | €0.10 |
| `mistral-small` | mistral-small-latest | 2 | General, multilingual | €0.10/0.30 |
| `devstral-small` | devstral-small-2505 | 2 | ALL code tasks, SWE | €0.10/0.30 |
| `magistral-small` | magistral-small-latest | 3 | Reasoning, CoT, planning | €0.50/1.50 |
| `magistral-medium` | magistral-medium-latest | 3 | Deep reasoning | €2.00/5.00 |
| `devstral-2` | devstral-latest | 4 | Complex SWE, monorepo | €0.50/1.50 |
| `pixtral-large` | pixtral-large-latest | 4 | Vision, multimodal, OCR | €2.00/6.00 |
| `mistral-large` | mistral-large-latest | 4 | Frontier, synthesis | €2.00/6.00 |
| `voxtral-mini` | voxtral-mini-latest | 1 | Voice input transcription | €0.04 |

**RULE: model="auto" → router decides. Never hardcode expensive models.**

---

## ⚙️ Router Decision Logic

```
has_vision?           → pixtral-large
task=code/has_code?
  complexity >= 4     → devstral-2
  else                → devstral-small
needs_reasoning?
  complexity >= 4     → magistral-medium
  else                → magistral-small
task=bulk/complexity=1 → ministral-7b
task=research+complexity>=3 → mistral-large
default               → mistral-small

budget constraint?    → downgrade to next cheaper that fits
locale=fr/de/es/it?   → prefer multilingual-strong models
--local flag?         → map all to Ollama equivalents
```

**Function calling always routes to ministral-7b unless reasoning required.**

---

## 🔑 Core Agent Class (implement exactly)

```python
class Agent(BaseModel):
    # IDENTITY — required (CrewAI UX pattern)
    role: str
    goal: str
    backstory: str

    # MODEL ROUTING — Tramontane-unique
    model: str = "auto"
    function_calling_model: str = "auto"
    reasoning_model: Optional[str] = None
    locale: str = "en"

    # TOOLS
    tools: list[Any] = []
    allow_code_execution: bool = False
    code_execution_mode: Literal["safe", "unsafe"] = "safe"

    # EXECUTION GUARDS — from CrewAI
    max_iter: int = 20
    max_rpm: Optional[int] = None
    max_execution_time: Optional[int] = None  # seconds
    max_retry_limit: int = 3
    respect_context_window: bool = True

    # INTELLIGENCE FLAGS
    reasoning: bool = False
    max_reasoning_attempts: Optional[int] = 3
    streaming: bool = True
    inject_date: bool = False
    allow_delegation: bool = False

    # MEMORY — from Agno
    memory: bool = True
    add_history_to_context: bool = True
    learning: bool = False

    # COST CONTROL — Tramontane-unique
    budget_eur: Optional[float] = None

    # GDPR — Tramontane-unique
    gdpr_level: Literal["none", "standard", "strict"] = "none"
    store_on_cloud: bool = True

    # OBSERVABILITY
    audit_actions: bool = True
    verbose: bool = False
    step_callback: Optional[Callable] = None
```

---

## 🔧 Pipeline Modes

**AGENTIC mode** — Mistral Handoffs API, non-deterministic
- Use `handoff_execution="client"` to intercept every handoff
- Inject: budget check → GDPR middleware → audit log → cost tracker
- Before passing control to next agent

**WORKFLOW mode** — deterministic, step-by-step (Agno pattern)
- Checkpoint to SQLite after every step
- On failure at step N: resume from step N, never restart from zero
- Each step has own model, budget, timeout

**Both modes support:**
- `budget_eur` hard ceiling (stop + return best result so far)
- `streaming=True` (SSE every agent token, not just final)
- Interrupt points (pause for human approval)
- Audit log entry per action
- Per-step cost breakdown

---

## 🛡️ 7 Failure Mode Guards (from HF paper 2503.13657)

Build these into pipeline executor:

1. `MAX_HANDOFF_DEPTH = 10` → raise HandoffLoopError
2. Circular handoff detection → same agent_id twice = error
3. Conflicting agent instructions check on Pipeline creation
4. Output format validation via Pydantic before each handoff
5. `asyncio.wait_for()` timeout on every agent execution
6. Empty output guard → retry once, then fallback message
7. Budget check BEFORE every LLM call, not after

---

## 🗄️ Memory Schema (SQLite + FTS5)

```sql
-- Main memory table
CREATE TABLE tramontane_memory (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    pipeline_name TEXT,
    entity_key TEXT,
    memory_type TEXT,  -- fact|preference|history|entity
    content TEXT NOT NULL,
    embedding BLOB,    -- mistral-embed vector
    importance REAL DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME,
    access_count INTEGER DEFAULT 0,
    expires_at DATETIME,   -- NULL = permanent
    erased_at DATETIME     -- GDPR Article 17
);

-- Full-text search
CREATE VIRTUAL TABLE tramontane_memory_fts
USING fts5(content, entity_key, pipeline_name);

-- GDPR erasure log
CREATE TABLE tramontane_erasure_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    erased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    erased_count INTEGER,
    requested_by TEXT
);

-- Audit log (APPEND ONLY — never delete rows)
CREATE TABLE tramontane_audit (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    pipeline_name TEXT,
    agent_role TEXT,
    action_type TEXT,  -- llm_call|tool_call|handoff|error
    model_used TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_eur REAL,
    gdpr_sensitivity TEXT,
    pii_detected BOOLEAN,
    pii_redacted BOOLEAN,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT      -- JSON
);
```

---

## 💻 CLI Commands to Implement

```
tramontane run <pipeline> [--input TEXT] [--file PATH]
              [--budget FLOAT] [--local] [--voice]
              [--output PATH] [--gdpr standard|strict]

tramontane schedule <pipeline> --cron "0 9 * * 1"
tramontane watch
tramontane serve [--port 8080] [--multitenancy]
tramontane hub search [QUERY]
tramontane hub install <org/name>
tramontane hub publish <yaml> --name <org/name>
tramontane audit [--pipeline NAME] [--export article30]
tramontane models
```

---

## 📦 Dependencies

```toml
[project]
name = "tramontane"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "mistralai>=1.0.0",
    "pydantic>=2.0.0",
    "typer[all]>=0.12.0",
    "rich>=13.0.0",
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "anyio>=4.0.0",
    "httpx>=0.27.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
redis   = ["redis>=5.0.0"]
postgres = ["asyncpg>=0.29.0", "pgvector>=0.2.0"]
voice   = ["sounddevice>=0.4.0", "numpy>=1.26.0"]
sandbox = ["e2b>=0.17.0"]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]
```

---

## 🔨 Build Order (strict — do not skip steps)

### Phase 1 — Foundation
1. `pyproject.toml` + `tramontane/__init__.py`
2. `tramontane/core/exceptions.py`
3. `tramontane/router/models.py` + `rules.yaml`
4. `tramontane/core/agent.py`
5. `tramontane/router/classifier.py`
6. `tramontane/router/router.py`

### Phase 2 — Pipeline Engine
7. `tramontane/core/handoff.py`
8. `tramontane/core/conversation.py`
9. `tramontane/core/pipeline.py`
10. `tramontane/core/workflow.py`

### Phase 3 — Memory + GDPR
11. `tramontane/memory/schema.sql` + `longterm.py`
12. `tramontane/memory/conversation.py` + `pipeline.py`
13. `tramontane/gdpr/pii.py`
14. `tramontane/gdpr/audit.py`
15. `tramontane/gdpr/middleware.py`
16. `tramontane/gdpr/reports.py`

### Phase 4 — Tools + Voice
17. `tramontane/tools/registry.py` + `builtin.py`
18. `tramontane/tools/mcp.py` + `sandbox.py`
19. `tramontane/voice/gateway.py`

### Phase 5 — CLI + Server
20. `tramontane/cli/main.py`
21. `tramontane/server/app.py` + `routes.py` + `streaming.py`

### Phase 6 — Hub + Tests + Pipelines
22. `tramontane/hub/client.py` + `publisher.py`
23. All 5 example files
24. All 5 test files
25. Built-in pipeline YAMLs
26. `Dockerfile` + `docker-compose.yml`

---

## 📐 Coding Rules (never break these)

1. **NEVER** import langchain, liteLLM, openai. Mistral-native only.
2. **ALWAYS** async/await for all Mistral API calls.
3. **ALWAYS** Pydantic v2 syntax (not v1).
4. **EVERY** Mistral API call wrapped in try/except:
   `MistralAPIException | BudgetExceededError | AgentTimeoutError | HandoffLoopError`
5. **EVERY** agent action → write to audit log before AND after.
6. **ALWAYS** run router before any LLM call when `model="auto"`.
7. **COST** calculated in EUR not USD.
   Formula: `(input_tokens/1_000_000 * cost_in) + (output_tokens/1_000_000 * cost_out)`
8. **ALL** YAML pipeline files validate against PipelineSchema on load.
9. **TYPE HINTS** everywhere. No bare `Any` except in Agent tools list.
10. **DOCSTRINGS** on every public method.
11. **IMPORTS** order in every file:
    ```python
    from __future__ import annotations
    # stdlib
    # third party (mistralai, pydantic, typer...)
    # internal (from tramontane.core import ...)
    ```
12. After each phase: `uv run ruff check . && uv run mypy .` must pass.
13. **NO** print() statements — use Rich console or Python logging.
14. **NO** hardcoded API keys — always `os.environ["MISTRAL_API_KEY"]`.

---

## 🌍 Frameworks We Studied (use their patterns where noted)

| Framework | Pattern to Use | Pattern to Avoid |
|---|---|---|
| **Mistral Agents API** | Handoffs, handoff_execution="client", Conversations API, MCP tools | Cloud-only thinking |
| **CrewAI** | Agent attributes (role/goal/backstory), max_iter, reasoning, inject_date, function_calling_llm | LiteLLM, their kickoff() pattern |
| **Agno** | AgentOS concept, learning=True, add_history_to_context, SQLite db=, deploy templates | OpenAI defaults |
| **LangGraph** | Durable execution, checkpoint/resume, interrupt/approve, time travel | LangSmith lock-in, StateGraph complexity |
| **smolagents** | Hub push/pull, CodeAgent sandbox, CLI single-command, stream_outputs=True default | Model agnosticism |

---

## 🎯 What We're Ultimately Building

Tramontane is the foundation. On top of it:

```
TRAMONTANE (this repo)
├── ArkhosAI  — EU answer to Lovable/Bolt (rebuilt on Tramontane pipelines)
├── CVBleu.fr — already live, gets smarter pipeline routing
├── Gerald    — lead-gen agent, routes through Tramontane
├── AEGIS     — trading signals, pipeline-based
└── Future    — LexBleu, AdminBleu, EduBleu
```

ArkhosAI's 6-agent app-generation pipeline is the flagship demo:
`planner(ministral-3b) → architect(magistral-small) → frontend_dev(devstral-small) →
backend_dev(devstral-small) → sandbox_runner(devstral-small) → debugger(auto)`

The live preview / streaming is the Lovable feeling. It works because
`streaming=True` on every agent sends SSE tokens in real time to the UI.

---

## 🔗 Key External Resources

- Mistral Agents API docs: https://docs.mistral.ai/agents/introduction
- Mistral Handoffs: https://docs.mistral.ai/agents/handoffs
- Mistral Models: https://docs.mistral.ai/getting-started/models
- Mistral Cookbook (2.2k stars): https://github.com/mistralai/cookbook
- HF paper — MasRouter: https://hf.co/papers/2502.11133
- HF paper — Why Multi-Agent Fails: https://hf.co/papers/2503.13657
- HF paper — SuperLocalMemory: https://hf.co/papers/2603.02240
- HF paper — FullStack-Agent: https://hf.co/papers/2602.03798

---

## 🚦 Current Status

**Phase 1 — NOT STARTED**

Next action: Run environment check, scaffold repo, begin Phase 1.

```bash
# First thing to run:
python3 --version   # needs 3.12+
node --version      # needs 20+
uv --version        # needs installed
docker --version    # needs installed

# Then:
uv init tramontane
cd tramontane
uv add mistralai pydantic "typer[all]" rich fastapi "uvicorn[standard]" \
    anyio httpx pyyaml python-dotenv
uv add --dev pytest pytest-asyncio respx ruff mypy
```

---

## 🔑 Environment Variables Needed

```bash
# .env (never commit this file)
MISTRAL_API_KEY=sk-...          # required
TRAMONTANE_ENV=development      # development | production
TRAMONTANE_DB=tramontane.db     # SQLite path
TRAMONTANE_LOG_LEVEL=INFO
TRAMONTANE_BUDGET_DEFAULT=0.10  # default pipeline budget in EUR

# Optional
REDIS_URL=redis://localhost:6379
SCALEWAY_REGION=fr-par          # for EU deployment
```

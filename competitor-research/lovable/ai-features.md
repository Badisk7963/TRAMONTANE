# Lovable — AI Features Analysis
> Source: docs.lovable.dev/integrations/ai (scraped 2026-03-30)

## Lovable AI (Shared Connector for Deployed Apps)
Lovable AI adds AI capabilities to apps users build — not just the builder itself.

### Default Model
- **Gemini 3 Flash** — fast, efficient, general-purpose

### Supported AI Models

| Model | Best For |
|-------|---------|
| Gemini 3 Flash (default) | Fast interactive builds, agent workflows |
| Gemini 3.1 Pro | Agentic workflows, advanced coding, multimodal |
| Nano Banana 2 (Gemini 3.1 Flash Image) | Rapid image generation, visual editing |
| Nano Banana Pro | High-quality image generation |
| Gemini 2.5 Pro | Deep reasoning, complex multimodal tasks |
| Gemini 2.5 Flash | Balanced speed + intelligence |
| Gemini 2.5 Flash Lite | High-volume lightweight tasks |
| Gemini 2.5 Flash Image | Image generation |
| GPT-5.2 | Complex reasoning, deep coding |
| GPT-5 | Accuracy-critical tasks |
| GPT-5 Mini | Mid-complexity reasoning |
| GPT-5 Nano | Simple tasks, high-volume |

### Model Selection
- Users can specify model in their prompt
- Agent auto-selects appropriate model if not specified

### Pricing
- **Usage-based** — same cost as going directly to LLM provider
- No hidden fees
- $1 free AI usage per month per workspace
- **Temporary:** $25 Cloud + $1 AI free monthly until end of Q1 2026
- Paid plans can top up balance

### Permission Preferences
- Always allow (default)
- Ask each time
- Never allow

### Rate Limits
- Per-workspace rate limits
- 429 Too Many Requests on exceed
- More restrictive for free users

## Key Observations for ArkhosAI
- **NO MISTRAL MODELS** — all Google Gemini and OpenAI GPT
- This is a MAJOR gap we can exploit — Mistral-native with transparent routing
- Usage-based pricing "same as provider" is honest but not transparent per-call
- No model routing intelligence — user must specify or get default
- No cost estimation before calls
- No budget controls per-project
- Heavy Google/Gemini dependency

# Bolt.new — Agents & Models Analysis
> Source: support.bolt.new/building/using-bolt/agents (scraped 2026-03-30)

## Agent Architecture
Bolt offers two agents:

### Claude Agent (recommended, primary)
- Powered by Anthropic's Claude model family
- Best for production-quality apps and larger development work
- More complete results, fewer errors
- May take longer and use more tokens
- **Plan Mode** available
- Can create Bolt Databases and connect to Supabase

### v1 Agent (legacy — being retired)
- Based on original Bolt experience
- Uses Anthropic Claude Sonnet
- Faster, fewer tokens, less capable
- Best for quick prototypes
- **Discussion Mode** (powered by Google Gemini for planning)
- **Retirement:** Can't select after April 13, 2026; can't access projects after August 3, 2026

## Model Selection (Claude Agent)

| Model | Speed | Reasoning | Best For |
|-------|-------|-----------|----------|
| **Haiku 4.5** | Fastest | Light | Quick UI edits, styling, content |
| **Sonnet 4.5** (default) | Balanced | Strong | Most everyday development |
| **Sonnet 4.6** | Balanced | Deep | Complex multi-step, larger codebases |
| **Opus 4.5** | Slower | Deep | Enterprise, compliance, high-stakes |
| **Opus 4.6** | Slower | Deepest | Advanced reasoning, legacy codebases |

## Key Technical Details
- All Claude models support large context windows
- Bolt limits active history to recent messages for performance
- Switching Claude models does NOT clear chat history
- Switching between agents DOES clear chat history
- Per-project model memory — Bolt remembers your selection
- Default model can be set in personal settings
- Supports `claude.md` files for project instructions

## Notable for ArkhosAI
- **100% Anthropic Claude** — no model routing, no cost optimization
- User must manually choose model — no automatic routing based on task
- No mention of cost per model or cost visibility
- No budget controls
- No Mistral, no OpenAI for the builder itself (only for Discussion Mode via Gemini)
- Model selection is a flat list — no intelligence about which to use

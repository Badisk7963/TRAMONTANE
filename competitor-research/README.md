# ArkhosAI Competitive Research
> Compiled: 2026-03-30 via Firecrawl MCP deep crawl

## Purpose
Granular competitive intelligence on the 3 major AI app builders to inform ArkhosAI product decisions.

## Competitors Analyzed
1. **Lovable** (lovable.dev) — Market leader by adoption (36M+ projects)
2. **Bolt.new** (bolt.new) — StackBlitz-powered, Claude-first builder
3. **v0** (v0.dev/v0.app) — Vercel's AI builder, React/Next.js focused

## Directory Structure

### Per-Competitor Files
```
lovable/     — 9 files (homepage, pricing, features, integrations, security-gdpr, ai-features, onboarding, summary)
bolt/        — 9 files (homepage, agents-models, bolt-cloud, supported-tech, token-system, integrations, mcp-support, prompting-guide, summary)
v0/          — 4 files (homepage, pricing, features, summary)
```

### Cross-Competitor Analysis
- **comparison-matrix.md** — Feature-by-feature comparison table
- **pricing-analysis.md** — Detailed pricing comparison with EUR conversion
- **ux-patterns.md** — Key user flows compared (onboarding, generation, iteration, deploy, errors)
- **integration-map.md** — Every integration each competitor supports
- **gaps-and-opportunities.md** — What they don't do that ArkhosAI can

## How to Read These Files
1. Start with **gaps-and-opportunities.md** for the strategic summary
2. Read **comparison-matrix.md** for feature-by-feature decisions
3. Read **pricing-analysis.md** for pricing strategy
4. Dive into per-competitor folders for detailed intelligence

## Pages Crawled
- **Lovable:** 10 pages (homepage, pricing, welcome, plan-mode, integrations, changelog*, security, DPA, AI features, getting-started)
- **Bolt.new:** 8 pages (homepage, intro, agents, supported-tech, bolt-cloud, discussion-mode, tokens, MCP)
- **v0/Vercel:** 5 pages (homepage, pricing, pricing-blog, vercel-pricing, search results)
- **Total: 23 pages successfully scraped**

*Changelog was too large to process in-conversation; key data extracted from other pages.

## Methodology
- Firecrawl MCP scrape tool for structured content extraction
- Markdown format, main content only
- All data from public pages (no auth-gated content)
- Pricing converted to EUR at 0.92 rate

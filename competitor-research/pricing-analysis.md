# Pricing Analysis — Lovable vs Bolt.new vs v0
> Compiled: 2026-03-30 | All prices USD with EUR conversion at 0.92

## Side-by-Side: Solo Developer

| | Lovable | Bolt.new | v0 + Vercel |
|---|---------|----------|-------------|
| Free tier | 5 credits/day (30/mo) | ~1M tokens/mo | $5 credits, 7 msg/day |
| Entry paid | $25/mo (EUR 23) | ~$20/mo Pro 20 | $30/mo + $20 Vercel = $50 (EUR 46) |
| Mid-tier | $50/mo (EUR 46) | ~$50/mo Pro 50 | $100/mo + $20 = $120 (EUR 110) |
| Enterprise | Custom | Custom | Custom |

## Side-by-Side: 5-Person Team

| | Lovable | Bolt.new | v0 + Vercel |
|---|---------|----------|-------------|
| Pro/Team | $25/mo total (EUR 23) | ~$100/mo (5x$20) | $150/mo (5x$30) + $20 = $170 (EUR 156) |
| Business | $50/mo total (EUR 46) | ~$250/mo (5x$50) | $500/mo (5x$100) + $20 = $520 (EUR 478) |

**Lovable is 3-10x cheaper for teams** due to per-workspace pricing.

## Credit/Token Economics

### Lovable
- Credit-based (opaque unit)
- 1 Plan mode message = 1 credit
- Agent mode cost unclear
- $25/mo = 100 credits + 5 daily = ~250/mo effective

### Bolt.new
- Token-based (AI tokens)
- Cost per message varies by project size
- Free: ~1M tokens/mo, 300K daily limit
- Rollover: 2 months on paid plans
- Reloaded tokens never expire

### v0
- Credit-based (dollar-valued)
- Transparent per-token pricing per model
- Free: $5/mo credits, 7 msg/day hard limit
- Team: $30/user + $2 daily login bonus
- Purchased credits expire after 1 year

## Transparency Ranking
1. **v0** — Most transparent (per-token pricing published)
2. **Bolt** — Medium (token counts visible, but cost per token unclear)
3. **Lovable** — Least transparent ("credits" with no published cost breakdown)

## Where Users Overpay
- **v0 teams:** Per-user pricing multiplies fast. 10-person team on Business = $1,200/mo
- **Bolt heavy users:** Large projects burn tokens on context sync, not just generation
- **Lovable free users:** 5 daily credits is extremely limited; pushes upgrades
- **v0 Max Fast:** $150/1M output tokens is extreme for iteration-heavy workflows

## ArkhosAI Pricing Opportunity
- **Per-workspace pricing** (like Lovable) — proven model, cheapest for teams
- **Transparent per-call pricing** (like v0) — show cost before each generation
- **Budget controls** (unique) — set max spend per project/pipeline
- **Mistral cost advantage** — Mistral models are 2-10x cheaper than Claude/GPT
- **EUR-native** — price in EUR, no currency risk for EU customers
- **No training surcharge** — GDPR compliance included in all plans, not a premium add-on

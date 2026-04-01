# Gaps & Opportunities for ArkhosAI
> Compiled: 2026-03-30 | Based on competitive analysis of Lovable, Bolt.new, v0

---

## 1. Table Stakes — Features ALL Competitors Have (MUST have in v0.1)

- Chat-to-app generation with natural language
- Real-time streaming preview during generation
- Template library for quick starts
- GitHub integration for code sync
- One-click deployment to hosted domain
- Plan/thinking mode before building
- Error detection and auto-fix
- Custom domain support (paid)
- Team workspaces with roles
- Database + auth + hosting bundled

## 2. Features NO Competitor Has (Our Differentiators)

| Gap | ArkhosAI Advantage |
|-----|-------------------|
| **Intelligent model routing** | Auto-select best model for task (cost + quality) |
| **Per-call cost transparency** | Show estimated cost BEFORE each generation |
| **Budget controls per project** | Hard budget ceiling, never overspend |
| **EU-native AI models** | Mistral fleet, data stays in EU |
| **Self-hostable open-core** | Deploy on your own infra |
| **Multi-agent pipeline visibility** | See which agent does what, why, cost |
| **GDPR on all plans** | No premium for privacy compliance |
| **Multi-model routing with quality floors** | Never silently downgrade below minimum quality |
| **Pipeline-based architecture** | Deterministic workflows, not just chat |
| **Cost in EUR** | Native European pricing, no currency risk |

## 3. Features Only ONE Competitor Has (Cherry-Pick)

| Feature | Who Has It | Should We Build? |
|---------|-----------|-----------------|
| Design Mode (visual editor) | v0 | Yes (v0.2+) — killer feature for non-coders |
| iOS creation app | v0 | No (not priority) |
| Expo mobile app building | Bolt | Yes (v0.2+) — mobile is growing market |
| Multiplayer real-time editing | Lovable | Yes (v0.2+) — team collaboration |
| Import from competitor | Bolt (from Lovable) | Yes — migration tools are growth hacks |
| AI in deployed apps (Lovable AI) | Lovable | Yes — this IS Tramontane's core value |
| Security scanning (4 scanners) | Lovable | Yes (v0.2+) — enterprise requirement |
| 98% less errors claim | Bolt | Aspire to — better error handling pipeline |
| Community app gallery (Discover) | Lovable | Yes (v0.2+) — social proof + discovery |
| claude.md project instructions | Bolt | Yes — we already have pipeline YAMLs |

## 4. Common User Complaints (from docs, FAQs, support pages)

| Issue | Who | ArkhosAI Solution |
|-------|-----|------------------|
| Opaque credit/token costs | All | Transparent per-call pricing |
| Context window limits | Bolt, v0 | Mistral's large context + smart truncation |
| Token waste on project sync | Bolt | Efficient context management |
| Large projects break things | All | Pipeline checkpointing, resume from failure |
| No cost visibility before action | All | Pre-call cost estimation |
| Training on user data | v0 (default), Lovable (service data) | Never train, contractually guaranteed |
| Vendor lock-in | v0 (Vercel), All (hosting) | Deploy anywhere, self-hostable |
| JavaScript-only backend | Bolt | Multi-language via Mistral code models |
| Manual model selection | Bolt, v0 | Automatic routing |
| No budget controls | All | Hard budget per project/pipeline |

## 5. Pricing Gaps

| Opportunity | Detail |
|-------------|--------|
| **Team pricing** | v0 at $30-100/user is 3-10x more than Lovable's $25/workspace |
| **Privacy premium** | v0 charges $100/user for training opt-out; we include it free |
| **Hosting bundled** | v0 charges Vercel hosting on top; we can bundle |
| **Mistral cost advantage** | Mistral models are 2-10x cheaper than Claude/GPT-5 |
| **EUR pricing** | All competitors price in USD; EU customers pay FX fees |
| **Student/startup plans** | Only Lovable has student discount; opportunity for startup plans |

## 6. EU/GDPR Gaps

| Issue | Lovable | Bolt | v0 | ArkhosAI |
|-------|---------|------|----|---------|
| EU entity | Swedish AB (secondary) | No | No | **Primary EU entity** |
| Primary entity | US (Delaware) | US | US | **France (Bleucommerce SAS)** |
| Data residency | EU/US/AU options | Not mentioned | Not specified | **EU-only default** |
| DPA availability | Business+ only | Not mentioned | Enterprise only | **All plans** |
| GDPR certification | Yes | Not mentioned | Yes (Vercel) | **Native** |
| No-training guarantee | Yes (contractual) | Not mentioned | Business+ only | **All plans, all tiers** |
| Sub-processor transparency | On request | Not mentioned | Not mentioned | **Public list** |
| Data sovereignty | Region selection | None | None | **EU infrastructure only** |
| Right to erasure | 30 days post-termination | Unknown | Unknown | **Immediate on request** |

---

## TOP 10 ACTIONABLE FINDINGS FOR ARKHOSAI

1. **Model routing is our killer feature** — NO competitor does automatic cost-optimized model selection
2. **Per-workspace pricing** (like Lovable) is 3-10x cheaper for teams than per-user (v0, Bolt)
3. **GDPR/privacy as default** is a massive differentiator — competitors charge $100/user for training opt-out
4. **Mistral cost advantage** means we can offer more generation for less money
5. **Transparent pricing + budget controls** — every competitor has opaque costs
6. **Design Mode** (v0's visual editor) is the most requested UX feature — plan for v0.2
7. **All-in-one backend** (like Bolt Cloud) is table stakes — hosting+DB+auth must be bundled
8. **Plan Mode before Build** is proven UX — both Lovable and Bolt have it, we need it
9. **Template gallery + community discovery** drives adoption — Lovable and v0 prove this
10. **Self-hostable open-core** is unique — NO competitor offers this, huge for enterprise EU

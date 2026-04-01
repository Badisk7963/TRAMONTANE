# Bolt.new — Token System & Pricing Analysis
> Source: support.bolt.new/account-and-subscription/tokens, bolt.new/pricing (scraped 2026-03-30)

## Token System
- Bolt uses **AI tokens** (not credits like Lovable)
- Tokens = small pieces of text processed by AI
- Both input and output tokens count
- Most token usage comes from Bolt **reading/syncing project files** (not user prompts)
- Bigger projects = more tokens per message

## Pricing Tiers (from bolt.new pricing page)
Bolt's pricing page is behind the app, but from docs:
- **Free plan:** token-based, resets 1st of each month, 300K daily limit, ~1M/month
- **Paid plans:** various tiers (Pro 20, Pro 50, etc.), reset on renewal date
- Token reload available on highest individual monthly or any annual plan
- Reloaded tokens **never expire**

## Token Reset
- Free: 1st of each calendar month
- Paid: on subscription renewal date
- Downgrading mid-month with >1M tokens used = wait until next month

## Token Rollover
- Paid subscription tokens roll over for **1 additional month** (2 months total validity)
- First-in, first-out consumption (oldest tokens used first)
- Canceling loses all tokens (rollover and current) at billing cycle end
- Resubscribing within rollover period restores unexpired tokens
- Annual plans: monthly allocation, same 2-month rollover per allocation
- Team plans: tokens assigned per member, stay linked to person

## Key Observations
- Token pricing is NOT transparent — no per-token cost visible
- "Most cost-effective option is to upgrade" — upsell language
- Rollover complexity creates lock-in
- 300K daily limit on free plan even with reloaded tokens
- No mention of cost per model (Claude Haiku vs Opus)
- No budget controls or cost estimation

## EUR Conversion
- Specific USD pricing not publicly listed on docs pages
- Bolt pricing page requires login to view

# Lovable — Integrations Analysis
> Source: docs.lovable.dev/integrations/introduction (scraped 2026-03-30)

## Three Integration Types

### 1. Shared Connectors (workspace-level, for deployed apps)
- **Lovable Cloud** — built-in backend: auth, database, hosting
- **Lovable AI** — AI capabilities (Gemini, GPT models)
- **Aikido** — AI-powered penetration testing
- **ElevenLabs** — audio/text-to-speech
- **Firecrawl** — web scraping/crawling
- **GitLab** — code sync (in addition to GitHub)
- **Perplexity** — web-backed research
- **Shopify** — ecommerce
- **Slack** — alerts, channels, updates
- **Stripe** — payments/subscriptions
- **Supabase** — auth + data storage
- **Telegram** — bot messaging
- **Twilio** — SMS, MMS, voice calls

Gateway-based connectors: OAuth handled automatically, 1,000 req/min/connector/project limit

### 2. Personal Connectors (MCP Servers, for build-time context)
- **Amplitude** — product analytics
- **Atlassian (Jira, Confluence)** — tickets, roadmaps, docs
- **Granola** — meeting notes
- **Linear** — issues and specs
- **Miro** — boards and diagrams
- **Notion** — docs and pages
- **n8n** — automation workflows
- **Polar** — billing/subscription data
- **Sanity** — CMS content
- **Custom MCP servers** — any internal/third-party system

### 3. Any API Integration
- Public or private, authenticated or not
- No-auth APIs: direct integration, zero setup
- Authenticated APIs: auto-creates Edge Function via Lovable Cloud
- Supports OpenAPI specs and documentation links

## Key Technical Details
- Shared connectors are workspace-level, configured once
- Personal connectors are per-user, not shared
- Business/Enterprise admins can enable/disable connectors
- Lovable Cloud cannot be disabled
- API integration automatically detects auth requirements

## Notable for ArkhosAI
- MCP support is comprehensive — both as shared and personal connectors
- Gateway model handles OAuth + token refresh automatically
- Any-API integration is a strong selling point
- GitLab support in addition to GitHub — EU-friendly
- No mention of Mistral in any integrations

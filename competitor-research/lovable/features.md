# Lovable — Features Analysis
> Sources: docs.lovable.dev/features/plan-mode, docs.lovable.dev/introduction/welcome (scraped 2026-03-30)

## Two-Mode Architecture

### Plan Mode (formerly Chat Mode)
- Planning and reasoning mode — no code changes
- Explores ideas, investigates issues, reasons about changes
- Asks clarifying questions
- Creates formal implementation plans when ready
- Plans include: high-level overview, decisions/assumptions, components/data models/APIs, step-by-step sequencing, optional diagrams
- Plans are editable as markdown before approval
- Cost: **1 credit per message**
- Plans saved to `.lovable/plan.md`
- Previous plans accessible from chat history
- Supports `@file` references and cross-project referencing

### Agent Mode
- Execution mode — implements changes and verifies outcomes
- Triggered when user approves a plan
- Implements based strictly on approved plan
- Can switch back to Plan mode at any time

## What You Can Build
- SaaS and business applications
- Consumer-facing web applications
- Marketplaces and online commerce
- Internal tools
- Websites and marketing pages
- Educational tools
- Games and interactive content

## Who It's For
- Individual builders (founders, students, makers)
- Product/design/go-to-market teams
- Technical teams and agencies
- Enterprises

## Key Features
- Natural language to working app
- Full-stack: frontend + backend + database + auth + integrations
- Shared workspaces for collaboration
- Code ownership (sync to GitHub)
- Real-time generation with streaming preview
- Template library
- Cross-project referencing within workspace
- File reference in chat (`@src/components/...`)

## Code Editor
- Built-in code editor (Code mode)
- Can reference files directly in chat
- Full code visibility and editability

## Collaboration (Lovable 2.0)
- "Multiplayer vibe coding"
- Shared workspaces
- Real-time collaboration
- User roles and permissions
- Publishing controls (edit/approve/publish separation)

## Deployment
- One-click deploy to lovable.app domains
- Custom domains (Pro+)
- Lovable Cloud for backend services

## Security Features
- Built-in security checks and guidance
- Automatic security scanning
- AI penetration testing (audit-ready reports)
- 4 automated scanners: RLS policies, database schema, application code, dependencies

## Limitations
- Credit-based — heavy users burn through credits quickly
- No explicit mobile app support mentioned (web apps only)
- No mention of self-hosting option

# UX Patterns — Competitor Comparison
> Compiled: 2026-03-30

---

## 1. First-Time User Experience (Landing → First Generation)

### Lovable
- Land → "Get started" → Sign up (no credit card) → Describe app OR pick template → Watch real-time generation
- **Clicks to first output:** ~3
- **While waiting:** Real-time streaming shows code being written and preview updating
- **Result:** Working app with live preview, editable via chat

### Bolt.new
- Land → "Build now" or "Plan" → Sign up → Describe app OR import from Figma/GitHub → Generation
- **Clicks to first output:** ~3
- **While waiting:** Code generation visible in editor, preview panel updates
- **Result:** Full project in WebContainers with live preview and code editor

### v0
- Land → Type in chat box → Sign up → Generation
- **Clicks to first output:** ~2-3 (chat box is right on homepage)
- **While waiting:** Streaming response with code blocks and preview
- **Result:** React/Next.js component or app with live preview

### ArkhosAI Should
- Match the ~3 click threshold
- Show pipeline progress (which agent is working, which model, estimated cost)
- Real-time streaming is non-negotiable

---

## 2. Generation Flow

### Lovable
- **Input:** Natural language description, screenshots, docs, @file references
- **Planning step:** Plan Mode available (optional, 1 credit per message)
- **Streaming:** Real-time preview as AI builds
- **Duration:** Not specified, real-time streaming masks wait

### Bolt.new
- **Input:** Natural language, Figma import, GitHub import
- **Planning step:** Plan Mode (Claude Agent) or Discussion Mode (v1 Agent)
- **Streaming:** Code generation visible in editor + preview
- **Duration:** Varies by complexity, Claude Agent is slower but better

### v0
- **Input:** Natural language, file attachments, suggested prompts
- **Planning step:** "Agentic by default" — v0 auto-plans
- **Streaming:** Code + preview streaming
- **Duration:** Varies by model (Mini=fast, Max=slower, Max Fast=fast+expensive)

---

## 3. Iteration Flow

### Lovable
- Chat with follow-up requests in Agent Mode
- Can reference specific files with `@`
- Can switch to Plan Mode to think about changes first
- Credits consumed per message (1 for Plan, more for Agent)

### Bolt.new
- Chat in same project, continue building
- Switch models mid-project (Claude model switch keeps history)
- Switch agents (clears history but keeps project files)
- Tokens consumed per message (varies by project size)

### v0
- Chat continuation in same thread
- Can switch between v0 Mini/Pro/Max/Max Fast per message
- Design Mode for visual fine-tuning
- Credits consumed based on input/output tokens

---

## 4. Export/Deploy Flow

### Lovable
- **Export:** Sync to GitHub (+ GitLab)
- **Deploy:** One-click to lovable.app → custom domain on Pro+
- **Clicks to deploy:** 1
- **Hosting:** Lovable Cloud (included)

### Bolt.new
- **Export:** Sync to GitHub
- **Deploy:** Share/Publish buttons → bolt.host domain → custom domain on paid
- **Clicks to deploy:** 1-2
- **Hosting:** Bolt Cloud (Netlify-powered)

### v0
- **Export:** Sync to GitHub
- **Deploy:** One-click to Vercel
- **Clicks to deploy:** 1
- **Hosting:** Vercel (additional cost on Pro+)

---

## 5. Error Recovery

### Lovable
- Agent Mode auto-detects and fixes errors
- 4 automated security scanners (RLS, schema, code, dependencies)
- AI penetration testing available
- Can switch to Plan Mode to debug before fixing

### Bolt.new
- Claims "98% less errors" with Claude Agent
- Auto tests, refactors, iterates
- Rollback/backup system for reverting changes
- Plan Mode for debugging discussions

### v0
- "Agentic by default" includes error handling
- Iterative fixes via chat
- No specific error recovery features documented
- Vercel deployment error logs available

---

## Key UX Insights for ArkhosAI

1. **Plan → Build → Deploy** is the universal flow — we must support it
2. **Real-time streaming** is table stakes — every competitor has it
3. **~3 clicks to first output** is the benchmark
4. **Model/cost visibility during generation** is our unique UX opportunity
5. **Visual editing** (v0's Design Mode) is the next frontier — plan for v0.2
6. **File references** (@filename) in chat is essential DX
7. **Rollback/version history** is important safety net
8. **Multi-entry points:** prompt, template, import (Figma/GitHub/competitor)

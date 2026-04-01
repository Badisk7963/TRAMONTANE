# Bolt.new — Prompting Guide & Best Practices
> Source: support.bolt.new/best-practices/discussion-mode (scraped 2026-03-30)

## Plan Mode (Claude Agent)
- Available from homepage or within project
- Creates structured plans through back-and-forth discussion
- Executes plans step-by-step after approval
- Starts by creating base app structure, then shares plan in chatbox
- Can review, suggest changes, continue building iteratively

### Use Cases
- Debugging assistance
- Tool/library/API recommendations
- Product/project decision-making
- Design improvement suggestions
- Feature suggestions
- API integration understanding
- Implementation plan generation
- Inspector tool for highlighting components

### Features
- Project context awareness (codebase included in every message)
- Web research capability (real-time, up-to-date info from web)
- Quick action buttons (Implement this plan, Show example, Refine idea)
- Sources displayed when web search conducted

## Discussion Mode (v1 Agent, legacy)
- Powered by Google Gemini
- Versatile for wide range of topics
- Being retired along with v1 Agent

## Token Efficiency Tips (from docs)
- Use Plan/Discussion mode to think before building
- Saves tokens by avoiding unnecessary code generation
- "Ensure you get things right before moving into Build Mode"

## Key Observations for ArkhosAI
- Plan mode from homepage = users start with planning, not coding
- Web research during planning is valuable — reduces hallucination
- Inspector tool for visual selection is great UX
- Quick action buttons reduce friction between planning and execution

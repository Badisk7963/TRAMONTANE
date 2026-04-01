# Bolt.new — MCP Support Analysis
> Source: support.bolt.new/building/using-bolt/connect-mcp (scraped 2026-03-30)

## Overview
MCP (Model Context Protocol) servers let Bolt access real-world data from external apps during building.

## Authentication Methods
- **API key** — from app's developer settings
- **MCP OAuth** — sign-in flow (like OAuth social login)
- **None** — for public sites

## Built-in Connectors
- Notion
- Linear
- GitHub
- Others (not fully enumerated)

## Custom MCP Setup
Required: Name, URL, Transport type (HTTP or SSE), Authentication method

## Features
- Per-project enable/disable
- Auto-enable for all projects option
- Tool-level management (enable/disable specific actions)
- Auto-discovery of new tools when provider updates server
- Connection refresh capability
- Edit/delete connectors

## Best Practices (from Bolt docs)
- Turn off connectors for irrelevant projects
- Disable unused tools
- Toggle connectors on/off as needed during build
- Multiple active connectors = more context = more tokens = slower

## Key Observations for ArkhosAI
- MCP support is solid but user-facing only
- No server-side MCP integration for deployed apps (unlike Lovable's shared connectors)
- Token impact of MCP context is a real concern
- Bolt is honest about performance tradeoffs
- Custom MCP requires knowing server URL — not discoverable

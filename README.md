# TokenRelay: The Intelligent Orchestrator That Routes IDE Tasks to the Best, Cheapest Models

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-orange.svg)](#)
[![Support via Square](https://img.shields.io/badge/Donate-Square%20Pay-10b981.svg)](https://square.link/u/donate-tokenrelay)

> **TokenRelay** autonomously manages your AI coding workflow. By evaluating prompt complexity, it seamlessly transfers tasks between models like Claude, GPT, and DeepSeek, slashing your token spend without sacrificing code quality.

---

## ⚡ Why TokenRelay? The Missing Desktop Link

While backend proxies like **LiteLLM** (62,000+ stars, 90M+ monthly downloads) focus on cloud server infrastructure and terminal tools like **Aider** (28,000+ stars) require separate CLI workflows, **TokenRelay** operates **invisibly on your desktop**. You type naturally inside **Claude Desktop**, **Cursor**, **VS Code**, or **Windsurf**, and TokenRelay intercepts, compresses, and routes your prompts in real time before expensive cloud bills occur.

### Reverse-Engineered Superpowers Synthesized via REA:
* **From LiteLLM:** Fault-tolerant multi-tier fallback cascades, automatic 429 quota exhaustion recovery, provider cooldown timers, and daily spend caps.
* **From Aider:** AST code signature extraction (reducing prompt footprint by up to 80%) and bit-identical prefix pinning for 90% prompt caching.
* **TokenRelay Moat:** Zero-touch desktop interception, active IDE detection, real-time desktop warnings, one-click prompt copying, and hardware-aware local model offloading.

---

## 🚀 Quickstart

TokenRelay requires **zero external pip dependencies** — standard Python 3.8+ library only.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/tokenrelay.git
cd tokenrelay

# 2. Launch the interactive Control Center & Proxy Daemon
python agent.py dashboard
```
*(On Windows, simply run `run.bat` to launch the interactive dashboard and local proxy).*

### Register with Claude Desktop (Zero Configuration)
TokenRelay automatically registers with Claude Desktop via the Model Context Protocol (MCP):
```bash
python agent.py mcp
```
*(Automatically configured at `%APPDATA%\Claude\claude_desktop_config.json`)*.

---

## 💰 Pricing & Monetization Model

TokenRelay adopts a sustainable developer-first monetization model inspired by Portkey and OpenRouter:

| Plan | Price | Features Included |
|---|---|---|
| **Community Edition** | **Free Forever (MIT)** | Local desktop proxy, CLI, Aider AST compression, LiteLLM fallback cascades, local Ollama routing, local receipts ledger. |
| **Cloud MCP Hub** | **$2.00 / month** | Managed zero-config hosted MCP gateway, cross-machine rule sync, shared team cache pools, Slack/Discord cost anomaly alerts. |
| **Token Micropayment Pool** | **2% margin per turn** | Unified API wallet. Deposit $5 or $10 once; TokenRelay routes to DeepSeek, Groq, and Anthropic with zero individual account management. |
| **Creator Sponsorship** | **Voluntary Donation** | Developers who save hundreds of dollars each month can support continued open-source development directly via [Square Pay](https://square.link/u/donate-tokenrelay). |

---

## 🏗️ Tri-Layer Synchronized Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TOKENRELAY TRI-LAYER SYNC ENGINE                     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   LiteLLM Core   │      │    Aider Core    │      │  TokenRelay UI   │
│  (Resilience)    │      │  (Compression)   │      │   (Telemetry)    │
├──────────────────┤      ├──────────────────┤      ├──────────────────┤
│• 429 Cooldowns   │      │• AST Signatures  │      │• Claude Active   │
│• Fallback Chains │      │• Prefix Pinning  │      │• Live Intercept  │
│• Quota Recovery  │      │• Diff Directives │      │• Verified Ledger │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

### 1. Resilient Routing & Fallback Cascade (`tokenopt/router.py`)
When you hit a usage limit or credit depletion on Claude Desktop (`claude-fable-5-1` or `opus`), TokenRelay catches the error and instantly cascades through high-parity alternatives without aborting your work:
1. **Primary Target:** `claude-fable-5-1` ($10.00 in / $50.00 out)
2. **First Parity Fallback:** `deepseek-r1` ($0.55/1M — **98.2% savings**)
3. **Second Parity Fallback:** `gemini-2.0-flash` ($0.00 Free Tier / $0.10/1M)
4. **Local Hardware Fallback:** `qwen-2.5-coder:7b` ($0.00 local Ollama)

### 2. AST Code Context Compressor (`AiderContextOptimizer`)
* Strips redundant internal implementation blocks from reference code, retaining only function signatures, class interfaces, type annotations, and docstrings.
* Enforces strict **Search/Replace diff directives**, slashing output token generation from 1,500 tokens down to 150 tokens per edit.

### 3. Desktop IDE Hooking & Telemetry
* Intercepts incoming requests on `http://localhost:8088` (OpenAI & Anthropic wire protocols).
* Monitors active session logs across `~/.claude/projects/` and `~/.cursor/`.
* Telemetry feeds dynamically into the **Control Center Dashboard** (`http://localhost:8085`).

---

## 🖥️ Live Control Center Dashboard

Access the interactive dashboard at **`http://localhost:8085`**:
* **Command Center:** Live IDE Window showing captured prompts from Claude Desktop and real-time parity savings.
* **Prompt Optimizer:** Smart technical enrichment, diff directives, and **One-Click Copy** to clipboard.
* **Model Router:** Side-by-side pricing matrix across 10+ providers with customizable fallback policies.
* **Savings & ROI:** Verified receipts ledger and instant CSV export.
* **Integrations:** Automatic detection of Cursor, Claude Desktop, and CLI agents with one-click cross-IDE sync.
* **Settings & Vault:** Secure local storage of `DEEPSEEK_API_KEY` and `GEMINI_API_KEY` with Square donation support.

---

## 🧪 Testing & Verification

Run the full automated test suite:
```bash
python -m unittest discover -s tests
```
* 14/14 unit tests pass cleanly covering routing cascades, cooldown triggers, AST compression, prefix stabilization, prompt optimization, and receipts.

---

## ☕ Support & Donations

If TokenRelay cuts your monthly AI bills, consider supporting ongoing open-source engineering:
* **Donate via Square:** [https://square.link/u/donate-tokenrelay](https://square.link/u/donate-tokenrelay) *(Supports Square Pay, Apple Pay, Google Pay, and Cash App)*.

---

## 📜 License

MIT License. Engineered for developers who want frontier AI capabilities without runaway token invoices.

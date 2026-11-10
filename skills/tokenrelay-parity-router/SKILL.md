---
name: tokenrelay-parity-router
description: Dynamically routes expensive flagship queries (Claude Opus $15/1M, Fable $50/1M, GPT-4) to 96% cheaper parity alternatives (DeepSeek R1/V3, Gemini Flash, local Ollama) based on task complexity.
version: 1.0.0
tools: [claude, cursor, codex, antigravity, cline]
---

# TokenRelay Equi-Capability Parity Router

Use this skill to determine the most cost-effective execution model for a given coding or reasoning task.

## Parity Mapping Rules

| Requested Model | Target Alternative | Price Delta | Quality Parity |
|---|---|---|---|
| **Claude Fable 5.1** ($10 in / $50 out) | **DeepSeek R1 / V3** ($0.27 in / $0.55 out) | **98.2% Savings** | Equivalent on reasoning & Python/JS tasks |
| **Claude 3.5 Opus** ($15 in / $75 out) | **DeepSeek R1** ($0.55 / 1M) | **96.3% Savings** | Equivalent or superior on math, logic & code |
| **GPT-4o** ($2.50 in / $10.00 out) | **Gemini 2.0 Flash** ($0.10 / 1M / Free Tier) | **96.0% Savings** | Equal coding accuracy; ultra-low latency |
| **Flagship Offline** | **Qwen 2.5 Coder 7B / 14B** ($0.00 via Ollama) | **100% Free** | High local coding completion for laptops & desktops |

## LiteLLM-Inspired Fallback Cascade

When executing requests through TokenRelay, follow this resilience chain:
1. Try Primary Target (if within daily budget).
2. If **429 Rate Limit**, **Usage Cap**, or **Error** occurs:
   - Shift to **DeepSeek R1** ($0.55/1M).
   - If offline or unauthenticated: Shift to **Local Ollama** (port 11434).
   - Record provider failure and activate a 60-second cooldown window.

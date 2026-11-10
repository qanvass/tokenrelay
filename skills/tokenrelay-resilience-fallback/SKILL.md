---
name: tokenrelay-resilience-fallback
description: LiteLLM-grade fault-tolerance engine that handles provider cooldowns, 429 quota exhaustion recovery, and automatic cascade to local Ollama.
version: 1.0.0
tools: [claude, cursor, codex, antigravity, cline]
---

# TokenRelay Resilience & Fallback Engine

Use this skill when an upstream provider fails, throws a 429 rate limit, or runs out of credits.

## Cascade Chain Rules

1. **Failure Interception:**
   - Detect 429 (Too Many Requests), 402 (Payment Required), or quota limit error strings in API responses.
   - Immediately activate a **60-second cooldown timer** for that provider.

2. **Automated Parity Cascade:**
   - Seamlessly transfer the active session to the next healthy model in the chain without interrupting the developer:
     ```
     claude-fable-5-1 / opus  ➔  deepseek-r1  ➔  gemini-2.0-flash  ➔  local-ollama
     ```

3. **Offline Zero-Dependency Fallback:**
   - If network drops or cloud keys expire, probe `http://localhost:11434` (Ollama).
   - Route to `qwen-2.5-coder:7b` or `deepseek-r1:7b` for 100% free, private execution.

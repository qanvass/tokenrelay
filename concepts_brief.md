# Concept Brief: TokenOptimizer (Universal LLM & AI IDE Cost Savings Agent)

## 1. Problem Statement
Software developers and engineering teams face escalating, opaque cloud bills from modern AI coding tools and LLM APIs. Token waste occurs primarily across three vectors:
1. **IDE Context Leaks & Cache Invalidation**: AI IDEs (Cursor, Windsurf, Copilot, Cline, Claude Code, Continue, Aider, JetBrains, Void, Antigravity) repeatedly re-transmit volatile tokens (timestamps, git hashes, dynamic directory dumps) in system rules and headers, busting 50%–90% prompt caching discounts across frontier providers.
2. **Suboptimal Model & Timing Selection**: Running heavy reasoning models (Claude 3.7 Sonnet, OpenAI o1/o3-mini, DeepSeek R1) for routine edits, unit tests, or autocomplete instead of tiered routing (e.g. local Ollama/Qwen 2.5 Coder for autocompletion; Flash/Haiku for editing; reasoning models strictly for architectural planning). Furthermore, developers miss explicit off-peak discount windows (such as DeepSeek's 50% discount between 00:30–08:30 UTC) and fail to utilize 50% discounted Batch APIs for non-interactive workloads.
3. **Verbose Prompt & Output Bloat**: Uncompressed context, redundant conversational framing, and whole-file rewrites (instead of unified diff / search-and-replace blocks) inflate output tokens, which cost 3x to 5x more than input tokens.

## 2. Goals
- Deliver an open-source, production-grade agent accessible via **CLI**, **MCP Server (Model Context Protocol)**, and a **Zero-Latency Local Interceptor Proxy** (`localhost:8080/v1`).
- Support the **Top 10 LLM Providers**: OpenAI, Anthropic, Google DeepMind, DeepSeek, Mistral AI, Meta Llama/Open Weights (Ollama/Groq/vLLM), xAI Grok, Cohere, Amazon Bedrock, and Microsoft Azure OpenAI.
- Support the **Top 10 AI IDEs & Environments**: Cursor, Windsurf, GitHub Copilot, Cline/Roo Code, Claude Code, Continue.dev, Aider, JetBrains AI, Void, and Antigravity.
- **Cross-IDE Context & Rules Synchronization Engine**: Single source of truth (integrating patterns from `rulesync`, `ai-rulez`, and `ByteRover`) that auto-compiles clean, cache-optimized rules to `.cursor/rules`, `.windsurfrules`, `CLAUDE.md`, `.clinerules`, `.copilotignore`, and `continue/config.json`.
- **Equi-Capability Dynamic Model Routing (Parity Engine)**: When a chosen flagship (e.g., GPT-6 Astra, Claude 3.7 Sonnet) runs low on credits or hits peak rates, dynamically recommend or route to an equivalent-tier model (e.g. DeepSeek R1 for reasoning, Codestral/DeepSeek V3 for implementation, or local Qwen 2.5 Coder for autocompletion) preserving performance parity while saving up to 90%.
- **Pre-Send Prompt Optimization & Interception**: Allow developers to sanitize prompts before they leave the machine—either via MCP tool (`optimize_prompt`) or by pointing IDE endpoints to the local proxy, which strips conversational fluff, enforces diff-only outputs, and freezes static prefixes.
- **Automated Time-of-Day / Off-Peak Detection**: Warn users before dispatching heavy jobs during peak windows (e.g. DeepSeek's 50% discount between 00:30–08:30 UTC), offering one-click conversion to Batch API or off-peak scheduling.
- **Digital Receipts & Live ROI Telemetry**: Output verifiable itemized receipts showing baseline cost, cache savings, off-peak savings, net billed, and total developer ROI per session and per project.
- **Free-Tier Stacking Gateway**: Pools free developer tiers (Google AI Studio 1,500 req/day, Groq, Cohere, local Ollama) behind a dual OpenAI/Anthropic wire translator, enabling tools like Claude Code and Cursor to operate 100% free ($0.00) with automatic failover on rate limits.
- **IDE Rule & Config Auditor**: Scan and fix rules files to eliminate per-turn token waste.

## 3. Non-Goals
- Building a proprietary closed-source cloud proxy that intercepts developer API keys in third-party infrastructure.
- Re-implementing full code-editing UI from scratch.
- Downgrading to inferior models on critical reasoning paths without developer confirmation.

## 4. System Architecture & Boundaries

```
[ Developer / AI IDE (Cursor, Windsurf, Claude Code, Cline, Aider) ]
       │
       ├──► Mode A: MCP Server (`tokenopt-mcp`)
       │       ├── tool: optimize_prompt_roi (pre-send compression & diff constraint)
       │       ├── tool: check_offpeak_windows (DeepSeek & provider timing alerts)
       │       ├── tool: route_model_by_parity (equi-capability cheaper fallback)
       │       ├── tool: sync_ide_rules (cross-IDE single source of truth)
       │       ├── tool: audit_ide_configuration (.cursorrules, CLAUDE.md, etc.)
       │       ├── tool: generate_savings_receipt (itemized ROI breakdown)
       │       └── tool: batchify_payload (50% Batch API converter)
       │
       ├──► Mode B: Local Proxy Interceptor (`localhost:8088/v1`)
       │       ├── Transparent pass-through for any OpenAI/Anthropic-compatible IDE
       │       ├── Dynamic fallback routing on budget thresholds or peak hours
       │       ├── Pre-send prompt optimizer & prefix stabilizer
       │       ├── Peak-window warning injection in system header
       │       └── Live token counting & receipt persistence (SQLite / JSON)
       │
       ├──► Mode C: Cross-IDE Sync Daemon (`tokenopt sync`)
       │       ├── Reads `.tokenopt/rules.md` (clean single source of truth)
       │       ├── Compiles out to Cursor, Windsurf, Copilot, Claude Code, Cline
       │       └── Removes cache-busters across all configs automatically
       │
       └──► Mode D: Standalone CLI (`tokenopt`)
               ├── `tokenopt audit <file>`
               ├── `tokenopt optimize "<prompt>"`
               ├── `tokenopt offpeak`
               ├── `tokenopt route --target astra --budget tight`
               ├── `tokenopt sync`
               ├── `tokenopt compare --in 500k --out 50k`
               └── `tokenopt receipts --summary`
```

## 5. Concrete Data & Pricing Schema

The centralized pricing specification (`references/pricing_matrix.json`) defines per-model costs per 1M tokens (USD), caching discounts, batch discounts, and time-of-day off-peak rules:

```json
{
  "version": "2.0.0",
  "providers": {
    "deepseek": {
      "name": "DeepSeek",
      "off_peak_window_utc": {
        "start": "00:30",
        "end": "08:30",
        "discount_pct": 50
      },
      "models": {
        "deepseek-v3": {
          "input_standard": 0.27,
          "input_cached": 0.07,
          "output": 1.10,
          "batch_discount_pct": 50,
          "supports_prompt_caching": true
        },
        "deepseek-r1": {
          "input_standard": 0.55,
          "input_cached": 0.14,
          "output": 2.19,
          "batch_discount_pct": 50,
          "supports_prompt_caching": true
        }
      }
    }
  }
}
```

### 5.1 Itemized Digital Receipt Specification
Whenever an API call or task completes, the engine calculates the ROI receipt:
```text
======================= TOKEN SAVINGS RECEIPT =======================
Timestamp:      2026-11-09 11:30:00 UTC
Provider/Model: DeepSeek V3 (Coding Task)
Total Tokens:   45,200 In / 1,400 Out
---------------------------------------------------------------------
Standard Baseline Cost:                      $0.0137
- Prompt Prefix Cache Hit (82% cached):     -$0.0074  (60% cache cut)
- Off-Peak Window Discount (00:30-08:30 UTC):-$0.0031  (50% timing cut)
---------------------------------------------------------------------
Net Billed Cost:                             $0.0032
YOUR SAVINGS ON THIS RUN:                    $0.0105  (76.6% ROI)
Cumulative Session Savings:                  $14.28 across 84 runs
=====================================================================
```

## 6. Failure Modes & Mitigations
1. **Stale Pricing Data**: Pricing schedules change frequently across cloud providers.
   - *Mitigation*: Fallback to bundled local matrix with an optional `--update-pricing` flag that pulls verified public pricing feeds, plus explicit version stamping.
2. **Over-Aggressive Prompt Compression**: Stripping critical variable names or API signatures causes hallucinated code.
   - *Mitigation*: Strict semantic preservation rules: never remove identifiers, types, or syntax structures; only strip redundant conversational fluff, Markdown embellishments, and duplicate instructions.
3. **Cache Invalidation through Dynamic Rules**: An IDE updating timestamps or volatile metadata in rules files ruins provider prefix cache.
   - *Mitigation*: Audit engine flags volatile regex matches (ISO dates, timestamps, git commits, UUIDs) and generates frozen static rule equivalents.
4. **Timezone Miscalculations**: Developer local time vs server UTC misaligned.
   - *Mitigation*: Use standard ISO 8601 with explicit UTC normalization for all off-peak calculations.

## 7. Open Questions for Alignment
1. **Packaging & Distribution**: Should the agent be published as a standalone pip package (`pip install tokenopt`), a standalone zero-dependency Python script, a Node/TypeScript CLI, or dual-distributed (Python stdlib CLI + FastMCP / stdio MCP server)?

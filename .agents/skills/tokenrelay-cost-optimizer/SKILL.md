---
name: tokenrelay-cost-optimizer
description: Slashes LLM input and output token spend by 80% through cache-buster sanitization, conversational bloat removal, and strict diff-only search/replace directives.
version: 1.0.0
tools: [claude, cursor, codex, antigravity, cline]
---

# TokenRelay Prompt ROI Optimizer

Use this skill whenever an agent is preparing prompts, modifying code, or dispatching queries to frontier LLMs. It eliminates runaway token invoices without compromising code quality.

## Core Optimization Rules

1. **Cache-Buster Neutralization:**
   - Remove volatile ISO timestamps, HTTP date headers, dynamic session UUIDs, and raw commit hashes from system prompts.
   - Replace them with static token anchors (`<STATIC_REF>`).
   - Ensures prompt prefix caching hits the **90% discount window** on Anthropic, OpenAI, and DeepSeek.

2. **Conversational Bloat Stripping:**
   - Strip polite fillers (*"Could you please make sure to"*, *"As an expert senior engineer"*, *"Thanks in advance"*).
   - Preserve 100% of technical specifications, file paths, function names, and constraints.

3. **Strict Diff-Only Output Constraint:**
   - Always append the TokenRelay output directive to coding requests:
     ```
     [TOKEN_ROI_DIRECTIVE]: Output edits strictly as targeted SEARCH/REPLACE blocks or unified diffs.
     Do NOT output the full file or repeat unchanged code. Omit conversational pleasantries.
     ```
   - Slashes average response size from 1,200 tokens to ~150 tokens (**87.5% output token savings**).

## Example Transformation

**Original (Bloated):**
> "Could you please help me refactor my blender python script for the car build so that it exports without camera jitter? Thanks in advance!"

**Optimized (TokenRelay):**
> "Task: Refactor Blender Python bpy script to export vehicle mesh without camera jitter.
> [TOKEN_ROI_DIRECTIVE]: Output edits strictly as targeted SEARCH/REPLACE blocks or unified diffs. Do NOT output the full file or repeat unchanged code."

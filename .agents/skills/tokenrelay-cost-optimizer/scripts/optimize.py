#!/usr/bin/env python3
"""
TokenRelay Cost Optimizer CLI
Strips cache-busting volatile tokens, eliminates conversational bloat,
and appends strict diff-only search/replace directives.
"""

import sys
import re
import argparse

CONVERSATIONAL_BLOAT_PATTERNS = [
    r"(?i)^(hello|hi|hey|greetings|dear agent|good morning|good afternoon)[,.]?\s*",
    r"(?i)could you (please )?(help me )?(to )?",
    r"(?i)as (an expert|a senior|a world-class|a professional) (software )?engineer[,.]?\s*",
    r"(?i)thanks( in advance| so much)?(,? have a great day)?[.!]?",
    r"(?i)please make sure (that )?",
    r"(?i)i would really appreciate it if you could",
    r"(?i)don't forget to",
]

CACHE_BUSTER_PATTERNS = [
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})", "<TIMESTAMP_STABLE>"),
    (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID_STABLE>"),
    (r"\b[0-9a-f]{40}\b", "<COMMIT_HASH_STABLE>"),
]

DIFF_DIRECTIVE = """
[TOKEN_ROI_DIRECTIVE]: Output edits strictly as targeted SEARCH/REPLACE blocks or unified diffs.
Do NOT output the full file or repeat unchanged code. Omit conversational pleasantries."""

def optimize_prompt(text: str, append_directive: bool = True) -> dict:
    original_len = len(text)
    original_tokens = max(1, original_len // 4)
    
    cleaned = text
    # Clean bloat
    for pat in CONVERSATIONAL_BLOAT_PATTERNS:
        cleaned = re.sub(pat, "", cleaned)
    
    # Clean cache busters
    for pat, repl in CACHE_BUSTER_PATTERNS:
        cleaned = re.sub(pat, repl, cleaned)
        
    cleaned = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned).strip()
    
    if append_directive and "[TOKEN_ROI_DIRECTIVE]" not in cleaned:
        cleaned += "\n" + DIFF_DIRECTIVE.strip()
        
    optimized_len = len(cleaned)
    optimized_tokens = max(1, optimized_len // 4)
    
    # Output savings calculation (typical diff saves ~85% output tokens)
    estimated_output_savings_pct = 85.0
    
    return {
        "original_text": text,
        "optimized_text": cleaned,
        "input_tokens_est": original_tokens,
        "optimized_input_tokens_est": optimized_tokens,
        "input_token_reduction_pct": round(max(0.0, (1 - optimized_tokens / original_tokens) * 100), 1),
        "expected_output_savings_pct": estimated_output_savings_pct,
    }

def main():
    parser = argparse.ArgumentParser(description="TokenRelay Cost Optimizer")
    parser.add_argument("input", nargs="?", default="", help="Prompt text or file path to optimize")
    parser.add_argument("--file", "-f", help="Read input from file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-directive", action="store_true", help="Do not append diff directive")
    args = parser.parse_args()

    content = ""
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.input:
        content = args.input
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print("Usage: python optimize.py 'Could you please refactor my code...'")
        return

    result = optimize_prompt(content, append_directive=not args.no_directive)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print("=== TokenRelay Optimized Prompt ===")
        print(result["optimized_text"])
        print("-----------------------------------")
        print(f"Est. Input Tokens: {result['input_tokens_est']} -> {result['optimized_input_tokens_est']}")
        print(f"Est. Output Reduction: ~{result['expected_output_savings_pct']}% via diff constraint")

if __name__ == "__main__":
    main()

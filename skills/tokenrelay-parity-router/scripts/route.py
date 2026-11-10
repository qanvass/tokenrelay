#!/usr/bin/env python3
"""
TokenRelay Parity Router CLI
Classifies task complexity and routes expensive frontier queries to
96% cheaper parity models (DeepSeek R1/V3, Qwen 2.5 Coder, Gemini Flash, Ollama).
"""

import sys
import re
import argparse
import json

RATES = {
    "claude-3-7-sonnet": {"in": 3.00, "out": 15.00, "name": "Claude 3.7 Sonnet"},
    "claude-opus-3":     {"in": 15.00, "out": 75.00, "name": "Claude 3 Opus"},
    "gpt-4o":            {"in": 2.50, "out": 10.00, "name": "OpenAI GPT-4o"},
    "deepseek-v3":       {"in": 0.14, "out": 0.28, "name": "DeepSeek V3 / Coder"},
    "deepseek-r1":       {"in": 0.55, "out": 2.19, "name": "DeepSeek R1 Reasoning"},
    "gemini-1-5-flash":  {"in": 0.075, "out": 0.30, "name": "Gemini 1.5 Flash"},
    "ollama-local":      {"in": 0.00, "out": 0.00, "name": "Ollama Local (Offline $0)"},
}

COMPLEXITY_TRIGGERS = {
    "high": [
        "architecture", "formal verification", "cryptographic", "kernel", "distributed consensus",
        "race condition", "memory corruption", "complex refactor", "security audit"
    ],
    "medium": [
        "refactor", "unit test", "write function", "add api", "endpoint", "database migration",
        "crud", "react component", "sql query", "regex", "dockerfile"
    ],
    "low": [
        "explain", "comment", "format", "typo", "docstring", "lint", "markdown",
        "translate", "summarize", "commit message", "variable name"
    ]
}

def analyze_and_route(prompt: str) -> dict:
    prompt_lower = prompt.lower()
    
    score = 0
    reasons = []
    
    for word in COMPLEXITY_TRIGGERS["high"]:
        if word in prompt_lower:
            score += 3
            reasons.append(f"High-complexity keyword '{word}'")
            
    for word in COMPLEXITY_TRIGGERS["medium"]:
        if word in prompt_lower:
            score += 1
            reasons.append(f"Medium-complexity keyword '{word}'")
            
    for word in COMPLEXITY_TRIGGERS["low"]:
        if word in prompt_lower:
            score -= 1
            reasons.append(f"Low-complexity keyword '{word}'")

    token_count = max(1, len(prompt) // 4)
    
    if score >= 4:
        routed_model = "claude-3-7-sonnet"
        tier = "Flagship Tier (Heavy Architecture / Complex Logic)"
    elif score >= 1:
        routed_model = "deepseek-v3"
        tier = "Parity Coder Tier (Code Generation & Refactoring)"
    elif score <= -1 and token_count < 300:
        routed_model = "gemini-1-5-flash"
        tier = "Fast Explainer Tier (Docs, Explain, Formatting)"
    else:
        routed_model = "deepseek-v3"
        tier = "Balanced Parity Tier"
        
    baseline_cost_1m = RATES["claude-opus-3"]["out"]
    routed_cost_1m = RATES[routed_model]["out"]
    savings_pct = round(((baseline_cost_1m - routed_cost_1m) / baseline_cost_1m) * 100, 1)

    return {
        "score": score,
        "tier": tier,
        "selected_model": routed_model,
        "model_name": RATES[routed_model]["name"],
        "rate_in_per_1m": RATES[routed_model]["in"],
        "rate_out_per_1m": RATES[routed_model]["out"],
        "baseline_comparison": "Claude 3 Opus ($75/1M out)",
        "cost_reduction_pct": savings_pct,
        "reasons": reasons[:4] if reasons else ["Standard coding flow"]
    }

def main():
    parser = argparse.ArgumentParser(description="TokenRelay Parity Router")
    parser.add_argument("prompt", nargs="?", default="", help="Prompt or task to route")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    content = args.prompt
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()
    if not content:
        content = "Write a unit test for the user authentication helper in pytest."

    res = analyze_and_route(content)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("=== TokenRelay Parity Route Decision ===")
        print(f"Decision:     {res['model_name']} ({res['selected_model']})")
        print(f"Tier:         {res['tier']}")
        print(f"Rate:         ${res['rate_in_per_1m']:.2f}/1M in | ${res['rate_out_per_1m']:.2f}/1M out")
        print(f"Cost Savings: {res['cost_reduction_pct']}% vs {res['baseline_comparison']}")
        print(f"Signals:      {', '.join(res['reasons'])}")

if __name__ == "__main__":
    main()

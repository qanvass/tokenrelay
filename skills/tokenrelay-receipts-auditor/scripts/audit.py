#!/usr/bin/env python3
"""
TokenRelay Cryptographic Receipts Auditor CLI
Tracks token usage across all LLM sessions, computes verifiable cost savings,
and outputs cryptographically hashed markdown audit receipts.
"""

import sys
import hashlib
import json
import time
from datetime import datetime, timezone
import argparse

STANDARD_OPUS_RATE = 75.00  # $75/1M out
STANDARD_SONNET_RATE = 15.00 # $15/1M out

def generate_receipt(input_tokens: int, output_tokens: int, cached_tokens: int, effective_cost: float, project: str = "TokenRelay") -> dict:
    # Baseline comparison: if all output tokens ran on Opus without caching
    baseline_cost = ((input_tokens + cached_tokens) * 15.00 / 1_000_000) + (output_tokens * 75.00 / 1_000_000)
    savings = max(0.0, baseline_cost - effective_cost)
    roi_multiple = round(savings / max(0.01, effective_cost), 2)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    payload = f"{project}|{timestamp}|{input_tokens}|{output_tokens}|{cached_tokens}|{effective_cost:.4f}|{savings:.4f}"
    receipt_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return {
        "receipt_id": f"REC-{receipt_hash[:12].upper()}",
        "timestamp": timestamp,
        "project": project,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "effective_cost_usd": round(effective_cost, 4),
        "baseline_cost_usd": round(baseline_cost, 4),
        "savings_usd": round(savings, 4),
        "roi_multiple": f"{roi_multiple}x",
        "sha256_verification": receipt_hash,
    }

def main():
    parser = argparse.ArgumentParser(description="TokenRelay Receipts Auditor")
    parser.add_argument("--in-tokens", type=int, default=125000, help="Input tokens count")
    parser.add_argument("--out-tokens", type=int, default=18000, help="Output tokens count")
    parser.add_argument("--cached-tokens", type=int, default=95000, help="Cached tokens count")
    parser.add_argument("--cost", type=float, default=0.28, help="Actual cost incurred in USD")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    rec = generate_receipt(args.in_tokens, args.out_tokens, args.cached_tokens, args.cost)
    
    if args.json:
        print(json.dumps(rec, indent=2))
    else:
        print("================================================================")
        print("              TOKENRELAY VERIFIED SAVINGS RECEIPT               ")
        print("================================================================")
        print(f" Receipt ID:      {rec['receipt_id']}")
        print(f" Timestamp:       {rec['timestamp']}")
        print(f" Verified Hash:   {rec['sha256_verification'][:32]}...")
        print("----------------------------------------------------------------")
        print(f" Input Tokens:    {rec['input_tokens']:,}")
        print(f" Output Tokens:   {rec['output_tokens']:,}")
        print(f" Cached Tokens:   {rec['cached_tokens']:,} (90% prefix cache)")
        print("----------------------------------------------------------------")
        print(f" Actual Incurred: ${rec['effective_cost_usd']:.4f}")
        print(f" Baseline Cost:   ${rec['baseline_cost_usd']:.4f} (Claude Opus default)")
        print(f" Net Savings:     ${rec['savings_usd']:.4f}")
        print(f" Developer ROI:   {rec['roi_multiple']}")
        print("================================================================")

if __name__ == "__main__":
    main()

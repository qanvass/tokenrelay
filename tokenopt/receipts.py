"""
Verifiable Digital Receipts and ROI Ledger Engine.
Records and outputs itemized token expenditures, prompt caching discounts,
off-peak timing savings, and cumulative developer return on investment.
"""

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, List, Optional


def get_receipts_store_path() -> str:
    """Path to the local receipts ledger."""
    base_dir = os.path.join(os.getcwd(), ".tokenopt")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "receipts.json")


def load_receipts_history() -> List[Dict[str, Any]]:
    """Load persistent receipts history."""
    path = get_receipts_store_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_receipt(receipt_record: Dict[str, Any]) -> None:
    """Append a new receipt to the persistent ledger."""
    path = get_receipts_store_path()
    history = load_receipts_history()
    history.append(receipt_record)
    # Keep last 500 receipts
    history = history[-500:]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


def format_receipt(
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    baseline_cost: float,
    actual_cost: float,
    cached_ratio: float = 0.8,
    is_offpeak: bool = False,
    task_description: str = "AI Coding Task",
) -> str:
    """
    Format a terminal-friendly itemized digital receipt.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    savings_usd = max(0.0, baseline_cost - actual_cost)
    savings_pct = (savings_usd / baseline_cost * 100.0) if baseline_cost > 0 else 0.0

    # Load cumulative history
    history = load_receipts_history()
    cum_savings = sum(r.get("savings_usd", 0.0) for r in history) + savings_usd
    total_runs = len(history) + 1

    lines = [
        "======================= TOKEN SAVINGS RECEIPT =======================",
        f"Timestamp:        {now_str}",
        f"Provider/Model:   {provider} / {model}",
        f"Task:             {task_description}",
        f"Tokens Processed: {input_tokens:,} In / {output_tokens:,} Out",
        "---------------------------------------------------------------------",
        f"Standard Baseline Cost:                      ${baseline_cost:>8.4f}",
        f"- Prefix Cache Hit ({int(cached_ratio*100)}% cached):           -${(baseline_cost * cached_ratio * 0.75):>8.4f}",
    ]
    if is_offpeak:
        lines.append(f"- Off-Peak Window Discount (50% cut):        -${(baseline_cost * 0.5 * 0.25):>8.4f}")

    lines.extend([
        "---------------------------------------------------------------------",
        f"Net Billed Cost:                             ${actual_cost:>8.4f}",
        f"YOUR NET SAVINGS THIS RUN:                   ${savings_usd:>8.4f}  ({savings_pct:>4.1f}% ROI)",
        f"Cumulative Session Savings:                  ${cum_savings:>8.2f} across {total_runs} runs",
        "=====================================================================",
    ])

    # Record to ledger
    record = {
        "timestamp": now_str,
        "provider": provider,
        "model": model,
        "task": task_description,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "baseline_cost": round(baseline_cost, 6),
        "actual_cost": round(actual_cost, 6),
        "savings_usd": round(savings_usd, 6),
        "savings_pct": round(savings_pct, 1),
    }
    save_receipt(record)

    return "\n".join(lines)


def get_session_summary() -> Dict[str, Any]:
    """Retrieve cumulative statistics across all saved receipts."""
    history = load_receipts_history()
    if not history:
        return {
            "total_runs": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_baseline_spend": 0.0,
            "total_actual_spend": 0.0,
            "total_savings_usd": 0.0,
            "overall_savings_pct": 0.0,
        }

    total_in = sum(r.get("input_tokens", 0) for r in history)
    total_out = sum(r.get("output_tokens", 0) for r in history)
    total_base = sum(r.get("baseline_cost", 0.0) for r in history)
    total_actual = sum(r.get("actual_cost", 0.0) for r in history)
    total_savings = sum(r.get("savings_usd", 0.0) for r in history)
    pct = (total_savings / total_base * 100.0) if total_base > 0 else 0.0

    return {
        "total_runs": len(history),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_baseline_spend": round(total_base, 4),
        "total_actual_spend": round(total_actual, 4),
        "total_savings_usd": round(total_savings, 4),
        "overall_savings_pct": round(pct, 1),
    }

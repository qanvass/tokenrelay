"""
Pricing engine: Top 10 LLM providers, model costs, off-peak schedules, and caching math.
"""

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, List, Optional, Tuple


def get_pricing_matrix_path() -> str:
    """Find pricing_matrix.json relative to package or workspace."""
    candidate_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "references", "pricing_matrix.json"),
        os.path.join(os.getcwd(), "references", "pricing_matrix.json"),
        os.path.join(os.path.dirname(__file__), "pricing_matrix.json"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return ""


def load_pricing_matrix() -> Dict[str, Any]:
    """Load pricing matrix with safe fallback."""
    path = get_pricing_matrix_path()
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Built-in fallback
    return {
        "providers": {
            "deepseek": {
                "name": "DeepSeek",
                "off_peak_window_utc": {"start": "00:30", "end": "08:30", "discount_pct": 50},
                "models": {
                    "deepseek-v3": {"tier": "code_edit", "quality_score": 93, "input_standard": 0.27, "input_cached": 0.07, "output": 1.10, "batch_discount_pct": 50},
                    "deepseek-r1": {"tier": "reasoning_architect", "quality_score": 98, "input_standard": 0.55, "input_cached": 0.14, "output": 2.19, "batch_discount_pct": 50},
                }
            },
            "openai": {
                "name": "OpenAI",
                "models": {
                    "gpt-6-astra": {"tier": "reasoning_architect", "quality_score": 99, "input_standard": 10.0, "input_cached": 1.0, "output": 50.0, "batch_discount_pct": 50},
                    "gpt-6.1-sol": {"tier": "flagship_general", "quality_score": 95, "input_standard": 2.0, "input_cached": 0.10, "output": 10.0, "batch_discount_pct": 50},
                    "gpt-4o-mini": {"tier": "fast_workhorse", "quality_score": 85, "input_standard": 0.15, "input_cached": 0.075, "output": 0.60, "batch_discount_pct": 50},
                }
            },
            "anthropic": {
                "name": "Anthropic",
                "models": {
                    "claude-3-7-sonnet": {"tier": "reasoning_architect", "quality_score": 99, "input_standard": 3.0, "input_cached": 0.30, "output": 15.0, "batch_discount_pct": 50},
                    "claude-3-5-haiku": {"tier": "fast_workhorse", "quality_score": 88, "input_standard": 0.80, "input_cached": 0.08, "output": 4.0, "batch_discount_pct": 50},
                }
            }
        }
    }


def check_offpeak_status(provider_id: str = "deepseek", now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Check if a provider is currently within an off-peak discount window.
    Returns status, active discount, and countdown until the next window.
    """
    data = load_pricing_matrix()
    provider = data.get("providers", {}).get(provider_id, {})
    window = provider.get("off_peak_window_utc")

    if not window:
        return {
            "provider": provider.get("name", provider_id),
            "has_offpeak_schedule": False,
            "is_offpeak": False,
            "discount_pct": 0,
            "message": f"{provider.get('name', provider_id)} does not offer scheduled time-of-day discounts.",
        }

    now = now_utc or datetime.now(timezone.utc)
    current_minutes = now.hour * 60 + now.minute

    start_h, start_m = map(int, window["start"].split(":"))
    end_h, end_m = map(int, window["end"].split(":"))

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    is_offpeak = False
    if start_minutes <= end_minutes:
        is_offpeak = start_minutes <= current_minutes < end_minutes
    else:  # overnight window
        is_offpeak = current_minutes >= start_minutes or current_minutes < end_minutes

    # Calculate time until transition
    if is_offpeak:
        if current_minutes < end_minutes:
            diff = end_minutes - current_minutes
        else:
            diff = (1440 - current_minutes) + end_minutes
        hours_left = diff // 60
        mins_left = diff % 60
        countdown_msg = f"Off-peak ends in {hours_left}h {mins_left}m ({window['end']} UTC)"
    else:
        if current_minutes < start_minutes:
            diff = start_minutes - current_minutes
        else:
            diff = (1440 - current_minutes) + start_minutes
        hours_until = diff // 60
        mins_until = diff % 60
        countdown_msg = f"Next off-peak starts in {hours_until}h {mins_until}m ({window['start']} UTC)"

    return {
        "provider": provider.get("name", provider_id),
        "has_offpeak_schedule": True,
        "is_offpeak": is_offpeak,
        "discount_pct": window.get("discount_pct", 50) if is_offpeak else 0,
        "current_time_utc": now.strftime("%H:%M UTC"),
        "window_schedule": f"{window['start']} - {window['end']} UTC",
        "countdown_message": countdown_msg,
        "actionable_warning": (
            None if is_offpeak else
            f"PEAK HOURS ACTIVE for {provider.get('name', provider_id)}. Rates are 2x higher than off-peak. "
            f"Wait {countdown_msg.lower()} or convert to Batch API to save {window.get('discount_pct', 50)}%."
        ),
    }


def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_ratio: float = 0.8,
    is_batch: bool = False,
    apply_offpeak: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Calculate baseline vs optimized cost for any supported model.
    """
    data = load_pricing_matrix()
    target_spec = None
    target_provider = None

    for p_id, p_spec in data.get("providers", {}).items():
        for m_id, m_spec in p_spec.get("models", {}).items():
            if m_id == model_id or model_id.lower() in m_id.lower():
                target_spec = m_spec
                target_provider = p_spec
                model_id = m_id
                break
        if target_spec:
            break

    if not target_spec:
        # Generic default
        target_spec = {"input_standard": 1.0, "input_cached": 0.25, "output": 5.0, "batch_discount_pct": 50}
        target_provider = {"name": "Custom/Unknown", "off_peak_window_utc": None}

    in_rate = target_spec.get("input_standard", 1.0)
    cached_in_rate = target_spec.get("input_cached", in_rate * 0.25)
    out_rate = target_spec.get("output", 5.0)
    batch_discount = target_spec.get("batch_discount_pct", 50) / 100.0

    in_m = input_tokens / 1_000_000.0
    out_m = output_tokens / 1_000_000.0

    # 1. Baseline un-optimized cost
    baseline_cost = (in_m * in_rate) + (out_m * out_rate)

    # 2. Cached cost
    cached_in_m = in_m * cached_input_ratio
    uncached_in_m = in_m * (1.0 - cached_input_ratio)
    actual_in_cost = (uncached_in_m * in_rate) + (cached_in_m * cached_in_rate)
    actual_cost = actual_in_cost + (out_m * out_rate)

    # 3. Off-peak discount
    offpeak_status = check_offpeak_status(
        next((k for k, v in data.get("providers", {}).items() if v == target_provider), "custom")
    )
    is_now_offpeak = offpeak_status.get("is_offpeak", False) if apply_offpeak is None else apply_offpeak
    offpeak_discount_factor = 1.0
    if is_now_offpeak and offpeak_status.get("has_offpeak_schedule"):
        offpeak_discount_factor = (100.0 - offpeak_status.get("discount_pct", 50)) / 100.0
        actual_cost *= offpeak_discount_factor

    # 4. Batch discount
    if is_batch:
        actual_cost *= (1.0 - batch_discount)

    savings = max(0.0, baseline_cost - actual_cost)
    savings_pct = (savings / baseline_cost * 100.0) if baseline_cost > 0 else 0.0

    return {
        "model": model_id,
        "provider": target_provider.get("name", "Unknown"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "baseline_cost": round(baseline_cost, 6),
        "actual_cost": round(actual_cost, 6),
        "savings_usd": round(savings, 6),
        "savings_pct": round(savings_pct, 1),
        "is_offpeak_applied": is_now_offpeak,
        "is_batch_applied": is_batch,
    }

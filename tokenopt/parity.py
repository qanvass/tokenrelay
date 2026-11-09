"""
Equi-Capability Model Parity Engine.
Matches high-cost or credit-depleted models to functionally equivalent
alternatives that maintain code quality while slashing token bills.
"""

from typing import Any, Dict, List, Optional
from tokenopt.pricing import load_pricing_matrix, check_offpeak_status


def find_model_spec(model_name: str) -> Optional[Dict[str, Any]]:
    """Locate a model specification across all providers."""
    data = load_pricing_matrix()
    clean_name = model_name.lower().strip()
    for prov_id, prov_spec in data.get("providers", {}).items():
        for m_id, m_spec in prov_spec.get("models", {}).items():
            if m_id.lower() == clean_name or clean_name in m_id.lower():
                res = dict(m_spec)
                res["model_id"] = m_id
                res["provider_id"] = prov_id
                res["provider_name"] = prov_spec.get("name", prov_id)
                return res
    return None


def get_parity_alternatives(
    target_model: str,
    task_type: Optional[str] = None,
    allow_local: bool = True,
) -> Dict[str, Any]:
    """
    Find equivalent models that match or exceed the target model's quality tier,
    ranked by cost savings.
    """
    spec = find_model_spec(target_model)
    if not spec:
        return {
            "error": f"Model '{target_model}' not found in pricing matrix.",
            "available_providers": list(load_pricing_matrix().get("providers", {}).keys()),
        }

    target_tier = task_type or spec.get("tier", "flagship_general")
    target_quality = spec.get("quality_score", 90)
    target_input = spec.get("input_standard", 1.0)
    target_output = spec.get("output", 5.0)

    # Benchmark cost for 100k input / 10k output
    benchmark_base = (0.1 * target_input) + (0.01 * target_output)

    data = load_pricing_matrix()
    candidates = []

    for prov_id, prov_spec in data.get("providers", {}).items():
        is_local = "local" in prov_id
        if is_local and not allow_local:
            continue

        offpeak = check_offpeak_status(prov_id)
        offpeak_discount = (offpeak.get("discount_pct", 0) / 100.0) if offpeak.get("is_offpeak") else 0.0

        for m_id, m_spec in prov_spec.get("models", {}).items():
            if m_id == spec["model_id"]:
                continue

            tier = m_spec.get("tier", "")
            quality = m_spec.get("quality_score", 85)

            # Match tier or accept close quality score
            tier_match = (tier == target_tier) or (abs(quality - target_quality) <= 6)
            if not tier_match:
                continue

            inp = m_spec.get("input_standard", 1.0) * (1.0 - offpeak_discount)
            out = m_spec.get("output", 1.0) * (1.0 - offpeak_discount)
            cand_cost = (0.1 * inp) + (0.01 * out)

            savings_usd = benchmark_base - cand_cost
            savings_pct = (savings_usd / benchmark_base * 100.0) if benchmark_base > 0 else 0.0

            if savings_pct > 0:  # Only recommend cheaper options
                candidates.append({
                    "model_id": m_id,
                    "provider": prov_spec.get("name", prov_id),
                    "tier": tier,
                    "quality_score": quality,
                    "quality_delta": quality - target_quality,
                    "input_rate": round(inp, 4),
                    "output_rate": round(out, 4),
                    "benchmark_cost_100k_10k": round(cand_cost, 5),
                    "savings_pct": round(savings_pct, 1),
                    "is_offpeak_active": offpeak.get("is_offpeak", False),
                    "reasoning_warning": m_spec.get("thinking_token_warning"),
                })

    # Sort candidates by cost savings percentage descending
    candidates.sort(key=lambda x: x["savings_pct"], reverse=True)

    return {
        "target_model": spec["model_id"],
        "target_provider": spec["provider_name"],
        "target_tier": target_tier,
        "target_quality_score": target_quality,
        "target_benchmark_cost": round(benchmark_base, 5),
        "recommended_parity_alternatives": candidates[:5],
    }

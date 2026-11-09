"""
Free-Tier Stacking Gateway & Quota Manager.
Aggregates free-tier developer allowances across Google AI Studio, Groq,
Cohere, OpenRouter free models, and local Ollama into a resilient, zero-cost pool.
Enables Claude Code, Cursor, and Cline to run 100% free forever ($0.00).
"""

import os
import time
from typing import Any, Dict, List, Optional

FREE_TIER_PROVIDERS = [
    {
        "id": "gemini_free",
        "name": "Google AI Studio (Gemini 2.0 Flash)",
        "env_key": "GEMINI_API_KEY",
        "rpm_limit": 15,
        "rpd_limit": 1500,
        "model_id": "gemini-2.0-flash",
        "cost_per_token": 0.00,
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "notes": "15 RPM, 1,500 requests per day, 1M TPM free forever for prototyping.",
    },
    {
        "id": "groq_free",
        "name": "Groq Cloud (Llama 3.3 70B Versatile)",
        "env_key": "GROQ_API_KEY",
        "rpm_limit": 30,
        "rpd_limit": 14400,
        "model_id": "llama-3.3-70b-versatile",
        "cost_per_token": 0.00,
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "notes": "Generous free RPM with ultra-fast LPU inference (250+ tokens/sec).",
    },
    {
        "id": "ollama_local",
        "name": "Local Ollama (Qwen 2.5 Coder 7B)",
        "env_key": None,  # No key needed
        "rpm_limit": 99999,
        "rpd_limit": 999999,
        "model_id": "qwen2.5-coder:7b",
        "cost_per_token": 0.00,
        "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
        "notes": "100% offline, zero network latency, unlimited requests, $0.00 cost.",
    },
    {
        "id": "cohere_free",
        "name": "Cohere Trial (Command R)",
        "env_key": "COHERE_API_KEY",
        "rpm_limit": 20,
        "rpd_limit": 1000,
        "model_id": "command-r",
        "cost_per_token": 0.00,
        "endpoint": "https://api.cohere.com/v1/chat",
        "notes": "Free developer trial key with Cohere Rerank support.",
    },
]


class FreeTierPool:
    """Manages active free-tier backends with automatic failover on rate limits (429)."""

    def __init__(self):
        self.cooldowns: Dict[str, float] = {}

    def get_available_backends(self) -> List[Dict[str, Any]]:
        """Return list of configured free backends not currently cooling down."""
        available = []
        now = time.time()
        for prov in FREE_TIER_PROVIDERS:
            # Check cooldown
            if self.cooldowns.get(prov["id"], 0) > now:
                continue

            # Check if key is available or local
            if prov["env_key"]:
                key_val = os.environ.get(prov["env_key"], "").strip()
                if not key_val:
                    continue

            available.append(prov)
        return available

    def trigger_cooldown(self, provider_id: str, cooldown_seconds: float = 60.0):
        """Mark a provider as cooling down due to rate limit (429)."""
        self.cooldowns[provider_id] = time.time() + cooldown_seconds

    def get_status_report(self) -> List[Dict[str, Any]]:
        """Generate human-readable status of the free tier pool."""
        now = time.time()
        report = []
        for prov in FREE_TIER_PROVIDERS:
            has_key = True
            if prov["env_key"]:
                has_key = bool(os.environ.get(prov["env_key"], "").strip())

            cooling = self.cooldowns.get(prov["id"], 0) > now
            secs_left = int(self.cooldowns.get(prov["id"], 0) - now) if cooling else 0

            report.append({
                "id": prov["id"],
                "name": prov["name"],
                "configured": has_key,
                "status": "COOLING_DOWN" if cooling else ("READY" if has_key else "KEY_MISSING"),
                "cooldown_remaining_sec": secs_left,
                "notes": prov["notes"],
            })
        return report


# Global instance
free_pool = FreeTierPool()


def get_claude_code_free_env() -> Dict[str, str]:
    """
    Returns environment variable exports to run Claude Code 100% free
    via TokenRelay's local gateway.
    """
    return {
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:8080",
        "ANTHROPIC_API_KEY": "tokenopt-free-tier-proxy",
    }

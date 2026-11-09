"""
Cross-IDE Orchestration Engine & Shared Heartbeat Bus.
Enables Cursor, Windsurf, Claude Code, and Cline to work together in sync
on a shared project, maintaining a live heartbeat, shared task state,
and domain-specific model failover (e.g., 3D Blender, Full-Stack, Browser Automation).
"""

from datetime import datetime, timezone
import json
import os
import time
from typing import Any, Dict, List, Optional
from tokenopt.parity import get_parity_alternatives
from tokenopt.pricing import calculate_cost, check_offpeak_status

DOMAIN_SPECIALIZATION_MATRIX = {
    "3d_blender": {
        "label": "3D Asset Generation & Blender Scripting (bpy)",
        "flagship": "gpt-6-astra",
        "parity_alternatives": [
            {
                "model": "deepseek-v3",
                "provider": "DeepSeek",
                "specialty": "Elite Python bpy script generation at 97.5% lower cost ($0.27/1M vs $10.00/1M)",
                "quality_parity_pct": 94,
            },
            {
                "model": "gemini-2.5-pro",
                "provider": "Google DeepMind",
                "specialty": "Multimodal visual inspection of rendered 3D frames with 1M context",
                "quality_parity_pct": 97,
            },
            {
                "model": "qwen-2.5-coder-32b-local",
                "provider": "Meta / Ollama Local",
                "specialty": "100% offline, $0.00/token unlimited iteration for complex geometry math",
                "quality_parity_pct": 92,
            },
        ],
    },
    "fullstack_web": {
        "label": "Full-Stack Web & Multi-File Architecture",
        "flagship": "claude-3-7-sonnet",
        "parity_alternatives": [
            {
                "model": "deepseek-r1",
                "provider": "DeepSeek",
                "specialty": "Deep multi-file dependency reasoning at $0.55/1M (95% savings)",
                "quality_parity_pct": 98,
            },
            {
                "model": "codestral-25.08",
                "provider": "Mistral AI",
                "specialty": "High-throughput TypeScript / Next.js implementation ($0.30/1M)",
                "quality_parity_pct": 93,
            },
        ],
    },
    "browser_automation": {
        "label": "Browser Takeover & Computer Use",
        "flagship": "gpt-6-astra",
        "parity_alternatives": [
            {
                "model": "gemini-2.0-flash",
                "provider": "Google DeepMind",
                "specialty": "Ultra-fast screenshot DOM parsing at $0.10/1M (or free on AI Studio)",
                "quality_parity_pct": 91,
            },
            {
                "model": "deepseek-v3",
                "provider": "DeepSeek",
                "specialty": "Generates robust Playwright / Puppeteer execution scripts directly",
                "quality_parity_pct": 94,
            },
        ],
    },
}


def get_orchestration_bus_dir(workspace_root: Optional[str] = None) -> str:
    """Directory for the cross-IDE shared heartbeat and task bus."""
    root = workspace_root or os.getcwd()
    bus_dir = os.path.join(root, ".tokenopt", "bus")
    os.makedirs(bus_dir, exist_ok=True)
    return bus_dir


def update_ide_heartbeat(
    ide_id: str,
    active_project: str,
    active_model: str,
    current_task: str,
    tokens_spent: int = 0,
    credit_exhaustion_warning: bool = False,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Publish an IDE heartbeat to the shared bus so all connected assistants
    understand active state, model health, and credit status.
    """
    bus_dir = get_orchestration_bus_dir(workspace_root)
    heartbeat_file = os.path.join(bus_dir, f"{ide_id}_heartbeat.json")
    now_utc = datetime.now(timezone.utc).isoformat()

    record = {
        "ide_id": ide_id,
        "active_project": active_project,
        "active_model": active_model,
        "current_task": current_task,
        "tokens_spent": tokens_spent,
        "credit_exhaustion_warning": credit_exhaustion_warning,
        "timestamp_utc": now_utc,
        "epoch_time": time.time(),
    }

    try:
        with open(heartbeat_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
    except Exception:
        pass

    return record


def get_all_ide_heartbeats(workspace_root: Optional[str] = None, max_age_seconds: float = 300.0) -> List[Dict[str, Any]]:
    """Query live heartbeats across all IDEs connected to this project."""
    bus_dir = get_orchestration_bus_dir(workspace_root)
    active_heartbeats = []
    now = time.time()

    for fname in os.listdir(bus_dir):
        if fname.endswith("_heartbeat.json"):
            fpath = os.path.join(bus_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    age = now - data.get("epoch_time", 0)
                    data["is_alive"] = age <= max_age_seconds
                    data["age_seconds"] = int(age)
                    active_heartbeats.append(data)
            except Exception:
                continue

    return active_heartbeats


def trigger_cross_ide_handoff(
    from_ide: str,
    target_ide: str,
    task_description: str,
    exhausted_model: str,
    fallback_model: str,
    context_notes: str = "",
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Emit a handoff signal allowing a task to seamlessly migrate between IDEs
    or between models (e.g. Cursor -> Claude Code) without context loss.
    """
    bus_dir = get_orchestration_bus_dir(workspace_root)
    handoff_file = os.path.join(bus_dir, "active_handoff.json")
    now_utc = datetime.now(timezone.utc).isoformat()

    payload = {
        "status": "PENDING_HANDOFF",
        "timestamp_utc": now_utc,
        "source_ide": from_ide,
        "target_ide": target_ide,
        "task_description": task_description,
        "exhausted_model": exhausted_model,
        "assigned_fallback_model": fallback_model,
        "context_notes": context_notes,
    }

    with open(handoff_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


def query_domain_parity(domain_key: str) -> Dict[str, Any]:
    """
    Get domain-specific model alternatives (e.g. for Blender 3D, Full-Stack, Browser Use)
    with cost comparisons and quality parity scores.
    """
    if domain_key not in DOMAIN_SPECIALIZATION_MATRIX:
        return {
            "error": f"Unknown domain '{domain_key}'. Available: {list(DOMAIN_SPECIALIZATION_MATRIX.keys())}"
        }
    return DOMAIN_SPECIALIZATION_MATRIX[domain_key]

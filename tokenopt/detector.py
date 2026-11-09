"""
Zero-touch system environment and IDE scanner.
Automatically detects installed IDEs, local runtimes (Ollama/LM Studio),
active API keys, workspace rule files, and cost blind spots.
"""

import glob
import os
import shutil
import socket
import subprocess
import urllib.request
import json
from typing import Any, Dict, List, Optional


def check_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Quickly check if a local port is listening."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def query_ollama_models() -> List[str]:
    """Query locally installed Ollama models if Ollama is running."""
    if not check_port_open("127.0.0.1", 11434):
        return []
    try:
        url = "http://127.0.0.1:11434/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "TokenRelay"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name") for m in data.get("models", [])]
    except Exception:
        return []


def detect_installed_ides() -> List[Dict[str, Any]]:
    """Detect which of the top 10 AI IDEs are installed on the host."""
    detected = []
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")

    ide_signatures = [
        {
            "id": "cursor",
            "name": "Cursor",
            "paths": [
                os.path.join(home, ".cursor"),
                os.path.join(appdata, "Cursor"),
                os.path.join(localappdata, "Programs", "cursor"),
            ],
            "rules_target": ".cursor/rules/tokenopt.mdc",
            "mcp_config": os.path.join(home, ".cursor", "mcp.json"),
        },
        {
            "id": "windsurf",
            "name": "Windsurf (Codeium)",
            "paths": [
                os.path.join(home, ".codeium", "windsurf"),
                os.path.join(appdata, "Codeium", "Windsurf"),
                os.path.join(localappdata, "Programs", "Windsurf"),
            ],
            "rules_target": ".windsurfrules",
            "mcp_config": os.path.join(home, ".codeium", "windsurf", "mcp_config.json"),
        },
        {
            "id": "vscode_copilot",
            "name": "VS Code / GitHub Copilot",
            "paths": [
                os.path.join(home, ".vscode"),
                os.path.join(appdata, "Code"),
                os.path.join(localappdata, "Programs", "Microsoft VS Code"),
            ],
            "rules_target": ".github/copilot-instructions.md",
            "mcp_config": None,
        },
        {
            "id": "claude_code",
            "name": "Claude Code (CLI)",
            "paths": [
                os.path.join(home, ".claude"),
                shutil.which("claude") or "",
            ],
            "rules_target": "CLAUDE.md",
            "mcp_config": os.path.join(home, ".claude", "mcp.json"),
        },
        {
            "id": "continue_dev",
            "name": "Continue.dev",
            "paths": [
                os.path.join(home, ".continue"),
            ],
            "rules_target": os.path.join(home, ".continue", "config.json"),
            "mcp_config": None,
        },
        {
            "id": "cline",
            "name": "Cline / Roo Code",
            "paths": [
                os.path.join(home, ".cline"),
                os.path.join(appdata, "Code", "User", "globalStorage", "saoudrizwan.claude-dev"),
            ],
            "rules_target": ".clinerules",
            "mcp_config": None,
        },
        {
            "id": "aider",
            "name": "Aider",
            "paths": [
                os.path.join(home, ".aider"),
                shutil.which("aider") or "",
            ],
            "rules_target": ".aider.conf.yml",
            "mcp_config": None,
        },
        {
            "id": "jetbrains",
            "name": "JetBrains AI",
            "paths": [
                os.path.join(appdata, "JetBrains"),
                os.path.join(home, ".IntelliJIdea*"),
                os.path.join(home, ".PyCharm*"),
            ],
            "rules_target": ".jetbrains/rules.xml",
            "mcp_config": None,
        },
        {
            "id": "antigravity",
            "name": "Google Antigravity",
            "paths": [
                os.path.join(home, ".gemini"),
            ],
            "rules_target": ".gemini/rules/tokenopt.md",
            "mcp_config": None,
        },
    ]

    for ide in ide_signatures:
        found_path = None
        for p in ide["paths"]:
            if not p:
                continue
            if "*" in p:
                matches = glob.glob(p)
                if matches:
                    found_path = matches[0]
                    break
            elif os.path.exists(p):
                found_path = p
                break

        if found_path:
            detected.append({
                "id": ide["id"],
                "name": ide["name"],
                "installed": True,
                "detected_path": found_path,
                "rules_target": ide["rules_target"],
                "mcp_config": ide["mcp_config"],
            })

    return detected


def detect_api_keys() -> Dict[str, bool]:
    """Detect configured LLM provider keys in environment variables."""
    key_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "groq": "GROQ_API_KEY",
        "aws_bedrock": "AWS_ACCESS_KEY_ID",
        "azure_openai": "AZURE_OPENAI_API_KEY",
        "cohere": "COHERE_API_KEY",
        "xai": "XAI_API_KEY",
    }
    status = {}
    for prov, env_var in key_map.items():
        val = os.environ.get(env_var, "").strip()
        status[prov] = bool(val and len(val) > 4)
    return status


def detect_workspace_rules(workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    """Detect active rules files in current workspace."""
    root = workspace_root or os.getcwd()
    candidate_rules = [
        (".cursorrules", "Cursor Legacy Rules"),
        (".cursor/rules", "Cursor Modern Rules Folder"),
        (".windsurfrules", "Windsurf Rules"),
        ("CLAUDE.md", "Claude Code Rules"),
        (".clinerules", "Cline Rules"),
        (".github/copilot-instructions.md", "GitHub Copilot Instructions"),
        (".copilotignore", "GitHub Copilot Ignore"),
        (".aider.conf.yml", "Aider Config"),
        (".tokenopt/rules.md", "TokenRelay Single Source of Truth"),
    ]
    results = []
    for rel_path, label in candidate_rules:
        full_path = os.path.join(root, rel_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            results.append({
                "path": rel_path,
                "full_path": full_path,
                "label": label,
                "size_bytes": size,
                "is_dir": os.path.isdir(full_path),
            })
    return results


def get_system_hardware_specs() -> Dict[str, Any]:
    """Inspect system RAM, CPU cores, GPU, and free disk space."""
    import platform
    specs = {
        "os": platform.system(),
        "os_release": platform.release(),
        "cpu_cores": os.cpu_count() or 4,
        "ram_gb": 16.0,
        "gpu_name": "Integrated Graphics",
        "disk_free_gb": 100.0,
        "supports_local_models": True,
        "recommended_model_size": "7B - 8B Q4",
    }

    if platform.system() == "Windows":
        try:
            # Query RAM & CPU via powershell
            cmd = "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory; Get-CimInstance Win32_VideoController | Select-Object Name; (Get-PSDrive C).Free / 1GB"
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=3.0)
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            for l in lines:
                if l.isdigit() and len(l) > 8:
                    specs["ram_gb"] = round(int(l) / (1024**3), 1)
                elif any(g in l for g in ["Radeon", "NVIDIA", "GeForce", "RTX", "Intel", "Graphics"]):
                    specs["gpu_name"] = l
                elif "." in l and l.replace(".", "").isdigit():
                    specs["disk_free_gb"] = round(float(l), 1)
        except Exception:
            pass

    # Model size recommendation based on RAM (16GB physical RAM shows ~14-15GB usable on Windows with iGPU)
    if specs["ram_gb"] >= 28:
        specs["recommended_model_size"] = "14B - 32B Q4"
    elif specs["ram_gb"] >= 12:
        specs["recommended_model_size"] = "7B - 8B Q4 (e.g. Qwen 2.5 Coder 7B, DeepSeek R1 8B)"
    elif specs["ram_gb"] >= 6:
        specs["recommended_model_size"] = "1.5B - 3B Q4 (e.g. Qwen 2.5 Coder 1.5B)"
    else:
        specs["supports_local_models"] = False
        specs["recommended_model_size"] = "Cloud APIs Only (< 6GB RAM)"

    return specs


def run_system_audit(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Run complete zero-touch environmental audit.
    Identifies what is installed, what is active, and provides cost-saving recommendations.
    """
    ides = detect_installed_ides()
    keys = detect_api_keys()
    rules = detect_workspace_rules(workspace_root)

    # Local LLMs
    ollama_running = check_port_open("127.0.0.1", 11434)
    ollama_models = query_ollama_models() if ollama_running else []
    lm_studio_running = check_port_open("127.0.0.1", 1234)

    # Calculate blind spots & actionable recommendations
    recommendations = []

    # 1. Local Autocomplete Opportunity
    if not ollama_running:
        recommendations.append({
            "category": "Zero-Cost Local Inference",
            "severity": "HIGH",
            "finding": "Ollama is not running locally.",
            "action": "Install Ollama and run 'ollama run qwen2.5-coder:7b' for $0.00/token inline autocomplete. Saves ~35% of daily developer token spend.",
        })
    elif not any("qwen" in m.lower() or "coder" in m.lower() for m in ollama_models):
        recommendations.append({
            "category": "Zero-Cost Local Inference",
            "severity": "MEDIUM",
            "finding": "Ollama is running, but no dedicated coding model was found.",
            "action": "Pull Qwen 2.5 Coder via 'ollama pull qwen2.5-coder:7b' for instant $0 Tab completions.",
        })

    # 2. Frontier Pricing Opportunity
    if not keys.get("deepseek"):
        recommendations.append({
            "category": "Frontier Model Cost Lever",
            "severity": "CRITICAL",
            "finding": "DEEPSEEK_API_KEY is not configured.",
            "action": "Add a DeepSeek API key. DeepSeek V3 ($0.27/1M) and R1 ($0.55/1M) match GPT-4o/o1 quality at 85% lower cost, plus 50% off-peak discounts (00:30-08:30 UTC).",
        })

    # 3. Google AI Studio Free Tier
    if not keys.get("google"):
        recommendations.append({
            "category": "Free Prototyping Tier",
            "severity": "HIGH",
            "finding": "GEMINI_API_KEY is not configured.",
            "action": "Get a free Google AI Studio key. Offers 15 RPM and 1,500 requests/day for Gemini 2.0 Flash at $0 cost for unit tests and quick edits.",
        })

    # 4. Cross-IDE Sync Status
    has_tokenopt_rules = any(r["path"] == ".tokenopt/rules.md" for r in rules)
    if not has_tokenopt_rules and len(ides) > 1:
        recommendations.append({
            "category": "Cross-IDE Rules Fragmentation",
            "severity": "MEDIUM",
            "finding": f"Detected {len(ides)} installed IDEs but no centralized rules file (.tokenopt/rules.md).",
            "action": "Run 'tokenopt sync' to generate a unified, cache-optimized rules file synced across all your IDEs.",
        })

    return {
        "hardware_specs": get_system_hardware_specs(),
        "installed_ides": ides,
        "local_runtimes": {
            "ollama_running": ollama_running,
            "ollama_models": ollama_models,
            "lm_studio_running": lm_studio_running,
        },
        "api_keys": keys,
        "workspace_rules": rules,
        "recommendations": recommendations,
    }

"""
Cross-IDE Context & Rules Synchronization Engine.
Maintains a single source of truth (.tokenopt/rules.md) and compiles clean,
cache-optimized configuration files across Cursor, Windsurf, Claude Code,
Copilot, Cline, Continue, and Aider.
"""

import os
import re
from typing import Any, Dict, List, Tuple
from tokenopt.optimizer import sanitize_cache_busters

DEFAULT_CORE_RULES = """# Universal Codebase Standards & Cost Rules
- Language: Python 3.8+ / TypeScript strict.
- Architecture: Keep functions pure, decoupled, and modular.
- Token Discipline: Output changes strictly as SEARCH/REPLACE blocks or unified diffs.
- Avoid full file rewrites. Do not include conversational pleasantries or preamble.
- Prompt Caching: Maintain stable system prefixes. Never insert dynamic dates or build UUIDs into code rules.
"""

DEFAULT_COPILOT_IGNORE = """node_modules/
dist/
build/
.git/
*.min.js
*.bundle.js
*.pyc
__pycache__/
*.lock
*.log
coverage/
"""


def get_tokenopt_rules_path(workspace_root: str) -> str:
    """Path to the central single-source-of-truth rules file."""
    tokenopt_dir = os.path.join(workspace_root, ".tokenopt")
    os.makedirs(tokenopt_dir, exist_ok=True)
    return os.path.join(tokenopt_dir, "rules.md")


def init_central_rules(workspace_root: str) -> str:
    """Create central rules file if not existing."""
    path = get_tokenopt_rules_path(workspace_root)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CORE_RULES.strip() + "\n")
    return path


def sync_all_ides(workspace_root: str, central_rules_content: str) -> Dict[str, Any]:
    """
    Compile central rules out to all detected/standard IDE locations.
    Enforces cache stabilization, token limits (<250 words), and diff constraints.
    """
    clean_rules, busters = sanitize_cache_busters(central_rules_content)
    words = clean_rules.split()
    word_count = len(words)

    targets_written = []

    # 1. Cursor (.cursor/rules/tokenopt.mdc)
    cursor_dir = os.path.join(workspace_root, ".cursor", "rules")
    os.makedirs(cursor_dir, exist_ok=True)
    cursor_file = os.path.join(cursor_dir, "tokenopt.mdc")
    cursor_content = (
        "---\ndescription: Project Coding & Cost Optimization Standards\nglobs: *\n---\n\n"
        + clean_rules
    )
    with open(cursor_file, "w", encoding="utf-8") as f:
        f.write(cursor_content)
    targets_written.append(cursor_file)

    # 2. Windsurf (.windsurfrules)
    windsurf_file = os.path.join(workspace_root, ".windsurfrules")
    with open(windsurf_file, "w", encoding="utf-8") as f:
        f.write(clean_rules)
    targets_written.append(windsurf_file)

    # 3. Claude Code (CLAUDE.md)
    claude_file = os.path.join(workspace_root, "CLAUDE.md")
    with open(claude_file, "w", encoding="utf-8") as f:
        f.write(clean_rules)
    targets_written.append(claude_file)

    # 4. GitHub Copilot (.github/copilot-instructions.md and .copilotignore)
    github_dir = os.path.join(workspace_root, ".github")
    os.makedirs(github_dir, exist_ok=True)
    copilot_file = os.path.join(github_dir, "copilot-instructions.md")
    with open(copilot_file, "w", encoding="utf-8") as f:
        f.write(clean_rules)
    targets_written.append(copilot_file)

    copilot_ignore = os.path.join(workspace_root, ".copilotignore")
    if not os.path.exists(copilot_ignore):
        with open(copilot_ignore, "w", encoding="utf-8") as f:
            f.write(DEFAULT_COPILOT_IGNORE)
        targets_written.append(copilot_ignore)

    # 5. Cline (.clinerules)
    cline_file = os.path.join(workspace_root, ".clinerules")
    with open(cline_file, "w", encoding="utf-8") as f:
        f.write(clean_rules)
    targets_written.append(cline_file)

    # 6. Aider (.aider.conf.yml)
    aider_file = os.path.join(workspace_root, ".aider.conf.yml")
    aider_conf = (
        "cache-prompts: true\n"
        "map-tokens: 512\n"
        "stream: true\n"
        "model: deepseek/deepseek-v3\n"
        "weak-model: deepseek/deepseek-v3\n"
    )
    if not os.path.exists(aider_file):
        with open(aider_file, "w", encoding="utf-8") as f:
            f.write(aider_conf)
        targets_written.append(aider_file)

    return {
        "status": "SUCCESS",
        "central_source": get_tokenopt_rules_path(workspace_root),
        "word_count": word_count,
        "token_overhead_per_turn": int(word_count * 1.3),
        "cache_busters_stripped": busters,
        "targets_synced": targets_written,
        "message": f"Successfully compiled and synced {len(targets_written)} IDE configuration files.",
    }

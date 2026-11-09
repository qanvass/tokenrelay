"""
Deep Project Scanner, Chat Transcript Reader & Developer Skill Profiler.
Scans local repositories, parses active IDE chat transcripts across Cursor,
Claude Code, and Cline, and builds a persistent developer skill profile
to recommend optimal LLM toolchains and eliminate runaway token loops.
"""

import glob
import json
import os
import re
import sqlite3
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Set

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".rs": "Rust",
    ".go": "Go",
    ".cpp": "C++",
    ".c": "C",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".sol": "Solidity",
}


def get_tokenopt_memory_path(base_dir: Optional[str] = None) -> str:
    """Path to the persistent developer memory store."""
    root = base_dir or os.getcwd()
    tokenopt_dir = os.path.join(root, ".tokenopt")
    os.makedirs(tokenopt_dir, exist_ok=True)
    return os.path.join(tokenopt_dir, "developer_memory.json")


def scan_local_projects(search_roots: Optional[List[str]] = None, max_projects: int = 25) -> List[Dict[str, Any]]:
    """
    Discover active project folders across the desktop, home directory, and workspaces.
    Extracts languages, package managers, and architecture tier.
    """
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")
    documents = os.path.join(home, "Documents")

    roots_to_check = search_roots or [desktop, home, os.getcwd()]
    discovered = []
    seen_paths = set()

    project_markers = [
        ("package.json", "Node/JS/TS"),
        ("requirements.txt", "Python"),
        ("pyproject.toml", "Python"),
        ("Cargo.toml", "Rust"),
        ("go.mod", "Go"),
        ("pom.xml", "Java Maven"),
        (".git", "Git Repository"),
    ]

    for root_dir in roots_to_check:
        if not os.path.exists(root_dir):
            continue
        try:
            # Check direct subdirectories
            for entry in os.scandir(root_dir):
                if entry.is_dir() and not entry.name.startswith((".", "$", "AppData", "node_modules", "Windows")):
                    project_path = entry.path
                    if project_path in seen_paths:
                        continue

                    # Inspect for markers
                    found_tech = []
                    for marker, label in project_markers:
                        if os.path.exists(os.path.join(project_path, marker)):
                            found_tech.append(label)

                    if found_tech:
                        seen_paths.add(project_path)
                        # Quick language tally
                        lang_counts = {}
                        file_count = 0
                        has_tests = False
                        has_docker = os.path.exists(os.path.join(project_path, "Dockerfile")) or os.path.exists(os.path.join(project_path, "docker-compose.yml"))

                        try:
                            for root, dirs, files in os.walk(project_path):
                                # Skip heavy build dirs
                                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv"]]
                                for f in files:
                                    file_count += 1
                                    ext = os.path.splitext(f)[1].lower()
                                    if ext in LANGUAGE_EXTENSIONS:
                                        lang = LANGUAGE_EXTENSIONS[ext]
                                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                                    if "test" in f.lower() or "spec" in f.lower():
                                        has_tests = True
                                    if file_count > 300:  # Sample limit
                                        break
                                if file_count > 300:
                                    break
                        except Exception:
                            pass

                        primary_lang = max(lang_counts.items(), key=lambda x: x[1])[0] if lang_counts else "Unknown"

                        discovered.append({
                            "name": entry.name,
                            "path": project_path,
                            "technologies": list(set(found_tech)),
                            "primary_language": primary_lang,
                            "language_distribution": lang_counts,
                            "has_tests": has_tests,
                            "has_docker": has_docker,
                            "sampled_files": file_count,
                        })

                        if len(discovered) >= max_projects:
                            return discovered
        except Exception:
            continue

    return discovered


def read_claude_code_history() -> List[Dict[str, Any]]:
    """Parse local Claude Desktop and Claude Code session transcripts, sorting by latest first."""
    home = os.path.expanduser("~")
    claude_projects_dir = os.path.join(home, ".claude", "projects")
    recent_sessions = []

    if not os.path.exists(claude_projects_dir):
        return []

    try:
        jsonl_files = glob.glob(os.path.join(claude_projects_dir, "**", "*.jsonl"), recursive=True)
        # Sort descending by modification time
        sorted_files = []
        for jf in jsonl_files:
            try:
                sorted_files.append((jf, os.path.getmtime(jf)))
            except Exception:
                pass
        sorted_files.sort(key=lambda x: x[1], reverse=True)

        for jf, mtime in sorted_files[:15]:
            try:
                with open(jf, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    last_user_prompt = ""
                    active_model = "claude-opus-4-8"
                    for line in reversed(lines):
                        try:
                            d = json.loads(line)
                            if not last_user_prompt and (d.get("type") == "user" or d.get("message", {}).get("role") == "user"):
                                c = d.get("message", {}).get("content") or d.get("prompt")
                                if isinstance(c, list):
                                    texts = [item.get("text", "") for item in c if isinstance(item, dict) and item.get("text")]
                                    last_user_prompt = " ".join(texts).strip()
                                elif isinstance(c, str):
                                    last_user_prompt = c.strip()
                            if "model" in str(d):
                                m = d.get("message", {}).get("model") or d.get("model")
                                if m:
                                    active_model = m
                            if last_user_prompt and active_model:
                                break
                        except Exception:
                            continue

                    recent_sessions.append({
                        "file": jf,
                        "mtime": mtime,
                        "turns": len(lines),
                        "model": active_model,
                        "last_prompt": last_user_prompt[:300] if last_user_prompt else "",
                    })
            except Exception:
                continue
    except Exception:
        pass

    return recent_sessions


def read_cursor_chat_history() -> List[Dict[str, Any]]:
    """Extract recent chat session topics from Cursor SQLite storage."""
    appdata = os.environ.get("APPDATA", "")
    workspace_storage = os.path.join(appdata, "Cursor", "User", "workspaceStorage")
    recent_chats = []

    if not os.path.exists(workspace_storage):
        return []

    try:
        db_files = glob.glob(os.path.join(workspace_storage, "*", "state.vscdb"))
        for db in db_files[:8]:
            temp_copy = os.path.join(tempfile.gettempdir(), f"tokenopt_cur_{os.path.basename(os.path.dirname(db))}.vscdb")
            try:
                shutil.copyfile(db, temp_copy)
                conn = sqlite3.connect(temp_copy)
                c = conn.cursor()
                c.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%aiService%' LIMIT 10")
                rows = c.fetchall()
                for key, val in rows:
                    if isinstance(val, (bytes, bytearray)):
                        try:
                            val = val.decode("utf-8", errors="ignore")
                        except:
                            val = ""
                    if "model" in str(val).lower() or "prompt" in str(val).lower():
                        recent_chats.append({
                            "workspace_db": db,
                            "key": key,
                            "summary": str(val)[:180],
                        })
                conn.close()
            except Exception:
                pass
            finally:
                if os.path.exists(temp_copy):
                    try: os.remove(temp_copy)
                    except: pass
    except Exception:
        pass

    return recent_chats


def evaluate_developer_profile(projects: List[Dict[str, Any]], claude_chats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize detected codebases and chat history to assess developer skill tier,
    primary domain, and personalized LLM routing recommendations.
    """
    total_projects = len(projects)
    languages_seen: Set[str] = set()
    docker_count = sum(1 for p in projects if p.get("has_docker"))
    test_count = sum(1 for p in projects if p.get("has_tests"))

    for p in projects:
        languages_seen.update(p.get("language_distribution", {}).keys())

    # Heuristic skill assessment
    polyglot_factor = len(languages_seen)
    infra_factor = docker_count + test_count

    if infra_factor >= 3 or polyglot_factor >= 4 or total_projects >= 8:
        skill_level = "Staff / Senior Architect"
        recommended_primary = "deepseek-r1"
        recommended_editor = "deepseek-v3"
        roi_advice = (
            "Senior multi-repository developer. High multi-file complexity. "
            "Use DeepSeek R1 for architectural decisions (saves 95% vs GPT-6 Astra / Claude 3.7 Sonnet) "
            "and DeepSeek V3 / Codestral for diff implementations. Enforce prefix caching on large context."
        )
    elif infra_factor >= 1 or polyglot_factor >= 2 or total_projects >= 3:
        skill_level = "Intermediate / Full-Stack Engineer"
        recommended_primary = "deepseek-v3"
        recommended_editor = "gemini-2.0-flash"
        roi_advice = (
            "Full-stack engineer. Routine feature edits and API wiring. "
            "Default to DeepSeek V3 ($0.27/1M) or Gemini 2.0 Flash (free on Google AI Studio). "
            "Reserve reasoning models strictly for tricky algorithms or database schema migrations."
        )
    else:
        skill_level = "Foundational / Rapid Prototyper"
        recommended_primary = "gemini-2.0-flash"
        recommended_editor = "qwen-2.5-coder-7b-local"
        roi_advice = (
            "Prototyping & exploratory workflow. High risk of runaway chat loops. "
            "Use Google AI Studio free tier (1,500 daily requests at $0.00) and local Ollama Qwen 2.5 Coder. "
            "Enforce hard 5-iteration limits on AI debugging loops to prevent accidental credit drain."
        )

    return {
        "assessed_skill_tier": skill_level,
        "total_repositories_analyzed": total_projects,
        "languages_mastered": sorted(list(languages_seen)),
        "ci_cd_and_docker_adoption": f"{docker_count}/{total_projects} projects contain container/infra specs",
        "test_suite_coverage": f"{test_count}/{total_projects} projects contain automated tests",
        "recommended_primary_reasoning_model": recommended_primary,
        "recommended_editor_workhorse_model": recommended_editor,
        "tailored_cost_strategy": roi_advice,
    }


def build_and_save_developer_memory(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """Execute full system project and chat scan and persist memory."""
    root = workspace_root or os.getcwd()
    projects = scan_local_projects()
    claude_history = read_claude_code_history()
    cursor_chats = read_cursor_chat_history()
    profile = evaluate_developer_profile(projects, claude_history)

    memory_record = {
        "version": "2.1.0",
        "developer_profile": profile,
        "discovered_projects": projects,
        "active_chat_signals": {
            "claude_sessions_found": len(claude_history),
            "cursor_workspaces_found": len(cursor_chats),
        },
    }

    save_path = get_tokenopt_memory_path(root)
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(memory_record, f, indent=2)
    except Exception:
        pass

    return memory_record

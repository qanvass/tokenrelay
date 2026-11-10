"""
Command-Line Interface for TokenRelay: The Universal Cost Savings Agent.
"""

import argparse
import json
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from tokenopt.detector import run_system_audit, detect_installed_ides
from tokenopt.optimizer import optimize_prompt
from tokenopt.parity import get_parity_alternatives
from tokenopt.pricing import check_offpeak_status, load_pricing_matrix, calculate_cost
from tokenopt.receipts import format_receipt, get_session_summary, load_receipts_history
from tokenopt.sync import sync_all_ides, init_central_rules
from tokenopt.proxy import start_proxy
from tokenopt.server_mcp import run_mcp_server
from tokenopt.freetier import free_pool, get_claude_code_free_env
from tokenopt.profiler import build_and_save_developer_memory
from tokenopt.orchestrator import (
    update_ide_heartbeat,
    get_all_ide_heartbeats,
    query_domain_parity,
    trigger_cross_ide_handoff,
)
from tokenopt.dashboard import start_dashboard

COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def print_banner():
    banner = rf"""{COLOR_CYAN}{COLOR_BOLD}
  _____     _               ___        _   
 |_   _|___| |_____ _ _    / _ \ _ __ | |_ 
   | | / _ \ / / -_) ' \  | (_) | '_ \|  _|
   |_| \___/_\_\___|_||_|  \___/| .__/ \__|
                                |_|        
  Universal LLM & AI IDE Cost Savings Agent (v2.1.0)
{COLOR_RESET}"""
    print(banner)


def cmd_doctor(args):
    """Zero-touch environment audit."""
    print_banner()
    print(f"{COLOR_BOLD}=== RUNNING ZERO-TOUCH SYSTEM & IDE AUDIT ==={COLOR_RESET}\n")
    audit = run_system_audit()

    # 1. Detected IDEs
    print(f"{COLOR_BOLD}1. Detected AI IDEs & Coding Agents:{COLOR_RESET}")
    if audit["installed_ides"]:
        for ide in audit["installed_ides"]:
            print(f"  {COLOR_GREEN}✓{COLOR_RESET} {ide['name']:<24} (Path: {ide['detected_path']})")
    else:
        print(f"  {COLOR_YELLOW}!{COLOR_RESET} No standard IDE directories auto-detected in default locations.")

    # 2. Local LLM Runtimes
    print(f"\n{COLOR_BOLD}2. Local Runtimes ($0.00/token Autocomplete):{COLOR_RESET}")
    runtimes = audit["local_runtimes"]
    if runtimes["ollama_running"]:
        print(f"  {COLOR_GREEN}✓{COLOR_RESET} Ollama: Active on port 11434")
        if runtimes["ollama_models"]:
            print(f"    Models: {', '.join(runtimes['ollama_models'][:5])}")
    else:
        print(f"  {COLOR_YELLOW}!{COLOR_RESET} Ollama: Not detected on localhost:11434")

    # 3. API Keys
    print(f"\n{COLOR_BOLD}3. Provider API Keys in Environment:{COLOR_RESET}")
    keys = audit["api_keys"]
    for prov, active in keys.items():
        symbol = f"{COLOR_GREEN}✓ Active{COLOR_RESET}" if active else f"{COLOR_RED}✗ Not set{COLOR_RESET}"
        print(f"  {prov:<16}: {symbol}")

    # 4. Actionable Cost Recommendations
    print(f"\n{COLOR_BOLD}4. Cost Reduction Recommendations:{COLOR_RESET}")
    for rec in audit["recommendations"]:
        sev_color = COLOR_RED if rec["severity"] == "CRITICAL" else (COLOR_YELLOW if rec["severity"] == "HIGH" else COLOR_CYAN)
        print(f"  [{sev_color}{rec['severity']}{COLOR_RESET}] {rec['category']}")
        print(f"    Finding: {rec['finding']}")
        print(f"    Action : {rec['action']}\n")


def cmd_profile(args):
    """Deep project scan & developer skill assessment."""
    print_banner()
    print(f"{COLOR_BOLD}=== RUNNING DEEP SYSTEM & PROJECT SCAN ==={COLOR_RESET}\n")
    mem = build_and_save_developer_memory()
    prof = mem["developer_profile"]

    print(f"{COLOR_BOLD}Assessed Skill Tier:{COLOR_RESET}  {COLOR_GREEN}{COLOR_BOLD}{prof['assessed_skill_tier']}{COLOR_RESET}")
    print(f"{COLOR_BOLD}Repositories Found:{COLOR_RESET}   {prof['total_repositories_analyzed']}")
    print(f"{COLOR_BOLD}Languages Mastered:{COLOR_RESET}   {', '.join(prof['languages_mastered'])}")
    print(f"{COLOR_BOLD}Docker / Infra:{COLOR_RESET}       {prof['ci_cd_and_docker_adoption']}")
    print(f"{COLOR_BOLD}Automated Testing:{COLOR_RESET}    {prof['test_suite_coverage']}")
    print(f"\n{COLOR_BOLD}Tailored Model Recommendations:{COLOR_RESET}")
    print(f"  Reasoning / Architecture : {COLOR_CYAN}{prof['recommended_primary_reasoning_model']}{COLOR_RESET}")
    print(f"  Code Generation / Edits  : {COLOR_CYAN}{prof['recommended_editor_workhorse_model']}{COLOR_RESET}")
    print(f"\n{COLOR_BOLD}Strategy:{COLOR_RESET} {prof['tailored_cost_strategy']}")

    print(f"\n{COLOR_BOLD}Discovered Project Repositories (Sample):{COLOR_RESET}")
    for p in mem["discovered_projects"][:8]:
        langs = ", ".join(p["language_distribution"].keys()) or p["primary_language"]
        print(f"  - {p['name']:<24} [{langs}] -> {p['path']}")


def cmd_install(args):
    """Zero-touch one-click configuration for all detected IDEs."""
    print_banner()
    root = os.getcwd()
    print(f"{COLOR_BOLD}Running zero-touch setup in:{COLOR_RESET} {root}\n")

    # 1. Initialize central rules file
    central_path = init_central_rules(root)
    print(f"{COLOR_GREEN}✓{COLOR_RESET} Central rules initialized at: {central_path}")

    with open(central_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Sync to all IDEs
    res = sync_all_ides(root, content)
    for target in res["targets_synced"]:
        print(f"{COLOR_GREEN}✓{COLOR_RESET} Synced & stabilized: {os.path.relpath(target, root)}")

    print(f"\n{COLOR_BOLD}{COLOR_GREEN}All IDE configurations synced and cache-stabilized!{COLOR_RESET}")
    print(f"To connect your IDE to TokenRelay's MCP tools, add this to your MCP config:")
    print(f"""
{{
  "mcpServers": {{
    "tokenopt": {{
      "command": "python",
      "args": ["-m", "tokenopt.server_mcp"]
    }}
  }}
}}
""")


def cmd_sync(args):
    """Sync rules across all IDEs."""
    root = os.getcwd()
    central_path = init_central_rules(root)
    with open(central_path, "r", encoding="utf-8") as f:
        content = f.read()
    res = sync_all_ides(root, content)
    print(f"{COLOR_GREEN}✓{COLOR_RESET} {res['message']}")
    print(f"Token overhead per prompt turn: ~{res['token_overhead_per_turn']} tokens ({res['word_count']} words)")


def cmd_offpeak(args):
    """Check provider time-of-day off-peak discount windows."""
    print_banner()
    status = check_offpeak_status(args.provider)
    print(f"{COLOR_BOLD}Provider:{COLOR_RESET}         {status['provider']}")
    print(f"{COLOR_BOLD}Current UTC Time:{COLOR_RESET} {status.get('current_time_utc')}")
    if status.get("has_offpeak_schedule"):
        state_color = COLOR_GREEN if status["is_offpeak"] else COLOR_YELLOW
        state_label = "OFF-PEAK (50% DISCOUNT ACTIVE)" if status["is_offpeak"] else "PEAK HOURS ACTIVE"
        print(f"{COLOR_BOLD}Window Status:{COLOR_RESET}    {state_color}{state_label}{COLOR_RESET}")
        print(f"{COLOR_BOLD}Schedule:{COLOR_RESET}         {status.get('window_schedule')}")
        print(f"{COLOR_BOLD}Transition:{COLOR_RESET}       {status.get('countdown_message')}")
        if status.get("actionable_warning"):
            print(f"\n{COLOR_YELLOW}⚠ {status['actionable_warning']}{COLOR_RESET}")
    else:
        print(status["message"])


def cmd_route(args):
    """Query model parity alternatives."""
    print_banner()
    print(f"{COLOR_BOLD}Searching Equi-Capability Parity for:{COLOR_RESET} {args.model}\n")
    res = get_parity_alternatives(args.model, task_type=args.task_type)
    if "error" in res:
        print(f"{COLOR_RED}Error: {res['error']}{COLOR_RESET}")
        return

    print(f"Target Model:   {res['target_model']} ({res['target_provider']})")
    print(f"Quality Tier:   {res['target_tier']} (Score: {res['target_quality_score']}/100)")
    print(f"Benchmark Cost: ${res['target_benchmark_cost']:.4f} per 100k In / 10k Out\n")

    print(f"{'Alternative Model':<28} {'Provider':<18} {'Quality':<10} {'Cost':<10} {'Savings':<10}")
    print("-" * 80)
    for alt in res["recommended_parity_alternatives"]:
        print(
            f"{alt['model_id']:<28} {alt['provider']:<18} "
            f"{alt['quality_score']:>3}/100    "
            f"${alt['benchmark_cost_100k_10k']:>7.4f}  "
            f"{COLOR_GREEN}{alt['savings_pct']:>5.1f}%{COLOR_RESET}"
        )
        if alt.get("reasoning_warning"):
            print(f"  {COLOR_YELLOW}↳ Note: {alt['reasoning_warning']}{COLOR_RESET}")


def cmd_optimize(args):
    """Pre-send prompt optimization pass."""
    text = args.prompt
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    if not text:
        print(f"{COLOR_RED}Please provide --prompt or --file.{COLOR_RESET}")
        return

    res = optimize_prompt(text, enforce_diff_constraint=not args.no_diff)
    print(f"{COLOR_BOLD}=== PROMPT OPTIMIZATION REPORT ==={COLOR_RESET}")
    print(f"Initial Tokens:         {res['initial_tokens']}")
    print(f"Optimized Tokens:       {res['optimized_input_tokens']}")
    print(f"Input Tokens Saved:     {res['input_tokens_saved']}")
    print(f"Projected Out Saved:    {res['projected_output_tokens_saved']}")
    print(f"Cache Hit Eligible:     {res['prompt_cache_hit_eligible']}")
    if res["cache_busters_neutralized"]:
        print(f"Neutralized Busters:    {', '.join(res['cache_busters_neutralized'])}")
    print("\n--- OPTIMIZED PROMPT ---")
    print(res["optimized_prompt"])


def cmd_freetier(args):
    """Inspect and configure the Free-Tier Stacking Gateway."""
    print_banner()
    print(f"{COLOR_BOLD}=== FREE-TIER STACKING GATEWAY STATUS ==={COLOR_RESET}\n")
    report = free_pool.get_status_report()

    print(f"{'Provider / Model':<36} {'Status':<16} {'Daily Allocation':<20}")
    print("-" * 75)
    for b in report:
        st_color = COLOR_GREEN if b["status"] == "READY" else (COLOR_RED if b["status"] == "KEY_MISSING" else COLOR_YELLOW)
        print(f"{b['name']:<36} {st_color}{b['status']:<16}{COLOR_RESET} {b['notes'][:30]}")

    print(f"\n{COLOR_BOLD}How to Run Claude Code 100% FREE ($0.00):{COLOR_RESET}")
    print("1. Start the TokenRelay Gateway:")
    print("   python agent.py proxy")
    print("2. In your terminal session, set:")
    if sys.platform == "win32":
        print("   $env:ANTHROPIC_BASE_URL=\"http://127.0.0.1:8088\"")
        print("   $env:ANTHROPIC_API_KEY=\"tokenopt-free\"")
    else:
        print("   export ANTHROPIC_BASE_URL=\"http://127.0.0.1:8088\"")
        print("   export ANTHROPIC_API_KEY=\"tokenopt-free\"")
    print("3. Launch Claude Code:")
    print("   claude")
    print("\nTokenRelay will intercept Claude Code's Anthropic requests, translate them to free-tier Google Gemini or Groq, enforce diff constraints, and give you unlimited free agentic coding.")


def cmd_orchestrate(args):
    """Inspect and manage the Cross-IDE Heartbeat Bus & Orchestration."""
    print_banner()
    print(f"{COLOR_BOLD}=== CROSS-IDE ORCHESTRATION & HEARTBEAT BUS ==={COLOR_RESET}\n")

    # If domain parity query requested
    if args.domain:
        spec = query_domain_parity(args.domain)
        if "error" in spec:
            print(f"{COLOR_RED}{spec['error']}{COLOR_RESET}")
            return
        print(f"{COLOR_BOLD}Domain Task:{COLOR_RESET}     {spec['label']}")
        print(f"{COLOR_BOLD}Primary Model:{COLOR_RESET}   {spec['flagship']} (High Cost)\n")
        print(f"{'Equi-Capable Alternative':<28} {'Provider':<20} {'Quality Parity':<15} {'Specialty'}")
        print("-" * 88)
        for alt in spec["parity_alternatives"]:
            print(f"{alt['model']:<28} {alt['provider']:<20} {alt['quality_parity_pct']:>3}% parity      {alt['specialty']}")
        return

    # Otherwise show active heartbeats
    heartbeats = get_all_ide_heartbeats()
    if not heartbeats:
        print(f"{COLOR_YELLOW}! No active IDE heartbeats detected in .tokenopt/bus/{COLOR_RESET}")
        print("Connected IDEs (Cursor, Claude Code, Windsurf, Cline) report their live heartbeat automatically via MCP.")
        print("You can simulate an IDE heartbeat with: tokenopt heartbeat --ide cursor --project MyCar --model gpt-6-astra\n")
    else:
        print(f"{'IDE':<16} {'Active Model':<20} {'Project':<20} {'Status':<12} {'Tokens':<10}")
        print("-" * 80)
        for hb in heartbeats:
            st_color = COLOR_GREEN if hb.get("is_alive") else COLOR_RED
            st_text = "ACTIVE" if hb.get("is_alive") else "STALE"
            warn = f" {COLOR_RED}[CREDIT WARN]{COLOR_RESET}" if hb.get("credit_exhaustion_warning") else ""
            print(f"{hb['ide_id']:<16} {hb['active_model']:<20} {hb['active_project']:<20} {st_color}{st_text:<12}{COLOR_RESET} {hb['tokens_spent']:,}{warn}")


def cmd_receipts(args):
    """Show cumulative token savings and recent receipts."""
    print_banner()
    summary = get_session_summary()
    print(f"{COLOR_BOLD}=== CUMULATIVE DEVELOPER ROI SUMMARY ==={COLOR_RESET}\n")
    print(f"Total Runs Processed:      {summary['total_runs']}")
    print(f"Total Tokens Processed:    {summary['total_input_tokens']:,} In / {summary['total_output_tokens']:,} Out")
    print(f"Baseline Un-cached Spend:  ${summary['total_baseline_spend']:.2f}")
    print(f"Net Actual Spend:          ${summary['total_actual_spend']:.2f}")
    print(f"{COLOR_GREEN}{COLOR_BOLD}Total Dollars Saved:       ${summary['total_savings_usd']:.2f} ({summary['overall_savings_pct']:.1f}% Net ROI){COLOR_RESET}\n")

    history = load_receipts_history()
    if history:
        print(f"{COLOR_BOLD}Recent Runs (Last 5):{COLOR_RESET}")
        for r in history[-5:]:
            print(f"  [{r['timestamp']}] {r['provider']}/{r['model']}: Saved ${r['savings_usd']:.4f} ({r['savings_pct']}%)")


def cmd_compare(args):
    """Compare pricing across all providers."""
    print_banner()
    data = load_pricing_matrix()
    total_in = args.input_tokens * args.requests
    total_out = args.output_tokens * args.requests

    print(f"COST COMPARISON: {args.requests} requests x ({args.input_tokens:,} in / {args.output_tokens:,} out)")
    print(f"{'Provider':<20} {'Model':<26} {'Baseline':<12} {'Cached':<12} {'Batch (50%)':<12}")
    print("-" * 84)

    for prov_id, prov_spec in data.get("providers", {}).items():
        for m_id, m_spec in prov_spec.get("models", {}).items():
            cost = calculate_cost(m_id, total_in, total_out, cached_input_ratio=0.8)
            batch_cost = cost["actual_cost"] * 0.5
            print(
                f"{prov_spec['name'][:19]:<20} {m_id[:25]:<26} "
                f"${cost['baseline_cost']:>8.2f}    "
                f"${cost['actual_cost']:>8.2f}    "
                f"${batch_cost:>8.2f}"
            )


def main():
    parser = argparse.ArgumentParser(description="TokenRelay: Universal LLM & AI IDE Cost Savings Agent")
    subparsers = parser.add_subparsers(dest="command")

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Start interactive web dashboard on localhost:8085")
    p_dash.add_argument("--port", type=int, default=8085)
    p_dash.add_argument("--no-browser", action="store_true")

    # doctor
    subparsers.add_parser("doctor", help="Auto-audit installed IDEs, API keys, local runtimes, and blind spots")
    subparsers.add_parser("audit", help="Alias for doctor")

    # profile
    subparsers.add_parser("profile", help="Deep system scan of all project folders, active chats & developer skill profiling")

    # install
    subparsers.add_parser("install", help="Zero-touch configuration: sync rules and set up all IDEs")

    # sync
    subparsers.add_parser("sync", help="Compile and synchronize rules across all installed IDEs")

    # offpeak
    p_offpeak = subparsers.add_parser("offpeak", help="Check provider off-peak discount windows")
    p_offpeak.add_argument("--provider", type=str, default="deepseek", help="Provider ID (default: deepseek)")

    # route
    p_route = subparsers.add_parser("route", help="Find equi-capability parity alternatives")
    p_route.add_argument("model", type=str, help="Target model ID (e.g. gpt-6-astra, claude-3-7-sonnet)")
    p_route.add_argument("--task-type", type=str, default=None, choices=["reasoning_architect", "code_edit", "fast_workhorse"])

    # optimize
    p_opt = subparsers.add_parser("optimize", help="Optimize a prompt before dispatch")
    p_opt.add_argument("--prompt", type=str, default="", help="Prompt string")
    p_opt.add_argument("--file", type=str, default=None, help="Prompt file path")
    p_opt.add_argument("--no-diff", action="store_true", help="Do not enforce diff constraints")

    # receipts
    subparsers.add_parser("receipts", help="Display cumulative token savings and ROI receipts")

    # free-tier
    subparsers.add_parser("free-tier", help="Inspect and configure the Free-Tier Stacking Gateway for Claude Code/Cursor")

    # compare
    p_comp = subparsers.add_parser("compare", help="Compare pricing across all providers")
    p_comp.add_argument("--input-tokens", type=int, default=500000)
    p_comp.add_argument("--output-tokens", type=int, default=50000)
    p_comp.add_argument("--requests", type=int, default=10)

    # proxy
    p_proxy = subparsers.add_parser("proxy", help="Run local interceptor proxy daemon (localhost:8088)")
    p_proxy.add_argument("--port", type=int, default=8088)

    # mcp
    subparsers.add_parser("mcp", help="Run MCP stdio server for IDE integration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    elif args.command == "dashboard":
        start_dashboard(port=args.port, open_browser=not args.no_browser)
    elif args.command in ["doctor", "audit"]:
        cmd_doctor(args)
    elif args.command == "profile":
        cmd_profile(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "offpeak":
        cmd_offpeak(args)
    elif args.command == "route":
        cmd_route(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "free-tier":
        cmd_freetier(args)
    elif args.command == "receipts":
        cmd_receipts(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "proxy":
        start_proxy(args.port)
    elif args.command == "mcp":
        run_mcp_server()


if __name__ == "__main__":
    main()

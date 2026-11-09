"""
Model Context Protocol (MCP) Server for TokenRelay.
Enables AI IDEs (Cursor, Windsurf, Claude Code, Cline) to natively query
pricing, optimize prompts, check off-peak hours, and audit costs via stdio.
"""

import json
import sys
from typing import Any, Dict, List
from tokenopt.detector import run_system_audit
from tokenopt.optimizer import optimize_prompt
from tokenopt.parity import get_parity_alternatives
from tokenopt.pricing import check_offpeak_status, calculate_cost
from tokenopt.receipts import format_receipt, get_session_summary
from tokenopt.sync import sync_all_ides, init_central_rules
from tokenopt.profiler import build_and_save_developer_memory

TOOLS_DEFINITION = [
    {
        "name": "audit_environment",
        "description": "Scans host system for installed AI IDEs, local LLM runtimes (Ollama/LM Studio), API keys, and identifies token cost blind spots.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_root": {"type": "string", "description": "Workspace root directory (defaults to current dir)"}
            }
        }
    },
    {
        "name": "optimize_prompt_roi",
        "description": "Pre-send prompt sanitizer: strips cache-busting dynamic tokens (dates, UUIDs), removes conversational padding, and enforces diff-only outputs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The raw prompt or instructions to optimize"},
                "enforce_diff_constraint": {"type": "boolean", "description": "Force SEARCH/REPLACE blocks to prevent full file rewrites"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "check_offpeak_status",
        "description": "Checks if providers (e.g. DeepSeek) are in an off-peak 50% discount window and reports countdown until the next window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider_id": {"type": "string", "description": "Provider ID (e.g. 'deepseek')", "default": "deepseek"}
            }
        }
    },
    {
        "name": "route_model_by_parity",
        "description": "Finds functionally equivalent, cheaper alternatives for an expensive or credit-depleted model (e.g. falling back from GPT-6 Astra to DeepSeek R1).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_model": {"type": "string", "description": "Target model ID (e.g. 'gpt-6-astra', 'claude-3-7-sonnet')"},
                "task_type": {"type": "string", "description": "Task type ('reasoning_architect', 'code_edit', 'fast_workhorse')"}
            },
            "required": ["target_model"]
        }
    },
    {
        "name": "generate_savings_receipt",
        "description": "Generates a verifiable itemized digital receipt comparing baseline cost against cache hits and off-peak discounts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model used"},
                "input_tokens": {"type": "integer", "description": "Input token count"},
                "output_tokens": {"type": "integer", "description": "Output token count"},
                "cached_ratio": {"type": "number", "description": "Ratio of input tokens retrieved from cache (0.0 to 1.0)", "default": 0.8}
            },
            "required": ["model", "input_tokens", "output_tokens"]
        }
    },
    {
        "name": "sync_ide_rules",
        "description": "Compiles central rules from .tokenopt/rules.md into Cursor, Windsurf, Claude Code, Copilot, and Cline while stripping cache busters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_root": {"type": "string", "description": "Workspace root path"}
            }
        }
    },
    {
        "name": "get_developer_profile",
        "description": "Performs deep scan of local repositories, chat history, and identifies developer skill tier and optimal model toolchains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_root": {"type": "string", "description": "Workspace root directory (optional)"}
            }
        }
    }
]


def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Dispatch MCP tool execution."""
    if name == "audit_environment":
        root = arguments.get("workspace_root")
        return run_system_audit(root)

    elif name == "optimize_prompt_roi":
        prompt = arguments.get("prompt", "")
        enforce_diff = arguments.get("enforce_diff_constraint", True)
        return optimize_prompt(prompt, enforce_diff_constraint=enforce_diff)

    elif name == "check_offpeak_status":
        prov = arguments.get("provider_id", "deepseek")
        return check_offpeak_status(prov)

    elif name == "route_model_by_parity":
        target = arguments.get("target_model", "")
        task_type = arguments.get("task_type")
        return get_parity_alternatives(target, task_type=task_type)

    elif name == "generate_savings_receipt":
        model = arguments.get("model", "deepseek-v3")
        in_tok = arguments.get("input_tokens", 10000)
        out_tok = arguments.get("output_tokens", 1000)
        cached_ratio = arguments.get("cached_ratio", 0.8)
        cost_info = calculate_cost(model, in_tok, out_tok, cached_input_ratio=cached_ratio)
        receipt_text = format_receipt(
            model=model,
            provider=cost_info.get("provider", "LLM Provider"),
            input_tokens=in_tok,
            output_tokens=out_tok,
            baseline_cost=cost_info["baseline_cost"],
            actual_cost=cost_info["actual_cost"],
            cached_ratio=cached_ratio,
            is_offpeak=cost_info.get("is_offpeak_applied", False),
        )
        return {"receipt": receipt_text, "metrics": cost_info}

    elif name == "sync_ide_rules":
        root = arguments.get("workspace_root") or "."
        init_central_rules(root)
        rules_path = f"{root}/.tokenopt/rules.md"
        with open(rules_path, "r", encoding="utf-8") as f:
            content = f.read()
        return sync_all_ides(root, content)

    elif name == "get_developer_profile":
        root = arguments.get("workspace_root")
        return build_and_save_developer_memory(root)

    else:
        raise ValueError(f"Unknown tool: {name}")


def run_mcp_server():
    """Run JSON-RPC 2.0 stdio loop conforming to MCP protocol."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "tokenopt", "version": "2.1.0"}
                }
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_DEFINITION}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result_data = handle_call_tool(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result_data, indent=2)}
                        ]
                    }
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()

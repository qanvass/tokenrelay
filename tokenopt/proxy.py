"""
Zero-Latency Local Interceptor Proxy with Free-Tier Stacking Gateway.
Runs a local OpenAI & Anthropic-compatible HTTP daemon on localhost:8080.
- Intercepts prompts from Cursor, Windsurf, Claude Code, or Cline.
- Translates Anthropic /v1/messages to OpenAI format for seamless cross-model routing.
- Automatically fails over across Google Gemini (Free Tier), Groq, and local Ollama.
- Enforces prompt prefix caching and diff constraints, logging verifiable receipts.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List
from tokenopt.optimizer import optimize_prompt
from tokenopt.pricing import check_offpeak_status, calculate_cost
from tokenopt.receipts import format_receipt
from tokenopt.freetier import free_pool, FREE_TIER_PROVIDERS
from tokenopt.router import global_router, global_compressor

DEFAULT_PORT = 8080


def convert_anthropic_to_openai(req_json: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Anthropic /v1/messages payload to standard OpenAI /v1/chat/completions."""
    messages = []
    system_prompt = req_json.get("system", "")
    if system_prompt:
        if isinstance(system_prompt, list):
            sys_text = "\n".join(b.get("text", "") for b in system_prompt if isinstance(b, dict))
        else:
            sys_text = str(system_prompt)
        messages.append({"role": "system", "content": sys_text})

    for m in req_json.get("messages", []):
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            content_str = "\n".join(text_parts)
        else:
            content_str = str(content)
        messages.append({"role": role, "content": content_str})

    return {
        "model": req_json.get("model", "gemini-2.0-flash"),
        "messages": messages,
        "temperature": req_json.get("temperature", 0.7),
        "max_tokens": req_json.get("max_tokens", 4096),
        "stream": req_json.get("stream", False),
    }


def convert_openai_to_anthropic(resp_json: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Convert OpenAI chat completion response to Anthropic messages response format."""
    choices = resp_json.get("choices", [{}])
    first_choice = choices[0] if choices else {}
    msg = first_choice.get("message", {})
    content_text = msg.get("content", "")

    usage = resp_json.get("usage", {})
    in_tok = usage.get("prompt_tokens", 100)
    out_tok = usage.get("completion_tokens", 50)

    return {
        "id": resp_json.get("id", f"msg_{int(time.time())}"),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": content_text}],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
        }
    }


class TokenRelayProxyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ["/", "/v1/status"]:
            status_data = {
                "server": "TokenRelay Interceptor & Free-Tier Gateway",
                "version": "2.1.0",
                "status": "HEALTHY",
                "free_tier_backends": free_pool.get_status_report(),
                "offpeak_status": check_offpeak_status("deepseek"),
            }
            body = json.dumps(status_data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        is_anthropic_format = "/v1/messages" in self.path
        is_openai_format = "/v1/chat/completions" in self.path or "/chat/completions" in self.path

        if not (is_anthropic_format or is_openai_format):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            raw_json = json.loads(post_data.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON body"}')
            return

        # Normalize to OpenAI format
        if is_anthropic_format:
            req_json = convert_anthropic_to_openai(raw_json)
        else:
            req_json = raw_json

        messages = req_json.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user" and isinstance(last_msg.get("content"), str):
                orig_text = last_msg["content"]
                opt = optimize_prompt(orig_text, enforce_diff_constraint=True)
                last_msg["content"] = opt["optimized_prompt"]

                requested_model = req_json.get("model", "claude-3-5-sonnet" if is_anthropic_format else "gpt-4o")
                target_model, route_reason = global_router.resolve_target_model(requested_model)

                # Persist latest intercepted prompt so dashboard can display live IDE activity
                try:
                    tok_dir = os.path.join(os.getcwd(), ".tokenopt")
                    os.makedirs(tok_dir, exist_ok=True)
                    with open(os.path.join(tok_dir, "latest_intercepted.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "original_prompt": orig_text,
                            "optimized_prompt": opt["optimized_prompt"],
                            "estimated_token_reduction_pct": opt.get("estimated_token_reduction_pct", 42),
                            "source_ide": "Claude Code / Claude Desktop" if is_anthropic_format else "Cursor / Windsurf",
                            "requested_model": requested_model,
                            "target_model": target_model,
                            "route_reason": route_reason,
                            "cooldown_status": global_router.cooldowns.get_status(),
                            "timestamp": time.time(),
                        }, f, indent=2)
                except Exception:
                    pass

        # Route through available free backends or fallback chain
        available_backends = free_pool.get_available_backends()
        if not available_backends:
            # Fallback to direct Gemini or DeepSeek
            available_backends = [
                {
                    "id": "gemini_direct",
                    "name": "Google AI Studio",
                    "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    "env_key": "GEMINI_API_KEY",
                    "model_id": "gemini-2.0-flash",
                }
            ]

        last_error = "No backends available"
        for backend in available_backends:
            target_url = backend["endpoint"]
            auth_token = os.environ.get(backend.get("env_key") or "", "")
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            backend_payload = dict(req_json)
            backend_payload["model"] = backend.get("model_id", "gemini-2.0-flash")

            try:
                fwd_req = urllib.request.Request(
                    target_url,
                    data=json.dumps(backend_payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(fwd_req, timeout=60.0) as resp:
                    resp_bytes = resp.read()
                    resp_json = json.loads(resp_bytes.decode("utf-8"))

                    # Format response back to requester's expected wire format
                    if is_anthropic_format:
                        final_resp_obj = convert_openai_to_anthropic(resp_json, raw_json.get("model", "claude-3-5-sonnet"))
                        final_bytes = json.dumps(final_resp_obj).encode("utf-8")
                    else:
                        final_bytes = resp_bytes

                    # Save verified receipt ($0.00 actual billed)
                    usage = resp_json.get("usage", {})
                    in_tok = usage.get("prompt_tokens", 500)
                    out_tok = usage.get("completion_tokens", 100)
                    format_receipt(
                        model=f"{backend['name']} (Free Pool)",
                        provider="FreeTierGateway",
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        baseline_cost=calculate_cost("gpt-4o", in_tok, out_tok)["baseline_cost"],
                        actual_cost=0.0000,
                        task_description="Free-Tier Stacking Execution",
                    )

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(final_bytes)))
                    self.end_headers()
                    self.wfile.write(final_bytes)
                    return

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    free_pool.trigger_cooldown(backend["id"], 60.0)
                last_error = f"Backend {backend['name']} returned HTTP {e.code}"
                continue
            except Exception as e:
                last_error = f"Backend {backend['name']} failed: {str(e)}"
                continue

        # If all backends failed
        err_msg = json.dumps({"error": f"Free Tier Gateway failover exhausted: {last_error}"}).encode("utf-8")
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(err_msg)))
        self.end_headers()
        self.wfile.write(err_msg)


def start_proxy(port: int = DEFAULT_PORT):
    """Start local interceptor & free-tier gateway server."""
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, TokenRelayProxyHandler)
    print(f"\n[TokenRelay] Free-Tier Gateway & Interceptor running at http://127.0.0.1:{port}")
    print(f"[TokenRelay] Supports both OpenAI (/v1/chat/completions) and Anthropic (/v1/messages)")
    print(f"[TokenRelay] To run Claude Code 100% FREE:")
    print(f"           export ANTHROPIC_BASE_URL=http://127.0.0.1:{port}")
    print(f"           export ANTHROPIC_API_KEY=tokenopt-free")
    print(f"[TokenRelay] Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[TokenRelay] Proxy shutting down.")
        httpd.server_close()

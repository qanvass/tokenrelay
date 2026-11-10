#!/usr/bin/env python3
"""
TokenRelay Context Compressor CLI
Aider-inspired AST code signature compressor that condenses source code
repositories down to skeleton signatures, slashing context window tokens by 80%.
"""

import os
import sys
import ast
import re
import argparse
import json

def compress_python_code(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return compress_generic_regex(source)

    lines = []
    
    # Docstring of module
    doc = ast.get_docstring(tree)
    if doc:
        lines.append(f'"""{doc.strip()}"""\n')

    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            lines.append(f"import {', '.join(names)}")
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            lines.append(f"from {node.module or ''} import {', '.join(names)}")
        elif isinstance(node, ast.ClassDef):
            lines.append(f"\nclass {node.name}:")
            class_doc = ast.get_docstring(node)
            if class_doc:
                lines.append(f'    """{class_doc.strip()}"""')
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args]
                    prefix = "async def" if isinstance(item, ast.AsyncFunctionDef) else "def"
                    lines.append(f"    {prefix} {item.name}({', '.join(args)}): ...")
            if not any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) for item in node.body):
                lines.append("    ...")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            func_doc = ast.get_docstring(node)
            lines.append(f"\n{prefix} {node.name}({', '.join(args)}):")
            if func_doc:
                lines.append(f'    """{func_doc.strip()}"""')
            lines.append("    ...")

    return "\n".join(lines).strip()

def compress_generic_regex(source: str) -> str:
    # Retain function and class declarations in JS/TS/Go/Rust
    out = []
    for line in source.splitlines():
        trimmed = line.strip()
        if re.match(r"^(export\s+)?(function|class|interface|type|const\s+[A-Za-z0-9_]+\s*=|async\s+function|def|pub\s+fn|func)", trimmed):
            out.append(line)
        elif trimmed.startswith(("//", "/*", "*", "#")):
            out.append(line)
    return "\n".join(out) if out else source[:200]

def compress_file(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    orig_chars = len(content)
    orig_tokens = max(1, orig_chars // 4)
    
    if file_path.endswith(".py"):
        compressed = compress_python_code(content)
    else:
        compressed = compress_generic_regex(content)
        
    comp_chars = len(compressed)
    comp_tokens = max(1, comp_chars // 4)
    reduction = round(max(0.0, (1 - comp_tokens / orig_tokens) * 100), 1)

    return {
        "file": file_path,
        "original_tokens": orig_tokens,
        "compressed_tokens": comp_tokens,
        "reduction_pct": reduction,
        "compressed_content": compressed
    }

def main():
    parser = argparse.ArgumentParser(description="TokenRelay Context Compressor")
    parser.add_argument("path", help="Path to file or directory to compress")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path {args.path} does not exist.")
        sys.exit(1)

    results = []
    if os.path.isfile(args.path):
        results.append(compress_file(args.path))
    else:
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith((".py", ".ts", ".js", ".jsx", ".tsx")):
                    results.append(compress_file(os.path.join(root, file)))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        total_orig = sum(r["original_tokens"] for r in results)
        total_comp = sum(r["compressed_tokens"] for r in results)
        total_sav = round((1 - total_comp / max(1, total_orig)) * 100, 1)
        print(f"=== TokenRelay Context Compression Report ===")
        print(f"Files Processed:   {len(results)}")
        print(f"Original Tokens:   {total_orig:,}")
        print(f"Compressed Tokens: {total_comp:,}")
        print(f"Net Savings:       {total_sav}%\n")
        if len(results) == 1:
            print("--- AST Outline ---")
            print(results[0]["compressed_content"])

if __name__ == "__main__":
    main()

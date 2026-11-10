---
name: tokenrelay-context-compressor
description: Aider-inspired AST code signature compressor and immutable prefix stabilizer that compresses repository context by up to 80% without losing structural awareness.
version: 1.0.0
tools: [claude, cursor, codex, antigravity, cline]
---

# TokenRelay Context Compressor

Use this skill when loading large multi-file codebases into an agent context or generating repository maps.

## Compression Directives

1. **AST Signature Extraction:**
   - Parse Python, TypeScript, Go, Rust, or C++ source files.
   - Extract only:
     - Class definitions (`class ServiceManager:`)
     - Function & method signatures (`def process_order(id: str, amount: float) -> Receipt:`)
     - Decorators (`@router.post(...)`)
     - Exported types and interfaces (`interface UserSession { ... }`)
     - Module-level constants and top-level docstrings
   - Omit the internal implementation body lines unless actively targeted for modification.

2. **Immutable Prefix Stabilization:**
   - Always place static system directives and unchanging file skeletons at the head of the payload.
   - Separate with the TokenRelay boundary marker:
     ```
     [CACHEABLE_SYSTEM_BOUNDARY_V1]
     ```
   - Do NOT inject changing timestamps or request counts ahead of this boundary.
   - Preserves bit-for-bit cache validation, earning the **90% discount** on Anthropic and DeepSeek prompt caching.

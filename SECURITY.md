# Security Policy

The TokenRelay core team takes the security of our universal model routing and local proxy infrastructure seriously. Because TokenRelay intercepts developer prompts and communicates with upstream LLM providers, maintaining strict local privacy and credential isolation is our top priority.

## Supported Versions

We release patches and security fixes for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| 2.1.x   | :white_check_mark: |
| < 2.1.0 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in TokenRelay:

1. **Email Disclosure:** Send details to the maintainers at [security@tokenrelay.dev](mailto:security@tokenrelay.dev) or open a **GitHub Private Security Advisory** directly on the repository:
   👉 [https://github.com/qanvass/tokenrelay/security/advisories/new](https://github.com/qanvass/tokenrelay/security/advisories/new)
2. **Details to Include:**
   - Detailed description of the vulnerability and attack vector.
   - Proof-of-concept script, reproduction steps, or affected IDE environment.
   - Any potential impact on local API keys, session memory, or system isolation.
3. **Response Timeline:**
   - You will receive an acknowledgment within **24 hours**.
   - A triage update and targeted remediation timeline will follow within **72 hours**.
   - Coordinated public disclosure will take place once a patch is released and tested.

## Local Isolation & Credential Safety

TokenRelay is designed with strict local security guarantees:
* **No Telemetry Phone-Home:** TokenRelay does NOT collect, store, or transmit your raw code, prompts, or proprietary project assets to any central server.
* **Local Vault:** API keys configured via `.env` or the Control Center remain strictly local on `127.0.0.1`.
* **Zero Cloud Dependencies:** TokenRelay operates entirely with standard Python libraries and can run 100% offline via local Ollama.

# Contributing to TokenRelay

Thank you for your interest in contributing to **TokenRelay**! We welcome contributions to make local LLM routing, prompt optimization, and IDE cost controls even faster and more resilient.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/tokenrelay.git
   cd tokenrelay
   ```
2. Verify standard tests:
   ```bash
   python -m unittest discover -s tests
   ```
3. Run the local development dashboard:
   ```bash
   python agent.py dashboard
   ```

## Contribution Principles
* **Zero External Dependencies:** TokenRelay's core daemon and MCP server must rely exclusively on the Python standard library.
* **Preserve User Privacy:** Never send local file contents or unoptimized prompts to unapproved third-party servers.
* **Test Coverage:** Every new router rule, parser, or provider integration must include unit tests under `tests/`.

## Code Style
* Follow PEP 8 style guidelines.
* Ensure type hints and docstrings are included for public functions.

## Submitting Pull Requests
1. Fork the repo and create your feature branch: `git checkout -b feature/amazing-feature`
2. Commit your changes: `git commit -m 'feat: Add support for local vLLM endpoint'`
3. Push to your branch: `git push origin feature/amazing-feature`
4. Open a Pull Request on GitHub.

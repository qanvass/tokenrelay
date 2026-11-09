#!/usr/bin/env python3
"""
TokenRelay: Universal Cost Savings Agent Entry Point.
Can be executed directly:
    python agent.py doctor
    python agent.py install
    python agent.py sync
    python agent.py offpeak
    python agent.py route gpt-6-astra
    python agent.py receipts
"""

import sys
from tokenopt.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default zero-touch action if run without arguments: run doctor & audit
        sys.argv.append("doctor")
    main()

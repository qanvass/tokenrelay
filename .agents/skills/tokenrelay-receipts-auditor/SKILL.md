---
name: tokenrelay-receipts-auditor
description: Real-time token accounting, off-peak discount detection, and verifiable cryptographic receipts tracking cumulative developer ROI and cloud savings.
version: 1.0.0
tools: [claude, cursor, codex, antigravity, cline]
---

# TokenRelay Receipts Auditor

Use this skill to inspect token usage, calculate net cash savings across model shifts, detect off-peak provider discounts, and export accounting ledgers.

## Receipt Schema & Ledgers

Every request intercepted by TokenRelay generates an itemized JSON receipt stored locally at `.tokenopt/receipts.json`:

```json
{
  "receipt_id": "rcpt_1794250938",
  "timestamp_utc": "2026-11-10T06:40:00Z",
  "client_ide": "Claude Desktop",
  "requested_model": "claude-fable-5-1",
  "routed_model": "deepseek-r1",
  "gross_cost_usd": 0.060,
  "net_billed_usd": 0.00055,
  "savings_usd": 0.05945,
  "savings_pct": 98.2,
  "is_offpeak": false
}
```

## Off-Peak Detection Rules

* **DeepSeek Off-Peak Window:** 16:30 UTC to 00:30 UTC (00:30 to 08:30 Beijing Time).
* Applies an automatic **50% discount** on all API tokens.
* When active, prompts are tagged with `[OFFPEAK_OPTIMIZED]` in the dashboard ledger.

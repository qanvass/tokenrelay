"""
Unit and integration tests for TokenOpt.
"""

import os
import shutil
import tempfile
import unittest
from tokenopt.detector import run_system_audit, detect_api_keys
from tokenopt.pricing import check_offpeak_status, calculate_cost
from tokenopt.parity import get_parity_alternatives
from tokenopt.optimizer import optimize_prompt, sanitize_cache_busters
from tokenopt.receipts import format_receipt, get_session_summary
from tokenopt.sync import sync_all_ides, DEFAULT_CORE_RULES


class TestTokenOpt(unittest.TestCase):

    def test_detector_audit(self):
        audit = run_system_audit()
        self.assertIn("installed_ides", audit)
        self.assertIn("local_runtimes", audit)
        self.assertIn("api_keys", audit)
        self.assertIn("recommendations", audit)

    def test_offpeak_status(self):
        status = check_offpeak_status("deepseek")
        self.assertTrue(status["has_offpeak_schedule"])
        self.assertIn("countdown_message", status)
        self.assertEqual(status["provider"], "DeepSeek")

    def test_calculate_cost(self):
        cost = calculate_cost("deepseek-v3", 100_000, 10_000, cached_input_ratio=0.8)
        self.assertGreater(cost["baseline_cost"], 0)
        self.assertGreater(cost["actual_cost"], 0)
        self.assertGreaterEqual(cost["baseline_cost"], cost["actual_cost"])
        self.assertIn("savings_pct", cost)

    def test_parity_router(self):
        parity = get_parity_alternatives("gpt-6-astra")
        self.assertIn("recommended_parity_alternatives", parity)
        self.assertGreater(len(parity["recommended_parity_alternatives"]), 0)
        top = parity["recommended_parity_alternatives"][0]
        self.assertGreater(top["savings_pct"], 0)

    def test_prompt_optimizer_sanitizer(self):
        dirty_prompt = (
            "Please make sure to help me with this. "
            "Session ID: abc-1234-xyz. Commit 0123456789abcdef0123456789abcdef01234567. "
            "Timestamp 2026-11-09T11:24:25Z. Refactor this python class."
        )
        opt = optimize_prompt(dirty_prompt, enforce_diff_constraint=True)
        self.assertNotIn("2026-11-09T11:24:25Z", opt["optimized_prompt"])
        self.assertNotIn("Please make sure to", opt["optimized_prompt"])
        self.assertIn("[TOKEN_ROI_DIRECTIVE]", opt["optimized_prompt"])
        self.assertGreater(opt["projected_output_tokens_saved"], 0)

    def test_receipts_engine(self):
        receipt_text = format_receipt(
            model="deepseek-v3",
            provider="DeepSeek",
            input_tokens=50_000,
            output_tokens=2_000,
            baseline_cost=0.015,
            actual_cost=0.003,
            cached_ratio=0.8,
            is_offpeak=True,
            task_description="Unit Test Execution",
        )
        self.assertIn("TOKEN SAVINGS RECEIPT", receipt_text)
        self.assertIn("NET SAVINGS THIS RUN", receipt_text)

        summary = get_session_summary()
        self.assertGreaterEqual(summary["total_runs"], 1)

    def test_cross_ide_sync(self):
        temp_dir = tempfile.mkdtemp()
        try:
            res = sync_all_ides(temp_dir, DEFAULT_CORE_RULES)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".windsurfrules")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "CLAUDE.md")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".cursor", "rules", "tokenopt.mdc")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".github", "copilot-instructions.md")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".clinerules")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".aider.conf.yml")))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


    def test_free_tier_pool(self):
        from tokenopt.freetier import free_pool
        report = free_pool.get_status_report()
        self.assertGreaterEqual(len(report), 3)
        # Ollama local is always ready without an API key
        ollama_item = next(item for item in report if item["id"] == "ollama_local")
        self.assertEqual(ollama_item["status"], "READY")


    def test_developer_profiler(self):
        from tokenopt.profiler import scan_local_projects, evaluate_developer_profile
        projects = scan_local_projects()
        self.assertIsInstance(projects, list)
        profile = evaluate_developer_profile(projects, [])
        self.assertIn("assessed_skill_tier", profile)
        self.assertIn("recommended_primary_reasoning_model", profile)


    def test_dashboard_handler(self):
        from tokenopt.dashboard import DashboardHTTPHandler
        self.assertTrue(hasattr(DashboardHTTPHandler, 'do_GET'))
        self.assertTrue(hasattr(DashboardHTTPHandler, 'do_POST'))


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for TokenRelay Resilient Router and Aider Context Compressor.
"""

import unittest
from tokenopt.router import ResilientRouter, ProviderCooldownTracker, AiderContextOptimizer


class TestResilientRouter(unittest.TestCase):

    def test_provider_cooldown_trigger(self):
        tracker = ProviderCooldownTracker(cooldown_duration_sec=30, max_consecutive_fails=2)
        self.assertTrue(tracker.is_available("claude-opus-4-8"))
        
        # Test quota limit error instant cooldown
        tracker.record_failure("claude-opus-4-8", "Rate limit 429 quota exceeded")
        self.assertFalse(tracker.is_available("claude-opus-4-8"))
        
        # Test success clears
        tracker.record_success("claude-opus-4-8")
        self.assertTrue(tracker.is_available("claude-opus-4-8"))

    def test_fallback_cascade_resolution(self):
        router = ResilientRouter()
        
        # High cost model routes to parity
        model, reason = router.resolve_target_model("claude-opus-4-8")
        self.assertEqual(model, "deepseek-r1")
        self.assertIn("Parity routing", reason)

        # Standard cheap model routes directly
        model2, reason2 = router.resolve_target_model("deepseek-v3")
        self.assertEqual(model2, "deepseek-v3")

    def test_aider_context_compressor(self):
        code = '''
import os
import sys

class DatabaseManager:
    """Manages connections."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_sqlite()

    def query_records(self, query: str):
        # 50 lines of complex logic
        x = 1 + 2
        y = x * 3
        return y
'''
        compressed, saved = AiderContextOptimizer.compress_code_context(code)
        self.assertGreater(saved, 0)
        self.assertIn("class DatabaseManager:", compressed)
        self.assertIn("def query_records", compressed)
        self.assertNotIn("y = x * 3", compressed)

    def test_cache_prefix_stabilization(self):
        sys_prompt = "You are a coding assistant."
        files = ["main.py", "utils.py"]
        pinned = AiderContextOptimizer.stabilize_cache_prefix(sys_prompt, files)
        self.assertTrue(pinned.startswith("[CACHEABLE_SYSTEM_BOUNDARY_V1]"))
        self.assertIn("[FILE_SNAPSHOT]: main.py", pinned)


if __name__ == "__main__":
    unittest.main()

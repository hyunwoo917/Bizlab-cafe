"""Catch app/model API mismatches before deploying."""
import ast
from pathlib import Path
import inspect
import unittest
from model_v05 import simulate

class IntegrationTests(unittest.TestCase):
    def test_owner_toggle_supported_by_simulate(self):
        signature = inspect.signature(simulate)
        self.assertIn("include_owner_labor", signature.parameters)
        self.assertTrue(signature.parameters["include_owner_labor"].kind == inspect.Parameter.KEYWORD_ONLY)

    def test_app_calls_supported_simulate_keywords(self):
        tree = ast.parse(Path(__file__).with_name("app.py").read_text(encoding="utf-8"))
        allowed = set(inspect.signature(simulate).parameters)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "simulate":
                self.assertTrue(set(k.arg for k in node.keywords if k.arg) <= allowed)

    def test_reclassification_keywords_supported(self):
        params = inspect.signature(simulate).parameters
        self.assertIn("other_variable_share_pct", params)
        self.assertIn("reference_sales_manwon", params)

    def test_end_to_end_owner_toggle(self):
        costs = {"staff_labor":100, "rent":100, "taxes":10, "owner_labor":200, "other":50}
        with_owner = simulate(50, 6500, 30, 38.9, costs, include_owner_labor=True)
        without_owner = simulate(50, 6500, 30, 38.9, costs, include_owner_labor=False)
        self.assertAlmostEqual(without_owner.profit_won - with_owner.profit_won, 2_000_000)
        self.assertLess(without_owner.break_even_customers, with_owner.break_even_customers)

if __name__ == "__main__": unittest.main()

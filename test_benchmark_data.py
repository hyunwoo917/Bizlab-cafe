"""Consistency checks for manually reviewed official statistics."""
import unittest
from benchmark_data import load_benchmark, load_source_register, validate_benchmark

class BenchmarkRegistryTests(unittest.TestCase):
    def test_benchmark_transcription_is_internally_consistent(self):
        self.assertTrue(validate_benchmark(load_benchmark()))

    def test_all_segments_share_year_and_scope(self):
        data = load_benchmark()
        self.assertEqual(data["industry_code"], "5622")
        self.assertEqual(data["reference_year"], 2024)
        self.assertEqual(data["segments"]["all"]["sample_n"], 352)
        self.assertEqual(data["segments"]["all"]["annual_sales_manwon"], 19033)
        self.assertEqual(data["segments"]["all"]["costs"]["food"]["pct"], 38.9)

    def test_usable_register_has_reasons_and_limits(self):
        sources = load_source_register()["sources"]
        self.assertEqual(len({s["id"] for s in sources}), len(sources))
        for source in sources:
            for field in ["name", "metric_scope", "rationale", "limitations", "state", "url", "refresh"]:
                self.assertTrue(source[field])
            self.assertIn(source["state"], ("approved", "reference_only", "pending"))

if __name__ == "__main__":
    unittest.main()

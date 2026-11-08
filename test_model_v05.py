"""Regression tests: official-source defaults, editability, expense conservation."""
import unittest
from benchmark_data import load_benchmark, validate_benchmark
from model_v05 import COST_KEYS, benchmark_monthly, comparison, recommended_inputs, simulate


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_benchmark()
        validate_benchmark(cls.data)

    def test_recommend_all_segments_and_staff_merge(self):
        for segment in self.data["segments"].values():
            inputs = recommended_inputs(segment)
            expected_staff = (segment["costs"]["hired_labor"]["manwon"] + segment["costs"]["family_labor"]["manwon"]) / 12
            self.assertAlmostEqual(inputs["staff_labor"], expected_staff, delta=.0051)
            self.assertEqual(inputs["other_variable_share_pct"], 0)
            self.assertEqual(set(COST_KEYS), {k for k in inputs if k in COST_KEYS})
            self.assertLessEqual(abs(inputs["customers"] * 6500 * 30 - segment["annual_sales_manwon"] * 10000 / 12), 97501)

    def test_original_model_preserved_at_zero_reclassification(self):
        for segment in self.data["segments"].values():
            p = recommended_inputs(segment)
            costs = {k: p[k] for k in COST_KEYS}
            sim = simulate(p["customers"], p["ticket"], p["days"], p["food_pct"], costs,
                           reference_sales_manwon=segment["annual_sales_manwon"] / 12)
            self.assertAlmostEqual(sim.total_variable_pct, p["food_pct"])
            self.assertLess(abs(sim.profit_won / 10000 - benchmark_monthly(segment)["profit"]), 22)

    def test_reclassification_conserves_cost_at_reference_sales(self):
        seg = self.data["segments"]["independent"]
        p = recommended_inputs(seg)
        costs = {k: p[k] for k in COST_KEYS}
        ref = seg["annual_sales_manwon"] / 12
        # Choose revenue exactly equal to the benchmark monthly sales
        # by using an integer ticket in KRW and 1 transaction/day.
        ticket = seg["annual_sales_manwon"] * 10000 // 12
        base = simulate(1, ticket, 1, p["food_pct"], costs, reference_sales_manwon=ref)
        moved = simulate(1, ticket, 1, p["food_pct"], costs,
                         other_variable_share_pct=40, reference_sales_manwon=ref)
        self.assertAlmostEqual(base.profit_won, moved.profit_won, delta=5)
        self.assertAlmostEqual(base.fixed_won - moved.fixed_won, costs["other"] * .4 * 10000)
        self.assertAlmostEqual(moved.variable_won - base.variable_won, costs["other"] * .4 * 10000, delta=5)

    def test_reclassification_changes_sensitivity_not_new_cost(self):
        costs = {"staff_labor":100, "rent":100, "taxes":50, "owner_labor":100, "other":100}
        base = simulate(0, 6500, 30, 35, costs, reference_sales_manwon=1000)
        moved = simulate(0, 6500, 30, 35, costs, other_variable_share_pct=50,
                         reference_sales_manwon=1000)
        self.assertEqual(moved.variable_won, 0)
        self.assertAlmostEqual(moved.fixed_won, base.fixed_won - 500000)
        high = simulate(100, 6500, 30, 35, costs, other_variable_share_pct=50,
                        reference_sales_manwon=1000)
        self.assertGreater(high.variable_won, high.food_won)
        self.assertGreater(high.total_variable_pct, 35)

    def test_owner_toggle(self):
        costs = {k:50 for k in COST_KEYS}
        a = simulate(60,6500,30,35,costs,include_owner_labor=True,other_variable_share_pct=25,reference_sales_manwon=1000)
        b = simulate(60,6500,30,35,costs,include_owner_labor=False,other_variable_share_pct=25,reference_sales_manwon=1000)
        self.assertAlmostEqual(b.profit_won-a.profit_won, 500000)
        self.assertLessEqual(b.break_even_customers,a.break_even_customers)
        self.assertEqual(b.cost_won["owner_labor"],0)

    def test_input_validation(self):
        costs = {k:0 for k in COST_KEYS}
        with self.assertRaises(ValueError):
            simulate(10,6500,30,35,costs,other_variable_share_pct=10)
        with self.assertRaises(ValueError):
            simulate(10,6500,30,35,costs,other_variable_share_pct=101,reference_sales_manwon=100)
        with self.assertRaises(ValueError):
            simulate(10,0,30,35,costs)
        with self.assertRaises(ValueError):
            simulate(10,6500,30,35,{**costs,"unknown":0})

    def test_zero_sales_and_no_contribution(self):
        costs = {k:0 for k in COST_KEYS}
        self.assertIsNone(simulate(0,6500,30,35,costs).margin_pct)
        self.assertEqual(simulate(0,6500,30,35,costs).break_even_customers,0)
        self.assertIsNone(simulate(10,6500,30,100,{**costs,"rent":10}).break_even_customers)

    def test_comparison(self):
        s=self.data['segments']['all']; p=recommended_inputs(s)
        r=simulate(p['customers'],6500,30,p['food_pct'],{k:p[k] for k in COST_KEYS})
        self.assertAlmostEqual(comparison(r,s)['sales_diff_manwon'],r.revenue_won/10000-s['annual_sales_manwon']/12)

if __name__=='__main__': unittest.main()

"""Regression tests for statistical defaults and calculation transparency."""
import unittest
from benchmark_data import load_benchmark,validate_benchmark
from model_v05 import COST_KEYS,benchmark_monthly,comparison,recommended_inputs,simulate

class TestModel(unittest.TestCase):
    def setUp(self):
        self.data=load_benchmark()
        validate_benchmark(self.data)
    def test_recommend_all_segments(self):
        for s in self.data['segments'].values():
            p=recommended_inputs(s)
            self.assertEqual(p['food_pct'],s['costs']['food']['pct'])
            for k in COST_KEYS:
                self.assertAlmostEqual(p[k],round(s['costs'][k]['manwon']/12,1))
            self.assertLessEqual(abs(p['customers']*6500*30-s['annual_sales_manwon']*10000/12),6500*30/2+1)
    def test_standard_benchmark_at_exact_sales(self):
        for s in self.data['segments'].values():
            p=recommended_inputs(s)
            costs={k:p[k] for k in COST_KEYS}
            model=simulate(p['customers'],p['ticket'],p['days'],p['food_pct'],costs)
            avg=benchmark_monthly(s)
            self.assertLess(abs(model.profit_won/10000-avg['profit']),20)
    def test_customizable_food_and_fixed_cost(self):
        s=self.data['segments']['independent']
        p=recommended_inputs(s)
        costs={k:p[k] for k in COST_KEYS}
        base=simulate(100,6500,30,p['food_pct'],costs)
        higher=simulate(100,6500,30,p['food_pct']+10,costs)
        self.assertAlmostEqual(base.profit_won-higher.profit_won,base.revenue_won*.10)
        costs['rent']+=100
        raised=simulate(100,6500,30,p['food_pct'],costs)
        self.assertAlmostEqual(base.profit_won-raised.profit_won,1_000_000)
    def test_zero_and_no_contribution(self):
        costs={k:0 for k in COST_KEYS}
        r=simulate(0,6500,30,35,costs)
        self.assertIsNone(r.margin_pct)
        self.assertEqual(r.break_even_customers,0)
        r=simulate(10,6500,30,100,costs)
        self.assertIsNone(r.break_even_customers)
    def test_comparison(self):
        s=self.data['segments']['all'];p=recommended_inputs(s)
        model=simulate(p['customers'],6500,30,p['food_pct'],{k:p[k] for k in COST_KEYS})
        d=comparison(model,s)
        self.assertAlmostEqual(d['sales_diff_manwon'],model.revenue_won/10000-s['annual_sales_manwon']/12)

if __name__=='__main__': unittest.main()

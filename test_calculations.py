import unittest
from calculations import calculate


class TestBizLab(unittest.TestCase):
    def test_default(self):
        r = calculate(80, 6500, 30, 35, 9_000_000)
        self.assertEqual(r.revenue, 15_600_000)
        self.assertEqual(r.variable_cost, 5_460_000)
        self.assertEqual(r.operating_profit, 1_140_000)
        self.assertEqual(r.break_even_daily_customers, 72)
        self.assertAlmostEqual(r.operating_margin_pct, 1_140_000/15_600_000*100)

    def test_exact_breakeven(self):
        r = calculate(10, 10000, 20, 50, 1_000_000)
        self.assertEqual(r.operating_profit, 0)
        self.assertEqual(r.break_even_daily_customers, 10)

    def test_zero_ticket_and_full_variable_cost(self):
        self.assertIsNone(calculate(100, 0, 30, 35, 9000000).break_even_daily_customers)
        self.assertIsNone(calculate(100, 6500, 30, 100, 9000000).break_even_daily_customers)

    def test_no_revenue(self):
        self.assertIsNone(calculate(0, 6500, 30, 35, 9000000).operating_margin_pct)

    def test_negative_invalid(self):
        with self.assertRaises(ValueError):
            calculate(-1, 6500, 30, 35, 9000000)


if __name__ == "__main__":
    unittest.main()

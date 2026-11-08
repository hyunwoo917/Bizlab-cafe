import math
import unittest
from investment_model import (INVESTMENT_LABELS,validate_investment,debt_schedule,
    monthly_discount_rate,npv,payback,project_cashflows)


def items(**kwargs):
    x={k:0.0 for k in INVESTMENT_LABELS};x.update(kwargs);return x

class TestCapital(unittest.TestCase):
    def test_total_includes_deposit_wc(self):
        self.assertEqual(validate_investment(items(deposit=200,working_capital=300,interior=500)),1000)
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):validate_investment(items(deposit=-1))
    def test_zero_interest_annuity(self):
        payments=debt_schedule(1200,0,12)
        self.assertAlmostEqual(sum(x['principal_paid'] for x in payments),1200)
        self.assertAlmostEqual(payments[0]['payment'],100)
    def test_amortization_both(self):
        for typ in ('annuity','equal_principal'):
            rows=debt_schedule(3000,6,60,typ)
            self.assertAlmostEqual(sum(x['principal_paid'] for x in rows),3000,places=7)
            self.assertAlmostEqual(rows[-1]['balance'],0,places=7)
            self.assertGreater(sum(x['interest'] for x in rows),0)
        self.assertAlmostEqual(debt_schedule(3000,6,60,'equal_principal')[0]['principal_paid'],50)
    def test_pbp_month_end(self):
        self.assertEqual(payback(100,[25]*12),4)
        self.assertIsNone(payback(100,[-2]*12))
        self.assertIsNone(payback(100,[1]*12))
        self.assertEqual(payback(0,[0]*10),0)
    def test_discount_zero_equivalent(self):
        self.assertEqual(payback(100,[10]*12,0),payback(100,[10]*12))
        self.assertAlmostEqual(npv(100,[10]*12,0),20)
        self.assertAlmostEqual(monthly_discount_rate(0),0)
    def test_positive_discount_pushes_pbp(self):
        self.assertGreaterEqual(payback(100,[10]*24,8),payback(100,[10]*24,0))
    def test_no_loan_and_loan_identity(self):
        base=project_cashflows(items(interior=6000),200,horizon_months=60)
        self.assertEqual(base.business_pbp,30)
        self.assertEqual(base.equity_pbp,30)
        self.assertAlmostEqual(base.business_npv,base.equity_npv,delta=2000) # different discount rates
        financed=project_cashflows(items(interior=6000),200,loan_manwon=3000,
                                    loan_rate_pct=5,loan_months=60,horizon_months=60)
        self.assertEqual(financed.total_capital,6000)
        self.assertEqual(financed.equity_capital,3000)
        self.assertAlmostEqual(financed.rows[0]['business_cf']-financed.rows[0]['equity_cf'],
                               financed.rows[0]['loan_payment'])
        self.assertAlmostEqual(financed.business_npv,base.business_npv)
    def test_deposit_event_only_when_selected(self):
        gross=items(deposit=1000,interior=2000)
        none=project_cashflows(gross,0,horizon_months=60)
        refund=project_cashflows(gross,0,horizon_months=60,deposit_return_month=36,deposit_return_pct=80)
        self.assertAlmostEqual(refund.rows[35]['deposit_return'],800)
        self.assertAlmostEqual(none.rows[35]['deposit_return'],0)
        self.assertAlmostEqual(refund.rows[34]['business_cf'],0)
        self.assertAlmostEqual(refund.rows[35]['business_cf'],800)
    def test_extras_no_double_count(self):
        r=project_cashflows(items(interior=1000,working_capital=200),100,horizon_months=12,
                working_capital_return_month=12,one_time_capex_month=6,
                one_time_capex_amount=50,monthly_maintenance_capex=10)
        self.assertAlmostEqual(r.rows[5]['business_cf'],40)
        self.assertAlmostEqual(r.rows[-1]['business_cf'],290)
    def test_balance_at_horizon(self):
        r=project_cashflows(items(interior=10000),100,loan_manwon=3000,
                            loan_rate_pct=5,loan_months=120,horizon_months=60)
        self.assertGreater(r.balance_at_horizon,0)
    def test_loan_larger_than_capital_rejected(self):
        with self.assertRaises(ValueError):project_cashflows(items(interior=100),10,loan_manwon=101)
    def test_bad_event_rejected(self):
        with self.assertRaises(ValueError):project_cashflows(items(interior=100),10,deposit_return_month=61)
    def test_zero_flow_horizon_not_recovered(self):
        r=project_cashflows(items(interior=500),0,horizon_months=60)
        self.assertIsNone(r.business_pbp)

if __name__=='__main__':unittest.main()

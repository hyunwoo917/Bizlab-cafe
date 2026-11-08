"""BizLab v0.8: explicit unlevered / equity monthly cash flow model.

Amounts are KRW 10,000 (만원); effective annual discount rates; month-end flows.
A forecast is not a tax calculation. No terminal sale value or deposit refund is assumed.
"""
from dataclasses import dataclass
from math import isfinite

INVESTMENT_LABELS = {
    'deposit': '임대보증금 (환급 가능성 별도)',
    'premium': '권리금',
    'interior': '인테리어·시설 공사',
    'equipment': '설비·비품',
    'franchise_fee': '가맹비·교육비',
    'inventory': '초도 재고·오픈 준비',
    'opening_other': '마케팅·인허가·기타 초기비',
    'working_capital': '초기 운영자금',
}


def validate_investment(items: dict) -> float:
    if set(items) != set(INVESTMENT_LABELS):
        raise ValueError('Missing/unknown investment category')
    if any(not isfinite(float(v)) or v < 0 for v in items.values()):
        raise ValueError('Investment cannot be negative/non-finite')
    return sum(float(v) for v in items.values())


def debt_schedule(principal: float, annual_rate_pct: float, term_months: int,
                  method: str = 'annuity') -> list[dict]:
    if principal < 0 or not isfinite(principal) or not 0 <= annual_rate_pct <= 100 or not 1 <= term_months <= 600:
        raise ValueError('Invalid loan terms')
    if method not in {'annuity', 'equal_principal'}:
        raise ValueError('Unsupported repayment method')
    if principal == 0:
        return []
    rate = annual_rate_pct / 1200  # nominal annual loan interest rate /12
    payment = principal / term_months if rate == 0 else principal * rate / (1-(1+rate)**(-term_months))
    outstanding = principal
    result = []
    for month in range(1, term_months+1):
        interest = outstanding * rate
        paid_principal = (payment - interest if method == 'annuity' else principal / term_months)
        if month == term_months:
            paid_principal = outstanding
        paid_principal = min(outstanding, max(0, paid_principal))
        outstanding = max(0, outstanding-paid_principal)
        result.append({'month': month, 'interest': interest,
                       'principal_paid': paid_principal, 'payment': paid_principal + interest,
                       'balance': outstanding})
    return result


def monthly_discount_rate(effective_annual_rate_pct: float) -> float:
    if not isfinite(effective_annual_rate_pct) or effective_annual_rate_pct <= -100 or effective_annual_rate_pct > 100:
        raise ValueError('Discount rate out of range')
    return (1 + effective_annual_rate_pct / 100) ** (1/12) - 1


def npv(initial_outflow: float, flows: list[float], annual_rate_pct: float) -> float:
    r = monthly_discount_rate(annual_rate_pct)
    return -initial_outflow + sum(value / (1+r)**i for i, value in enumerate(flows, 1))


def payback(initial_outflow: float, flows: list[float], annual_rate_pct: float = 0) -> int | None:
    if initial_outflow <= 0:
        return 0
    r = monthly_discount_rate(annual_rate_pct)
    cumulative = -initial_outflow
    for month, flow in enumerate(flows, 1):
        cumulative += flow / ((1+r)**month)
        if cumulative >= -1e-9:
            return month
    return None


@dataclass(frozen=True)
class InvestmentResult:
    total_capital: float
    equity_capital: float
    business_pbp: int | None
    business_discounted_pbp: int | None
    business_npv: float
    equity_pbp: int | None
    equity_discounted_pbp: int | None
    equity_npv: float
    rows: list[dict]
    balance_at_horizon: float


def project_cashflows(items: dict, operating_cash_manwon: float, *,
                      loan_manwon: float = 0, loan_rate_pct: float = 0,
                      loan_months: int = 60, loan_method: str = 'annuity',
                      horizon_months: int = 60,
                      project_discount_pct: float = 8,
                      equity_discount_pct: float = 10,
                      deposit_return_month: int = 0,
                      deposit_return_pct: float = 100,
                      working_capital_return_month: int = 0,
                      working_capital_return_pct: float = 100,
                      monthly_maintenance_capex: float = 0,
                      one_time_capex_month: int = 0,
                      one_time_capex_amount: float = 0) -> InvestmentResult:
    capital = validate_investment(items)
    if not isfinite(operating_cash_manwon):
        raise ValueError('Operating cash not finite')
    if not 1 <= horizon_months <= 360:
        raise ValueError('Invalid horizon')
    if not 0 <= loan_manwon <= capital:
        raise ValueError('Loan must be within total capital')
    for amount in (monthly_maintenance_capex, one_time_capex_amount):
        if not isfinite(amount) or amount < 0:
            raise ValueError('Additional capex cannot be negative')
    for month in (deposit_return_month, working_capital_return_month, one_time_capex_month):
        if not 0 <= month <= horizon_months:
            raise ValueError('Cash event must fall within horizon, or be disabled')
    for rate in (deposit_return_pct, working_capital_return_pct):
        if not 0 <= rate <= 100:
            raise ValueError('Recovery percent out of range')
    schedule = debt_schedule(loan_manwon, loan_rate_pct, loan_months, loan_method) if loan_manwon else []
    debt_by_month = {row['month']: row for row in schedule}
    rows = []
    cumulative_biz = -capital
    cumulative_equity = -(capital - loan_manwon)
    biz_flows, equity_flows = [], []
    for month in range(1, horizon_months + 1):
        deposit_recovery = items['deposit'] * deposit_return_pct/100 if month == deposit_return_month else 0
        wc_recovery = items['working_capital'] * working_capital_return_pct/100 if month == working_capital_return_month else 0
        extra_capex = one_time_capex_amount if month == one_time_capex_month else 0
        payment = debt_by_month.get(month, {'payment':0, 'interest':0, 'principal_paid':0, 'balance':0})
        business_flow = operating_cash_manwon - monthly_maintenance_capex - extra_capex + deposit_recovery + wc_recovery
        equity_flow = business_flow - payment['payment']
        cumulative_biz += business_flow
        cumulative_equity += equity_flow
        biz_flows.append(business_flow)
        equity_flows.append(equity_flow)
        rows.append({'month':month, 'operating_cash':operating_cash_manwon,
                     'maintenance_capex':monthly_maintenance_capex,
                     'extra_capex':extra_capex, 'deposit_return': deposit_recovery,
                     'working_capital_return':wc_recovery,
                     'loan_interest':payment['interest'],
                     'loan_principal':payment['principal_paid'],
                     'loan_payment':payment['payment'],
                     'loan_balance':payment['balance'] if month <= loan_months else 0,
                     'business_cf':business_flow, 'equity_cf':equity_flow,
                     'cumulative_business':cumulative_biz, 'cumulative_equity':cumulative_equity})
    return InvestmentResult(capital, capital-loan_manwon,
                            payback(capital,biz_flows),payback(capital,biz_flows,project_discount_pct),
                            npv(capital,biz_flows,project_discount_pct),
                            payback(capital-loan_manwon,equity_flows),
                            payback(capital-loan_manwon,equity_flows,equity_discount_pct),
                            npv(capital-loan_manwon,equity_flows,equity_discount_pct),
                            rows, debt_by_month.get(horizon_months, {'balance':0})['balance'] if horizon_months <= loan_months else 0)

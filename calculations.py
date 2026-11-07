"""BizLab cafe break-even calculations. Currency values are KRW."""
from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Results:
    revenue: float
    variable_cost: float
    fixed_cost: float
    operating_profit: float
    operating_margin_pct: float | None
    contribution_margin_pct: float
    break_even_daily_customers: int | None
    break_even_monthly_sales: float | None


def calculate(daily_customers: float, average_ticket: float, open_days: int,
              variable_cost_pct: float, monthly_fixed_cost: float) -> Results:
    if daily_customers < 0 or average_ticket < 0 or monthly_fixed_cost < 0:
        raise ValueError("Customers, ticket and fixed cost cannot be negative.")
    if not 1 <= open_days <= 31:
        raise ValueError("Open days must be between 1 and 31.")
    if not 0 <= variable_cost_pct <= 100:
        raise ValueError("Variable cost ratio must be between 0 and 100%.")
    revenue = daily_customers * average_ticket * open_days
    variable_cost = revenue * variable_cost_pct / 100
    profit = revenue - variable_cost - monthly_fixed_cost
    contribution = 1 - variable_cost_pct / 100
    if contribution <= 0 or average_ticket == 0:
        bep_customers = None
        bep_sales = None
    else:
        bep_customers = ceil((monthly_fixed_cost / (average_ticket * contribution * open_days)) - 1e-12)
        bep_sales = monthly_fixed_cost / contribution
    return Results(
        revenue=revenue,
        variable_cost=variable_cost,
        fixed_cost=monthly_fixed_cost,
        operating_profit=profit,
        operating_margin_pct=(profit / revenue * 100 if revenue else None),
        contribution_margin_pct=contribution * 100,
        break_even_daily_customers=bep_customers,
        break_even_monthly_sales=bep_sales,
    )

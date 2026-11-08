"""BizLab v0.7: source-registered benchmark and editable contribution-margin model.

Source annual averages are preserved verbatim in data/benchmarks.json.
For simulations: food scales with sales; hired+family labor are a single
editable monthly staff cost. A user-chosen share of 'other' is reclassified
from fixed to sales-linked using the SOURCE GROUP monthly average sales as the
reference denominator (not the simulated sales). No new cost is added.
Taxes/dues, staff cost, rent and owner compensation remain monthly amounts;
these are modeling conventions, not empirically identified fixed costs.
"""
from dataclasses import dataclass
from math import ceil

COST_KEYS = ("staff_labor", "rent", "taxes", "owner_labor", "other")
COST_LABELS = {
    "staff_labor": "직원 인건비 (고용인 + 가족)",
    "rent": "임차료", "taxes": "세금·공과 (조사 항목)",
    "owner_labor": "대표자 인건비", "other": "기타 운영비 (총액)",
}


def recommended_inputs(segment: dict, ticket_won: int = 6500, open_days: int = 30) -> dict:
    """Source annual amounts in 만원; transactions/day is derived, not observed."""
    if ticket_won <= 0 or not 1 <= open_days <= 31:
        raise ValueError("Ticket and open days must be positive")
    monthly_sales_won = segment["annual_sales_manwon"] * 10_000 / 12
    cs = segment["costs"]
    return {
        "customers": int(round(monthly_sales_won / ticket_won / open_days)),
        "ticket": ticket_won, "days": open_days,
        "food_pct": float(cs["food"]["pct"]),
        "staff_labor": round((cs["hired_labor"]["manwon"] + cs["family_labor"]["manwon"]) / 12, 2),
        "rent": round(cs["rent"]["manwon"] / 12, 2),
        "taxes": round(cs["taxes"]["manwon"] / 12, 2),
        "owner_labor": round(cs["owner_labor"]["manwon"] / 12, 2),
        "other": round(cs["other"]["manwon"] / 12, 2),
        "other_variable_share_pct": 0,
    }


@dataclass(frozen=True)
class Simulation:
    revenue_won: float
    food_won: float
    variable_won: float
    fixed_won: float
    profit_won: float
    margin_pct: float | None
    break_even_customers: int | None
    cost_won: dict
    total_variable_pct: float
    other_variable_pct: float


def simulate(customers: int, ticket: int, days: int, food_pct: float,
             monthly_costs_manwon: dict, *, include_owner_labor: bool = True,
             other_variable_share_pct: float = 0.0,
             reference_sales_manwon: float | None = None) -> Simulation:
    """All monthly_costs_manwon are monthly amounts, food_pct is a percent.

    Share of 'other' reclassified as variable remains anchored to official
    group average revenue. For zero sales, variable costs are zero, while
    remaining fixed expenses persist. For impossible >=100% contribution,
    break-even is unavailable when positive fixed costs remain.
    """
    if customers < 0 or ticket <= 0 or not 1 <= days <= 31 or not 0 <= food_pct <= 100:
        raise ValueError("Invalid scenario input")
    if set(monthly_costs_manwon) != set(COST_KEYS) or any(v < 0 for v in monthly_costs_manwon.values()):
        raise ValueError("Missing/negative cost")
    if not 0 <= other_variable_share_pct <= 100:
        raise ValueError("Other-variable share must be 0-100")
    if other_variable_share_pct > 0 and (reference_sales_manwon is None or reference_sales_manwon <= 0):
        raise ValueError("Positive reference sales required for reclassification")
    sales = customers * ticket * days
    food = sales * food_pct / 100
    other_total = monthly_costs_manwon["other"]
    variable_other_at_reference = other_total * other_variable_share_pct / 100
    other_variable_pct = (100 * variable_other_at_reference / reference_sales_manwon
                          if other_variable_share_pct else 0.0)
    variable_other = sales * other_variable_pct / 100
    fixed_manwon = sum(v for k, v in monthly_costs_manwon.items()
                       if include_owner_labor or k != "owner_labor") - variable_other_at_reference
    fixed = fixed_manwon * 10000
    variable = food + variable_other
    contribution_rate = 1 - (food_pct + other_variable_pct) / 100
    if fixed <= 1e-7:
        bep = 0 if contribution_rate >= 0 else None
    elif contribution_rate <= 0:
        bep = None
    else:
        bep = ceil(fixed / (ticket * days * contribution_rate) - 1e-12)
    cost_won = {
        "food": food,
        "other_variable": variable_other,
        "other_fixed": (other_total - variable_other_at_reference) * 10000,
        **{k: v * 10000 if (include_owner_labor or k != "owner_labor") else 0
           for k, v in monthly_costs_manwon.items() if k != "other"},
    }
    profit = sales - variable - fixed
    return Simulation(sales, food, variable, fixed, profit,
                      100 * profit / sales if sales else None, bep, cost_won,
                      food_pct + other_variable_pct, other_variable_pct)


def benchmark_monthly(segment: dict) -> dict:
    return {"sales": segment["annual_sales_manwon"] / 12,
            "profit": segment["annual_profit_manwon"] / 12,
            "margin": segment["operating_margin_pct"]}


def comparison(sim: Simulation, segment: dict) -> dict:
    avg = benchmark_monthly(segment)
    return {
        "sales_diff_manwon": sim.revenue_won / 10000 - avg["sales"],
        "profit_diff_manwon": sim.profit_won / 10000 - avg["profit"],
        "margin_diff_pp": sim.margin_pct - avg["margin"] if sim.margin_pct is not None else None,
    }

"""Convert a source-registered annual benchmark into a transparent scenario.

Statistical source reports food-cost ratios and annual category means. For
scenario purposes ONLY, food cost scales with revenue; all other reported cost
categories are held fixed at their average monthly values. This is an explicit
model assumption, not a finding that these categories are entirely fixed.
"""
from dataclasses import dataclass
from math import ceil

COST_KEYS = ("hired_labor", "rent", "taxes", "family_labor", "owner_labor", "other")
COST_LABELS = {
    "hired_labor": "직원 인건비", "rent": "임차료", "taxes": "세금",
    "family_labor": "가족 종사자 인건비", "owner_labor": "대표자 인건비", "other": "기타 운영비"
}


def recommended_inputs(segment: dict, ticket_won: int = 6500, open_days: int = 30) -> dict:
    """Annual reported amounts are in 10,000 KRW. Customers are DERIVED, not observed."""
    if ticket_won <= 0 or not 1 <= open_days <= 31:
        raise ValueError("Ticket and open days must be positive.")
    monthly_sales_won = segment["annual_sales_manwon"] * 10_000 / 12
    return {
        "customers": int(round(monthly_sales_won / ticket_won / open_days)),
        "ticket": ticket_won,
        "days": open_days,
        "food_pct": float(segment["costs"]["food"]["pct"]),
        **{key: round(segment["costs"][key]["manwon"] / 12, 1) for key in COST_KEYS},
    }


@dataclass(frozen=True)
class Simulation:
    revenue_won: float
    food_won: float
    fixed_won: float
    profit_won: float
    margin_pct: float | None
    break_even_customers: int | None
    cost_won: dict


def simulate(customers: int, ticket: int, days: int, food_pct: float,
             monthly_costs_manwon: dict, *, include_owner_labor: bool = True) -> Simulation:
    if customers < 0 or ticket < 0 or not 1 <= days <= 31 or not 0 <= food_pct <= 100:
        raise ValueError("Out of-range scenario input")
    if any(v < 0 for v in monthly_costs_manwon.values()):
        raise ValueError("Costs cannot be negative")
    if set(monthly_costs_manwon) != set(COST_KEYS):
        raise ValueError("Required cost categories missing")
    sales = customers * ticket * days
    food = sales * food_pct / 100
    fixed = sum(v for k, v in monthly_costs_manwon.items() if include_owner_labor or k != "owner_labor") * 10000
    profit = sales - food - fixed
    contribution = ticket * days * (1 - food_pct / 100)
    bep = ceil(fixed / contribution - 1e-12) if contribution > 0 else None
    return Simulation(sales, food, fixed, profit,
                      100 * profit / sales if sales else None, bep,
                      {"food": food, **{k: (v * 10000 if include_owner_labor or k != "owner_labor" else 0.0) for k, v in monthly_costs_manwon.items()}})


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

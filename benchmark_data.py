"""Read-only, source-registered reference statistics for BizLab."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_benchmark():
    with (ROOT / "data" / "benchmarks.json").open(encoding="utf-8") as file:
        return json.load(file)


def load_source_register():
    with (ROOT / "data" / "sources.json").open(encoding="utf-8") as file:
        return json.load(file)


def validate_benchmark(data):
    """Fail closed on an internally inconsistent official table transcription."""
    assert data["status"] == "reference_only"
    assert data["reference_year"] == 2024
    assert data["industry_code"] == "5622"
    for key in ("all", "franchise", "independent"):
        item = data["segments"][key]
        assert item["sample_n"] > 0
        assert item["annual_sales_manwon"] > item["annual_profit_manwon"] >= 0
        total_cost = sum(v["manwon"] for v in item["costs"].values())
        # Tables provide rounded means; an error of 2 manwon allows rounding.
        assert abs(item["annual_sales_manwon"] - item["annual_profit_manwon"] - total_cost) <= 2, (key, total_cost)
        total_pct = sum(v["pct"] for v in item["costs"].values())
        assert abs(total_pct + item["operating_margin_pct"] - 100) <= 0.4, (key, total_pct)
    assert data["segments"]["franchise"]["sample_n"] + data["segments"]["independent"]["sample_n"] == data["segments"]["all"]["sample_n"]
    return True

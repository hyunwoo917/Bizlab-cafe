# BizLab v0.5 — Cafe Insights

Source-based, editable cafe economics simulator with a clean, accessible, mobile-friendly interface.

## Local run (Windows, VS Code)

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## Deploy to existing Streamlit Cloud app

Upload **all files and directories** in this project to the root of the existing GitHub repository. Preserve `.streamlit/config.toml`, `data/benchmarks.json`, `data/sources.json`, `model_v05.py`, and `benchmark_data.py`. Streamlit Cloud main file remains `app.py`. After pushing changes, hard-refresh the app.

## What happens when you choose a category?

- Individual / franchise / combined => monthly cost initial values from the associated 2025 KREI/MaFRA report category; costs are the report's **average annual KRW 10k amounts / 12**.
- Food-cost percentage copies the official 'food cost as % of sales' ratio.
- Initial monthly sales reference = official category's annual per-business sales / 12.
- **Customers are NOT an observed mean**. Daily customer count = official average monthly sales / (assumed ticket KRW 6,500 x assumed monthly opening days 30), rounded.
- All user fields are editable; select a new group or hit Reset to return to the new group's defaults.
- Comparison reports the user's forecast against the category's independent official mean values. It is an arithmetic reference, **not a performance ranking**.

## Accounting and methodological limits

The model makes food costs variable with sales and provisionally models the other 6 official expense categories as fixed monthly costs. This is a modeling shortcut, not a claim that actual taxes, labor, packaging, card fees and overhead are fixed. It can overstate or understate profits in non-average revenue scenarios. The official report includes proprietor/family labor in expenses; their cash flow interpretation may differ. Consistent VAT treatment is essential. The 5622 category includes coffee shops and other non-alcoholic beverage shops. Restaurant-specific benchmarks are not asserted.

Source: `2025 외식업체 경영실태 조사`, Table 3-16-1 to 3-16-3 (printed pp. 321–322), https://www.mafra.go.kr/bbs/home/798/595246/download.do. `data/benchmarks.json` and `data/sources.json` preserve source registry and review caveats. Automated API updates are *not* built yet. Commercial reuse permissions should be verified separately.

## Tests

```powershell
py -m unittest discover -p "test_*.py" -v
```

Design inspiration: Toss's publicly described Product Principles (simplicity, value first, clear action and explanation). This is a distinct BizLab design, not an official Toss interface or a copy of Toss proprietary assets.

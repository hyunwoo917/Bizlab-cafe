"""BizLab v0.1 | Cafe break-even simulator."""
from math import ceil
import pandas as pd
import streamlit as st
from calculations import calculate

st.set_page_config(page_title="BizLab | 카페 손익분기점", page_icon="☕", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1120px; padding-top: 2.2rem; padding-bottom: 3rem;}
h1,h2,h3 {letter-spacing:-.04em;}
div[data-testid="stMetric"] {background: #F3F6F8; border:1px solid #E3EAEE; border-radius:14px; padding:18px 20px;}
div[data-testid="stMetricLabel"] {color:#667887;}
.stApp {background-color:#FCFDFE;}
</style>
""", unsafe_allow_html=True)

st.caption("BIZLAB  /  WEEKEND PROJECT 01  /  v0.1")
st.title("☕ BizLab | 나의 첫 번째 AI 웹서비스")
st.write("예상 고객 수와 비용을 바꾸면 월매출·영업이익·손익분기점을 바로 확인할 수 있습니다.")
st.info("학습용 추정 모델입니다. 세금·금융비용·감가상각·창업 초기투자비·사장 인건비는 고정비에 직접 포함하지 않는 한 반영되지 않습니다.", icon="ℹ️")

with st.sidebar:
    st.subheader("입력 조건")
    daily_customers = st.number_input("일평균 고객 수 (명)", min_value=0, max_value=10000, value=80, step=5)
    average_ticket = st.number_input("1인당 객단가 (원)", min_value=0, max_value=10000000, value=6500, step=500)
    open_days = st.number_input("월 영업일 수 (일)", min_value=1, max_value=31, value=30, step=1)
    variable_cost_pct = st.slider("매출 대비 변동비율 (%)", min_value=0, max_value=100, value=35, step=1,
                                   help="원재료비, 포장비, 결제수수료 등 판매량에 비례하는 비용의 비율")
    fixed_cost_manwon = st.number_input("월 고정비 합계 (만원)", min_value=0, max_value=100000, value=900, step=50,
                                        help="월세, 고정 인건비, 관리비, 사장 인건비 등을 필요한 만큼 포함하세요.")
    st.caption("입력을 변경하면 자동으로 결과가 갱신됩니다. 입력 정보는 서버에 별도로 저장하지 않습니다.")

result = calculate(daily_customers, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon * 10000)
won_to_man = lambda won: f"{won / 10000:,.0f}만원"

st.subheader("월간 핵심 지표")
a, b, c, d = st.columns(4)
a.metric("예상 월매출", won_to_man(result.revenue))
b.metric("예상 월 영업이익", won_to_man(result.operating_profit))
c.metric("영업이익률", f"{result.operating_margin_pct:.1f}%" if result.operating_margin_pct is not None else "계산 불가")
d.metric("일평균 손익분기 고객", f"{result.break_even_daily_customers:,}명" if result.break_even_daily_customers is not None else "도달 불가")

if result.break_even_daily_customers is None:
    st.warning("객단가가 0원이거나 변동비율이 100%라서, 현재 조건에서는 매출을 늘려도 손익분기점을 계산할 수 없습니다.")
elif daily_customers >= result.break_even_daily_customers:
    st.success(f"현재 일평균 {daily_customers:,}명 기준으로 손익분기점({result.break_even_daily_customers:,}명/일)에 도달합니다.")
else:
    st.warning(f"손익분기점까지 일평균 고객 {result.break_even_daily_customers - daily_customers:,}명이 더 필요합니다.")

left, right = st.columns([1.1, 1])
with left:
    st.subheader("비용 및 이익 구조")
    structure = pd.DataFrame({
        "항목": ["변동비", "고정비", "영업이익"],
        "금액(만원)": [result.variable_cost / 10000, result.fixed_cost / 10000, result.operating_profit / 10000]
    })
    st.dataframe(structure.style.format({"금액(만원)": "{:,.1f}"}), hide_index=True, use_container_width=True)
    st.caption("영업이익 = 월매출 - 변동비 - 고정비")
with right:
    st.subheader("고객 수 민감도")
    base = max(1, daily_customers)
    cases = [("비관 -20%", round(base * .8)), ("현재 가정", daily_customers), ("낙관 +20%", round(base * 1.2))]
    table = []
    for label, count in cases:
        rr = calculate(count, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon * 10000)
        table.append({"시나리오": label, "일평균 고객": count, "월매출(만원)": rr.revenue / 10000, "영업이익(만원)": rr.operating_profit / 10000})
    st.dataframe(pd.DataFrame(table).style.format({"월매출(만원)": "{:,.0f}", "영업이익(만원)": "{:,.0f}"}), hide_index=True, use_container_width=True)

st.subheader("매출 변화에 따른 예상 영업이익")
start = 0
end = max(150, round(daily_customers * 1.8), (result.break_even_daily_customers or 0) + 30)
step = max(1, ceil(end / 24))
rows = []
for n in range(start, end+1, step):
    rr = calculate(n, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon * 10000)
    rows.append({"일평균 고객 수": n, "영업이익(만원)": rr.operating_profit / 10000})
chart_df = pd.DataFrame(rows).set_index("일평균 고객 수")
st.line_chart(chart_df, color="#397C89")
with st.expander("계산식과 가정 확인"):
    st.markdown("""
    - **월매출** = 일평균 고객 수 × 객단가 × 월 영업일 수
    - **변동비** = 월매출 × 변동비율
    - **영업이익** = 월매출 − 변동비 − 월 고정비
    - **손익분기 고객 수(일평균)** = 월 고정비 ÷ (객단가 × (1 − 변동비율) × 월 영업일 수), 올림
    - 객단가가 0원이거나 변동비율이 100%면 손익분기를 달성할 수 없습니다.
    - 월매출·고정비는 부가가치세 처리 기준을 통일해서 입력해야 합니다. 본 계산기는 세금 신고용이 아닙니다.
    """)
st.divider()
st.caption("BizLab v0.1 · 가상 데이터로 제작 · 개인 학습/검증용")

# ─────────────────────────────
# 시나리오별 수익성 비교
# ─────────────────────────────

st.divider()
st.subheader("📊 시나리오별 수익성 비교")

scenario_data = []

for name, ratio in [
    ("비관 (-25%)", 0.75),
    ("기준", 1.00),
    ("낙관 (+25%)", 1.25),
]:
    scenario_customers = round(daily_customers * ratio)

    scenario_result = calculate(
        scenario_customers,
        average_ticket,
        open_days,
        variable_cost_pct,
        fixed_cost_manwon * 10000
    )

    scenario_data.append({
        "시나리오": name,
        "일평균 고객 수": scenario_customers,
        "월매출(만원)": round(scenario_result.revenue / 10000, 1),
        "월 영업이익(만원)": round(
            scenario_result.operating_profit / 10000, 1
        ),
    })

scenario_df = pd.DataFrame(scenario_data)

st.dataframe(
    scenario_df,
    hide_index=True,
    use_container_width=True
)

st.bar_chart(
    scenario_df.set_index("시나리오")["월 영업이익(만원)"],
    color="#397C89"
)

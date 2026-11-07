"""BizLab v0.3 | Cafe economics, with a future-ready industry model."""
from math import ceil
import pandas as pd
import streamlit as st
from calculations import calculate

st.set_page_config(page_title="BizLab | 카페 사업성 분석", page_icon="☕", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2.4rem; padding-bottom: 3rem;}
h1,h2,h3 {letter-spacing: -.035em; color: #233443;}
div[data-testid="stMetric"] {background: #F3F6F8; border: 1px solid #E4EBF0; border-radius: 12px; padding: 16px 18px;}
div[data-testid="stMetricLabel"] {color: #617481;}
[data-testid="stSidebar"] {background: #F5F8FA;}
</style>
""", unsafe_allow_html=True)

st.caption("BIZLAB  /  BUSINESS INTELLIGENCE  /  v0.3")
st.title("카페 사업성 분석")
st.write("내 사업의 수익구조를 분석하고, 시나리오별 손익분기점을 확인합니다.")

with st.sidebar:
    st.subheader("분석 조건")
    st.selectbox("업종", ["카페 · 커피전문점"], help="카페 모델 검증 후 업종을 추가할 예정입니다.")
    st.caption("현재는 업종 평균값을 제공하지 않습니다. 아래 값은 분석용 예시이며 실제 업종 통계가 아닙니다.")
    if st.button("예시 가정 적용", use_container_width=True):
        for k in ["customers", "ticket", "days", "variable", "fixed"]:
            st.session_state.pop(k, None)
        st.rerun()
    daily_customers = st.number_input("일평균 고객 수 (명)", 0, 10000, 80, 5, key="customers")
    average_ticket = st.number_input("객단가 (원)", 0, 10000000, 6500, 500, key="ticket")
    open_days = st.number_input("월 영업일 수 (일)", 1, 31, 30, 1, key="days")
    variable_cost_pct = st.slider("변동비율 (%)", 0, 100, 35, 1, key="variable", help="원재료·포장·결제수수료 등 매출에 연동되는 비용")
    fixed_cost_manwon = st.number_input("월 고정비 (만원)", 0, 100000, 900, 50, key="fixed", help="임대료·고정 인건비·관리비 등")
    st.divider()
    st.caption("입력값은 현재 세션에서만 유지됩니다. 별도 데이터베이스에 저장하지 않습니다.")

result = calculate(daily_customers, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon * 10000)
st.subheader("월간 핵심 지표")
a,b,c,d = st.columns(4)
a.metric("월매출", f"{result.revenue/10000:,.0f}만원")
b.metric("영업이익", f"{result.operating_profit/10000:,.0f}만원")
c.metric("영업이익률", f"{result.operating_margin_pct:.1f}%" if result.operating_margin_pct is not None else "계산 불가")
d.metric("손익분기 고객 수/일", f"{result.break_even_daily_customers:,}명" if result.break_even_daily_customers is not None else "도달 불가")

if result.break_even_daily_customers is None:
    st.warning("현재 가정에서는 손익분기 고객 수를 계산할 수 없습니다.")
elif daily_customers >= result.break_even_daily_customers:
    st.success(f"손익분기 고객 수 {result.break_even_daily_customers:,}명/일을 충족합니다.")
else:
    st.warning(f"손익분기까지 일평균 고객 {result.break_even_daily_customers - daily_customers:,}명이 더 필요합니다.")

st.subheader("시나리오별 수익성")
low, high = st.columns(2)
with low:
    downside = st.slider("비관 시나리오 고객 감소율 (%)", 0, 80, 25, 5)
with high:
    upside = st.slider("낙관 시나리오 고객 증가율 (%)", 0, 100, 25, 5)
scenarios = [("비관", max(0, round(daily_customers * (1-downside/100)))), ("기준", daily_customers), ("낙관", round(daily_customers * (1+upside/100)))]
records = []
for label, customers in scenarios:
    rr = calculate(customers, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon * 10000)
    records.append({"시나리오": label, "일평균 고객": customers, "월매출(만원)": round(rr.revenue/10000,1), "영업이익(만원)": round(rr.operating_profit/10000,1)})
df = pd.DataFrame(records)
left,right = st.columns([1,1.15])
with left:
    st.dataframe(df, hide_index=True, use_container_width=True)
with right:
    st.bar_chart(df.set_index("시나리오").reindex(["비관","기준","낙관"])["영업이익(만원)"], color="#397C89")

st.subheader("고객 수에 따른 영업이익")
end = min(20000, max(150, round(daily_customers*1.8), (result.break_even_daily_customers or 0)+30))
step = max(1, ceil(end/28))
points = []
for n in range(0, end+1, step):
    rr = calculate(n, average_ticket, open_days, variable_cost_pct, fixed_cost_manwon*10000)
    points.append({"일평균 고객 수": n, "영업이익(만원)": rr.operating_profit/10000})
st.line_chart(pd.DataFrame(points).set_index("일평균 고객 수"), color="#397C89")

with st.expander("업종 벤치마크 · 준비 중"):
    st.write("향후 업종별 평균 변동비율, 영업이익률, 매출 규모 등을 공식 통계와 연결합니다. 각 값에는 출처·기준연도·표본·비용 정의를 명시하고, 적용 후에도 사용자가 직접 수정할 수 있도록 설계합니다.")
    st.info("현재 35% 변동비율과 900만원 고정비는 예시값이며 카페 업종 평균이 아닙니다.")
with st.expander("계산식과 모델의 한계"):
    st.markdown("""- 월매출 = 일평균 고객 수 × 객단가 × 월 영업일 수
- 변동비 = 월매출 × 변동비율
- 영업이익 = 월매출 − 변동비 − 월 고정비
- 손익분기 고객 수 = 월 고정비 ÷ (객단가 × (1 − 변동비율) × 영업일 수), 올림
- 창업 투자비·감가상각·세금·금융비용·사업주 인건비는 입력 고정비에 포함하지 않는 한 반영하지 않습니다.
- 매출·비용의 부가세 처리 기준을 통일해야 합니다.""")
st.divider()
st.caption("BizLab v0.3 · 예시 가정 기반 학습용 시뮬레이터 · 실제 창업 판단에는 추가 검증 필요")

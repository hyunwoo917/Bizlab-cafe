"""BizLab v0.6 — source-based cafe economics with an editable scenario."""
from html import escape
import pandas as pd
import streamlit as st
from benchmark_data import load_benchmark, load_source_register, validate_benchmark
from model_v05 import COST_KEYS, COST_LABELS, recommended_inputs, simulate, benchmark_monthly, comparison

st.set_page_config(page_title="BizLab | 카페 수익 분석", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
:root {color-scheme:light;}
html,body,[class*="css"], [data-testid="stAppViewContainer"] {font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif;}
.stApp {background:#FFFFFF;color:#191F28;}
.block-container {max-width:1100px; padding-top:1.7rem; padding-bottom:4rem;}
header[data-testid="stHeader"] {background:rgba(255,255,255,.93);}
h1,h2,h3,p {letter-spacing:-.035em;}
h1 {font-size:2.15rem !important; font-weight:800 !important; line-height:1.3 !important;}
h2,h3 {font-weight:750 !important;}
[data-testid="stCaptionContainer"], .stCaption {color:#8B95A1 !important;}
div[data-testid="stVerticalBlock"] > div {min-width:0;}
[data-testid="stNumberInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {border-radius:12px !important; background:#F6F8FA !important; border-color:#E5E8EB !important;}
[data-testid="stNumberInput"] input {font-size:1.05rem; font-weight:650; color:#191F28;}
.stButton button[kind="primary"] {background:#3182F6; border-color:#3182F6; color:#FFFFFF; border-radius:12px; font-weight:700; min-height:44px;}
.stButton button[kind="secondary"] {background:#F2F4F6; border:0; border-radius:12px; font-weight:650; min-height:44px; color:#333D4B;}
[data-testid="stMetric"] {background:#F6F8FA;border:0;border-radius:18px;padding:18px 20px;}
[data-testid="stMetricLabel"] {color:#6B7684;font-weight:600;}
[data-testid="stMetricValue"] {color:#191F28;font-weight:750;letter-spacing:-.055em;}
[data-testid="stTabs"] button[role="tab"] {font-weight:700; padding:12px 14px;}
[data-testid="stExpander"] {border:1px solid #E5E8EB; border-radius:16px; overflow:hidden;}
hr {border-color:#F2F4F6;}
.biz-eyebrow {font-weight:800;color:#3182F6;font-size:12px;letter-spacing:.11em;margin-bottom:10px;}
.biz-hero {font-size:15px;color:#6B7684;line-height:1.85;margin:5px 0 20px;}
.biz-section {font-size:23px;font-weight:800;letter-spacing:-.05em;margin:24px 0 8px;color:#191F28;}
.biz-quiet {font-size:13px;color:#8B95A1;line-height:1.7;}
.biz-pill {display:inline-block;padding:7px 12px;border-radius:99px;background:#E8F3FF;color:#1B64DA;font-weight:750;font-size:12px;margin-bottom:14px;}
.biz-card {background:#F6F8FA;padding:23px 24px;border-radius:20px;margin:5px 0 12px;}
.biz-card.white {background:white;border:1px solid #E5E8EB;}
.biz-card.dark {background:#191F28;color:white;}
.biz-card .label {font-size:13px;color:#6B7684;font-weight:650;}
.biz-card.dark .label {color:#B0B8C1;}
.biz-card .value {font-size:34px;font-weight:800;letter-spacing:-.06em;line-height:1.5;}
.biz-card .note {font-size:12px;color:#8B95A1;margin-top:6px;}
.biz-card.dark .note {color:#C1C7CE;}
.biz-inline {color:#3182F6;font-weight:750;}
.biz-rule {border:0;border-top:1px solid #E5E8EB;margin:20px 0;}
@media(max-width:700px) {.block-container{padding-top:1rem;padding-left:1rem;padding-right:1rem;}h1{font-size:1.75rem !important;}.biz-card{padding:17px 18px;}.biz-card .value{font-size:27px;}}
</style>
""", unsafe_allow_html=True)

benchmark = load_benchmark()
register = load_source_register()
validate_benchmark(benchmark)
SEGMENTS = benchmark["segments"]
DISPLAY = {"all": "전체 평균", "independent": "개인 카페", "franchise": "프랜차이즈"}


def m(value):
    return f"{value:,.1f}".rstrip("0").rstrip(".")


def card(label, value, note="", *, dark=False):
    cls = "biz-card dark" if dark else "biz-card"
    return f'<div class="{cls}"><div class="label">{escape(str(label))}</div><div class="value">{escape(str(value))}</div><div class="note">{escape(str(note))}</div></div>'


def reset_from_benchmark():
    seg = SEGMENTS[st.session_state["biz_segment"]]
    ticket = st.session_state.get("biz_ticket", 6500)
    days = st.session_state.get("biz_days", 30)
    suggested = recommended_inputs(seg, ticket, days)
    for key, value in suggested.items():
        st.session_state[f"biz_{key}"] = value
    st.session_state["biz_dirty"] = False


if "biz_segment" not in st.session_state:
    st.session_state["biz_segment"] = "independent"
if "biz_dirty" not in st.session_state:
    st.session_state["biz_dirty"] = False
if "biz_customers" not in st.session_state:
    reset_from_benchmark()

st.markdown('<div class="biz-eyebrow">BIZLAB <span style="color:#8B95A1">/ CAFE INSIGHTS</span></div>', unsafe_allow_html=True)
st.title("내 카페, 얼마나 남을까?")
st.markdown('<p class="biz-hero">실제 업종 통계로 시작하고, 내 가게에 맞게 바꿔보세요.<br>매출부터 손익분기점까지 한눈에 확인할 수 있어요.</p>', unsafe_allow_html=True)

tab_main, tab_data, tab_source = st.tabs(["내 사업 분석", "업종 평균 보기", "데이터 출처 · 검증"])
with tab_main:
    st.markdown('<div class="biz-section">01  어떤 카페를 준비하세요?</div>', unsafe_allow_html=True)
    st.selectbox("운영 방식", ["independent", "franchise", "all"],
                 format_func=lambda key: DISPLAY[key], key="biz_segment", on_change=reset_from_benchmark,
                 help="커피 전문점 단독 통계가 아니라 비알코올 음료점업(5622)의 운영 형태별 평균이에요.")
    segment = SEGMENTS[st.session_state["biz_segment"]]
    avg = benchmark_monthly(segment)
    st.markdown('<span class="biz-pill">2025년 조사 · 공식 통계로 초기값 설정</span>', unsafe_allow_html=True)
    st.caption("적용 시 월 영업비용은 해당 집단의 사업체당 평균 연간 비용을 12로 나눈 금액이에요. 고객 수는 공식 조사값이 아닌 객단가·영업일수로 역산한 추정치예요.")
    if st.button("↺  업종 평균으로 다시 설정", use_container_width=False, on_click=reset_from_benchmark):
        pass

    st.markdown('<div class="biz-section">02  내 가게 조건을 입력해요</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3, gap="medium")
    with a:
        st.number_input("하루 예상 결제 건수", min_value=0, max_value=10000, step=1, key="biz_customers", help="업종 평균 월매출을 가정 객단가로 나눈 결제 건수입니다. 실제 관측 데이터가 아닙니다.")
    with b:
        st.number_input("한 사람당 결제금액 · 원", min_value=1, max_value=1000000, step=500, key="biz_ticket", help="초기 6,500원은 사용자 가정이며 공식 업종 평균 객단가가 아닙니다.")
    with c:
        st.number_input("한 달 영업일 수", min_value=1, max_value=31, step=1, key="biz_days", help="초기 30일은 사용자 가정입니다.")

    st.markdown('<div class="biz-section">03  비용을 설정해요</div>', unsafe_allow_html=True)
    st.caption("식재료비는 매출에 비례해 계산합니다. 나머지는 통계의 연간 금액을 월 환산한 뒤 고정 처리하는 가정이며, 항목별 자유 수정이 가능해요.")
    c1, c2 = st.columns([1,2], gap="large")
    with c1:
        st.number_input("식재료비율 · %", min_value=0.0, max_value=100.0, step=0.5, format="%.1f", key="biz_food_pct",
                        help="공식 통계의 식재료비율만 자동 설정합니다. 총변동비율이나 원재료비 전체를 뜻하지 않습니다.")
    with c2:
        with st.expander("직원 인건비 · 임차료 등 세부 비용 변경", expanded=True):
            left, right = st.columns(2)
            for index, key in enumerate(COST_KEYS):
                with (left if index % 2 == 0 else right):
                    st.number_input(f"{COST_LABELS[key]} · 만원/월", min_value=0.0, max_value=100000.0,
                                    step=10.0, format="%.1f", key=f"biz_{key}")
            st.caption("대표자·가족 인건비와 세금도 포함돼 있어요. 실제 현금 유출과 회계상 비용은 다를 수 있습니다.")

    monthly_costs = {k: float(st.session_state[f"biz_{k}"]) for k in COST_KEYS}
    st.markdown('<div class="biz-section">04  월 비용을 한눈에 확인해요</div>', unsafe_allow_html=True)
    owner_cost = monthly_costs["owner_labor"]
    other_monthly_costs = sum(monthly_costs.values()) - owner_cost
    food_est_manwon = (st.session_state["biz_customers"] * st.session_state["biz_ticket"]
                       * st.session_state["biz_days"] * st.session_state["biz_food_pct"] / 100 / 10000)
    ctotal, cowner, cfood = st.columns(3)
    ctotal.metric("월 비용 합계 (대표자 포함)", f"{other_monthly_costs + owner_cost + food_est_manwon:,.1f}만원",
                  help="현재 예상 매출에 연동된 식재료비와 월 고정 처리 비용을 모두 합한 값입니다.")
    cowner.metric("월 고정 처리 비용", f"{other_monthly_costs + owner_cost:,.1f}만원",
                  help="공식 고정비 통계가 아닌, 시뮬레이션에서 고정으로 처리한 비용의 합계입니다.")
    cfood.metric("예상 월 식재료비", f"{food_est_manwon:,.1f}만원",
                 help="현재 예상 매출 × 식재료비율")
    with st.expander("비용 합계가 어떻게 계산됐나요?", expanded=False):
        cost_rows = [{"항목": "식재료비 (매출 연동)", "월 비용(만원)": round(food_est_manwon, 1), "계산 방식": "매출 연동"}]
        cost_rows += [{"항목": COST_LABELS[k], "월 비용(만원)": round(monthly_costs[k], 1), "계산 방식": "월 금액 고정 가정"}
                      for k in COST_KEYS]
        st.dataframe(pd.DataFrame(cost_rows), hide_index=True, use_container_width=True)
        st.caption("여기서 '고정'은 현실의 고정비 분류가 아니라 시뮬레이션 계산 가정입니다. 세금, 인건비, 기타비용은 실제로 변동할 수 있어요.")

    st.markdown('<div class="biz-section">05  사업주 인건비를 어떻게 볼까요?</div>', unsafe_allow_html=True)
    st.toggle("대표자 인건비를 비용에 포함", value=True, key="biz_include_owner",
              help="켜면 대표자 인건비를 차감한 후 이익을, 끄면 대표자 인건비 차감 전 잔여금액을 보여줘요. 사업주의 실제 현금소득을 뜻하지 않습니다.")
    include_owner = bool(st.session_state["biz_include_owner"])
    sim = simulate(st.session_state["biz_customers"], st.session_state["biz_ticket"],
                   st.session_state["biz_days"], st.session_state["biz_food_pct"],
                   monthly_costs, include_owner_labor=include_owner)
    sim_with_owner = simulate(st.session_state["biz_customers"], st.session_state["biz_ticket"],
                              st.session_state["biz_days"], st.session_state["biz_food_pct"], monthly_costs)
    comparison_with_owner = comparison(sim_with_owner, segment)
    sim_before_owner = simulate(st.session_state["biz_customers"], st.session_state["biz_ticket"],
                                st.session_state["biz_days"], st.session_state["biz_food_pct"],
                                monthly_costs, include_owner_labor=False)
    owncol, beforecol = st.columns(2)
    owncol.metric("대표자 인건비 차감 후 잔여이익", f"{sim_with_owner.profit_won / 10000:,.1f}만원")
    beforecol.metric("대표자 인건비 차감 전 잔여이익", f"{sim_before_owner.profit_won / 10000:,.1f}만원")
    st.caption(f"두 금액의 차이는 설정한 대표자 인건비 {owner_cost:,.1f}만원입니다. 두 지표 모두 실제 사업주의 세후 현금수입을 의미하지 않아요.")
    bep_col1, bep_col2 = st.columns(2)
    bep_col1.metric("대표자 인건비 포함 손익분기", f"{sim_with_owner.break_even_customers:,}건/일" if sim_with_owner.break_even_customers is not None else "도달 불가")
    bep_col2.metric("대표자 인건비 제외 손익분기", f"{sim_before_owner.break_even_customers:,}건/일" if sim_before_owner.break_even_customers is not None else "도달 불가")
    st.caption("결제 건수 기준. 한 사람이 여러 건을 결제할 수 있어 실제 방문객 수와 다릅니다.")

    st.markdown('<div class="biz-section">06  그래서, 한 달에 얼마나 남을까요?</div>', unsafe_allow_html=True)
    left, right = st.columns([1,1], gap="medium")
    with left:
        st.markdown(card("내 예상 월매출", f"{sim.revenue_won / 10000:,.0f}만원", f"업종 평균 {avg['sales']:,.0f}만원 / 월"), unsafe_allow_html=True)
    with right:
        st.markdown(card("내 예상 월 영업이익" if include_owner else "대표자 인건비 차감 전 잔여금액", f"{sim.profit_won / 10000:,.0f}만원", f"업종 평균 {avg['profit']:,.0f}만원 / 월 (대표자 인건비 포함)", dark=True), unsafe_allow_html=True)
    k1,k2,k3=st.columns(3)
    k1.metric("예상 영업이익률" if include_owner else "대표자 인건비 차감 전 잔여율", f"{sim.margin_pct:.1f}%" if sim.margin_pct is not None else "계산 불가")
    k2.metric("손익분기 결제 건수/일", f"{sim.break_even_customers:,}명" if sim.break_even_customers is not None else "도달 불가")
    k3.metric("업종 평균 대비 월 영업이익 차이 (동일 비용 범위)", f"{comparison_with_owner['profit_diff_manwon']:+,.0f}만원", help="대표자 인건비 포함 기준으로만 비교합니다.")

    if sim.break_even_customers is None:
        st.warning("매출에서 식재료비를 제외한 금액으로 고정비를 충당할 수 없어요.")
    elif st.session_state["biz_customers"] >= sim.break_even_customers:
        st.success(f"현재 조건에서 하루 {sim.break_even_customers:,}건 이상이면 손익분기점을 넘어요.")
    else:
        st.info(f"손익분기점까지 하루 {sim.break_even_customers - st.session_state['biz_customers']:,}건 더 필요해요.")

    st.markdown('<div class="biz-section">07  업종 평균과 비교해요</div>', unsafe_allow_html=True)
    st.caption("비교는 대표자 인건비 포함 기준으로 통일합니다. 업종 평균은 실제 조사 실적이고, 내 예상은 비용 일부를 고정한 시뮬레이션으로 측정 방식은 다릅니다.")
    if not include_owner:
        st.info("현재 위쪽 결과는 대표자 인건비 차감 전입니다. 이 비교 표는 공정한 비교를 위해 대표자 인건비를 포함한 결과로 표시합니다.")
    a,b=st.columns([1,1.1],gap="large")
    with a:
        compare_df=pd.DataFrame({
            "구분": ["월매출", "월 영업이익 (대표자 포함)", "영업이익률 (대표자 포함)"],
            "업종 평균": [f"{avg['sales']:,.0f}만원", f"{avg['profit']:,.0f}만원", f"{avg['margin']:.1f}%"],
            "내 예상": [f"{sim.revenue_won/10000:,.0f}만원", f"{sim_with_owner.profit_won/10000:,.0f}만원", f"{sim_with_owner.margin_pct:.1f}%" if sim_with_owner.margin_pct is not None else "—"],
            "차이": [f"{comparison_with_owner['sales_diff_manwon']:+,.0f}만원", f"{comparison_with_owner['profit_diff_manwon']:+,.0f}만원", f"{comparison_with_owner['margin_diff_pp']:+.1f}%p" if comparison_with_owner['margin_diff_pp'] is not None else "—"],
        })
        st.dataframe(compare_df, hide_index=True, use_container_width=True)
        st.markdown('<p class="biz-quiet">※ 차이는 업종 평균 대비 내 입력 조건의 산술적 차이이며, 우수·열위 판단이나 수익 달성 가능성을 보증하지 않아요.</p>',unsafe_allow_html=True)
    with b:
        chart=pd.DataFrame({"업종 평균": [avg["sales"],avg["profit"]], "내 예상": [sim_with_owner.revenue_won/10000,sim_with_owner.profit_won/10000]},index=["월매출(만원)","월이익(만원)"])
        st.bar_chart(chart, color=["#B0B8C1", "#3182F6"], horizontal=True)

    with st.expander("고객 수가 바뀌면 어떻게 될까요?"):
        low,high=st.columns(2)
        with low: downside=st.slider("고객 감소 · %",0,80,25,5)
        with high: upside=st.slider("고객 증가 · %",0,100,25,5)
        scenario_rows=[]
        for name, count in [("비관",round(st.session_state['biz_customers']*(1-downside/100))),
                            ("현재",st.session_state['biz_customers']),
                            ("낙관",round(st.session_state['biz_customers']*(1+upside/100)))]:
            rr=simulate(count,st.session_state["biz_ticket"],st.session_state["biz_days"],st.session_state["biz_food_pct"],monthly_costs, include_owner_labor=include_owner)
            scenario_rows.append({"시나리오":name,"결제 건수/일":count,"월매출(만원)":round(rr.revenue_won/10000,1),"월 잔여금액(만원)":round(rr.profit_won/10000,1)})
        st.dataframe(pd.DataFrame(scenario_rows),hide_index=True,use_container_width=True)

    st.markdown('<p class="biz-quiet">모델 주의: 식재료비만 매출 연동 비용으로 처리하고, 인건비·임차료·세금·기타비용을 시뮬레이션 범위 내에서 고정합니다. 실제 운영에서는 결제수수료·배달비·인건비 등이 매출에 따라 변할 수 있으며, 대표자 인건비를 제외한 결과는 엄밀한 영업이익이 아니라 차감 전 잔여금액이며, 실제 현금흐름과 다를 수 있어요. 모든 금액의 부가세 기준을 통일해야 합니다.</p>',unsafe_allow_html=True)

with tab_data:
    st.markdown('<div class="biz-section">공식 통계는 이렇게 조사됐어요</div>',unsafe_allow_html=True)
    st.caption("출처: 농림축산식품부·한국농촌경제연구원 「2025 외식업체 경영실태 조사」, 2024년 사업실적 기준 / 비알코올 음료점업(5622)")
    chosen=st.selectbox("통계 비교 그룹", ["all","independent","franchise"],format_func=lambda k:DISPLAY[k],key="data_segment")
    dat=SEGMENTS[chosen]
    aa,bb,cc=st.columns(3)
    aa.metric("업체당 월평균 매출",f"{dat['annual_sales_manwon']/12:,.0f}만원")
    bb.metric("업체당 월평균 영업이익",f"{dat['annual_profit_manwon']/12:,.0f}만원")
    cc.metric("영업이익률",f"{dat['operating_margin_pct']:.1f}%")
    st.markdown("**평균 비용 구조**")
    detail=pd.DataFrame([{"비용 항목":benchmark['cost_labels'][k],"연간 평균(만원)":item['manwon'],"월 환산(만원)":round(item['manwon']/12,1),"매출 대비(%)":item['pct']} for k,item in dat['costs'].items()])
    st.dataframe(detail,hide_index=True,use_container_width=True)
    st.caption("공식 조사에서 산출한 각 항목의 평균이며, 표본 352개(전체)·140개(프랜차이즈)·212개(비프랜차이즈). 분류별 수치는 커피 전문점 단독이 아닙니다.")
    st.link_button("공식 조사 보고서 보기 ↗",benchmark['source']['pdf_url'])
    with st.expander("이 자료가 모든 카페를 대표하나요?"):
        st.write("커피전문점(56221)과 기타 비알코올 음료점업(56229)을 합산한 5622 업종 평균입니다. 브랜드·입지·규모에 따라 손익은 달라집니다. 평균은 사업 성공 가능성이나 예상 매출을 보장하지 않습니다.")

with tab_source:
    st.markdown('<div class="biz-section">왜 이 데이터를 선택했나요?</div>',unsafe_allow_html=True)
    st.caption("공식성, 업종의 일치도, 비용 항목의 정합성, 업데이트 및 접근성을 기준으로 검토했어요. 언론 인용 빈도는 검증 자료가 없어 순위를 매기지 않았어요.")
    sources_df=pd.DataFrame([{"출처":x['name'],"제공 정보":x['metric_scope'],"상태":{"reference_only":"참고 채택","approved":"승인","pending":"후속 검증"}[x['state']]} for x in register['sources']])
    st.dataframe(sources_df,hide_index=True,use_container_width=True)
    ix=st.selectbox("출처별 근거 확인",range(len(register['sources'])),format_func=lambda i:register['sources'][i]['name'])
    source=register['sources'][ix]
    st.markdown(f"**선정 목적**  \n{source['selection']}")
    st.markdown(f"**선정 근거**  \n{source['rationale']}")
    st.markdown(f"**한계·확인할 사항**  \n{source['limitations']}")
    st.caption(f"제공 방식: {source['delivery']} · 갱신: {source['refresh']}")
    st.link_button("원본 사이트 열기 ↗",source['url'])
    with st.expander("현재 버전의 계산·데이터 원칙"):
        st.markdown("""- 공식 통계의 **식재료비율**만 매출 연동 비용으로 활용합니다. 전체 변동비율로 해석하지 않습니다.
- 나머지 공식 연간 비용은 **12개월로 나눠 월 고정비 초기값**으로 전환합니다. 실제로 전부 고정비라는 뜻은 아닙니다.
- **객단가 6,500원 / 월 30일**은 공식 통계가 아닌 편집 가능한 가정입니다. 이 가정과 공식 월평균 매출로 하루 고객 수를 역산합니다.
- 프랜차이즈·비프랜차이즈는 커피전문점 단독이 아닌 **5622 업종 통계**입니다.
- 기준자료는 수동으로 검증한 스냅샷입니다. **API 자동 업데이트는 아직 구현하지 않았습니다.**
- 원본 보고서 인용과 데이터의 상업적 재배포는 별도 이용 조건 확인이 필요합니다.""")

st.divider()
st.markdown('<p class="biz-quiet">BIZLAB v0.6 · 공식 업종 통계 기반 시뮬레이션 · 초기값은 추정 출발점이며 실제 창업 수익을 보증하지 않습니다.</p>',unsafe_allow_html=True)

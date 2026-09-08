import os
import sys
import time
import requests

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from google import genai
from google.genai import errors

# ==========================================
# 🔑 [백엔드 영구 내장] 관리자 인증 키
# ==========================================
DEFAULT_API_KEY = "AQ.Ab8RN6IRJtuY_E7ZScZnj6KB5AYsv8NjZ0EpiyioU7d2fiY7PQ"

def get_secret_key():
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return DEFAULT_API_KEY

BACKEND_GEMINI_API_KEY = get_secret_key()
SERVER_BOT_TOKEN = "8865676246:AAGP_iR4n1Wy7R6IkmdPI9UlqSBg8vOZAE8"

# 페이지 기본 설정
st.set_page_config(
    page_title="매장비서 AI | 소상공인 올인원 마케팅 솔루션",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모던 대시보드 스타일
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; text-align: center; }
    .metric-card h4 { margin: 0; color: #475569; font-size: 0.85rem; }
    .metric-card p { margin: 4px 0 0 0; color: #0F172A; font-size: 1.15rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 텔레그램 발송 함수
def send_telegram_msg(bot_token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

# 사이드바 설정 (API 키 입력창 완전 삭제)
with st.sidebar:
    st.markdown("## 🏪 매장비서 AI")
    st.caption("소상공인 전담 모바일 마케팅 센터")
    st.markdown("---")
    
    st.markdown("### 🔔 스마트폰 전송 설정")
    user_chat_id = st.text_input("알림 받을 텔레그램 ID", value="234698805", placeholder="숫자 ID 입력")
    
    with st.expander("❓ 내 텔레그램 ID 확인법"):
        st.caption("1. 텔레그램에서 **@Dreamoptbot** 검색 후 [시작(Start)] 터치")
        st.caption("2. **@getmyid_bot** 검색 후 [시작] 누르면 나오는 숫자 복사")
        st.caption("3. 위 입력창에 붙여넣기")
        
    st.markdown("---")
    st.success("🟢 AI 자동 인증 연결됨 (활성화)")
    st.caption("© 2026 StoreMate AI. All rights reserved.")

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

# 글로벌 최상위 마케터 시스템 프롬프트
SYSTEM_DIRECTIVE = """
너는 업종별 소비 심리와 구매 전환 알고리즘을 꿰뚫고 있는 세계 최정상 마케팅 디렉터다.

[핵심 작성 원칙]
1. 완벽한 업종 맞춤 어휘(Jargon & Tone) 사용:
   - 요식업/주점/카페: 오감을 자극하는 표현(불향, 쫄깃함, 깊은 감칠맛, 손맛, 아늑한 아지트, 퇴근길 한잔) 중심. 절대로 병원이나 기계에 쓰는 '정밀 검사' 따위의 단어를 쓰지 말 것.
   - 패션/안경/뷰티: 전문성, 편안한 착용감, 얼굴형/개인 체형 맞춤 컨설팅, 꼼꼼한 관리 중심.
   - 생활/기술/정비: 신뢰, 정직한 공임, 철저한 사후관리(A/S), 20년 내공의 손기술 중심.
   - 학원/피트니스: 목표 달성, 1:1 밀착 피드백, 쾌적한 환경, 동기부여 중심.

2. 사실 기반의 지명 및 위치 서술 (환각 완전 차단):
   - 사용자가 입력하지 않은 위치 정보(가짜 정류장, 허구의 대로변 등)를 절대로 날조하지 말 것.
   - 골목 안쪽 매장은 '아는 단골들만 찾아가는 골목 속 아늑한 찐맛집/아지트'로 매력적이면서도 정직하게 서술할 것.
   - 읍·면·리 단위를 임의로 '동'으로 바꾸지 말 것.
"""

def generate_safe_content(prompt):
    max_retries = 3
    full_prompt = f"{SYSTEM_DIRECTIVE}\n\n{prompt}"
    for attempt in range(max_retries):
        try:
            res = client.models.generate_content(model=TARGET_MODEL, contents=full_prompt)
            return res.text
        except errors.ServerError:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                st.error("서버 지연이 발생했습니다. 잠시 후 다시 시도해 주세요.")
                return None
        except Exception as e:
            st.error(f"오류: {str(e)}")
            return None

# 메인 헤더
st.markdown('<div class="main-header">🏪 매장비서 AI (StoreMate Pro)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">복잡한 설정 없이, 매장 정보만 넣으면 프로급 마케팅 원고가 3초 만에 완성됩니다.</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card"><h4>원고 제작 시간</h4><p>평균 3초</p></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><h4>AI 엔진 탑재</h4><p>자동 인증 완료</p></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><h4>위치 정밀도</h4><p>허구 날조 0% 차단</p></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><h4>전송 방식</h4><p>스마트폰 즉시 배달</p></div>', unsafe_allow_html=True)

st.markdown("---")

tabs = st.tabs([
    "📝 상위노출 블로그",
    "📸 인스타 카드뉴스",
    "🥕 당근마켓 소식",
    "⏰ 모닝 자동발송 (스마트폰)",
    "💬 카톡 단골 재방문",
    "🛡️ 영수증/컴플레인 답글",
    "🌦️ 날씨/당일 팝업",
    "📌 매장 POP & 안내문",
    "🎯 현수막/입간판 카피",
    "🤝 상권 제휴 기획서",
    "📅 30일 마케팅 달력"
])

# 1. 블로그
with tabs[0]:
    st.subheader("📝 네이버 뷰탭 상위노출 블로그 (업종별 전문 어휘 모드)")
    col_a, col_b = st.columns([2, 2])
    with col_a:
        b_cat = st.selectbox("매장 업종 카테고리", [
            "🍽️ 요식업/주점 (포차, 고깃집, 식당, 카페, 베이커리)",
            "👓 패션/잡화/뷰티 (안경원, 헤어샵, 네일샵, 의류)",
            "🔧 생활/정비/시공 (인테리어, 카센터, 세탁, 철물)",
            "🏋️ 운동/교육/학원 (헬스, PT, 필라테스, 교습소)"
        ], key="b_cat")
    with col_b:
        b_loc_type = st.selectbox("매장 위치 특성", [
            "골목 안쪽 (아늑하고 정겨운 숨은 아지트/찐맛집)",
            "주요 도로변 (접근성 좋고 찾기 쉬운 위치)",
            "상가 단지 / 주택가 골목"
        ], key="b_loc_type")

    c1, c2 = st.columns([3, 2])
    with c1:
        b_name = st.text_input("상호명 및 지역", placeholder="예: 쫜디포차 (용인 처인구) / 드림안경 송전점 (용인 이동읍)", key="b_name")
    with c2:
        b_addr = st.text_input("정확한 주소 또는 주변 랜드마크", placeholder="예: 이동읍 송전리 골목길 / OO마트 뒤편", key="b_addr")
        
    b_point = st.text_input("대표 메뉴/제품 및 장점", placeholder="예: 칼칼한 국물닭발과 계란찜 / 가볍고 편한 누진다초점렌즈", key="b_point")
        
    if st.button("🚀 업종 맞춤 프로 블로그 원고 생성", use_container_width=True, key="btn_b"):
        if not b_name:
            st.warning("상호명 및 지역을 입력해 주세요.")
        else:
            with st.spinner("전문 마케팅 원고를 작성 중입니다..."):
                prompt = f"""
                [의뢰 정보]
                - 업종: {b_cat}
                - 상호명 및 지역: {b_name}
                - 매장 위치 특성: {b_loc_type}
                - 상세 위치/랜드마크: {b_addr if b_addr else '입력되지 않았으므로 정류장 앞 등의 허구 정보를 절대 지어내지 말 것'}
                - 핵심 시그니처: {b_point if b_point else '뛰어난 품질과 친절한 고객 서비스'}

                [작성 가이드라인]
                1. {b_cat}의 소비자가 반응하는 최고급 어휘만을 사용할 것.
                2. 위치가 골목이라면 숨은 아지트 분위기를 살려 손님이 직접 찾아오고 싶게 만들 것.
                3. 구성:
                   - 🔍 상위노출 키워드 5선 및 제목 3개
                   - 📷 [사진/움짤 촬영 가이드]
                   - 📄 본문 완성본
                   - 🗺️ [네이버 지도 연동 '찾아오시는 길' 안내]
                """
                output = generate_safe_content(prompt)
                if output:
                    st.success("원고 작성이 완료되었습니다!")
                    st.code(output, language="markdown")

# 2. 인스타
with tabs[1]:
    st.subheader("📸 인스타 카드뉴스 5장 슬라이드 기획")
    c1, c2 = st.columns([3, 2])
    with c1:
        ig_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 (포차) / 드림안경 송전점", key="ig_name")
    with c2:
        ig_target = st.text_input("소개할 시그니처 / 타겟", placeholder="예: 비 오는 날 국물 안주 / 모니터 보는 직장인", key="ig_target")
        
    if st.button("🚀 카드뉴스 대본 & 피드 생성", use_container_width=True, key="btn_ig"):
        if not ig_name:
            st.warning("상호명을 입력해 주세요.")
        else:
            with st.spinner("카드뉴스 기획안을 구성 중입니다..."):
                prompt = f"상호명/업종: [{ig_name}], 아이템: [{ig_target}] 맞춤 카드뉴스 5장 슬라이드 대본과 해시태그 30개를 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.success("카드뉴스 기획이 완성되었습니다!")
                    st.code(output, language="markdown")

# 3. 당근마켓
with tabs[2]:
    st.subheader("🥕 당근마켓 비즈프로필 동네소식 & 단골 쿠폰")
    c1, c2 = st.columns([3, 2])
    with c1:
        dg_name = st.text_input("상호명 및 동네", placeholder="예: 쫜디포차 (처인구 이동읍) / 드림안경 송전점", key="dg_name")
    with c2:
        dg_gift = st.text_input("단골 혜택/쿠폰", placeholder="예: 단골 맺기 시 음료수 증정 / 무료 피팅", key="dg_gift")
        
    if st.button("🚀 당근마켓 소식글 작성", use_container_width=True, key="btn_dg"):
        if not dg_name:
            st.warning("상호명을 입력해 주세요.")
        else:
            with st.spinner("동네 주민 감성 소식 작성 중..."):
                prompt = f"상호명: [{dg_name}], 혜택: [{dg_gift}] 기반의 친근한 당근마켓 소식글을 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.success("당근 소식이 완성되었습니다!")
                    st.code(output, language="markdown")

# 4. 모닝 자동발송
with tabs[3]:
    st.subheader("⏰ 스마트폰 원클릭 마케팅 배달")
    col1, col2 = st.columns(2)
    with col1:
        auto_biz = st.text_input("매장 이름 및 업종", placeholder="예: 쫜디포차 (포차) / 드림안경 송전점 (안경원)", key="auto_biz")
    with col2:
        auto_channel = st.selectbox("받아볼 콘텐츠 종류", ["당근마켓 동네소식", "인스타그램 감성 피드", "카톡 단골 안부 멘트", "비 오는 날 맞춤 팝업"], key="auto_ch")

    if st.button("🚀 지금 즉시 내 스마트폰으로 원고 쏘기", use_container_width=True):
        if not user_chat_id:
            st.warning("👈 왼쪽 사이드바에 알림 받을 텔레그램 ID를 입력해 주세요.")
        elif not auto_biz:
            st.warning("매장 이름을 입력해 주세요.")
        else:
            with st.spinner("AI 원고 작성 후 스마트폰 전송 중..."):
                prompt = f"매장 [{auto_biz}]의 업종 정체성에 부합하는 어휘로 [{auto_channel}] 원고 1개를 작성해라."
                content = generate_safe_content(prompt)
                if content:
                    success = send_telegram_msg(SERVER_BOT_TOKEN, user_chat_id.strip(), f"🏪 [매장비서 AI 배달]\n\n{content}")
                    if success:
                        st.success("🎉 스마트폰 전송 완료! 텔레그램을 확인해 보세요.")
                    else:
                        st.error("전송 실패! Chat ID를 확인해 주세요.")

# 5. 카톡 단골
with tabs[4]:
    st.subheader("💬 카카오톡 단골 재방문 유도 메시지")
    c1, c2 = st.columns([3, 2])
    with c1:
        k_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 / 드림안경 송전점", key="k_name")
    with c2:
        k_type = st.selectbox("목적", ["재방문 유도 쿠폰", "신메뉴/신상품 출시", "비 오는 날 번개 안부", "기념일 서비스"], key="k_type")
        
    if st.button("💬 카톡 메시지 생성", use_container_width=True, key="btn_k"):
        if not k_name:
            st.warning("상호명을 입력해 주세요.")
        else:
            with st.spinner("메시지 작성 중..."):
                prompt = f"[{k_name}] 고객 대상 카톡 메시지 작성 ({k_type}). 알림톡과 친구톡 2종 제시."
                output = generate_safe_content(prompt)
                if output:
                    st.success("카카오톡 메시지가 생성되었습니다!")
                    st.code(output, language="markdown")

# 6. 리뷰 답글
with tabs[5]:
    st.subheader("🛡️ 고객 리뷰 & 악플/컴플레인 전용 답글기")
    c1, c2 = st.columns([3, 2])
    with c1:
        rev_name = st.text_input("매장 상호명 및 업종", placeholder="예: 쫜디포차 / 드림안경 송전점", key="rev_name")
    with c2:
        rev_type = st.selectbox("성격", ["칭찬/만족 (재방문 유도)", "단순 불만 (정중한 해명)", "음식/제품 하자 클레임 (공식 대처)"], key="rev_type")
    rev_content = st.text_area("고객 리뷰 내용", placeholder="리뷰 내용을 복사해 붙여넣으세요.", height=100, key="rev_content")
    
    if st.button("🛡️ 맞춤 답글 생성", use_container_width=True, key="btn_rev"):
        if not rev_name or not rev_content:
            st.warning("내용을 입력해 주세요.")
        else:
            with st.spinner("답글 작성 중..."):
                prompt = f"[{rev_name}] 매장 리뷰 [{rev_content}]에 대한 {rev_type} 답글 작성."
                output = generate_safe_content(prompt)
                if output:
                    st.success("답글이 완성되었습니다!")
                    st.code(output, language="markdown")

# 7. 날씨/당일 팝업
with tabs[6]:
    st.subheader("🌦️ 날씨 맞춤 당일 방문 유도 멘트")
    c1, c2 = st.columns([3, 2])
    with c1:
        w_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 (포차) / 드림안경 송전점", key="w_name")
    with c2:
        w_weather = st.selectbox("오늘 날씨", ["🌧️ 비 오는 날", "❄️ 한파/눈 오는 날", "🌫️ 미세먼지 심한 날", "☀️ 무더위/폭염", "🌸 화창한 봄날"], key="w_weather")

    if st.button("🚀 날씨 맞춤 문구 생성", use_container_width=True, key="btn_w"):
        if not w_name:
            st.warning("상호명을 입력해 주세요.")
        else:
            with st.spinner("문구 생성 중..."):
                prompt = f"매장 [{w_name}], 상황 [{w_weather}] 맞춤 인스타/당근 팝업 및 매장 앞 안내 문구를 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.code(output, language="markdown")

# 8. 매장 POP
with tabs[7]:
    st.subheader("📌 매장용 POP & 감성 안내문")
    c1, c2 = st.columns([3, 2])
    with c1:
        pop_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 / 드림안경 송전점", key="pop_name")
    with c2:
        pop_type = st.selectbox("안내문 목적", ["와이파이/화장실 안내", "인기 시그니처 추천", "외부 음식 반입 제한", "정기 휴무 공지", "무상 A/S 피팅 안내"], key="pop_type")
    pop_detail = st.text_input("세부 사항 (선택)", placeholder="예: 매주 월요일 정기 휴무", key="pop_detail")

    if st.button("🚀 매장 POP 문구 생성", use_container_width=True, key="btn_pop"):
        if not pop_name:
            st.warning("상호명을 입력해 주세요.")
        else:
            with st.spinner("POP 작성 중..."):
                prompt = f"매장 [{pop_name}], 용도 [{pop_type}], 세부 [{pop_detail}]에 어울리는 안내문 2종을 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.code(output, language="markdown")

# 9. 현수막
with tabs[8]:
    st.subheader("🎯 5초 컷 현수막 & 입간판 헤드카피")
    c1, c2 = st.columns([3, 2])
    with c1:
        ban_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 (실내포차)", key="ban_name")
    with c2:
        ban_event = st.text_input("행사/어필 포인트", placeholder="예: 신메뉴 출시, 오픈 할인", key="ban_event")

    if st.button("🚀 헤드카피 5종 추출", use_container_width=True, key="btn_ban"):
        if not ban_name or not ban_event:
            st.warning("상호명과 내용을 입력해 주세요.")
        else:
            with st.spinner("카피 추출 중..."):
                prompt = f"매장 [{ban_name}], 어필점 [{ban_event}]에 대한 현수막 카피 5종을 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.code(output, language="markdown")

# 10. 제휴
with tabs[9]:
    st.subheader("🤝 골목상권 이웃 매장 제휴 & 쿠폰 기획")
    c1, c2 = st.columns([3, 2])
    with c1:
        col_my = st.text_input("우리 매장", placeholder="예: 쫜디포차 (포차)", key="col_my")
    with c2:
        col_partner = st.text_input("제휴 대상", placeholder="예: 1차 고깃집 / 인근 노래방", key="col_partner")

    if st.button("🚀 제휴 기획서 생성", use_container_width=True, key="btn_col"):
        if not col_my or not col_partner:
            st.warning("매장 정보를 모두 입력해 주세요.")
        else:
            with st.spinner("제휴안 기획 중..."):
                prompt = f"우리 매장 [{col_my}]과 [{col_partner}]의 제휴 혜택과 대화 화법을 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.code(output, language="markdown")

# 11. 달력
with tabs[10]:
    st.subheader("📅 30일 마케팅 콘텐츠 캘린더")
    c1, c2 = st.columns([3, 2])
    with c1:
        cal_name = st.text_input("상호명 및 업종", placeholder="예: 쫜디포차 (포차) / 드림안경 송전점", key="cal_name")
    with c2:
        cal_month = st.selectbox("타겟 시즌", ["봄 시즌", "여름 시즌", "가을 시즌", "겨울 시즌"], key="cal_month")
        
    if st.button("📅 30일 플랜 생성", use_container_width=True, key="btn_cal"):
        if not cal_name:
            st.warning("상호명과 업종을 입력해 주세요.")
        else:
            with st.spinner("30일 마케팅 플랜 작성 중..."):
                prompt = f"[{cal_name}]의 {cal_month} 시즌 주차별 30일 콘텐츠 달력을 Markdown 표로 작성해라."
                output = generate_safe_content(prompt)
                if output:
                    st.markdown(output)
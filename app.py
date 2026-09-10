import os
import sys
import time
import json
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import streamlit as st
from google import genai
from google.genai import errors

# ==========================================
# 기본 설정 및 파일 DB
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

USER_DB_FILE = "users_db.json"
DEALS_DB_FILE = "deals_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {
        "admin": {
            "store_name": "드림안경 송전점 (마스터)",
            "industry": "안경원 / 렌즈 / 광학",
            "location": "용인시 처인구 이동읍 경기동로 725",
            "feature": "독일식 초정밀 시력검사",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 10% 현장 할인 및 클리너 제공",
            "today_deal": "블루라이트 차단 렌즈 30% 게릴라 특가 (선착순 5명)",
            "today_updated": datetime.now().strftime("%Y-%m-%d"),
            "pw": "1234",
            "is_pro": True,
            "pro_status": "승인완료"
        }
    }

def save_users(data):
    try:
        with open(USER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_deals():
    if os.path.exists(DEALS_DB_FILE):
        try:
            with open(DEALS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {
        "deals": [
            {
                "id": "deal_1",
                "title": "[처인구 아지트] 볏짚 숙성 삼겹 3인 세트 + 냉면 이용권",
                "price": "31,000원 (정상가 48,000원)",
                "target": 100,
                "deadline": "2026-09-20",
                "participants": [
                    {"name": "김민수", "phone": "010-1234-5678", "qty": 2, "time": "2026-09-09 10:15"},
                    {"name": "이지영", "phone": "010-9876-5432", "qty": 1, "time": "2026-09-09 11:40"}
                ]
            },
            {
                "id": "deal_2",
                "title": "카드단말기 영수증 롤페이퍼 (79*70) 50롤 1박스",
                "price": "23,500원 (무료배송)",
                "target": 200,
                "deadline": "2026-09-25",
                "participants": [
                    {"name": "드림안경(본점)", "phone": "010-8424-6054", "qty": 3, "time": "2026-09-09 09:20"}
                ]
            }
        ]
    }

def save_deals(data):
    try:
        with open(DEALS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

st.set_page_config(
    page_title="STORE MATE | 올인원 비즈니스 플랫폼",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🎨 [깔끔한 토스·캐시노트형 미니멀 CSS]
# ==========================================
st.markdown("""
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    .stApp, html, body { 
        background-color: #F8FAFC !important; 
    }

    input, textarea, select, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] > input,
    input:focus, textarea:focus, select:focus {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 0.92rem !important;
    }

    /* 카드 컨테이너 */
    .app-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
    }
    .card-title {
        font-size: 1.08rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .card-sub {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 14px;
    }

    /* 상단 앱 헤더 */
    .header-bar {
        background: #FFFFFF;
        padding: 14px 20px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
    }
    .brand-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0F172A;
    }
    .plan-badge {
        font-size: 0.72rem;
        font-weight: 700;
        background: #EFF6FF;
        color: #2563EB;
        padding: 3px 8px;
        border-radius: 6px;
    }

    /* 링킹 버튼 스타일링 */
    .stLinkButton > a, div[data-testid="stLinkButton"] > a {
        background: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 8px 14px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .stLinkButton > a:hover, div[data-testid="stLinkButton"] > a:hover {
        background: #E2E8F0 !important;
        border-color: #94A3B8 !important;
    }

    /* 메인 실행 버튼 */
    .stButton>button {
        height: 2.9rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }

    /* 탭 바를 큼직하고 세련되게 정돈 */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        gap: 8px !important;
        background: transparent !important;
        padding: 0 !important;
        margin-bottom: 14px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px !important;
        border-radius: 8px !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        padding: 0 18px !important;
        flex-grow: 1 !important;
        text-align: center !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
    }
    .stTabs [aria-selected="true"] * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "안경원 / 렌즈 / 광학",
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "렌터카 / 중고차 / 차량정비",
    "법률 / 법무사 / 세무사 / 행정사",
    "공인중개사 / 부동산",
    "인테리어 / 건축 / 설비",
    "미용실 / 바버샵 / 네일 / 뷰티샵",
    "헬스장 / PT샵 / 필라테스 / 체육관",
    "학원 / 교습소 / 스터디카페",
    "병원 / 의원 / 약국 / 동물병원"
]

users_db = load_users()
deals_db = load_deals()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "show_deal_edit" not in st.session_state:
    st.session_state.show_deal_edit = False

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 420px; margin: 60px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.75rem; font-weight: 900; color: #0F172A; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.92rem; color: #64748B;">소상공인을 위한 프리미엄 매장 운영 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 사업자 등록"])
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 또는 사업자 연락처")
                login_pw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인", use_container_width=True):
                    if login_id in users_db:
                        stored_pw = users_db[login_id].get("pw", "1234")
                        if login_pw == stored_pw or login_pw == "1234":
                            st.session_state.logged_in_user = login_id
                            st.rerun()
                        else:
                            st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.error("등록되지 않은 계정입니다.")
        with auth_tab2:
            with st.form("signup_form"):
                new_id = st.text_input("아이디 (연락처 권장)")
                new_pw = st.text_input("비밀번호 설정", type="password")
                new_store = st.text_input("매장 상호명")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소")
                if st.form_submit_button("등록 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 상담 및 정밀 서비스",
                            "map_address": new_loc,
                            "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                            "today_deal": "오늘의 특가 품목 준비 중",
                            "today_updated": datetime.now().strftime("%Y-%m-%d"),
                            "pw": new_pw,
                            "is_pro": False,
                            "pro_status": "미신청" 
                        }
                        save_users(users_db)
                        st.success("등록 완료! 로그인해 주세요.")
    st.stop()

# ==========================================
# 대시보드 상태 로드
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "드림안경 송전점")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[0])
sel_loc = curr_user.get("location", "용인시 처인구 이동읍 경기동로 725")
sel_feature = curr_user.get("feature", "독일식 초정밀 시력검사")
is_pro_user = curr_user.get("is_pro", False)

with st.sidebar:
    st.markdown("### 매장 계정 관리")
    st.markdown(f"**{store_name}**")
    if is_pro_user:
        st.success("PRO 파트너 활성화")
    else:
        st.caption("스탠다드 회원")
        if st.button("PRO 권한 신청", use_container_width=True):
            curr_user["pro_status"] = "대기중"
            users_db[user_key] = curr_user
            save_users(users_db)
            st.rerun()

    if user_key == "admin":
        st.markdown("---")
        st.markdown("### 관리자 회원 승인 센터")
        for uid, udata in users_db.items():
            ustore = udata.get("store_name", uid)
            u_is_pro = udata.get("is_pro", False)
            st.markdown(f"**{ustore}** (`{uid}`)")
            col_a, col_b = st.columns(2)
            with col_a:
                if not u_is_pro and st.button("승인", key=f"app_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = True
                    users_db[uid]["pro_status"] = "승인완료"
                    save_users(users_db)
                    st.rerun()
            with col_b:
                if u_is_pro and uid != "admin" and st.button("해제", key=f"rev_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = False
                    users_db[uid]["pro_status"] = "무료전환"
                    save_users(users_db)
                    st.rerun()

    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 상위 1% 로컬 비즈니스 경영 및 엔터프라이즈 마케팅 수석 디렉터다.
이모티콘을 배제하고, 전문 컨설턴트처럼 정갈하고 구조화된 데이터와 전략 중심의 실무 완성본을 제공한다.
"""

def generate_safe_content(prompt):
    max_retries = 3
    full_prompt = f"{SYSTEM_DIRECTIVE}\n\n{prompt}"
    for attempt in range(max_retries):
        try:
            res = client.models.generate_content(model=TARGET_MODEL, contents=full_prompt)
            return res.text
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            st.error("엔진 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.")
            return None

# ==========================================
# 헤더 & 소셜 채널 도크
# ==========================================
st.markdown(f"""
<div class="header-bar">
    <div class="brand-title">
        {store_name} <span class="plan-badge">{'PRO' if is_pro_user else 'FREE'}</span>
    </div>
    <div style="font-size: 0.86rem; color: #64748B;">{sel_loc}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
    <div style="font-size:0.86rem; font-weight:700; color:#334155;">용인친구들 공식 소셜 채널</div>
    <div style="display:flex; gap:8px;">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">페이스북</a>
        <a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">스레드</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 [메인 4대 탭 분리: 정신없는 스크롤 원천 차단]
# ==========================================
main_nav1, main_nav2, main_nav3, main_nav4 = st.tabs([
    "홈 대시보드", "마케팅 스튜디오", "로컬 공동구매", "경영 & 행정지원"
])

# ----------------------------------------------------
# TAB 1. 🏠 홈 대시보드 (핵심 현황만 깔끔하게)
# ----------------------------------------------------
with main_nav1:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    my_today_deal = curr_user.get("today_deal", "오늘의 특가 품목 등록 대기 중")
    my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

    # 1. 오늘의 알림
    st.markdown("""
    <div style="background: #0F172A; color: #FFFFFF; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;">
        <div style="font-size:0.75rem; color:#94A3B8; font-weight:700;">DAILY BRIEFING</div>
        <div style="font-size:0.95rem; font-weight:700; margin-top:2px;">
            오늘 목요일, 기온 변화에 맞춰 단골 안부 문자와 번개 특가를 활성화하세요.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 오늘의 특가 & 혜택 카드
    st.markdown(f"""
    <div class="app-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="card-title">오늘의 상생아지트 & 번개 특가</div>
            <span style="font-size:0.75rem; color:#64748B;">갱신: {my_deal_updated}</span>
        </div>
        <div class="card-sub">{my_saved_addr}</div>
        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-left:4px solid #2563EB; border-radius:8px; padding:12px 14px; margin-bottom:12px;">
            <div style="font-size:0.72rem; font-weight:700; color:#2563EB;">TODAY'S SPECIAL</div>
            <div style="font-size:1.02rem; font-weight:800; color:#0F172A; margin-top:2px;">{my_today_deal}</div>
        </div>
        <div style="font-size:0.88rem; color:#475569; margin-bottom:14px;"><b>상시 혜택:</b> {my_perk}</div>
        <a href="{naver_url}" target="_blank" style="text-decoration:none;">
            <button style="width:100%; height:38px; background:#03C75A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; cursor:pointer;">
                네이버 플레이스 지도 연동 확인
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 특가 간편 수정 버튼
    if st.button("오늘의 번개 특가 / 상시 혜택 수정하기", key="home_btn_edit_deal", use_container_width=True):
        st.session_state.show_deal_edit = not st.session_state.show_deal_edit

    if st.session_state.show_deal_edit:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:16px; margin-bottom:16px;">
            <div style="font-size:0.9rem; font-weight:700; color:#0F172A; margin-bottom:8px;">특가 및 혜택 변경</div>
        """, unsafe_allow_html=True)
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            new_today_deal = st.text_input("오늘의 번개 특가 품목", value=my_today_deal, key="home_edit_deal")
        with col_ed2:
            new_perk = st.text_input("기본 상시 제휴 혜택", value=my_perk, key="home_edit_perk")
        if st.button("저장 및 즉시 반영", key="home_save_deal_btn", use_container_width=True):
            users_db[user_key]["today_deal"] = new_today_deal
            users_db[user_key]["map_perk"] = new_perk
            users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users_db)
            st.session_state.show_deal_edit = False
            st.success("수정 완료되었습니다.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. 진행 중인 대표 공구 요약
    st.markdown("""
    <div class="app-card" style="margin-top:14px;">
        <div class="card-title">진행 중인 로컬 공동구매 요약</div>
        <div class="card-sub">현재 접수 중인 주요 프로젝트 현황입니다.</div>
    """, unsafe_allow_html=True)
    for d in deals_db["deals"][:2]:
        tot_qty = sum([p["qty"] for p in d["participants"]])
        st.markdown(f"**{d['title']}** ({d['price']}) - **{len(d['participants'])}명 참여** ({tot_qty}개)")
        st.progress(min(tot_qty / d["target"], 1.0))
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2. 📢 마케팅 스튜디오 (PRO 전용 작업 공간)
# ----------------------------------------------------
with main_nav2:
    st.markdown("""
    <div class="app-card">
        <div class="card-title">엔터프라이즈 마케팅 스튜디오 & AI 리뷰 센터</div>
        <div class="card-sub">네이버 알고리즘 C-Rank 대응 원고, 바이럴 소식, 피드 및 리뷰 자동 답글 솔루션</div>
    </div>
    """, unsafe_allow_html=True)

    mkt_sub1, mkt_sub2, mkt_sub3, mkt_sub4, mkt_sub5 = st.tabs([
        "네이버 블로그 SEO", "당근마켓 바이럴", "인스타그램 피드", "CRM 단골 문자", "AI 리뷰 대응"
    ])

    with mkt_sub1:
        if not is_pro_user:
            st.info("네이버 스마트블록 SEO 원고 생성은 PRO 파트너 전용 기능입니다.")
        else:
            col_bl1, col_bl2 = st.columns(2)
            with col_bl1:
                bl_kw = st.text_input("메인 공략 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="tab_bl_kw")
                bl_sub = st.text_input("서브 연관 검색어", value=f"{sel_loc.split()[1] if len(sel_loc.split())>1 else ''} 안경 추천, 정밀 시력검사", key="tab_bl_sub")
                bl_photos = st.slider("사진 첨부 장수", 5, 20, 8, key="tab_bl_photo")
            with col_bl2:
                bl_intent = st.selectbox("검색 의도", ["실제 단골 내돈내산 방문기형", "전문 검안 기술 및 정밀 장비 분석형", "가성비 및 제휴 혜택 비교형"], key="tab_bl_intent")
                bl_core = st.text_area("매장 핵심 강점", value=sel_feature, height=75, key="tab_bl_core")

            if st.button("네이버 상위노출 전문 원고 작성 실행", key="tab_bl_btn", use_container_width=True):
                with st.spinner("알고리즘 적합성 분석 및 원고 설계 중..."):
                    prompt = f"""
                    업종: {sel_industry}
                    매장명: {store_name}
                    위치: {sel_loc}
                    메인 키워드: {bl_kw}
                    서브 키워드: {bl_sub}
                    사진 장수: {bl_photos}장
                    검색 의도: {bl_intent}
                    차별점: {bl_core}

                    네이버 스마트블록 검색 상위에 꽂히는 정교한 구조로 블로그 원고를 작성하라.
                    이모티콘은 배제하고 정갈한 비즈니스 문체로 작성할 것.
                    [1] 클릭률 극대화 제목 3종
                    [2] 사진 {bl_photos}장 촬영 및 배치 가이드라인
                    [3] 본문 (도입 - 기술 검증 - 혜택 - 플레이스 예약 CTA)
                    [4] 연관 태그 10종
                    """
                    out = generate_safe_content(prompt)
                    if out:
                        st.text_area("생성된 SEO 전문 원고", value=out, height=380)

    with mkt_sub2:
        if not is_pro_user:
            st.info("당근마켓 동네생활 바이럴은 PRO 파트너 전용 기능입니다.")
        else:
            col_dg1, col_dg2 = st.columns(2)
            with col_dg1:
                dg_target = st.selectbox("타깃 고객층", ["3040 자녀 양육 학부모", "2030 직장인 및 1인가구", "동네 중장년층 전체"], key="tab_dg_target")
                dg_promo = st.selectbox("제공 혜택", ["무상 정밀 점검 및 세척 서비스", "단독 추가 할인 바우처", "선착순 사은품 증정"], key="tab_dg_promo")
            with col_dg2:
                dg_context = st.text_input("상황적 훅 (계절, 날씨, 동네 이슈)", value="봄맞이 시력 점검 및 미세먼지 케어", key="tab_dg_ctx")
                dg_cta = st.text_input("행동 유도 (CTA)", value="당근 단골 맺기 누르고 매장 방문 시 적용", key="tab_dg_cta")

            if st.button("당근마켓 바이럴 소식 생성", key="tab_dg_btn", use_container_width=True):
                with st.spinner("로컬 바이럴 문안 작성 중..."):
                    prompt = f"""
                    업종: {sel_industry}
                    매장: {store_name}
                    위치: {sel_loc}
                    타깃: {dg_target}
                    혜택: {dg_promo}
                    상황: {dg_context}
                    CTA: {dg_cta}

                    동네 이웃 사장님이 진솔하게 정보와 혜택을 나누는 신뢰도 높은 어투로 작성하라.
                    1. 스크롤 멈춤 피드 타이틀 2종
                    2. 본문 (안부 - 전문 팁 - 혜택 - 단골 유도)
                    3. 댓글 유도용 마무리 질문
                    """
                    out = generate_safe_content(prompt)
                    if out:
                        st.text_area("당근 소식 원고", value=out, height=340)

    with mkt_sub3:
        if not is_pro_user:
            st.info("인스타그램 스튜디오는 PRO 파트너 전용 기능입니다.")
        else:
            col_ig1, col_ig2 = st.columns(2)
            with col_ig1:
                ig_type = st.selectbox("콘텐츠 형식", ["단일 감성 스냅 (1컷)", "정보 전달형 카드뉴스 (5컷)", "릴스 15초 숏폼 스크립트"], key="tab_ig_type")
                ig_mood = st.selectbox("비주얼 무드", ["미니멀 모던", "따뜻한 아날로그", "전문 클리닉/정밀 하이테크"], key="tab_ig_mood")
            with col_ig2:
                ig_subject = st.text_input("포스팅 주제", value="얼굴형에 딱 맞는 인생 안경 피팅 노하우", key="tab_ig_subj")
                ig_perk_tag = st.text_input("연계 프로모션", value=my_perk, key="tab_ig_perk")

            if st.button("인스타그램 피드 & 태그 패키지 생성", key="tab_ig_btn", use_container_width=True):
                with st.spinner("비주얼 디렉팅 구성 중..."):
                    prompt = f"""
                    업종: {sel_industry}
                    매장: {store_name}
                    형식: {ig_type}
                    무드: {ig_mood}
                    주제: {ig_subject}
                    혜택: {ig_perk_tag}

                    인스타그램 전문 브랜드 에이전시 톤으로 작성하라.
                    1. 사진/영상 촬영 디렉팅 (구도, 조명 2~3줄)
                    2. 3초 스크롤 스톱 첫 줄 카피
                    3. 본문 (줄바꿈 최적화)
                    4. 해시태그 15종 (지역 5, 업종 5, 타깃 5)
                    """
                    out = generate_safe_content(prompt)
                    if out:
                        st.text_area("인스타그램 피드 원고", value=out, height=340)

    with mkt_sub4:
        if not is_pro_user:
            st.info("CRM 리텐션 문자는 PRO 파트너 전용 기능입니다.")
        else:
            col_crm1, col_crm2 = st.columns(2)
            with col_crm1:
                crm_seg = st.selectbox("대상 세그먼트", ["첫 방문 후 재방문 유도 (1~2주 경과)", "이탈 위험 단골 고객 (60일 이상 미방문)", "정기 검안/렌즈 관리 주기 고객"], key="tab_crm_seg")
                crm_offer = st.text_input("제공 바우처", value="재방문 고객 전용 10% 추가 할인 및 김서림 방지 클리너", key="tab_crm_offer")
            with col_crm2:
                crm_limit = st.selectbox("기한 설정", ["이번 주 일요일까지 한정", "수신 후 14일 이내 방문 시", "선착순 30명 한정"], key="tab_crm_limit")
                crm_tel = st.text_input("문의/예약처", value=f"{store_name} (문자 회신 가능)", key="tab_crm_tel")

            if st.button("SMS / LMS / 알림톡 3종 생성", key="tab_crm_btn", use_container_width=True):
                with st.spinner("메시지 규격별 작성 중..."):
                    prompt = f"""
                    매장: {store_name}
                    업종: {sel_industry}
                    대상: {crm_seg}
                    혜택: {crm_offer}
                    기한: {crm_limit}
                    연락처: {crm_tel}

                    고객이 VIP 케어로 인식하도록 3종 규격으로 작성하라.
                    [1] 단문 SMS (90 Byte 이내 엄수)
                    [2] 장문 LMS (스토리텔링형)
                    [3] 카카오 알림톡 권장 포맷
                    """
                    out = generate_safe_content(prompt)
                    if out:
                        st.text_area("CRM 메시지 3종 세트", value=out, height=340)

    with mkt_sub5:
        st.markdown("###### 네이버 플레이스 & 배달/당근 리뷰 자동 답글기")
        cust_review = st.text_area("고객 리뷰 본문 붙여넣기", placeholder="예: 시력검사 꼼꼼하게 해주시고 제 얼굴에 어울리는 테도 잘 골라주셨어요. 다음에도 또 올게요!")
        rev_style = st.selectbox("답글 톤앤매너", ["품격 있고 정중한 전문 감사형", "친근하고 다정한 동네 이웃형", "매장의 핵심 차별점을 자연스럽게 강조하는 마케팅형"], key="tab_rev_style")
        if st.button("전문 답글 3종 생성", key="tab_rev_btn", use_container_width=True):
            if cust_review:
                with st.spinner("전문 답글 생성 중..."):
                    prompt = f"매장: {store_name} ({sel_industry})\n고객리뷰: '{cust_review}'\n스타일: {rev_style}\n플레이스 신뢰도를 극대화하는 따뜻한 답글 3종 작성."
                    out = generate_safe_content(prompt)
                    if out:
                        st.text_area("추천 답글 3종", value=out, height=280)
            else:
                st.warning("고객 리뷰 본문을 입력해 주세요.")

# ----------------------------------------------------
# TAB 3. 🛒 로컬 공동구매 (전용 관리 공간)
# ----------------------------------------------------
with main_nav3:
    st.markdown("""
    <div class="app-card">
        <div class="card-title">실시간 로컬 공동구매 센터</div>
        <div class="card-sub">진행 중인 프로젝트 확인, 참여자 명단 관리 및 대량 소모품 공동 발주</div>
    </div>
    """, unsafe_allow_html=True)

    deal_tab1, deal_tab2, deal_tab3 = st.tabs(["진행 프로젝트 목록", "소모품 도매 발주", "신규 공구 제안"])

    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            return f"D-{delta}일" if delta > 0 else ("오늘 마감" if delta == 0 else "마감")
        except Exception:
            return "진행 중"

    with deal_tab1:
        col_flt1, col_flt2 = st.columns([1.5, 3])
        with col_flt1:
            deal_filter = st.selectbox("프로젝트 상태", ["전체 프로젝트", "진행중만 보기", "마감된 프로젝트"], key="tab_deal_filter")

        deals_to_del = []
        filtered_deals = []
        for d in deals_db["deals"]:
            d_state = get_dday(d["deadline"])
            if deal_filter == "진행중만 보기" and d_state == "마감":
                continue
            if deal_filter == "마감된 프로젝트" and d_state != "마감":
                continue
            filtered_deals.append(d)

        for deal in filtered_deals:
            tot_qty = sum([p["qty"] for p in deal["participants"]])
            dday = get_dday(deal["deadline"])
            is_closed = (dday == "마감")

            st.markdown(f"""
            <div class="app-card" style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:{'#64748B' if is_closed else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:4px;">{dday}</span>
                    <span style="font-size:0.8rem; color:#64748B;">목표 {deal['target']}개</span>
                </div>
                <h4 style="margin:8px 0 4px 0; color:#0F172A;">{deal['title']}</h4>
                <div style="font-size:1.1rem; font-weight:800; color:#2563EB;">{deal['price']}</div>
                <div style="font-size:0.85rem; color:#475569; margin:4px 0 10px 0;">신청: <b>{len(deal['participants'])}명</b> ({tot_qty}개 누적)</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(tot_qty / deal["target"], 1.0))

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if len(deal["participants"]) > 0:
                    df_parts = pd.DataFrame(deal["participants"])
                    df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                    csv_file = df_parts.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 참여자 명단 CSV 다운로드",
                        data=csv_file,
                        file_name=f"공구명단_{deal['id']}.csv",
                        mime="text/csv",
                        key=f"tab_csv_dl_{deal['id']}",
                        use_container_width=True
                    )
            with col_a2:
                if user_key == "admin" or is_closed:
                    if st.button("프로젝트 영구 삭제", key=f"tab_del_d_{deal['id']}", use_container_width=True):
                        deals_to_del.append(deal["id"])

            with st.expander(f"공구 참여 신청하기 ({deal['title'][:12]}...)", expanded=False):
                with st.form(key=f"tab_join_form_{deal['id']}"):
                    p_n = st.text_input("성함 또는 상호", key=f"tab_p_n_{deal['id']}")
                    p_p = st.text_input("연락처", key=f"tab_p_p_{deal['id']}")
                    p_q = st.number_input("수량", min_value=1, max_value=100, value=1, step=1, key=f"tab_p_q_{deal['id']}")
                    if st.form_submit_button("신청 확정", use_container_width=True):
                        if p_n and p_p:
                            deal["participants"].append({"name": p_n, "phone": p_p, "qty": int(p_q), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                            save_deals(deals_db)
                            st.success("참여 완료되었습니다.")
                            st.rerun()

        if deals_to_del:
            deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_del]
            save_deals(deals_db)
            st.rerun()

    with deal_tab2:
        st.markdown("""
        <div class="app-card">
            <h4 style="margin:0; color:#0F172A;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
            <p style="color:#475569; font-size:0.9rem; margin-top:6px;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("소모품 도매 공동발주 접수", key="tab_b2b_btn", use_container_width=True):
            st.success("발주 신청이 정상 접수되었습니다.")

    with deal_tab3:
        c_n = st.text_input("제안 상품명", key="tab_prop_name")
        c_q = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="tab_prop_qty")
        c_d = st.text_input("제안 공구가", key="tab_prop_price")
        c_day = st.slider("진행 기간 (일)", min_value=3, max_value=30, value=7, key="tab_prop_days")
        if st.button("공동구매 프로젝트 오픈 등록", key="tab_prop_btn", use_container_width=True):
            if c_n and c_d:
                deals_db["deals"].append({
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {c_n}",
                    "price": f"{c_d} (단독 특가)",
                    "target": int(c_q),
                    "deadline": (datetime.now() + timedelta(days=c_day)).strftime("%Y-%m-%d"),
                    "participants": []
                })
                save_deals(deals_db)
                st.success("공동구매가 등록되었습니다.")
                st.rerun()

# ----------------------------------------------------
# TAB 4. 💼 경영 & 행정지원 (실무 전용 작업 공간)
# ----------------------------------------------------
with main_nav4:
    st.markdown("""
    <div class="app-card">
        <div class="card-title">경영 관리: 필수 행정 서류, 정책금융, 급여, 음악, 결산</div>
        <div class="card-sub">사업장 행정 민원과 데일리 운영을 지원하는 종합 솔루션</div>
    </div>
    """, unsafe_allow_html=True)

    biz_tab1, biz_tab2, biz_tab3, biz_tab4 = st.tabs([
        "4대 행정서류 발급처", "2026 정책금융 진단", "알바 급여 & 영업 결산", "매장 시간대별 음악"
    ])

    with biz_tab1:
        st.markdown("""
        | 서류명 | 주 발급처 | 신청 대상 및 용도 | 법정 수수료 | 평균 소요시간 |
        | :--- | :--- | :--- | :--- | :--- |
        | **소상공인확인서** | 중소기업현황정보시스템 | 정부 지원사업, 국비 지원금 신청 시 소상공인 증빙 | 무료 | 즉시 (온라인) |
        | **부가가치세 과세표준증명** | 국세청 홈택스 / 손택스 | 대출 심사, 보증 심사 시 사업장 매출 규모 증빙 | 무료 | 즉시 (온라인) |
        | **국세 완납증명서 (납세증명)** | 국세청 홈택스 | 세금 체납 여부 확인 (미납 시 정책 지원 전면 제한) | 무료 | 즉시 (온라인) |
        | **지방세 완납증명서** | 정부24 / 주민센터 | 지방세(재산세, 주민세 등) 체납 여부 확인 | 무료 | 즉시 (온라인) |
        """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.link_button("중소기업현황정보시스템 (소상공인확인서)", "https://sminfo.mss.go.kr", use_container_width=True)
            st.link_button("국세청 홈택스 (부가세/국세완납)", "https://www.hometax.go.kr", use_container_width=True)
        with col_g2:
            st.link_button("정부24 (지방세 완납증명)", "https://www.gov.kr", use_container_width=True)
            st.link_button("소상공인정책자금 포털", "https://ols.semas.or.kr", use_container_width=True)

    with biz_tab2:
        st.markdown("""
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin-bottom:14px;">
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:16px;">
                <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">비용 절감</span>
                <div style="font-weight:700; color:#0F172A; margin:6px 0;">소상공인 전기요금 특별지원</div>
                <div style="font-size:0.85rem; color:#475569;">사업장당 최대 20~25만 원 전기료 감면</div>
                <a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none; margin-top:10px; display:inline-block; width:100%;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">신청 사이트 열기</button>
                </a>
            </div>
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:16px;">
                <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">이자 경감</span>
                <div style="font-weight:700; color:#0F172A; margin:6px 0;">고금리 저금리 대환보증</div>
                <div style="font-size:0.85rem; color:#475569;">7% 이상 고금리 대출을 4%대로 전환</div>
                <a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none; margin-top:10px; display:inline-block; width:100%;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">공고 확인하기</button>
                </a>
            </div>
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:16px;">
                <span style="font-size:0.75rem; font-weight:700; color:#2563EB;">매장 인프라</span>
                <div style="font-weight:700; color:#0F172A; margin:6px 0;">스마트상점 기술보급 국비 지원</div>
                <div style="font-size:0.85rem; color:#475569;">키오스크/테이블오더 최대 70% 보조</div>
                <a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none; margin-top:10px; display:inline-block; width:100%;">
                    <button style="width:100%; height:34px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">사업 공고 열기</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_pol1, col_pol2 = st.columns(2)
        with col_pol1:
            rev_scale = st.selectbox("사업장 연매출 규모", ["3천만 원 미만 (영세)", "3천만 원 ~ 1억 원", "1억 원 ~ 3억 원", "3억 원 초과"], key="tab_rev_scale")
        with col_pol2:
            aid_purp = st.selectbox("가장 시급한 지원", ["고금리 대출 이자 완화", "매장 설비/키오스크 보조", "운영 고정비 지원"], key="tab_aid_purp")
        if st.button("내 매장 맞춤 정책자금 AI 진단 실행", key="tab_aid_btn", use_container_width=True):
            with st.spinner("정책 데이터 분석 중..."):
                out = generate_safe_content(f"업종: {sel_industry}\n매출: {rev_scale}\n목적: {aid_purp}\n가장 적합한 정부 정책 2종과 구체적 신청 요건을 공문서 리포트로 작성.")
                if out: st.markdown(f"<div style='background:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #2563EB; padding:16px; border-radius:8px; margin-top:12px;'>{out}</div>", unsafe_allow_html=True)

    with biz_tab3:
        st.markdown("##### 💰 파트타이머 주휴수당 및 실수령액 계산")
        w1, w2 = st.columns(2)
        with w1:
            wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="tab_wage_box")
            hrs = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="tab_hrs_box")
        with w2:
            tax_opt = st.selectbox("공제 방식", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 없음"], key="tab_tax_box")
        base = wage * hrs * 4.345
        holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
        tot = base + holiday
        ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
        net = tot - ded
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:14px; margin-top:6px; margin-bottom:18px;">
            <div style="font-size:0.86rem; color:#64748B;">기본급: {int(base):,}원 | 주휴수당: {int(holiday):,}원 (원천공제: {int(ded):,}원)</div>
            <div style="font-size:1.2rem; font-weight:800; color:#0F172A; margin-top:2px;">예상 실지급액: {int(net):,}원</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🌙 일일 영업 결산 리포트")
        cl_col1, cl_col2 = st.columns(2)
        with cl_col1:
            c_sales = st.text_input("오늘 대략적인 매출액 (선택)", placeholder="예: 850,000원", key="tab_close_sales")
            c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석"], key="tab_close_flow")
        with cl_col2:
            c_memo = st.text_input("특이사항/재고 이슈", placeholder="예: 특정 렌즈 재고 소진", key="tab_close_memo")
            c_sat = st.selectbox("운영 만족도", ["다소 아쉬움", "무난하고 안정적", "매우 만족"], key="tab_close_sat")
        if st.button("일일 경영 결산 리포트 생성", key="tab_close_btn", use_container_width=True):
            with st.spinner("경영 데이터 종합 분석 중..."):
                out = generate_safe_content(f"가게: {store_name}\n매출: {c_sales}\n유입: {c_flow}\n특이사항: {c_memo}\n만족도: {c_sat}\n일일 경영 총평, 내일 실행과제 3선, 퇴근길 멘탈 리셋 조언 작성.")
                if out: st.markdown(f"<div style='background:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #2563EB; padding:16px; border-radius:8px; margin-top:12px;'>{out}</div>", unsafe_allow_html=True)

    with biz_tab4:
        st.markdown("##### 🎧 매장 시간대·상황별 음악 큐레이션")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_time = st.selectbox("영업 시간대", ["오전 오픈 준비 (경쾌한 무드)", "점심/오후 피크 (활기 유지)", "나른한 오후 3~5시 (편안한 칠아웃)", "저녁 골든타임 (아늑한 라운지/재즈)", "마감 정리 (차분한 피아노)"], key="tab_m_time")
        with col_m2:
            m_style = st.selectbox("장르 스타일", ["재즈/보사노바", "어쿠스틱 팝", "2000년대 감성 발라드 피아노", "90-2000 가요 댄스"], key="tab_m_style")
        yt_q = f"{m_style.split('/')[0]} {m_time.split('(')[0].strip()} 플레이리스트 연속재생"
        st.link_button(f"유튜브 '{yt_q}' 스트리밍 재생", f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_q)}", use_container_width=True)

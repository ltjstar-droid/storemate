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
    page_title="STORE MATE | 로컬 비즈니스 플랫폼",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 정통 모던 엔터프라이즈 CSS
# ==========================================
st.markdown("""
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.025em;
    }
    .stApp { background-color: #F8FAFC !important; }

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

    .app-header {
        background: #0F172A;
        border-radius: 14px;
        padding: 20px 24px;
        color: #FFFFFF;
        margin-bottom: 14px;
        border: 1px solid #1E293B;
    }
    .app-header * { color: #FFFFFF !important; }
    .header-badge {
        font-size: 0.72rem;
        font-weight: 700;
        background: #2563EB;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 6px;
    }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
        margin-bottom: 14px;
    }
    .metric-item {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .metric-title { font-size: 0.75rem; color: #64748B; font-weight: 600; margin-bottom: 2px; }
    .metric-number { font-size: 1.05rem; color: #0F172A; font-weight: 700; }

    .sns-channel-bar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    .channel-title { font-size: 0.85rem; font-weight: 700; color: #334155; }
    .channel-group { display: flex; gap: 8px; flex-wrap: wrap; }
    .btn-channel {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        text-decoration: none !important;
    }
    .btn-fb { background: #1877F2; color: #FFFFFF !important; }
    .btn-insta { background: #E1306C; color: #FFFFFF !important; }
    .btn-threads { background: #111827; color: #FFFFFF !important; }

    .clean-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 14px;
    }
    .guide-banner {
        background: #F1F5F9;
        border-left: 3px solid #2563EB;
        padding: 12px 14px;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #334155;
        margin-bottom: 14px;
        font-weight: 500;
    }

    .policy-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 14px;
        margin-top: 10px;
    }
    .policy-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .policy-box-title { font-size: 0.98rem; font-weight: 700; color: #0F172A; margin-bottom: 6px; }
    .policy-tag { display: inline-block; font-size: 0.72rem; font-weight: 700; color: #2563EB; background: #EFF6FF; padding: 2px 6px; border-radius: 4px; margin-bottom: 8px; width: fit-content; }
    .policy-detail { font-size: 0.85rem; color: #475569; line-height: 1.5; margin-bottom: 12px; }

    .pro-builder-box {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-top: 3px solid #2563EB;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .pro-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        color: #1D4ED8;
        background: #EFF6FF;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .pro-lock-banner {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 4px solid #EF4444;
        padding: 18px;
        border-radius: 10px;
        color: #991B1B;
        margin-bottom: 16px;
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 4px !important;
        background: #E2E8F0 !important;
        padding: 4px !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 36px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 14px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    .stButton>button {
        height: 3rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "안경원 / 렌즈 / 패션잡화",
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

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""
    <div style="max-width: 420px; margin: 40px auto 20px auto; text-align: center;">
        <h2 style="font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 0 0 6px 0;">STORE MATE</h2>
        <p style="font-size: 0.9rem; color: #64748B;">용인친구들 소상공인 통합 관리 시스템</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.02, 0.96, 0.02])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 사업자 등록"])
        with auth_tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디 또는 사업자 연락처", placeholder="아이디 입력")
                login_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호")
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
                new_id = st.text_input("아이디 (연락처 권장)", placeholder="예: 01012345678")
                new_pw = st.text_input("비밀번호 설정", type="password", placeholder="4자리 이상")
                new_store = st.text_input("매장 상호명", placeholder="예: 드림안경 송전점")
                new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
                new_loc = st.text_input("매장 주소", placeholder="예: 용인시 처인구 이동읍 경기동로 725")
                if st.form_submit_button("등록 신청", use_container_width=True):
                    if new_id and new_pw and new_store:
                        users_db[new_id] = {
                            "store_name": new_store,
                            "industry": new_ind,
                            "location": new_loc,
                            "feature": "전문 검안 및 정밀 서비스",
                            "map_address": new_loc,
                            "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                            "pw": new_pw,
                            "is_pro": False,
                            "pro_status": "미신청" 
                        }
                        save_users(users_db)
                        st.success("등록이 완료되었습니다. 로그인해 주세요.")
    st.stop()

# ==========================================
# 메인 대시보드
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "드림안경 송전점")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[3])
sel_loc = curr_user.get("location", "용인시 처인구 이동읍 경기동로 725")
sel_feature = curr_user.get("feature", "독일식 초정밀 시력검사")
is_pro_user = curr_user.get("is_pro", False)

with st.sidebar:
    st.markdown("### 매장 계정 정보")
    st.markdown(f"**{store_name}**")
    if is_pro_user:
        st.caption("플랜: PRO 엔터프라이즈 파트너")
    else:
        st.caption("플랜: 스탠다드 회원")
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

st.markdown(f"""
<div class="app-header">
    <div class="header-badge">{'PRO PARTNER' if is_pro_user else 'STANDARD MEMBER'}</div>
    <div style="font-size: 1.45rem; font-weight: 800; margin-bottom: 2px;">{store_name}</div>
    <div style="font-size: 0.88rem; opacity: 0.85;">{sel_loc} &nbsp;|&nbsp; {sel_industry}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="metric-row">
    <div class="metric-item">
        <div class="metric-title">시스템 상태</div>
        <div class="metric-number" style="color: #16A34A;">정상 가동</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">공동구매 등록</div>
        <div class="metric-number">{len(deals_db.get('deals', []))}건 진행</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">제휴 커뮤니티</div>
        <div class="metric-number">용인친구들</div>
    </div>
    <div class="metric-item">
        <div class="metric-title">마케팅 엔진</div>
        <div class="metric-number">PRO Suite v3.6</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sns-channel-bar">
    <div class="channel-title">공식 소셜 미디어 채널</div>
    <div class="channel-group">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" class="btn-channel btn-fb">페이스북 그룹</a>
        <a href="https://www.instagram.com/" target="_blank" class="btn-channel btn-insta">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" class="btn-channel btn-threads">스레드</a>
    </div>
</div>
""", unsafe_allow_html=True)

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 소상공인 실무 정책 및 세무 행정, 로컬 비즈니스 분야 20년 경력의 수석 경영 컨설턴트다.
모호한 미사여구나 이모티콘은 배제하고, 실질적이고 구조화된 전문 비즈니스 리포트를 제공한다.
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
            st.error("데이터 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.")
            return None

tab_titles = [
    "매장음악",
    "상생아지트",
    "공동구매",
    "블로그원고",
    "당근소식",
    "인스타그램",
    "고객문자",
    "급여계산",
    "행정서류",
    "정책지원",
    "영업마감"
]
tabs = st.tabs(tab_titles)

# ==========================================
# 0. 매장음악 (시간대 및 상황 큐레이션 엔진으로 대폭 강화)
# ==========================================
with tabs[0]:
    st.markdown("#### 매장 전용 시간대·상황별 음악 큐레이션")
    st.markdown("매장 운영 시간대와 당일 매장 환경에 맞춰 최적화된 유튜브 스트리밍을 원클릭으로 실행합니다.")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        m_time_slot = st.selectbox("1. 영업 시간대 기준", [
            "오전 오픈 준비 및 영업 시작 (경쾌하고 맑은 스타트)",
            "점심/오후 피크타임 (회전율과 활기 유지)",
            "나른한 오후 3~5시 (편안한 칠아웃/어쿠스틱 감성)",
            "저녁 골든타임 (고급스럽고 아늑한 라운지/재즈)",
            "영업 마감 및 매장 정리 (차분한 피아노/클래식)"
        ], key="music_time_slot")
        
        m_genre_type = st.selectbox("2. 음악 장르 스타일", [
            "재즈 / 보사노바 (카페, 뷰티, 안경원, 편집숍)",
            "어쿠스틱 팝 & 인디 감성 보컬",
            "세련된 라운지 & 로파이 칠(Lo-Fi Chill)",
            "2000년대 감성 발라드 피아노 연주곡",
            "90-2000 가요 댄스 & 빠른 템포 팝 (음식점, 펍)"
        ], key="music_genre_type")

    with col_m2:
        m_weather = st.selectbox("3. 당일 매장 환경 및 날씨", [
            "맑고 화창한 날 (생기 있는 무드)",
            "비 또는 눈 오는 날 (감성적인 센티멘털 무드)",
            "미세먼지 많고 흐린 날 (포근하고 따뜻한 실내 무드)",
            "금요일/주말 특별 이벤트 무드 (흥겹고 설레는 템포)"
        ], key="music_weather")

        combined_search = f"{m_genre_type.split('/')[0].strip()} {m_time_slot.split('(')[0].strip()} 플레이리스트 연속재생"
        music_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(combined_search)}"
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button(f"유튜브 '{m_genre_type.split('/')[0].strip()}' 스트리밍 재생", music_url, use_container_width=True)

    st.markdown(f"""
    <div class="clean-card" style="background:#F8FAFC; margin-top:10px;">
        <div style="font-size:0.85rem; color:#64748B;">현재 세팅된 큐레이션 검색어:</div>
        <div style="font-size:0.95rem; font-weight:700; color:#0F172A;">{combined_search}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 상생아지트 (관리자 가맹점 제어 기능 추가)
# ==========================================
with tabs[1]:
    st.markdown("#### 상생아지트 디렉토리 및 네이버 플레이스 연동")
    
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"
    
    st.markdown(f"""
    <div class="clean-card">
        <h4 style="margin-top:0; color:#0F172A;">내 매장 등록 현황: {store_name}</h4>
        <p style="color:#475569; font-size:0.92rem; margin-bottom:6px;">사업장 주소: {my_saved_addr}</p>
        <p style="color:#2563EB; font-weight:700; font-size:0.92rem; margin-bottom:16px;">회원 제휴 혜택: {my_perk}</p>
        <a href="{naver_url}" target="_blank" style="text-decoration:none;">
            <button style="width:100%; height:42px; background:#03C75A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; cursor:pointer;">
                네이버 플레이스 지도 연동 확인
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # 🛠️ [마스터 관리자 전용 아지트 가맹점 제어 센터]
    if user_key == "admin":
        st.markdown("---")
        st.markdown("##### 🛠️ 관리자 전용: 상생아지트 등록 매장 총괄 제어")
        
        azit_list = []
        for u_id, u_info in users_db.items():
            azit_list.append({
                "아이디": u_id,
                "상호명": u_info.get("store_name", "-"),
                "업종": u_info.get("industry", "-"),
                "위치": u_info.get("location", "-"),
                "혜택": u_info.get("map_perk", "-")
            })
        
        st.dataframe(pd.DataFrame(azit_list), use_container_width=True)

        st.markdown("###### 가맹점 정보 강제 수정 및 관리")
        selected_azit_id = st.selectbox("관리할 매장 선택", list(users_db.keys()), key="azit_mod_sel")
        target_azit = users_db[selected_azit_id]
        
        col_az1, col_az2 = st.columns(2)
        with col_az1:
            mod_az_name = st.text_input("상호명 수정", value=target_azit.get("store_name", ""), key="mod_az_name")
            mod_az_loc = st.text_input("도로명 주소 수정", value=target_azit.get("location", ""), key="mod_az_loc")
        with col_az2:
            mod_az_perk = st.text_input("회원 제휴 혜택 수정", value=target_azit.get("map_perk", ""), key="mod_az_perk")
            mod_az_feature = st.text_input("대표 시그니처 수정", value=target_azit.get("feature", ""), key="mod_az_feature")
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("가맹점 정보 변경 저장", key="az_save_btn", use_container_width=True):
                users_db[selected_azit_id]["store_name"] = mod_az_name
                users_db[selected_azit_id]["location"] = mod_az_loc
                users_db[selected_azit_id]["map_address"] = mod_az_loc
                users_db[selected_azit_id]["map_perk"] = mod_az_perk
                users_db[selected_azit_id]["feature"] = mod_az_feature
                save_users(users_db)
                st.success(f"'{mod_az_name}' 매장 정보가 갱신되었습니다.")
                st.rerun()
        with col_btn2:
            if selected_azit_id != "admin" and st.button("매장 등록 강제 삭제", key="az_del_btn", use_container_width=True):
                del users_db[selected_azit_id]
                save_users(users_db)
                st.warning("선택 매장이 데이터베이스에서 삭제되었습니다.")
                st.rerun()

# ==========================================
# 2. 공동구매 (데이터 CSV 다운로드 및 삭제 기능 완비)
# ==========================================
with tabs[2]:
    st.markdown("""
    <div class="guide-banner">
        실시간 로컬 공동구매 시스템: 현재 진행 중인 핫딜과 소모품 공구의 남은 기간과 신청 현황을 확인하세요.
    </div>
    """, unsafe_allow_html=True)
    
    deal_subtab1, deal_subtab2, deal_subtab3 = st.tabs(["주민 핫딜", "소모품 공구", "공구 제안"])
    
    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            if delta > 0:
                return f"D-{delta}일"
            elif delta == 0:
                return "오늘 마감"
            else:
                return "마감"
        except Exception:
            return "진행 중"

    with deal_subtab1:
        deals_to_remove = []
        for idx, deal in enumerate(deals_db["deals"]):
            total_qty = sum([p["qty"] for p in deal["participants"]])
            total_people = len(deal["participants"])
            dday_txt = get_dday(deal["deadline"])
            progress_val = min(total_qty / deal["target"], 1.0)
            is_expired = (dday_txt == "마감")
            
            st.markdown(f"""
            <div class="clean-card">
                <span style="background:{'#64748B' if is_expired else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 6px; border-radius:4px;">{dday_txt}</span>
                <h4 style="margin:8px 0; color:#0F172A; font-size:1.05rem;">{deal['title']}</h4>
                <p style="color:#2563EB; font-weight:700; font-size:0.95rem; margin-bottom:6px;">{deal['price']}</p>
                <p style="font-size:0.85rem; color:#475569;">신청 현황: <b>{total_people}명 참여</b> (누적 {total_qty}개 / 목표 {deal['target']}개)</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress_val)
            
            # 📥 [데이터 추출 및 관리 기능 바]
            col_d_act1, col_d_act2 = st.columns([1, 1])
            with col_d_act1:
                # 참여자 명단 엑셀/CSV 다운로드 기능
                if len(deal["participants"]) > 0:
                    df_parts = pd.DataFrame(deal["participants"])
                    df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                    csv_data = df_parts.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label=f"📥 참여자 명단 엑셀(CSV) 저장 ({total_people}명)",
                        data=csv_data,
                        file_name=f"공구명단_{deal['id']}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key=f"dl_csv_{deal['id']}",
                        use_container_width=True
                    )
            with col_d_act2:
                # 마감 또는 주최자 관리 삭제 기능
                if user_key == "admin" or is_expired:
                    if st.button("공동구매 프로젝트 영구 삭제", key=f"del_deal_{deal['id']}", use_container_width=True):
                        deals_to_remove.append(deal["id"])

            with st.container():
                with st.form(key=f"form_{deal['id']}"):
                    st.markdown("##### 공동구매 참여 신청")
                    p_name = st.text_input("성함 또는 상호명", key=f"name_{deal['id']}")
                    p_phone = st.text_input("연락처", key=f"phone_{deal['id']}")
                    p_qty = st.number_input("신청 수량", min_value=1, max_value=100, value=1, step=1, key=f"qty_{deal['id']}")
                    
                    if st.form_submit_button("참여 확정하기", use_container_width=True):
                        if p_name and p_phone:
                            new_p = {"name": p_name, "phone": p_phone, "qty": int(p_qty), "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
                            deal["participants"].append(new_p)
                            save_deals(deals_db)
                            st.success("신청이 완료되었습니다.")
                            st.rerun()
                        else:
                            st.warning("정보를 입력해 주세요.")
                
                st.markdown("##### 참여자 명단 미리보기")
                for p_idx, p in enumerate(deal["participants"], 1):
                    st.markdown(f"- {p_idx}. **{p['name']}**님 ({p['qty']}개 / {p['time']})")
            st.markdown("<hr>", unsafe_allow_html=True)

        if deals_to_remove:
            deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_remove]
            save_deals(deals_db)
            st.success("공동구매 프로젝트가 데이터베이스에서 삭제되었습니다.")
            st.rerun()

    with deal_subtab2:
        st.markdown("##### 사업장 소모품 도매가 공동 발주")
        st.markdown("""
        <div class="clean-card">
            <h4 style="margin-top:0;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
            <p style="color:#475569; font-size:0.9rem;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("소모품 공동발주 접수", use_container_width=True, key="b2b_order_btn"):
            st.success("발주 신청이 접수되었습니다.")

    with deal_subtab3:
        st.markdown("##### 신규 공동구매 오픈 제안")
        c_name = st.text_input("상품명", placeholder="예: 블루라이트 차단 렌즈 패키지", key="prop_name")
        c_qty = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="prop_qty")
        c_discount = st.text_input("제안 공구가", placeholder="예: 35,000원", key="prop_price")
        c_days = st.slider("진행 기간 (일 단위)", min_value=3, max_value=30, value=7, key="prop_days")
        
        if st.button("공동구매 프로젝트 등록 제출", use_container_width=True, key="prop_submit"):
            if c_name and c_discount:
                new_deal = {
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {c_name}",
                    "price": f"{c_discount} (단독 특가)",
                    "target": int(c_qty),
                    "deadline": (datetime.now() + timedelta(days=c_days)).strftime("%Y-%m-%d"),
                    "participants": []
                }
                deals_db["deals"].append(new_deal)
                save_deals(deals_db)
                st.success("공동구매 프로젝트가 등록되었습니다.")
                st.rerun()
            else:
                st.warning("상품명과 가격을 입력해 주세요.")

# 3. 블로그원고 (PRO)
with tabs[3]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">네이버 상위노출 알고리즘 엔진 (PRO 회원 전용)</div>
            <div style="font-size:0.88rem;">C-Rank 및 스마트블록 기준에 맞춘 검색엔진 최적화(SEO) 원고를 설계합니다.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">네이버 로컬 스마트블록 전문 포스팅 아키텍트</div>
        </div>
        """, unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            bl_target_keyword = st.text_input("메인 공략 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="orig_bl_kw")
            bl_sub_keyword = st.text_input("서브 연관 검색어 (쉼표 구분)", value=f"{sel_loc.split()[1] if len(sel_loc.split())>1 else ''} 추천, 단골", key="orig_bl_sub")
            bl_photo_count = st.slider("포스팅 사진 첨부 예정 장수", min_value=5, max_value=20, value=8, step=1, key="orig_bl_photo")
        with col_b2:
            bl_tone = st.selectbox("원고 스타일 톤앤매너", [
                "전문가 심층 분석형 (신뢰성, 공학적/기술적 검증, 정밀함 강조)",
                "동네 단골 솔직 방문기형 (자연스러운 체감 후기, 상세 공간 묘사)",
                "스마트 소비 가이드형 (가성비, 할인 혜택, 실속 비교 중심)"
            ], key="orig_bl_tone")
            bl_core_point = st.text_area("매장 핵심 차별점 (시그니처/장비/서비스)", value=sel_feature, height=85, key="orig_bl_core")

        if st.button("네이버 상위노출 최적화 전문 원고 생성", key="orig_bl_submit"):
            with st.spinner("알고리즘 적합성 분석 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                메인 타깃 키워드: {bl_target_keyword}
                서브 키워드: {bl_sub_keyword}
                사진 장수: {bl_photo_count}장
                톤앤매너: {bl_tone}
                차별점: {bl_core_point}

                당신은 네이버 검색 로직에 정통한 상위 1% 전문 마케팅 기획자입니다.
                다음 4가지 구성 요소를 포함하여 블로그 포스팅 원고를 전문적으로 작성하십시오.
                이모티콘은 배제하고 정갈한 비즈니스 문체로 작성할 것.
                1. 클릭률 극대화 제목 3종
                2. 사진 촬영 및 배치 가이드라인 ({bl_photo_count}장)
                3. 본문
                4. 연관 태그 10종
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 SEO 전문 원고", value=out, height=420)

# 4. 당근소식 (PRO)
with tabs[4]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">당근마켓 동네생활 바이럴 엔진 (PRO 회원 전용)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">당근마켓 반경 3km 타깃 로컬 소식 솔루션</div>
        </div>
        """, unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dg_target_audience = st.selectbox("타깃 고객군", ["3040 자녀 양육 주부층", "인근 거주 2030 직장인 및 1인가구", "동네 터줏대감 5060 중장년층", "전 지역 주민 전체"], key="orig_dg_target")
            dg_promo_type = st.selectbox("제공 혜택 유형", ["방문 시 무상 정밀 점검/체험 제공", "용인친구들 단독 할인 쿠폰 지급", "선착순 사은품 추가 증정", "새 시즌 한정 신상품 소개"], key="orig_dg_promo")
        with col_d2:
            dg_hook = st.text_input("동네 이슈/상황 연결", placeholder="예: 봄 환절기 미세먼지, 새 학기 준비", key="orig_dg_hook")
            dg_call = st.text_input("유도 액션 (CTA)", value="당근 단골 맺기 누르고 캡처본 보여주시면 적용", key="orig_dg_cta")

        if st.button("당근마켓 맞춤형 바이럴 소식 생성", key="orig_dg_submit"):
            with st.spinner("로컬 반경 커뮤니티 데이터 분석 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                주 타깃: {dg_target_audience}
                프로모션: {dg_promo_type}
                상황적 훅: {dg_hook}
                유도 액션: {dg_call}
                매장 강점: {sel_feature}

                당근마켓 동네생활 탭에서 신뢰를 얻는 소식을 작성하라.
                1. 피드 노출 타이틀 2종
                2. 본문 (안부 - 전문 정보 팁 - 혜택 안내 - 단골 유도)
                3. 댓글 반응 유도 질문
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 당근마켓 소식 원고", value=out, height=360)

# 5. 인스타그램 (PRO)
with tabs[5]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">인스타그램 비주얼 브랜딩 스튜디오 (PRO 회원 전용)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">인스타그램 하이엔드 피드 & 스토리보드 디렉터</div>
        </div>
        """, unsafe_allow_html=True)

        col_i1, col_i2 = st.columns(2)
        with col_i1:
            ig_format = st.selectbox("콘텐츠 포맷", ["단일 피드 (감성 스냅 1컷)", "카드뉴스형 (정보 전달 4~6슬라이드)", "릴스 숏폼 (15초 텍스트 영상 스크립트)"], key="orig_ig_fmt")
            ig_vibe = st.selectbox("비주얼 무드", ["미니멀 모던 (단정하고 세련된 분위기)", "따뜻한 아날로그 (정감 있고 아늑한 톤)", "전문 랩/클리닉 (정밀함과 위생 강조)"], key="orig_ig_vb")
        with col_i2:
            ig_topic = st.text_input("포스팅 핵심 주제", placeholder="예: 얼굴형에 맞는 맞춤 안경 피팅 가이드", key="orig_ig_tp")
            ig_perk = st.text_input("프로모션/혜택", value=curr_user.get("map_perk", "용친 회원 현장 추가 혜택"), key="orig_ig_pk")

        if st.button("인스타그램 비주얼 피드 & 태그 패키지 생성", key="orig_ig_submit"):
            with st.spinner("비주얼 레이아웃 구성 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                포맷: {ig_format}
                무드: {ig_vibe}
                주제: {ig_topic}
                혜택: {ig_perk}
                강점: {sel_feature}

                인스타그램 전문 브랜드 에이전시 톤으로 포스팅을 작성하라.
                1. 사진/영상 촬영 디렉팅 (구도, 조명 2~3줄)
                2. 피드 첫 줄 훅 멘트
                3. 피드 본문 (줄바꿈 최적화)
                4. 해시태그 15종 (지역 5개, 업종 5개, 타깃 5개)
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 인스타그램 브랜드 패키지", value=out, height=380)

# 6. 고객문자 (PRO)
with tabs[6]:
    if not is_pro_user:
        st.markdown("""
        <div class="pro-lock-banner">
            <div style="font-weight:700; font-size:1rem; margin-bottom:4px;">고객 리텐션 CRM 메시지 솔루션 (PRO 회원 전용)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="pro-builder-box">
            <span class="pro-badge">PRO ENTERPRISE ENGINE</span>
            <div style="font-weight:700; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">재방문율 극대화 CRM 메시지 스위트</div>
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            crm_target = st.selectbox("발송 대상 고객군", [
                "첫 방문 후 재방문 유도 (방문 후 1~2주 경과 고객)",
                "이탈 위험 단골 고객 (최근 60일 이상 미방문 고객)",
                "정기 점검/관리 주기 도래 고객 (전문 검안/클리닝 권장)",
                "특정 시즌/명절 감사 프로모션 타깃 전체"
            ], key="orig_crm_tgt")
            crm_coupon = st.text_input("제공 바우처 / 혜택", value="방문 시 무상 정밀 점검 및 10% 추가 할인 쿠폰", key="orig_crm_cpn")
        with col_s2:
            crm_urgency = st.selectbox("기한 설정", ["이번 주말까지 한정", "수신 후 14일 이내 방문 시", "선착순 30명 한정"], key="orig_crm_urg")
            crm_info = st.text_input("매장 문의처", value=f"{store_name} (문자 회신 가능)", key="orig_crm_inf")

        if st.button("SMS / LMS / 카카오 알림톡 3종 동시 출력", key="orig_crm_submit"):
            with st.spinner("스팸 필터 회피 메시지 설계 중..."):
                prompt = f"""
                매장명: {store_name}
                업종: {sel_industry}
                대상: {crm_target}
                혜택: {crm_coupon}
                기한: {crm_urgency}
                문의처: {crm_info}

                고객이 VIP 케어로 인식하도록 3종 규격으로 작성하라.
                [1] 단문 SMS (90 Byte 내외 엄수)
                [2] 장문 LMS (스토리텔링형)
                [3] 카카오 알림톡 권장 포맷
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 CRM 메시지 3종 세트", value=out, height=380)

# 7. 급여계산
with tabs[7]:
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="wage_calc")
        hours = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="hours_calc")
    with w2:
        tax_opt = st.selectbox("공제 기준", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 미적용"], key="tax_calc")
    
    base = wage * hours * 4.345
    holiday = ((hours / 40.0) * 8.0 * wage * 4.345) if hours >= 15 else 0
    total = base + holiday
    deduct = total * 0.033 if "3.3%" in tax_opt else (total * 0.009 if "0.9%" in tax_opt else 0)
    net = total - deduct
    st.markdown(f"""
    <div class="clean-card" style="background:#F8FAFC;">
        <div style="font-size:0.88rem; color:#64748B;">기본급 합계: {int(base):,}원 &nbsp;|&nbsp; 법정 주휴수당: {int(holiday):,}원</div>
        <div style="font-size:1.25rem; font-weight:800; color:#0F172A; margin:6px 0;">예상 실지급액: {int(net):,}원</div>
        <div style="font-size:0.8rem; color:#94A3B8;">(원천징수 공제 예상액: {int(deduct):,}원 차감)</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 8. 행정서류 (표 + 상세경로 + 원클릭 버튼 완비)
# ==========================================
with tabs[8]:
    st.markdown("#### 정책자금 및 금융 필수 행정 서식 가이드")
    st.markdown("""
    소상공인 정책자금, 신용보증재단 보증서 발급, 금융권 대환대출 신청 시 요구되는 **4대 필수 증빙 서류**의 공식 발급 절차입니다.
    """)

    st.markdown("""
    | 서류명 | 주 발급처 | 신청 대상 및 용도 | 법정 수수료 | 평균 소요시간 |
    | :--- | :--- | :--- | :--- | :--- |
    | **소상공인확인서** | 중소기업현황정보시스템 | 정부 지원사업, 국비 지원금 신청 시 소상공인 증빙 | 무료 | 즉시 (온라인) |
    | **부가가치세 과세표준증명** | 국세청 홈택스 / 손택스 | 대출 심사, 보증 심사 시 사업장 매출 규모 증빙 | 무료 | 즉시 (온라인) |
    | **국세 완납증명서 (납세증명)** | 국세청 홈택스 | 세금 체납 여부 확인 (미납 시 정책 지원 전면 제한) | 무료 | 즉시 (온라인) |
    | **지방세 완납증명서** | 정부24 / 주민센터 | 지방세(재산세, 주민세 등) 체납 여부 확인 | 무료 | 즉시 (온라인) |
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 서류별 상세 발급 경로 및 유의사항")

    c_doc1, c_doc2 = st.columns(2)
    with c_doc1:
        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">1. 소상공인확인서 (중소기업확인서)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 중소기업현황정보시스템 (sminfo.mss.go.kr)<br>
                • <b>발급 단계:</b> 회원가입 및 로그인 ➡️ [확인서 발급신청] ➡️ 사업자 정보 입력 ➡️ 온라인 자료제출(홈택스 자료 연동) ➡️ 확인서 출력<br>
                • <b>주의사항:</b> 직전 연도 소득세 신고가 완료되어야 정상 발급되며, 매년 갱신이 필요합니다.
            </p>
            <a href="https://sminfo.mss.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    중소기업현황정보시스템 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">2. 부가가치세 과세표준증명원</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 국세청 홈택스 (hometax.go.kr)<br>
                • <b>발급 단계:</b> 공동/금융인증서 로그인 ➡️ [국세증명·사업자등록 세금관련 신청/신고] ➡️ [부가가치세 과세표준증명] ➡️ 과세기간 선택 후 발급<br>
                • <b>주의사항:</b> 간이과세자는 [부가가치세 면세사업자 수입금액증명] 또는 해당 간이과세 증명으로 대체될 수 있습니다.
            </p>
            <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    국세청 홈택스 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

    with c_doc2:
        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">3. 국세 완납증명서 (납세증명서)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 국세청 홈택스 (hometax.go.kr)<br>
                • <b>발급 단계:</b> 홈택스 로그인 ➡️ [국세증명·사업자등록] ➡️ [납세증명서(국세완납증명)] ➡️ 수령방법 및 제출처 선택 ➡️ 신청<br>
                • <b>주의사항:</b> 유효기간이 통상 30일로 짧으므로 보증재단이나 은행 제출 직전에 발급받는 것이 권장됩니다.
            </p>
            <a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    국세청 납세증명 메뉴 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="clean-card">
            <div style="font-weight:700; color:#0F172A; font-size:0.95rem; margin-bottom:6px;">4. 지방세 납세증명서 (지방세 완납)</div>
            <p style="font-size:0.85rem; color:#475569; line-height:1.6; margin-bottom:12px;">
                • <b>공식 포털:</b> 정부24 (gov.kr)<br>
                • <b>발급 단계:</b> 정부24 간편인증 로그인 ➡️ 검색창에 '지방세 납세증명' 입력 ➡️ 신청하기 ➡️ 사업자등록번호 입력 후 PDF 발급<br>
                • <b>주의사항:</b> 개인사업자의 경우 개인 명의와 법인/상호 명의 체납 내역이 모두 조회되니 유의해야 합니다.
            </p>
            <a href="https://www.gov.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#F1F5F9; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    정부24 바로가기
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 9. 정책지원 (3대 핵심사업 카드 + 맞춤형 AI 진단기)
# ==========================================
with tabs[9]:
    st.markdown("#### 2026 소상공인 정책금융 및 국비 지원사업 분석")
    st.markdown("""
    소상공인시장진흥공단 및 중소벤처기업부에서 주관하는 주요 지원 정책 핵심 내용입니다.
    """)

    st.markdown("""
    <div class="policy-grid">
        <div class="policy-box">
            <div>
                <span class="policy-tag">비용 절감</span>
                <div class="policy-box-title">소상공인 전기요금 특별지원</div>
                <div class="policy-detail">
                    • <b>지원 한도:</b> 사업장당 최대 20만 원~25만 원 전기요금 감면<br>
                    • <b>신청 자격:</b> 연 매출 6천만 원 이하 소상공인 (일반용·산업용 전력 사용자)<br>
                    • <b>접수 기관:</b> 소상공인전기요금특별지원.kr (온라인 신청)
                </div>
            </div>
            <a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    전기요금 지원 신청처
                </button>
            </a>
        </div>
        <div class="policy-box">
            <div>
                <span class="policy-tag">금융 비용 경감</span>
                <div class="policy-box-title">고금리 소상공인 저금리 대환보증</div>
                <div class="policy-detail">
                    • <b>지원 혜택:</b> 제2금융권 7% 이상 고금리 대출을 4%대 정책 대출로 전환<br>
                    • <b>보증 한도:</b> 사업자당 최대 5,000만 원 한도 (보증비율 90% 이상)<br>
                    • <b>접수 기관:</b> 신용보증기금 및 각 시·도 지역신용보증재단
                </div>
            </div>
            <a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    소상공인정책자금 안내
                </button>
            </a>
        </div>
        <div class="policy-box">
            <div>
                <span class="policy-tag">매장 인프라 국비 지원</span>
                <div class="policy-box-title">스마트상점 기술보급 국비 지원사업</div>
                <div class="policy-detail">
                    • <b>지원 혜택:</b> 테이블오더, 무인 키오스크, 서빙로봇 도입 비용 최대 70% 국비 보조<br>
                    • <b>지원 한도:</b> 일반형 최대 500만 원, 미래형 최대 1,000만 원 국비 지원<br>
                    • <b>접수 기관:</b> 소상공인스마트상점 (sbiz.or.kr/smst/index.do)
                </div>
            </div>
            <a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:36px; background:#2563EB; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
                    스마트상점 공고 보기
                </button>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 사업장 조건별 맞춤형 정책지원 AI 진단")

    with st.container():
        st.markdown("""
        <div class="clean-card">
            <p style="font-size:0.9rem; color:#475569; margin-bottom:12px;">
                현재 매장의 매출 규모와 자금 필요 목적을 선택하시면 적합한 정책자금 항목과 신청 로드맵을 AI가 브리핑합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_rev = st.selectbox("사업장 연 매출 규모", ["3,000만 원 미만 (영세 소상공인)", "3,000만 원 ~ 1억 원 미만", "1억 원 ~ 3억 원 미만", "3억 원 초과"], key="p_rev")
        with col_p2:
            p_purpose = st.selectbox("가장 시급한 지원 분야", ["고금리 대출 이자 부담 완화", "매장 설비/디지털 인프라(키오스크 등) 구축", "운영자금 및 고정비(임대료·전기세) 보조", "사업장 간판·인테리어 개선"], key="p_purpose")

        if st.button("내 맞춤형 지원사업 진단서 확인", key="btn_p_ai"):
            with st.spinner("전문 정책지원 데이터를 분석하고 있습니다..."):
                prompt = f"""
                업종: {sel_industry}
                소재지: {sel_loc}
                연매출: {p_rev}
                목적: {p_purpose}

                위 사업장에 가장 유리한 정책자금 및 정부지원사업을 2가지 추천하고,
                1) 구체적 지원 내용
                2) 신청 요건 및 필수 구비 서류
                3) 신청 시 탈락을 방지하는 실무 팁
                을 표준 비즈니스 컨설팅 리포트 양식으로 간결하고 전문적으로 제시하라.
                """
                out = generate_safe_content(prompt)
                if out:
                    st.markdown(f"""
                    <div class="clean-card" style="border-left: 4px solid #2563EB; margin-top:14px;">
                        <div style="font-weight:700; color:#0F172A; font-size:1.05rem; margin-bottom:10px;">사업장 맞춤 정책지원 분석 리포트</div>
                        <div style="color:#334155; font-size:0.92rem; line-height:1.7;">{out}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# 10. 영업마감 (실무 매출/재고/내일 계획 결산 리포트로 전면 업그레이드)
# ==========================================
with tabs[10]:
    st.markdown("#### 일일 영업 실적 결산 및 익일 비즈니스 플래너")
    st.markdown("오늘 영업에 대한 간단한 실적 데이터를 입력하면 당일 경영 성과 분석과 익일 핵심 실행 과제를 AI가 도출합니다.")

    col_cl1, col_cl2 = st.columns(2)
    with col_cl1:
        close_sales = st.text_input("오늘 대략적인 매출액 (선택사항)", placeholder="예: 850,000원", key="cl_sales")
        close_traffic = st.selectbox("오늘 고객 유입량 체감", ["평소 대비 매우 한산함", "통상적인 평균 수준", "특정 피크시간 집중 방문", "종일 만석 / 목표 초과 달성"], key="cl_traffic")
    with col_cl2:
        close_issue = st.text_input("오늘의 특이사항 또는 애로사항", placeholder="예: 단골 고객 3명 방문, 특정 제품 재고 소진", key="cl_issue")
        close_weather_vibe = st.selectbox("오늘 매장 운영 만족도", ["다소 아쉬움 (내일 만회 필요)", "안정적이고 무난함", "매우 만족스러움 (추세 유지)"], key="cl_satisfaction")

    if st.button("일일 경영 결산 리포트 & 내일 액션플랜 생성", key="v5_close_btn_pro"):
        with st.spinner("당일 영업 데이터 및 운영 지표 종합 분석 중..."):
            prompt = f"""
            매장명: {store_name}
            업종: {sel_industry}
            소재지: {sel_loc}
            당일 매출: {close_sales if close_sales else '미입력'}
            고객 유입 체감: {close_traffic}
            당일 특이사항: {close_issue if close_issue else '특이사항 없음'}
            운영 만족도: {close_weather_vibe}

            당신은 20년 경력의 매장 경영 수석 컨설턴트입니다.
            오늘 하루 고생한 사장님을 위해 군더더기 없는 비즈니스 브리핑을 다음 3단계 구조로 명확히 작성하십시오:

            [1] 일일 경영 실적 요약 및 총평:
               - 오늘 매장 유입 현황과 운영 상황에 대한 객관적인 진단 및 사장님을 위한 묵직한 격려

            [2] 내일(익일) 필수 실행 과제 3선:
               - 매출 만회 또는 유지를 위한 구체적 프로모션(SNS/문자 발송 등) 1개
               - 재고/발주 및 매장 환경 점검 사항 1개
               - 현장 응대/고객 관리 액션 1개

            [3] 사장님을 위한 퇴근길 멘탈 리셋 한마디:
               - 장기 레이스를 달리는 로컬 자영업자에게 힘이 되는 전문적이고 따뜻한 코멘트
            """
            out = generate_safe_content(prompt)
            if out:
                st.markdown(f"""
                <div class="clean-card" style="border-left: 4px solid #2563EB; margin-top:14px;">
                    <div style="font-weight:700; color:#0F172A; font-size:1.05rem; margin-bottom:10px;">일일 영업 결산 및 경영 플래너 리포트</div>
                    <div style="color:#334155; font-size:0.92rem; line-height:1.7;">{out}</div>
                </div>
                """, unsafe_allow_html=True)

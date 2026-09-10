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
# 🎨 [순백색 바탕 & 선명한 버튼 & 층간 입체감 CSS]
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
    
    /* 1. 순백색 메인 배경 */
    .stApp, html, body { 
        background-color: #F8FAFC !important; 
    }

    /* 2. 입력창 가독성 최적화 */
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

    /* 3. 층(Floor) 분리형 구조화 카드 */
    .floor-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.04);
        position: relative;
    }
    .floor-badge {
        font-size: 0.72rem;
        font-weight: 800;
        color: #2563EB;
        background: #EFF6FF;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 8px;
        letter-spacing: 0.05em;
    }
    .floor-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 4px;
    }
    .floor-sub {
        font-size: 0.88rem;
        color: #64748B;
        margin-bottom: 18px;
    }

    /* 4. 클릭창 시인성 개선 (보이는 버튼 스타일링) */
    .stLinkButton > a, div[data-testid="stLinkButton"] > a {
        background: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 10px 16px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
        transition: all 0.15s ease !important;
    }
    .stLinkButton > a:hover, div[data-testid="stLinkButton"] > a:hover {
        background: #E2E8F0 !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }
    .stLinkButton > a * {
        color: #1E293B !important;
        font-weight: 700 !important;
    }

    /* 공통 액션 버튼 */
    .stButton>button {
        height: 2.9rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }

    /* 보조 기능 버튼 (회색빛 뚜렷한 버튼) */
    .btn-secondary-action {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 10px 14px;
        color: #334155;
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        cursor: pointer;
        display: inline-block;
        width: 100%;
    }
    .btn-secondary-action:hover {
        background: #E2E8F0;
    }

    /* 상단 앱 헤더 */
    .store-header {
        background: #FFFFFF;
        padding: 16px 20px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
    }
    .store-brand-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .store-plan-pill {
        font-size: 0.72rem;
        font-weight: 700;
        background: #EFF6FF;
        color: #2563EB;
        padding: 3px 8px;
        border-radius: 6px;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 6px !important;
        background: #F1F5F9 !important;
        padding: 5px !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 36px !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 14px !important;
        white-space: nowrap !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
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
# 메인 피드 대시보드
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
        st.success("PRO 파트너 등급 활성화")
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
# 1. 상단 헤더 & 브리핑 (최상단)
# ==========================================
st.markdown(f"""
<div class="store-header">
    <div class="store-brand-title">
        {store_name} <span class="store-plan-pill">{'PRO 파트너' if is_pro_user else '스탠다드'}</span>
    </div>
    <div style="font-size: 0.88rem; color: #475569; font-weight: 600;">
        {sel_loc}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #0F172A; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; color: #FFFFFF;">
    <div style="font-size:0.75rem; color:#94A3B8; font-weight:700; text-transform:uppercase;">TODAY'S BUSINESS BRIEFING</div>
    <div style="font-size:1rem; font-weight:700; margin-top:3px;">
        오늘 방문 고객을 위한 번개 특가와 대규모 공동구매 프로젝트가 가동 중입니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
    <div style="font-size:0.86rem; font-weight:700; color:#334155;">용인친구들 공식 채널 바로가기</div>
    <div style="display:flex; gap:8px;">
        <a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">페이스북 그룹</a>
        <a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">인스타그램</a>
        <a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:6px 12px; border-radius:6px; font-size:0.8rem; font-weight:700; text-decoration:none;">스레드</a>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# [FLOOR 1] 상생아지트 & 번개 특가 (독립 층)
# ==========================================
my_saved_addr = curr_user.get("map_address", sel_loc)
my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
my_today_deal = curr_user.get("today_deal", "오늘의 특가 품목 등록 대기 중")
my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

st.markdown(f"""
<div class="floor-container">
    <span class="floor-badge">SECTION 01</span>
    <div class="floor-title">오늘의 상생아지트 & 번개 특가</div>
    <div class="floor-sub">{my_saved_addr} (최근 갱신: {my_deal_updated})</div>
    <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-left:4px solid #2563EB; border-radius:8px; padding:14px 16px; margin-bottom:12px;">
        <div style="font-size:0.75rem; font-weight:700; color:#2563EB; text-transform:uppercase;">TODAY'S SPECIAL</div>
        <div style="font-size:1.05rem; font-weight:800; color:#0F172A; margin-top:2px;">{my_today_deal}</div>
    </div>
    <div style="font-size:0.9rem; color:#475569; margin-bottom:14px;"><b>상시 회원 혜택:</b> {my_perk}</div>
    <a href="{naver_url}" target="_blank" style="text-decoration:none;">
        <button style="width:100%; height:42px; background:#03C75A; color:#FFFFFF; border:none; border-radius:8px; font-weight:700; cursor:pointer;">
            네이버 플레이스 길찾기 및 지도 연동 확인
        </button>
    </a>
</div>
""", unsafe_allow_html=True)

col_f1_a, col_f1_b = st.columns([1, 4])
with col_f1_a:
    if st.button("특가/혜택 편집", key="btn_f1_edit", use_container_width=True):
        st.session_state.show_deal_edit = not st.session_state.show_deal_edit

if st.session_state.show_deal_edit:
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:18px; margin-bottom:24px;">
        <div style="font-size:0.9rem; font-weight:700; color:#0F172A; margin-bottom:10px;">오늘의 번개 특가 및 상시 혜택 실시간 변경</div>
    """, unsafe_allow_html=True)
    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
        new_today_deal = st.text_input("오늘의 특가 품목", value=my_today_deal, key="edit_td_deal_box")
    with col_ed2:
        new_perk = st.text_input("기본 상시 혜택", value=my_perk, key="edit_td_perk_box")
    if st.button("수정 내용 즉시 저장", key="btn_save_deal_box", use_container_width=True):
        users_db[user_key]["today_deal"] = new_today_deal
        users_db[user_key]["map_perk"] = new_perk
        users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_users(users_db)
        st.session_state.show_deal_edit = False
        st.success("매장 혜택 정보가 업데이트되었습니다.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# [FLOOR 2] 대규모 공동구매 아키텍처 (독립 층)
# ==========================================
st.markdown("""
<div class="floor-container">
    <span class="floor-badge">SECTION 02</span>
    <div class="floor-title">실시간 로컬 공동구매 센터</div>
    <div class="floor-sub">소상공인 대량 발주 및 지역 단독 핫딜 (확장형 필터 탑재)</div>
""", unsafe_allow_html=True)

deal_tab1, deal_tab2, deal_tab3 = st.tabs(["진행 중인 핫딜 목록", "소모품 도매 발주", "신규 공구 제안"])

def get_dday(deadline_str):
    try:
        d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
        delta = (d_date - datetime.now()).days
        return f"D-{delta}일" if delta > 0 else ("오늘 마감" if delta == 0 else "마감")
    except Exception:
        return "진행 중"

with deal_tab1:
    # 대량 공구 대비 상태 필터
    col_flt1, col_flt2 = st.columns([1.5, 3])
    with col_flt1:
        deal_filter = st.selectbox("공구 상태 필터링", ["전체 프로젝트 보기", "진행중인 공구만", "마감된 공구만"], key="deal_filter_sel")

    deals_to_del = []
    filtered_deals = []
    for d in deals_db["deals"]:
        d_state = get_dday(d["deadline"])
        if deal_filter == "진행중인 공구만" and d_state == "마감":
            continue
        if deal_filter == "마감된 공구만" and d_state != "마감":
            continue
        filtered_deals.append(d)

    if not filtered_deals:
        st.info("해당 조건에 부합하는 공동구매 프로젝트가 없습니다.")
    else:
        # 공구가 많아져도 깔끔한 2열 카드 그리드 배치
        for i in range(0, len(filtered_deals), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(filtered_deals):
                    deal = filtered_deals[i + j]
                    tot_qty = sum([p["qty"] for p in deal["participants"]])
                    dday = get_dday(deal["deadline"])
                    is_closed = (dday == "마감")
                    
                    with cols[j]:
                        st.markdown(f"""
                        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:12px; padding:18px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="background:{'#64748B' if is_closed else '#EF4444'}; color:#fff; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:4px;">{dday}</span>
                                <span style="font-size:0.8rem; color:#64748B;">목표 {deal['target']}개</span>
                            </div>
                            <h4 style="margin:10px 0 6px 0; color:#0F172A; font-size:1.02rem;">{deal['title']}</h4>
                            <div style="font-size:1.1rem; font-weight:800; color:#2563EB;">{deal['price']}</div>
                            <div style="font-size:0.85rem; color:#475569; margin:6px 0 10px 0;">신청: <b>{len(deal['participants'])}명</b> 참여 (총 {tot_qty}개 달성)</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.progress(min(tot_qty / deal["target"], 1.0))

                        # CSV 다운로드 및 삭제 제어
                        c_act1, c_act2 = st.columns(2)
                        with c_act1:
                            if len(deal["participants"]) > 0:
                                df_parts = pd.DataFrame(deal["participants"])
                                df_parts.columns = ["성함/상호", "연락처", "신청수량", "신청일시"]
                                csv_file = df_parts.to_csv(index=False, encoding="utf-8-sig")
                                st.download_button(
                                    label=f"명단 CSV 저장",
                                    data=csv_file,
                                    file_name=f"공구명단_{deal['id']}.csv",
                                    mime="text/csv",
                                    key=f"csv_dl_{deal['id']}",
                                    use_container_width=True
                                )
                        with c_act2:
                            if user_key == "admin" or is_closed:
                                if st.button("공구 삭제", key=f"del_d_{deal['id']}", use_container_width=True):
                                    deals_to_del.append(deal["id"])

                        # 간결한 참여 아코디언 폼
                        with st.expander(f"공구 참여하기 ({deal['title'][:12]}...)", expanded=False):
                            with st.form(key=f"join_form_{deal['id']}"):
                                p_n = st.text_input("성함 또는 상호", key=f"p_n_{deal['id']}")
                                p_p = st.text_input("연락처", key=f"p_p_{deal['id']}")
                                p_q = st.number_input("수량", min_value=1, max_value=100, value=1, step=1, key=f"p_q_{deal['id']}")
                                if st.form_submit_button("신청 확정", use_container_width=True):
                                    if p_n and p_p:
                                        deal["participants"].append({"name": p_n, "phone": p_p, "qty": int(p_q), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                                        save_deals(deals_db)
                                        st.success("참여 완료!")
                                        st.rerun()
                                    else:
                                        st.warning("정보를 입력하세요.")

    if deals_to_del:
        deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_del]
        save_deals(deals_db)
        st.rerun()

with deal_tab2:
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:18px;">
        <h4 style="margin:0; color:#0F172A;">카드단말기 영수증 롤페이퍼 (50롤 1박스)</h4>
        <p style="color:#475569; font-size:0.9rem; margin-top:6px;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("소모품 공동발주 접수", key="feed_b2b_btn", use_container_width=True):
        st.success("발주 신청이 접수되었습니다.")

with deal_tab3:
    c_n = st.text_input("제안 상품명", key="feed_prop_name")
    c_q = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="feed_prop_qty")
    c_d = st.text_input("제안 공구가", key="feed_prop_price")
    c_day = st.slider("진행 일수", min_value=3, max_value=30, value=7, key="feed_prop_days")
    if st.button("공구 등록 신청", key="feed_prop_btn", use_container_width=True):
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
            st.success("공동구매 프로젝트가 개설되었습니다.")
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# [FLOOR 3] 엔터프라이즈 PRO 마케팅 스튜디오 (독립 층)
# ==========================================
st.markdown("""
<div class="floor-container">
    <span class="floor-badge">SECTION 03</span>
    <div class="floor-title">엔터프라이즈 마케팅 스튜디오 & AI 리뷰 허브</div>
    <div class="floor-sub">네이버 알고리즘 대응 SEO 원고, 바이럴 소식, 감성 피드 및 전문 리뷰 답글 솔루션</div>
""", unsafe_allow_html=True)

mkt_tab1, mkt_tab2, mkt_tab3, mkt_tab4, mkt_tab5 = st.tabs([
    "네이버 블로그 SEO", "당근마켓 바이럴", "인스타그램 스튜디오", "CRM 리텐션 문자", "AI 리뷰 대응 센터"
])

with mkt_tab1:
    if not is_pro_user:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #FECACA; border-left:4px solid #EF4444; padding:16px; border-radius:8px;">
            <div style="font-weight:700; color:#991B1B;">네이버 상위노출 C-Rank 알고리즘 엔진 (PRO 파트너 전용)</div>
            <div style="font-size:0.86rem; color:#7F1D1D; margin-top:4px;">스마트블록 상위 점유를 위한 4단계 구조화 원고 설계 기능입니다.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_bl1, col_bl2 = st.columns(2)
        with col_bl1:
            bl_kw = st.text_input("메인 타깃 키워드", value=f"용인 {sel_industry.split('/')[0].strip()}", key="adv_bl_kw")
            bl_sub = st.text_input("서브 연관 검색어 (쉼표 구분)", value=f"{sel_loc.split()[1] if len(sel_loc.split())>1 else ''} 안경 추천, 정밀 시력검사", key="adv_bl_sub")
            bl_photos = st.slider("촬영 예정 사진 장수", 5, 20, 8, key="adv_bl_photo")
        with col_bl2:
            bl_intent = st.selectbox("공략 검색 의도", ["실제 내돈내산 단골 방문기 (체감 후기 강조)", "전문 검안 기술/장비 심층 분석 (신뢰도 중심)", "가격 대비 성능/할인 혜택 중심 가이드"], key="adv_bl_intent")
            bl_core = st.text_area("매장 핵심 강점", value=sel_feature, height=75, key="adv_bl_core")

        if st.button("네이버 상위노출 전문 원고 설계 실행", key="adv_bl_btn", use_container_width=True):
            with st.spinner("알고리즘 가중치 분석 및 구조화 원고 생성 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장명: {store_name}
                위치: {sel_loc}
                메인 키워드: {bl_kw}
                서브 키워드: {bl_sub}
                사진 장수: {bl_photos}장
                검색 의도: {bl_intent}
                핵심 강점: {bl_core}

                당신은 대한민국 0.1% 로컬 블로그 SEO 대행사 총괄 디렉터다.
                이모티콘은 배제하고, 실제 네이버 스마트블록 상위에 꽂히는 정교한 구조로 작성하라.

                [1] 클릭률을 장악하는 제목 3종 (검색량 최적화형, 궁금증 유발형, 솔직 후기형)
                [2] 사진 {bl_photos}장 배치 및 앵글 지침 (본문 흐름에 맞춘 구체적 가이드)
                [3] 본문 (공간 도입 - 전문 장비/기술 검증 - 실제 고객 혜택 - 플레이스 길찾기/예약 유도 CTA)
                [4] 스마트블록 노출용 연관 태그 10종
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("생성된 SEO 전문 원고", value=out, height=400)

with mkt_tab2:
    if not is_pro_user:
        st.info("당근마켓 동네생활 바이럴 엔진은 PRO 파트너 전용 기능입니다.")
    else:
        col_dg1, col_dg2 = st.columns(2)
        with col_dg1:
            dg_target = st.selectbox("타깃 고객층", ["3040 자녀 양육 학부모", "2030 직장인 및 1인가구", "동네 중장년층 전체"], key="adv_dg_target")
            dg_promo = st.selectbox("제공 혜택", ["무상 정밀 점검 및 세척 서비스", "단독 추가 할인 바우처", "선착순 사은품 증정"], key="adv_dg_promo")
        with col_dg2:
            dg_context = st.text_input("상황적 훅 (계절, 날씨, 동네 이슈)", value="봄맞이 시력 점검 및 미세먼지 케어", key="adv_dg_ctx")
            dg_cta = st.text_input("행동 유도 (CTA)", value="당근 단골 맺기 누르고 매장 방문 시 적용", key="adv_dg_cta")

        if st.button("당근마켓 바이럴 소식 생성", key="adv_dg_btn", use_container_width=True):
            with st.spinner("로컬 이웃 공감 알고리즘 반영 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장: {store_name}
                위치: {sel_loc}
                타깃: {dg_target}
                혜택: {dg_promo}
                상황: {dg_context}
                CTA: {dg_cta}

                전단지형 광고 말투를 완전히 배제하고, 동네 이웃 사장님이 진솔하게 건네는 신뢰도 높은 어투로 작성하라.
                1. 스크롤 멈춤 피드 타이틀 2종
                2. 본문 (이웃 안부 - 전문 팁 공유 - 혜택 안내 - 단골 유도)
                3. 댓글 참여 유도용 마무리 질문
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("당근마켓 바이럴 원고", value=out, height=360)

with mkt_tab3:
    if not is_pro_user:
        st.info("인스타그램 스튜디오는 PRO 파트너 전용 기능입니다.")
    else:
        col_ig1, col_ig2 = st.columns(2)
        with col_ig1:
            ig_type = st.selectbox("콘텐츠 형식", ["단일 감성 스냅 (1컷)", "정보 전달형 카드뉴스 (5컷)", "릴스 15초 숏폼 스크립트"], key="adv_ig_type")
            ig_mood = st.selectbox("비주얼 무드", ["미니멀 모던", "따뜻한 아날로그", "전문 클리닉/정밀 하이테크"], key="adv_ig_mood")
        with col_ig2:
            ig_subject = st.text_input("포스팅 주제", value="얼굴형에 딱 맞는 인생 안경 피팅 노하우", key="adv_ig_subj")
            ig_perk_tag = st.text_input("연계 프로모션", value=my_perk, key="adv_ig_perk")

        if st.button("인스타그램 피드 & 태그 패키지 생성", key="adv_ig_btn", use_container_width=True):
            with st.spinner("비주얼 디렉팅 구성 중..."):
                prompt = f"""
                업종: {sel_industry}
                매장: {store_name}
                형식: {ig_type}
                무드: {ig_mood}
                주제: {ig_subject}
                혜택: {ig_perk_tag}

                인스타그램 전문 브랜드 에이전시의 세련된 톤앤매너로 작성하라.
                1. 사진/영상 촬영 디렉팅 (구도, 조명, 소품 앵글 지침)
                2. 3초 스크롤 스톱 첫 줄 카피
                3. 본문 (리듬감 있는 줄바꿈)
                4. 복사용 해시태그 15종 (지역 5, 업종 5, 타깃 5)
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("인스타그램 브랜드 패키지", value=out, height=360)

with mkt_tab4:
    if not is_pro_user:
        st.info("CRM 리텐션 문자는 PRO 파트너 전용 기능입니다.")
    else:
        col_crm1, col_crm2 = st.columns(2)
        with col_crm1:
            crm_seg = st.selectbox("대상 세그먼트", ["첫 방문 후 재방문 유도 (1~2주 경과)", "이탈 위험 단골 고객 (60일 이상 미방문)", "정기 검안/렌즈 관리 주기 고객"], key="adv_crm_seg")
            crm_offer = st.text_input("제공 바우처", value="재방문 고객 전용 10% 추가 할인 및 김서림 방지 클리너", key="adv_crm_offer")
        with col_crm2:
            crm_limit = st.selectbox("기한 설정", ["이번 주 일요일까지 한정", "수신 후 14일 이내 방문 시", "선착순 30명 한정"], key="adv_crm_limit")
            crm_tel = st.text_input("문의/예약처", value=f"{store_name} (문자 회신 가능)", key="adv_crm_tel")

        if st.button("SMS / LMS / 알림톡 3종 생성", key="adv_crm_btn", use_container_width=True):
            with st.spinner("스팸 필터링 회피 및 규격별 문안 작성 중..."):
                prompt = f"""
                매장: {store_name}
                업종: {sel_industry}
                대상: {crm_seg}
                혜택: {crm_offer}
                기한: {crm_limit}
                연락처: {crm_tel}

                고객이 스팸이 아닌 VIP 케어로 인식하도록 3종 규격으로 작성하라.
                [1] 단문 SMS (90 Byte 이내 엄수)
                [2] 장문 LMS (스토리텔링형)
                [3] 카카오 알림톡 권장 포맷
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("CRM 메시지 3종 세트", value=out, height=360)

with mkt_tab5:
    st.markdown("###### 네이버 플레이스 & 배달/당근 리뷰 자동 답글기")
    cust_review = st.text_area("고객 리뷰 본문 붙여넣기", placeholder="예: 시력검사 꼼꼼하게 해주시고 제 얼굴에 어울리는 테도 잘 골라주셨어요. 다음에도 또 올게요!")
    rev_style = st.selectbox("답글 톤앤매너", ["품격 있고 정중한 전문 감사형", "친근하고 다정한 동네 이웃형", "매장의 핵심 차별점을 자연스럽게 강조하는 마케팅형"], key="adv_rev_style")
    if st.button("전문 답글 3종 생성", key="adv_rev_btn", use_container_width=True):
        if cust_review:
            with st.spinner("고객 감동 답글 분석 및 작성 중..."):
                prompt = f"""
                매장: {store_name} ({sel_industry})
                고객리뷰: "{cust_review}"
                스타일: {rev_style}

                플레이스 검색 고객들이 이 답글을 보고 매장에 신뢰를 가질 수 있도록 전문적이고 따뜻한 답글 3종을 작성하라.
                """
                out = generate_safe_content(prompt)
                if out:
                    st.text_area("추천 답글 3종", value=out, height=280)
        else:
            st.warning("고객 리뷰 본문을 입력해 주세요.")

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# [FLOOR 4] 행정서류 & 2026 정책지원 분석 (독립 층)
# ==========================================
st.markdown("""
<div class="floor-container">
    <span class="floor-badge">SECTION 04</span>
    <div class="floor-title">정책자금 필수 행정 서식 & 2026 국비 지원 분석</div>
    <div class="floor-sub">소상공인확인서, 부가세증명 등 4대 필수 서류 및 맞춤형 정책 진단</div>
""", unsafe_allow_html=True)

gov_tab1, gov_tab2 = st.tabs(["4대 필수 서류 발급 가이드", "2026 정책금융 AI 진단"])

with gov_tab1:
    st.markdown("""
    | 서류명 | 주 발급처 | 신청 대상 및 용도 | 법정 수수료 | 평균 소요시간 |
    | :--- | :--- | :--- | :--- | :--- |
    | **소상공인확인서** | 중소기업현황정보시스템 | 정부 지원사업, 국비 지원금 신청 시 소상공인 증빙 | 무료 | 즉시 (온라인) |
    | **부가가치세 과세표준증명** | 국세청 홈택스 / 손택스 | 대출 심사, 보증 심사 시 사업장 매출 규모 증빙 | 무료 | 즉시 (온라인) |
    | **국세 완납증명서 (납세증명)** | 국세청 홈택스 | 세금 체납 여부 확인 (미납 시 정책 지원 전면 제한) | 무료 | 즉시 (온라인) |
    | **지방세 완납증명서** | 정부24 / 주민센터 | 지방세(재산세, 주민세 등) 체납 여부 확인 | 무료 | 즉시 (온라인) |
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 서류별 공식 발급 포털 원클릭 이동")
    
    # 클릭창 시인성 개선 완료 (보이는 버튼 스타일)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.link_button("중소기업현황정보시스템 (소상공인확인서)", "https://sminfo.mss.go.kr", use_container_width=True)
        st.link_button("국세청 홈택스 (부가세/국세완납)", "https://www.hometax.go.kr", use_container_width=True)
    with col_g2:
        st.link_button("정부24 (지방세 완납증명)", "https://www.gov.kr", use_container_width=True)
        st.link_button("소상공인정책자금 포털", "https://ols.semas.or.kr", use_container_width=True)

with gov_tab2:
    st.markdown("""
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin-top:10px;">
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_pol1, col_pol2 = st.columns(2)
    with col_pol1:
        rev_scale = st.selectbox("사업장 연매출 규모", ["3천만 원 미만 (영세)", "3천만 원 ~ 1억 원", "1억 원 ~ 3억 원", "3억 원 초과"], key="feed_rev_scale")
    with col_pol2:
        aid_purp = st.selectbox("가장 시급한 지원", ["고금리 대출 이자 완화", "매장 설비/키오스크 보조", "운영 고정비(전기세 등) 지원"], key="feed_aid_purp")
    if st.button("내 매장 맞춤 정책자금 AI 진단 실행", key="feed_aid_btn", use_container_width=True):
        with st.spinner("정책 데이터 매칭 중..."):
            out = generate_safe_content(f"업종: {sel_industry}\n매출: {rev_scale}\n목적: {aid_purp}\n가장 적합한 정부 정책 2종과 구체적 신청 요건을 공문서 리포트로 작성.")
            if out: st.markdown(f"<div style='background:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #2563EB; padding:16px; border-radius:8px; margin-top:12px;'>{out}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# [FLOOR 5] 급여 계산, 영업 마감, 매장 음악 (독립 층)
# ==========================================
st.markdown("""
<div class="floor-container">
    <span class="floor-badge">SECTION 05</span>
    <div class="floor-title">경영 관리: 급여 산출, 영업 마감, 매장 음악</div>
    <div class="floor-sub">아르바이트 주휴수당 자동 계산 및 일일 결산 플래너</div>
""", unsafe_allow_html=True)

fin_tab1, fin_tab2, fin_tab3 = st.tabs(["알바 급여 계산기", "일일 영업 결산 리포트", "매장 시간대별 음악"])

with fin_tab1:
    w1, w2 = st.columns(2)
    with w1:
        wage = st.number_input("기본 시급 (원)", value=10030, step=100, key="feed_wage_box")
        hrs = st.number_input("주당 소정근로시간", value=16.0, step=0.5, key="feed_hrs_box")
    with w2:
        tax_opt = st.selectbox("공제 방식", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 없음"], key="feed_tax_box")
    base = wage * hrs * 4.345
    holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
    tot = base + holiday
    ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
    net = tot - ded
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:8px; padding:16px; margin-top:8px;">
        <div style="font-size:0.86rem; color:#64748B;">기본급: {int(base):,}원 | 주휴수당: {int(holiday):,}원 (원천공제: {int(ded):,}원)</div>
        <div style="font-size:1.25rem; font-weight:800; color:#0F172A; margin-top:2px;">예상 실지급액: {int(net):,}원</div>
    </div>
    """, unsafe_allow_html=True)

with fin_tab2:
    cl_col1, cl_col2 = st.columns(2)
    with cl_col1:
        c_sales = st.text_input("오늘 대략적인 매출액 (선택)", placeholder="예: 850,000원", key="feed_close_sales_box")
        c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석"], key="feed_close_flow_box")
    with cl_col2:
        c_memo = st.text_input("특이사항/재고 이슈", placeholder="예: 특정 렌즈 재고 소진", key="feed_close_memo_box")
        c_sat = st.selectbox("운영 만족도", ["다소 아쉬움", "무난하고 안정적", "매우 만족"], key="feed_close_sat_box")
    if st.button("일일 경영 결산 리포트 생성", key="feed_close_btn_box", use_container_width=True):
        with st.spinner("경영 데이터 종합 분석 중..."):
            out = generate_safe_content(f"가게: {store_name}\n매출: {c_sales}\n유입: {c_flow}\n특이사항: {c_memo}\n만족도: {c_sat}\n일일 경영 총평, 내일 실행과제 3선, 퇴근길 멘탈 리셋 조언 작성.")
            if out: st.markdown(f"<div style='background:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #2563EB; padding:16px; border-radius:8px; margin-top:12px;'>{out}</div>", unsafe_allow_html=True)

with fin_tab3:
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        m_time = st.selectbox("영업 시간대", ["오전 오픈 준비 (경쾌한 무드)", "점심/오후 피크 (활기 유지)", "나른한 오후 3~5시 (편안한 칠아웃)", "저녁 골든타임 (아늑한 라운지/재즈)", "마감 정리 (차분한 피아노)"], key="feed_m_time_box")
    with col_m2:
        m_style = st.selectbox("장르 스타일", ["재즈/보사노바", "어쿠스틱 팝", "2000년대 감성 발라드 피아노", "90-2000 가요 댄스"], key="feed_m_style_box")
    yt_q = f"{m_style.split('/')[0]} {m_time.split('(')[0].strip()} 플레이리스트 연속재생"
    st.link_button(f"유튜브 '{yt_q}' 스트리밍 재생", f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_q)}", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

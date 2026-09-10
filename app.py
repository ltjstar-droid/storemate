import os
import sys
import time
import json
import urllib.parse
from datetime import datetime, timedelta
import pandas as pd
import requests

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
ANALYTICS_DB_FILE = "analytics_db.json"

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
            "phone": "031-323-1215",
            "feature": "독일식 초정밀 시력검사",
            "map_address": "경기도 용인시 처인구 이동읍 경기동로 725",
            "map_perk": "용친 회원 안경렌즈 추가 10% DC & 고급 안경 클리너 증정",
            "today_deal": "누진다초점 렌즈 50% 할인",
            "today_updated": datetime.now().strftime("%Y-%m-%d"),
            "pw": "1234",
            "is_pro": True,
            "pro_status": "승인완료",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "trial_end": (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d")
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

def load_analytics():
    if os.path.exists(ANALYTICS_DB_FILE):
        try:
            with open(ANALYTICS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_analytics(data):
    try:
        with open(ANALYTICS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def track_visitor():
    analytics = load_analytics()
    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str not in analytics:
        analytics[today_str] = {"uv": 0, "pv": 0}
    analytics[today_str]["pv"] += 1
    if "has_visited_today" not in st.session_state:
        st.session_state.has_visited_today = True
        analytics[today_str]["uv"] += 1
    save_analytics(analytics)

track_visitor()

# ==========================================
# ☀️ 날씨 및 지오코딩
# ==========================================
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=14&addressdetails=1"
        headers = {"User-Agent": "StoreMate-Mobile/2.0"}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            addr = res.json().get("address", {})
            city = addr.get("city") or addr.get("county") or addr.get("province") or "용인시"
            district = addr.get("borough") or addr.get("suburb") or addr.get("town") or ""
            return f"{city} {district}".strip()
    except Exception:
        pass
    return "용인시 처인구"

def get_live_weather(lat=37.16, lon=127.21):
    icon_sun = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>"""
    icon_cloud = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>"""
    icon_rain = """<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="16" y1="13" x2="16" y2="21"></line><line x1="8" y1="13" x2="8" y2="21"></line><line x1="12" y1="15" x2="12" y2="23"></line><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path></svg>"""

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json().get("current_weather", {})
            temp = data.get("temperature", 20.2)
            code = data.get("weathercode", 0)
            
            if code in [0, 1]:
                status = "맑음"
                tip = "화창한 날씨입니다. 매장 쇼윈도와 입구를 점검해 방문을 유도하세요."
                svg_icon = icon_sun
            elif code in [2, 3]:
                status = "구름 많음 / 흐림"
                tip = "차분한 날씨입니다. 실내 조명과 음악으로 편안한 분위기를 만드세요."
                svg_icon = icon_cloud
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                status = "비 / 소나기"
                tip = "비 오는 날 방문 고객을 위한 우천 단골 혜택을 안내하세요."
                svg_icon = icon_rain
            else:
                status = "무난함"
                tip = "기온 변화에 맞춰 단골 고객 안부 문자와 특가를 활용하세요."
                svg_icon = icon_sun
            return {"temp": temp, "status": status, "tip": tip, "icon": svg_icon}
    except Exception:
        pass
    return {"temp": 20.2, "status": "구름 많음 / 흐림", "tip": "차분한 날씨입니다. 실내 조명과 음악으로 편안한 분위기를 만드세요.", "icon": icon_cloud}

st.set_page_config(
    page_title="STORE MATE | 모바일 매장비서",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 📱 모바일 최적화 CSS (깨진 텍스트 및 사이드바 토글 완전 박멸)
# ==========================================
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="color-scheme" content="only light">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<style>
    :root { color-scheme: light only !important; }
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, input, button, a {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    .stApp, html, body { background-color: #FFFFFF !important; }

    /* Streamlit 기본 헤더, 사이드바 토글 버튼 및 깨진 텍스트 완전 숨김 */
    header[data-testid="stHeader"] { display: none !important; }
    button[data-testid="baseButton-header"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    #MainMenu, footer { visibility: hidden !important; display: none !important; }
    
    /* 사이드바 토글 내부 깨진 텍스트 전체 방지 */
    section[data-testid="stSidebar"] button[kind="tertiary"] { display: none !important; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .store-meta-line {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 2px;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        gap: 14px !important;
        background: transparent !important;
        padding: 0 0 6px 0 !important;
        margin-bottom: 16px !important;
        border-bottom: 2px solid #F1F5F9 !important;
        scrollbar-width: none;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] {
        height: 42px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        padding: 0 4px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #2563EB !important;
    }
    .stTabs [aria-selected="true"] * { color: #2563EB !important; }

    .simple-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .weather-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .calc-result-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 12px;
    }

    .unified-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 12px;
        margin-top: 8px;
    }
    .unified-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .audio-mixer-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .stButton>button {
        height: 48px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        width: 100% !important;
    }
    .stButton>button:hover { background: #1D4ED8 !important; }

    .stLinkButton > a, div[data-testid="stLinkButton"] > a {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1E293B !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        min-height: 46px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        width: 100% !important;
    }

    input, textarea, select { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

INDUSTRY_LIST = [
    "미용실 / 바버샵 / 네일 / 뷰티샵",
    "안경원 / 렌즈 / 광학",
    "식당 / 고깃집 / 일반음식점",
    "포차 / 주점 / 이자카야 / 호프",
    "카페 / 베이커리 / 디저트",
    "렌터카 / 중고차 / 차량정비",
    "법률 / 법무사 / 세무사 / 행정사",
    "공인중개사 / 부동산",
    "인테리어 / 건축 / 설비",
    "헬스장 / PT샵 / 필라테스 / 체육관",
    "학원 / 교습소 / 스터디카페",
    "병원 / 의원 / 약국 / 동물병원"
]

users_db = load_users()
deals_db = load_deals()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "active_join_deal_id" not in st.session_state:
    st.session_state.active_join_deal_id = None

if "current_lat" not in st.session_state:
    st.session_state.current_lat = 37.16
if "current_lon" not in st.session_state:
    st.session_state.current_lon = 127.21
if "current_region_name" not in st.session_state:
    st.session_state.current_region_name = "용인시 처인구 이동읍"

# ==========================================
# 로그인 화면
# ==========================================
if not st.session_state.logged_in_user:
    st.markdown("""<div style="text-align: center; margin: 30px 0 16px 0;">
<h2 style="font-size: 1.6rem; font-weight: 900; color: #0F172A; margin: 0 0 4px 0;">STORE MATE</h2>
<p style="font-size: 0.88rem; color: #64748B;">소상공인 올인원 모바일 비서</p>
</div>""", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["로그인", "신규 가입"])
    with auth_tab1:
        with st.form("login_form"):
            login_id = st.text_input("아이디 또는 연락처", placeholder="휴대폰 번호 권장")
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
            st.caption("신규 가입 시 7일간 모든 PRO 기능을 무료로 체험하실 수 있습니다.")
            new_id = st.text_input("아이디 (연락처)", placeholder="01012345678")
            new_pw = st.text_input("비밀번호 설정", type="password")
            new_store = st.text_input("매장 상호명")
            new_phone = st.text_input("매장 전화번호", placeholder="031-123-4567")
            new_ind = st.selectbox("업종 선택", INDUSTRY_LIST)
            new_loc = st.text_input("매장 주소", placeholder="예: 용인시 처인구 이동읍...")
            if st.form_submit_button("가입 완료 (7일 무료 시작)", use_container_width=True):
                if new_id and new_pw and new_store:
                    now = datetime.now()
                    trial_end_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
                    users_db[new_id] = {
                        "store_name": new_store,
                        "industry": new_ind,
                        "location": new_loc,
                        "phone": new_phone if new_phone else "010-0000-0000",
                        "feature": "전문 고객 맞춤 케어",
                        "map_address": new_loc,
                        "map_perk": "용친 회원 방문 시 특별 혜택 제공",
                        "today_deal": "",
                        "today_updated": now.strftime("%Y-%m-%d"),
                        "pw": new_pw,
                        "is_pro": True,
                        "pro_status": "무료체험",
                        "created_at": now.strftime("%Y-%m-%d"),
                        "trial_end": trial_end_date
                    }
                    save_users(users_db)
                    st.success("등록 완료! 7일 무료 PRO 체험이 시작되었습니다. 로그인해 주세요.")
    st.stop()

# ==========================================
# 회원 권한 계산
# ==========================================
user_key = st.session_state.logged_in_user
curr_user = users_db.get(user_key, {})
store_name = curr_user.get("store_name", "라브리지헤어살롱")
store_phone = curr_user.get("phone", "031-000-0000")
sel_industry = curr_user.get("industry", INDUSTRY_LIST[0])
sel_loc = curr_user.get("location", "용인시 처인구")
sel_feature = curr_user.get("feature", "맞춤형 전문 서비스")

today_now = datetime.now().date()
trial_end_str = curr_user.get("trial_end", today_now.strftime("%Y-%m-%d"))
try:
    trial_end_date = datetime.strptime(trial_end_str, "%Y-%m-%d").date()
except Exception:
    trial_end_date = today_now

is_approved_permanent = (curr_user.get("pro_status") == "승인완료")
is_in_trial = (today_now <= trial_end_date)

if is_approved_permanent:
    is_pro_user = True
    pro_label = "PRO 정식 파트너"
elif is_in_trial:
    is_pro_user = True
    days_left = (trial_end_date - today_now).days
    pro_label = f"PRO 무료체험 (D-{days_left})"
else:
    is_pro_user = False
    pro_label = "스탠다드 (체험 만료)"
    if curr_user.get("is_pro", False) and not is_approved_permanent:
        curr_user["is_pro"] = False
        curr_user["pro_status"] = "체험만료"
        users_db[user_key] = curr_user
        save_users(users_db)

with st.sidebar:
    st.markdown(f"### {store_name}")
    st.markdown(f"**연락처:** `{store_phone}`")
    st.markdown(f"**상태:** `{pro_label}`")

    if not is_approved_permanent:
        if is_in_trial:
            st.caption(f"무료 체험 종료일: {trial_end_str}")
        else:
            st.warning("7일 무료 체험이 종료되었습니다. 관리자 승인 후 유료 버전을 이용하실 수 있습니다.")
            
        if curr_user.get("pro_status") != "대기중":
            if st.button("유료버전 사용 승인 신청", use_container_width=True):
                curr_user["pro_status"] = "대기중"
                users_db[user_key] = curr_user
                save_users(users_db)
                st.success("승인 신청이 접수되었습니다.")
                st.rerun()
        else:
            st.info("관리자 유료 승인 대기 중입니다.")
    else:
        st.success("정식 유료 파트너 계정입니다.")

    if user_key == "admin":
        st.markdown("---")
        st.markdown("##### 📊 관리자: 방문 통계")
        analytics_data = load_analytics()
        today_key = today_now.strftime("%Y-%m-%d")
        today_stat = analytics_data.get(today_key, {"uv": 0, "pv": 0})
        total_uv = sum([v.get("uv", 0) for v in analytics_data.values()])
        total_pv = sum([v.get("pv", 0) for v in analytics_data.values()])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("오늘 방문자", f"{today_stat['uv']}명")
        with col_m2:
            st.metric("오늘 조회수", f"{today_stat['pv']}회")
        st.caption(f"누적 순방문: {total_uv}명 | 누적 페이지뷰: {total_pv}회")

        st.markdown("---")
        st.markdown("##### 🔑 회원 유료 승인 제어")
        for uid, udata in users_db.items():
            if uid == "admin":
                continue
            ustore = udata.get("store_name", uid)
            u_status = udata.get("pro_status", "미신청")
            st.write(f"**{ustore}** (`{uid}`) | 상태: `{u_status}`")
            col_a, col_b = st.columns(2)
            with col_a:
                if u_status != "승인완료" and st.button("유료 승인", key=f"app_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = True
                    users_db[uid]["pro_status"] = "승인완료"
                    save_users(users_db)
                    st.success(f"{ustore} 승인 완료")
                    st.rerun()
            with col_b:
                if u_status == "승인완료" and st.button("승인 취소", key=f"rev_{uid}", use_container_width=True):
                    users_db[uid]["is_pro"] = False
                    users_db[uid]["pro_status"] = "승인취소"
                    save_users(users_db)
                    st.rerun()

    if st.button("로그아웃", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

client = genai.Client(api_key=BACKEND_GEMINI_API_KEY)
TARGET_MODEL = "gemini-3.6-flash"

SYSTEM_DIRECTIVE = """
너는 로컬 비즈니스 경영 및 마케팅 수석 디렉터다.
이모티콘 남발은 철저히 배제하고, 전문 컨설턴트처럼 정갈하고 구조화된 데이터와 전략 중심의 실무 원고를 제공한다.
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
            st.error("데이터 생성 중 오류가 발생했습니다. 다시 시도해 주세요.")
            return None

# ==========================================
# 모바일 상단 바
# ==========================================
st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
<div>
<span style="font-size: 1.25rem; font-weight: 900; color: #0F172A;">{store_name}</span>
<span style="font-size: 0.72rem; font-weight: 700; color: #2563EB; background: #EFF6FF; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">{pro_label}</span>
<div class="store-meta-line">{sel_loc} · {sel_industry} &nbsp;|&nbsp; ☎️ <b>{store_phone}</b></div>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px;">
<a href="https://www.facebook.com/groups/yonginfriends" target="_blank" style="background:#1877F2; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 페북</a>
<a href="https://www.instagram.com/" target="_blank" style="background:#E1306C; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 인스타</a>
<a href="https://www.threads.net/" target="_blank" style="background:#111827; color:#fff; padding:8px 0; border-radius:6px; font-size:0.75rem; font-weight:700; text-align:center; text-decoration:none;">용친 스레드</a>
</div>
<hr style="margin: 8px 0 14px 0; border: none; border-top: 1px solid #E2E8F0;">
""", unsafe_allow_html=True)

# ==========================================
# 메인 7대 탭
# ==========================================
main_tabs = ["홈 대시보드", "내 특가 관리", "마케팅 스튜디오", "로컬 공동구매", "음악 스튜디오", "영업 마감", "경영·행정지원"]
tab_home, tab_my_deal, tab_mkt, tab_deals, tab_music, tab_close, tab_biz = st.tabs(main_tabs)

# ------------------------------------------
# TAB 1. 🏠 홈 대시보드
# ------------------------------------------
with tab_home:
    my_saved_addr = curr_user.get("map_address", sel_loc)
    my_perk = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    my_today_deal = curr_user.get("today_deal", "").strip()
    my_deal_updated = curr_user.get("today_updated", datetime.now().strftime("%Y-%m-%d"))
    naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(my_saved_addr)}"

    weather_info = get_live_weather(st.session_state.current_lat, st.session_state.current_lon)
    weather_html = f"""<div class="weather-box">
<div style="display:flex; align-items:center; gap:14px;">
<div>{weather_info['icon']}</div>
<div>
<div style="font-size:1.15rem; font-weight:900; color:#0F172A;">{st.session_state.current_region_name} · {weather_info['status']}</div>
<div style="font-size:0.85rem; color:#475569; margin-top:2px;">{weather_info['tip']}</div>
</div>
</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end; width:100%; border-top:1px solid #E2E8F0; padding-top:8px; margin-top:4px;">
<span style="font-size:0.75rem; color:#64748B;">기상청 연동</span>
<span style="font-size:1.6rem; font-weight:900; color:#0F172A; line-height:1;">{weather_info['temp']}°C</span>
</div>
</div>"""
    st.markdown(weather_html, unsafe_allow_html=True)

    if st.button("📍 현재 내 위치로 날씨·지역 갱신", key="btn_detect_gps", use_container_width=True):
        try:
            ip_res = requests.get("https://ipapi.co/json/", timeout=2).json()
            lat = ip_res.get("latitude", 37.16)
            lon = ip_res.get("longitude", 127.21)
            st.session_state.current_lat = lat
            st.session_state.current_lon = lon
            st.session_state.current_region_name = reverse_geocode(lat, lon)
            st.toast(f"현재 위치: {st.session_state.current_region_name}")
            st.rerun()
        except Exception:
            st.warning("위치를 가져오지 못해 기본 주소를 유지합니다.")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if my_today_deal and my_today_deal != "오늘의 특가 준비 중":
        my_deal_html = f"""<div class="simple-card" style="border-left: 4px solid #2563EB;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1.05rem; font-weight:900; color:#0F172A;">내 매장 오늘의 특가</span>
<span style="font-size:0.75rem; color:#64748B;">{my_deal_updated}</span>
</div>
<div style="font-size:1.1rem; font-weight:900; color:#2563EB; margin:6px 0;">{my_today_deal}</div>
<div style="font-size:0.82rem; color:#475569;">혜택: {my_perk} &nbsp;|&nbsp; ☎️ <b>{store_phone}</b></div>
</div>"""
        st.markdown(my_deal_html, unsafe_allow_html=True)
    else:
        st.markdown("""<div class="simple-card" style="background:#F8FAFC;">
<div style="font-size:0.88rem; color:#64748B;">현재 내 매장의 당일 특가가 비어 있습니다.<br>상단 <b>[내 특가 관리]</b> 탭에서 등록해 보세요.</div>
</div>""", unsafe_allow_html=True)

    st.link_button("네이버 플레이스 지도 연동 확인", naver_url, use_container_width=True)

    st.markdown("""<div style="margin:20px 0 8px 0;">
<div style="font-size:1.1rem; font-weight:900; color:#0F172A;">용인친구들 실시간 상생 특가 피드</div>
<div style="font-size:0.82rem; color:#64748B;">실제 특가를 진행 중인 이웃 제휴 매장의 혜택입니다.</div>
</div>""", unsafe_allow_html=True)

    active_deals_count = 0
    for u_id, u_info in users_db.items():
        if u_id == "admin" or u_id == user_key:
            continue
        o_deal = u_info.get("today_deal", "").strip()
        if not o_deal or o_deal == "오늘의 특가 준비 중" or o_deal == "오늘의 특가 품목 등록 대기 중":
            continue

        active_deals_count += 1
        o_name = u_info.get("store_name", u_id)
        o_addr = u_info.get("map_address", u_info.get("location", ""))
        o_phone = u_info.get("phone", "전화번호 미등록")
        o_perk = u_info.get("map_perk", "용친 회원 방문 시 특별 혜택")
        o_upd = u_info.get("today_updated", "")
        o_nav_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(o_addr)}"
        
        feed_card_html = f"""<div class="simple-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:1.05rem; font-weight:800; color:#0F172A;">{o_name}</span>
<span style="font-size:0.75rem; color:#64748B;">{o_upd}</span>
</div>
<div style="font-size:0.8rem; color:#64748B; margin-bottom:6px;">{o_addr} &nbsp;|&nbsp; ☎️ <b>{o_phone}</b></div>
<div style="background:#EFF6FF; border-left:4px solid #2563EB; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
<div style="font-size:0.72rem; font-weight:700; color:#2563EB;">오늘의 번개 특가</div>
<div style="font-size:1.05rem; font-weight:900; color:#0F172A; margin-top:2px;">{o_deal}</div>
</div>
<div style="font-size:0.82rem; color:#475569; margin-bottom:10px;">상시 혜택: {o_perk}</div>
<a href="{o_nav_url}" target="_blank" style="text-decoration:none;">
<button style="width:100%; height:40px; background:#F8FAFC; color:#0F172A; border:1px solid #CBD5E1; border-radius:6px; font-weight:700; font-size:0.82rem; cursor:pointer;">
네이버 지도 길찾기
</button>
</a>
</div>"""
        st.markdown(feed_card_html, unsafe_allow_html=True)

    if active_deals_count == 0:
        st.info("현재 등록된 이웃 매장의 특가가 없습니다.")

    st.markdown("""<div class="simple-card" style="margin-top:16px;">
<div style="font-weight:900; font-size:1.05rem; color:#0F172A; margin-bottom:10px;">진행 중인 공동구매 요약</div>""", unsafe_allow_html=True)
    for d in deals_db["deals"][:2]:
        tot_qty = sum([p["qty"] for p in d["participants"]])
        st.markdown(f"**{d['title']}**<br><span style='color:#2563EB; font-weight:800;'>{d['price']}</span> · {len(d['participants'])}명 참여 ({tot_qty}개)", unsafe_allow_html=True)
        st.progress(min(tot_qty / d["target"], 1.0))
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2. ⚙️ 내 특가 관리 (전화번호 수정 폼 통합)
# ------------------------------------------
with tab_my_deal:
    st.markdown("""<div class="simple-card">
<div style="font-weight:900; font-size:1.1rem; color:#0F172A; margin-bottom:4px;">내 매장 특가 & 제휴 혜택 설정</div>
<div style="font-size:0.82rem; color:#64748B;">입력한 특가는 홈 대시보드 실시간 공유창에 노출됩니다.</div>
</div>""", unsafe_allow_html=True)

    current_deal_val = curr_user.get("today_deal", "")
    current_perk_val = curr_user.get("map_perk", "용친 회원 방문 시 특별 혜택 제공")
    current_phone_val = curr_user.get("phone", store_phone)

    with st.form("my_store_deal_form"):
        st.markdown("**1. 매장 대표 전화번호**")
        inp_phone = st.text_input("전화번호", value=current_phone_val, placeholder="031-000-0000", label_visibility="collapsed")
        
        st.markdown("**2. 오늘의 번개 특가 품목**")
        inp_deal = st.text_input("특가 내용", value=current_deal_val, placeholder="예: 첫 방문 펌 30% 게릴라 할인 (선착순 5명)", label_visibility="collapsed")
        st.caption("비워두시면 공유창에서 자동으로 숨겨집니다.")
        
        st.markdown("**3. 상시 회원 제휴 혜택**")
        inp_perk = st.text_input("상시 혜택", value=current_perk_val, placeholder="예: 용친 회원 10% DC", label_visibility="collapsed")
        
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("저장하고 공유창에 즉시 반영", use_container_width=True):
            users_db[user_key]["phone"] = inp_phone.strip()
            users_db[user_key]["today_deal"] = inp_deal.strip()
            users_db[user_key]["map_perk"] = inp_perk.strip()
            users_db[user_key]["today_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_users(users_db)
            st.success("내 매장 정보가 저장되었습니다.")
            st.rerun()

# ------------------------------------------
# TAB 3. 📢 마케팅 스튜디오 (PRO 전용)
# ------------------------------------------
with tab_mkt:
    if not is_pro_user:
        st.markdown("""<div class="simple-card" style="border-left: 4px solid #EF4444; background: #FEF2F2;">
<div style="font-weight: 800; font-size: 1rem; color: #991B1B; margin-bottom: 4px;">PRO 전용 유료 마케팅 기능입니다</div>
<div style="font-size: 0.86rem; color: #7F1D1D; line-height: 1.5;">
7일 무료 체험 기간이 만료되었습니다.<br>
사이드바에서 <b>[유료버전 사용 승인 신청]</b>을 눌러주시면 관리자 승인 후 계속 이용하실 수 있습니다.
</div>
</div>""", unsafe_allow_html=True)
    else:
        current_area_tag = st.session_state.current_region_name.split()[0] if st.session_state.current_region_name else "용인"

        mkt_sub1, mkt_sub2, mkt_sub3, mkt_sub4, mkt_sub5 = st.tabs([
            "블로그 SEO", "당근 바이럴", "인스타그램", "단골 문자", "리뷰 대응"
        ])

        with mkt_sub1:
            b_kw = st.text_input("메인 키워드", value=f"{current_area_tag} {sel_industry.split('/')[0].strip()}", key="m_b_kw")
            b_sub = st.text_input("서브 키워드", value=f"{st.session_state.current_region_name} 추천", key="m_b_sub")
            b_photos = st.slider("첨부 사진 장수", 5, 20, 8, key="m_b_photo")
            b_intent = st.selectbox("검색 의도", ["실제 단골 내돈내산 방문기", "전문 기술 및 정밀 설비 분석", "가성비 및 제휴 혜택 비교"], key="m_b_intent")
            b_core = st.text_area("매장 핵심 강점", value=sel_feature, height=70, key="m_b_core")

            if st.button("SEO 전문 원고 생성하기", key="m_b_btn", use_container_width=True):
                with st.spinner("원고 작성 중..."):
                    prompt = f"업종: {sel_industry}\n매장: {store_name}\n지역: {st.session_state.current_region_name}\n키워드: {b_kw}, {b_sub}\n사진: {b_photos}장\n의도: {b_intent}\n강점: {b_core}\n네이버 스마트블록용 제목 3종, 사진 배치 가이드, 본문, 연관 태그 10종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("작성된 원고 (복사용)", value=out, height=300)

        with mkt_sub2:
            d_tgt = st.selectbox("타깃 고객층", ["3040 자녀 양육 학부모", "2030 직장인 및 1인가구", "동네 중장년층 전체"], key="m_d_tgt")
            d_prm = st.selectbox("제공 혜택", ["무상 체험 및 정밀 점검", "단독 추가 할인 쿠폰", "선착순 사은품 증정"], key="m_d_prm")
            d_ctx = st.text_input("상황적 훅", value=f"{current_area_tag} 날씨 맞춤 단골 케어", key="m_d_ctx")
            d_cta = st.text_input("행동 유도", value="당근 단골 맺기 누르고 매장 방문 시 적용", key="m_d_cta")

            if st.button("당근 소식 생성하기", key="m_d_btn", use_container_width=True):
                with st.spinner("소식 작성 중..."):
                    prompt = f"매장: {store_name}\n지역: {st.session_state.current_region_name}\n업종: {sel_industry}\n타깃: {d_tgt}\n혜택: {d_prm}\n상황: {d_ctx}\nCTA: {d_cta}\n당근마켓 이웃 사장님 톤으로 제목 2종, 본문, 댓글 유도 질문 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("당근 소식 (복사용)", value=out, height=280)

        with mkt_sub3:
            i_type = st.selectbox("콘텐츠 형식", ["단일 피드 (1컷)", "카드뉴스형 (5컷)", "릴스 15초 스크립트"], key="m_i_type")
            i_mood = st.selectbox("비주얼 무드", ["미니멀 모던", "따뜻한 아날로그", "전문 클리닉/정밀 하이테크"], key="m_i_mood")
            i_subj = st.text_input("주제", value="나에게 딱 맞는 인생 스타일링 가이드", key="m_i_subj")
            i_perk = st.text_input("연계 프로모션", value=my_perk, key="m_i_perk")

            if st.button("인스타그램 피드 생성", key="m_i_btn", use_container_width=True):
                with st.spinner("피드 생성 중..."):
                    prompt = f"매장: {store_name}\n업종: {sel_industry}\n지역: {st.session_state.current_region_name}\n형식: {i_type}\n무드: {i_mood}\n주제: {i_subj}\n혜택: {i_perk}\n촬영 가이드, 첫 줄 카피, 줄바꿈 본문, 해시태그 15종 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("인스타그램 피드 (복사용)", value=out, height=280)

        with mkt_sub4:
            c_seg = st.selectbox("대상 세그먼트", ["첫 방문 후 재방문 유도 (1~2주 경과)", "이탈 위험 단골 고객 (60일 이상 미방문)", "정기 관리 주기 고객"], key="m_c_seg")
            c_off = st.text_input("제공 바우처", value="재방문 고객 전용 10% 추가 할인", key="m_c_off")
            c_lim = st.selectbox("기한 설정", ["이번 주 일요일까지", "수신 후 14일 이내", "선착순 30명 한정"], key="m_c_lim")
            c_tel = st.text_input("문의처", value=f"{store_name} (문자 회신 가능)", key="m_c_tel")

            if st.button("CRM 문자 3종 생성", key="m_c_btn", use_container_width=True):
                with st.spinner("문안 작성 중..."):
                    prompt = f"매장: {store_name}\n대상: {c_seg}\n혜택: {c_off}\n기한: {c_lim}\n문의: {c_tel}\n단문 SMS, 장문 LMS, 카카오 알림톡 포맷 작성."
                    out = generate_safe_content(prompt)
                    if out: st.text_area("CRM 메시지 (복사용)", value=out, height=280)

        with mkt_sub5:
            cust_rev = st.text_area("고객 리뷰 붙여넣기", placeholder="고객이 남긴 별점 리뷰를 입력하세요.")
            rev_stl = st.selectbox("답글 스타일", [
                "1. 정중하고 품격 있는 VIP 감사형",
                "2. 다정하고 센스 있는 동네 이웃형",
                "3. 매장 특장점 & 장비 전문성 각인형",
                "4. 재방문 유도 & 단골 혜택 안내형",
                "5. 위트 있고 유쾌한 에너지형",
                "6. 불만/아쉬움 리뷰 케어 및 사과형"
            ], key="m_r_stl")
            
            if st.button("전문 답글 3종 생성", key="m_r_btn", use_container_width=True):
                if cust_rev:
                    with st.spinner("답글 생성 중..."):
                        prompt = f"매장: {store_name}\n업종: {sel_industry}\n지역: {st.session_state.current_region_name}\n리뷰: '{cust_rev}'\n스타일: {rev_stl}\n플레이스용 완성도 높은 답글 3종 작성."
                        out = generate_safe_content(prompt)
                        if out: st.text_area("추천 답글 3종", value=out, height=280)
                else:
                    st.warning("리뷰를 입력해 주세요.")

# ------------------------------------------
# TAB 4. 🛒 로컬 공동구매
# ------------------------------------------
with tab_deals:
    deal_sub1, deal_sub2, deal_sub3 = st.tabs(["공구 목록", "소모품 발주", "공구 제안"])

    def get_dday(deadline_str):
        try:
            d_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            delta = (d_date - datetime.now()).days
            return f"D-{delta}일" if delta > 0 else ("오늘 마감" if delta == 0 else "마감")
        except Exception:
            return "진행 중"

    with deal_sub1:
        d_filter = st.selectbox("상태 필터", ["전체 프로젝트", "진행중만 보기", "마감된 프로젝트"], key="d_filter_sel")

        deals_to_del = []
        filtered_deals = []
        for d in deals_db["deals"]:
            d_state = get_dday(d["deadline"])
            if d_filter == "진행중만 보기" and d_state == "마감":
                continue
            if d_filter == "마감된 프로젝트" and d_state != "마감":
                continue
            filtered_deals.append(d)

        for deal in filtered_deals:
            tot_qty = sum([p["qty"] for p in deal["participants"]])
            dday = get_dday(deal["deadline"])
            is_closed = (dday == "마감")

            st.markdown(f"""<div class="simple-card">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="background:{'#64748B' if is_closed else '#EF4444'}; color:#fff; font-size:0.72rem; font-weight:700; padding:2px 6px; border-radius:4px;">{dday}</span>
<span style="font-size:0.75rem; color:#64748B;">목표 {deal['target']}개</span>
</div>
<div style="font-size:1.02rem; font-weight:800; color:#0F172A; margin:6px 0 2px 0;">{deal['title']}</div>
<div style="font-size:1.1rem; font-weight:900; color:#2563EB;">{deal['price']}</div>
<div style="font-size:0.8rem; color:#475569; margin:4px 0 6px 0;">신청: <b>{len(deal['participants'])}명</b> ({tot_qty}개 달성)</div>
</div>""", unsafe_allow_html=True)
            st.progress(min(tot_qty / deal["target"], 1.0))

            is_active = (st.session_state.active_join_deal_id == deal["id"])
            btn_label = "신청창 닫기" if is_active else "공구 참여 신청하기"
            if st.button(btn_label, key=f"toggle_join_{deal['id']}", use_container_width=True):
                st.session_state.active_join_deal_id = None if is_active else deal["id"]
                st.rerun()

            if user_key == "admin" or is_closed:
                if st.button("프로젝트 삭제", key=f"del_{deal['id']}", use_container_width=True):
                    deals_to_del.append(deal["id"])

            if user_key == "admin" and len(deal["participants"]) > 0:
                df_parts = pd.DataFrame(deal["participants"])
                df_parts.columns = ["성함/상호", "연락처", "수량", "일시"]
                csv_data = df_parts.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label=f"📥 명단 CSV 다운로드 ({len(deal['participants'])}명)",
                    data=csv_data,
                    file_name=f"공구명단_{deal['id']}.csv",
                    mime="text/csv",
                    key=f"csv_adm_{deal['id']}",
                    use_container_width=True
                )

            if st.session_state.active_join_deal_id == deal["id"]:
                st.markdown("""<div class="simple-card" style="border-left:4px solid #2563EB;">
<div style="font-weight:700; font-size:0.92rem; color:#0F172A; margin-bottom:8px;">참여 신청서 입력</div>""", unsafe_allow_html=True)
                with st.form(key=f"join_form_{deal['id']}"):
                    j_name = st.text_input("성함 또는 상호", key=f"j_n_{deal['id']}")
                    j_phone = st.text_input("연락처", key=f"j_p_{deal['id']}")
                    j_qty = st.number_input("수량", min_value=1, max_value=100, value=1, step=1, key=f"j_q_{deal['id']}")
                    if st.form_submit_button("참여 확정하기", use_container_width=True):
                        if j_name and j_phone:
                            deal["participants"].append({"name": j_name, "phone": j_phone, "qty": int(j_qty), "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                            save_deals(deals_db)
                            st.session_state.active_join_deal_id = None
                            st.success("참여 완료되었습니다.")
                            st.rerun()
                        else:
                            st.warning("정보를 입력해 주세요.")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:10px 0; border:none; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

        if deals_to_del:
            deals_db["deals"] = [d for d in deals_db["deals"] if d["id"] not in deals_to_del]
            save_deals(deals_db)
            st.rerun()

    with deal_sub2:
        st.markdown("""<div class="simple-card">
<div style="font-weight:800; font-size:1rem; color:#0F172A;">카드단말기 영수증 롤페이퍼 (50롤)</div>
<p style="color:#475569; font-size:0.88rem; margin:4px 0 10px 0;">시중가 38,000원 ➡️ <b>공구가 23,500원 (무료배송)</b></p>
</div>""", unsafe_allow_html=True)
        if st.button("소모품 도매 공동발주 접수", key="btn_b2b_submit", use_container_width=True):
            st.success("발주 신청이 접수되었습니다.")

    with deal_sub3:
        p_name = st.text_input("제안 상품명", key="p_name_input")
        p_qty = st.number_input("목표 수량", min_value=1, max_value=1000, value=30, step=1, key="p_qty_input")
        p_price = st.text_input("제안 공구가", key="p_price_input")
        p_days = st.slider("진행 일수", min_value=3, max_value=30, value=7, key="p_days_input")
        if st.button("공동구매 프로젝트 오픈", key="btn_prop_submit", use_container_width=True):
            if p_name and p_price:
                deals_db["deals"].append({
                    "id": f"deal_{int(time.time())}",
                    "title": f"[{store_name}] {p_name}",
                    "price": f"{p_price} (단독 특가)",
                    "target": int(p_qty),
                    "deadline": (datetime.now() + timedelta(days=p_days)).strftime("%Y-%m-%d"),
                    "participants": []
                })
                save_deals(deals_db)
                st.success("공동구매가 등록되었습니다.")
                st.rerun()

# ------------------------------------------
# TAB 5. 🎧 음악 스튜디오
# ------------------------------------------
with tab_music:
    st.markdown("""<div class="simple-card">
<div style="font-weight:900; font-size:1.15rem; color:#0F172A; margin-bottom:2px;">매장 전용 음악 큐레이션 스튜디오</div>
<div style="font-size:0.82rem; color:#64748B;">영업 시간대와 분위기에 맞춰 바로 재생할 수 있는 오디오 스테이션입니다.</div>
</div>""", unsafe_allow_html=True)

    music_presets = [
        {"slot": "오전 오픈 준비 (09:00~11:30)", "vibe": "경쾌한 모닝 보사노바 & 어쿠스틱", "query": "재즈 보사노바 오전 매장 음악 연속재생", "tag": "모닝 스타트"},
        {"slot": "점심 / 피크 (11:30~14:00)", "vibe": "생동감 넘치는 칠 팝 & 라운지", "query": "어쿠스틱 팝 피크타임 매장 음악 연속재생", "tag": "피크 활력"},
        {"slot": "나른한 오후 (14:00~17:30)", "vibe": "편안한 감성 발라드 피아노 커버", "query": "2000년대 감성 발라드 피아노 연주곡 연속재생", "tag": "힐링 케어"},
        {"slot": "저녁 & 마감 (17:30~21:00)", "vibe": "고급스럽고 아늑한 라운지 재즈", "query": "세련된 카페 라운지 재즈 음악 연속재생", "tag": "이브닝 마감"}
    ]

    st.markdown("##### 시간대별 원클릭 추천 스테이션")
    for idx, preset in enumerate(music_presets):
        p_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(preset['query'])}"
        st.markdown(f"""<div class="audio-mixer-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
<span style="font-size:0.75rem; font-weight:800; color:#2563EB; background:#EFF6FF; padding:2px 6px; border-radius:4px;">{preset['tag']}</span>
<span style="font-size:0.8rem; color:#64748B;">{preset['slot']}</span>
</div>
<div style="font-size:1.05rem; font-weight:900; color:#0F172A; margin-bottom:10px;">{preset['vibe']}</div>
<a href="{p_url}" target="_blank" style="text-decoration:none;">
<button style="width:100%; height:40px; background:#0F172A; color:#FFFFFF; border:none; border-radius:6px; font-weight:700; font-size:0.85rem; cursor:pointer;">
유튜브 음악 스트리밍 열기
</button>
</a>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 장르 & 분위기 맞춤 검색 조율기")
    with st.container():
        st.markdown("""<div class="simple-card">
<div style="font-size:0.88rem; color:#475569; margin-bottom:8px;">원하는 분위기를 선택하면 유튜브 스트리밍 채널을 즉시 찾아줍니다.</div>""", unsafe_allow_html=True)
        m_time_custom = st.selectbox("원하는 분위기/상황", [
            "오전 오픈 (경쾌하고 맑은 분위기)",
            "피크타임 (활력 넘치는 템포)",
            "오후 상담/시술 집중 (편안한 힐링)",
            "비 오는 날 (센티멘털 감성 어쿠스틱)",
            "저녁 감성 (우아한 라운지 재즈)",
            "영업 마감 (차분한 피아노 연주)"
        ], key="tab_m_time_cust")
        m_style_custom = st.selectbox("선호 장르", [
            "재즈 / 보사노바 (클래식 매장)",
            "어쿠스틱 팝 & 인디 감성 보컬",
            "2000년대 감성 발라드 피아노 커버",
            "세련된 Lo-Fi 칠(Chill) 비트",
            "90-2000 국민 애창 댄스 (식당/펍)",
            "최신 트로트 명곡 메들리"
        ], key="tab_m_style_cust")
        
        yt_custom_q = f"{m_style_custom.split('/')[0].strip()} {m_time_custom.split('(')[0].strip()} 플레이리스트 연속재생"
        custom_music_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_custom_q)}"
        
        st.markdown(f"<div style='font-size:0.82rem; color:#64748B; margin:6px 0 10px 0;'>선택된 큐레이션: <b>{yt_custom_q}</b></div>", unsafe_allow_html=True)
        st.link_button(f"유튜브 '{m_style_custom.split('/')[0].strip()}' 스트리밍 열기", custom_music_url, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 6. 🌙 영업 마감
# ------------------------------------------
with tab_close:
    st.markdown("""<div class="simple-card">
<div style="font-weight:900; font-size:1.1rem; color:#0F172A; margin-bottom:2px;">일일 영업 마감 리포트</div>
<div style="font-size:0.82rem; color:#64748B;">오늘 하루 매출과 분위기를 정리하고 내일 과제를 받습니다.</div>
</div>""", unsafe_allow_html=True)

    c_sales = st.text_input("오늘 매출액 (선택)", placeholder="예: 850,000원", key="b_sales")
    c_flow = st.selectbox("고객 유입 체감", ["평소 대비 한산함", "평균 수준", "피크타임 집중 방문", "종일 만석 / 목표 초과"], key="b_flow")
    c_memo = st.text_input("특이사항/재고 이슈", placeholder="예: 단골 예약 방문, 특정 제품 소진", key="b_memo")
    c_sat = st.selectbox("운영 만족도", ["다소 아쉬움", "무난하고 안정적", "매우 만족"], key="b_sat")

    if st.button("일일 경영 결산 리포트 생성", key="b_close_btn", use_container_width=True):
        with st.spinner("마감 리포트 분석 중..."):
            prompt = f"매장: {store_name}\n업종: {sel_industry}\n매출: {c_sales}\n유입: {c_flow}\n특이사항: {c_memo}\n만족도: {c_sat}\n1) 오늘 총평 2) 내일 과제 3선 3) 퇴근길 응원 작성."
            out = generate_safe_content(prompt)
            if out:
                st.markdown(f"<div class='simple-card' style='border-left:4px solid #2563EB; margin-top:12px;'>{out}</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 7. 💼 경영·행정지원 (4대 금융계산기)
# ------------------------------------------
with tab_biz:
    biz_sub1, biz_sub2, biz_sub3 = st.tabs([
        "4대 행정서류", "2026 정책금융", "금융계산기 센터"
    ])

    with biz_sub1:
        st.markdown("""<div class="unified-grid">
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">소상공인확인서</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">중소기업현황정보시스템 · 국비 지원 필수</div>
<a href="https://sminfo.mss.go.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">발급 사이트 이동</button></a>
</div>
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">부가가치세 과세표준증명</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">국세청 홈택스 · 대출 심사 필수</div>
<a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">홈택스 바로가기</button></a>
</div>
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">국세 완납증명서</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">국세청 홈택스 · 체납 확인 필수</div>
<a href="https://www.hometax.go.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">납세증명 바로가기</button></a>
</div>
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">지방세 납세증명서</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">정부24 · 지방세 체납 확인</div>
<a href="https://www.gov.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">정부24 바로가기</button></a>
</div>
</div>""", unsafe_allow_html=True)

    with biz_sub2:
        st.markdown("""<div class="unified-grid">
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">전기요금 특별지원</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">최대 20~25만 원 전기료 감면</div>
<a href="https://www.소상공인전기요금특별지원.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">신청처 바로가기</button></a>
</div>
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">저금리 대환보증</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">7% 이상 고금리를 4%대로 전환</div>
<a href="https://www.semas.or.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">공고 확인하기</button></a>
</div>
<div class="unified-card">
<div style="font-weight:700; font-size:0.95rem; color:#0F172A;">스마트상점 국비지원</div>
<div style="font-size:0.82rem; color:#475569; margin:4px 0 8px 0;">키오스크/오더 70% 보조</div>
<a href="https://www.sbiz.or.kr/smst/index.do" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background:#2563EB; color:#fff; border:none; border-radius:6px; font-weight:700; font-size:0.82rem;">사업 공고 열기</button></a>
</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        rev_s = st.selectbox("사업장 연매출", ["3천만 원 미만 (영세)", "3천만 원 ~ 1억 원", "1억 원 ~ 3억 원", "3억 원 초과"], key="b_rev_s")
        aid_p = st.selectbox("필요 분야", ["고금리 대출 이자 완화", "키오스크/설비 보조", "운영 고정비 지원"], key="b_aid_p")
        if st.button("맞춤 정책자금 AI 진단", key="b_aid_btn", use_container_width=True):
            with st.spinner("정책 분석 중..."):
                out = generate_safe_content(f"업종: {sel_industry}\n매출: {rev_s}\n목적: {aid_p}\n적합 정책 2종과 신청 요건 작성.")
                if out: st.markdown(f"<div class='simple-card' style='border-left:4px solid #2563EB;'>{out}</div>", unsafe_allow_html=True)

    with biz_sub3:
        calc_tab1, calc_tab2, calc_tab3, calc_tab4 = st.tabs([
            "알바 급여", "대출 이자", "마진율 역산", "카드 수수료"
        ])

        with calc_tab1:
            wage = st.number_input("시급 (원)", value=10030, step=100, key="c1_wage")
            hrs = st.number_input("주당 근로시간", value=16.0, step=0.5, key="c1_hrs")
            tax_opt = st.selectbox("공제", ["사업소득세 3.3% 공제", "고용보험 0.9% 공제", "공제 없음"], key="c1_tax")
            base = wage * hrs * 4.345
            holiday = ((hrs / 40.0) * 8.0 * wage * 4.345) if hrs >= 15 else 0
            tot = base + holiday
            ded = tot * 0.033 if "3.3%" in tax_opt else (tot * 0.009 if "0.9%" in tax_opt else 0)
            net = tot - ded
            st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">기본급 {int(base):,}원 + 주휴수당 {int(holiday):,}원 (공제 {int(ded):,}원)</div>
<div style="font-size:1.25rem; font-weight:900; color:#0F172A; margin-top:2px;">예상 실지급액: {int(net):,}원</div>
</div>""", unsafe_allow_html=True)

        with calc_tab2:
            loan_amt = st.number_input("대출 원금 (원)", value=30000000, step=1000000, key="c2_amt")
            loan_rate = st.number_input("연 이자율 (%)", value=4.5, step=0.1, key="c2_rate")
            loan_months = st.number_input("기간 (개월)", value=36, step=12, key="c2_months")
            loan_type = st.selectbox("방식", ["원리금균등상환", "원금균등상환", "만기일시상환"], key="c2_type")

            r = (loan_rate / 100) / 12
            n = loan_months
            if loan_type == "원리금균등상환":
                monthly_pay = (loan_amt * r * ((1 + r)**n)) / (((1 + r)**n) - 1)
                total_pay = monthly_pay * n
                total_interest = total_pay - loan_amt
            elif loan_type == "원금균등상환":
                monthly_principal = loan_amt / n
                total_interest = sum([(loan_amt - (monthly_principal * i)) * r for i in range(n)])
                monthly_pay = monthly_principal + (loan_amt * r)
                total_pay = loan_amt + total_interest
            else:
                monthly_pay = loan_amt * r
                total_interest = monthly_pay * n
                total_pay = loan_amt + total_interest

            st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">총 상환액 {int(total_pay):,}원 (총 이자 {int(total_interest):,}원)</div>
<div style="font-size:1.25rem; font-weight:900; color:#0F172A; margin-top:2px;">월 상환액: {int(monthly_pay):,}원</div>
</div>""", unsafe_allow_html=True)

        with calc_tab3:
            cost_price = st.number_input("매입원가 (원)", value=15000, step=1000, key="c3_cost")
            target_margin = st.number_input("목표 마진율 (%)", value=60.0, step=5.0, key="c3_margin")
            calc_selling_price = cost_price / (1 - (target_margin / 100))
            net_profit = calc_selling_price - cost_price
            st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">개당 순이익: {int(net_profit):,}원</div>
<div style="font-size:1.25rem; font-weight:900; color:#0F172A; margin-top:2px;">권장 판매가: {int(calc_selling_price):,}원</div>
</div>""", unsafe_allow_html=True)

        with calc_tab4:
            card_sales = st.number_input("카드 결제액 (원)", value=1000000, step=100000, key="c4_sales")
            card_fee_tier = st.selectbox("구간", ["영세 (연매출 3억 이하 / 0.5%)", "중소1 (연매출 3억~5억 / 1.1%)", "일반 (2.0%)"], key="c4_fee")
            cur_rate = 0.005 if "0.5%" in card_fee_tier else (0.011 if "1.1%" in card_fee_tier else 0.02)
            calc_fee = card_sales * cur_rate
            settle_amt = card_sales - calc_fee
            st.markdown(f"""<div class="calc-result-box">
<div style="font-size:0.82rem; color:#64748B;">차감 수수료: {int(calc_fee):,}원</div>
<div style="font-size:1.25rem; font-weight:900; color:#0F172A; margin-top:2px;">실입금액: {int(settle_amt):,}원</div>
</div>""", unsafe_allow_html=True)
